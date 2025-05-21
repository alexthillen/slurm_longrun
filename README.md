## Slurm Longrun

Slurm Longrun is a Python package that wraps Slurm’s `sbatch` command to automatically resubmit jobs that time out, allowing you to run workloads that exceed a single‐job walltime without manual intervention. It supports optional terminal detachment (so your monitor survives after you log out), configurable retry limits, and built-in logging via Loguru.

This tool was developed as a project for the [Large-Scale AI Engineering](https://ai.ethz.ch/education/courses/large-scale-ai-engineering.html) course on the CSCS Alps supercomputer.

---

## Installation

Prerequisites  
- Python 3.10+  
- Slurm workload manager (`sbatch`, `sacct`, `scontrol` in your `PATH`)  

Install from PyPI:  
```bash
pip install slurm-longrun
```

---

## Quickstart

Instead of calling `sbatch` directly, use the `sbatch_longrun` wrapper:

```bash
sbatch_longrun [OPTIONS] [SBATCH_ARGS…]
```


Example: your job runs longer than 30 minutes, so you give it a 30 min walltime and let Longrun resubmit on timeout:

```bash
sbatch_longrun --max-restarts 999 --time=00:30:00 --job-name=my_job my_script.sbatch
#sbatch_longrun <thiswrapperargs> <=========sbatch args===========> <===script.sh==>
```

This will:  
1. Submit `my_script.sbatch` with a 30 min limit.  
2. When it hits the 30 min walltime (`TIMEOUT`), automatically resubmit (opens log file in append mode).  
3. Resubmit up to 999 times or until the job completes successfully.

---

## Command-Line Interface

Usage  
```bash
sbatch_longrun [OPTIONS] [SBATCH_ARGS…]
```

Options  
-  `--use-verbosity [DEFAULT|VERBOSE|SILENT]`  
 Logging level (DEFAULT = INFO, VERBOSE = DEBUG, SILENT = WARNING).  
-  `--detached / --no-detached`  
 Run the monitor loop in background (detached from your terminal).  
-  `--max-restarts INTEGER`  
 Maximum number of resubmissions on `JobStatus.should_resubmit`. Default: 999.  
-  `-h, --help`  
 Show help and exit.  

All other flags are forwarded to `sbatch`, they must be provided **after** the wrapper flags. 

### Examples

1. Basic, retry up to 3 times, verbose logging:  
   ```bash
   sbatch_longrun --use-verbosity VERBOSE --max-restarts 3 \
     --time=02:00:00 --job-name=deep_train train.sbatch
   ```

   `--use-verbosity VERBOSE --max-restarts 3` are passed to the monitor process.
   `--time=02:00:00 --job-name=deep_train` are passed to `sbatch`.

2. Detach the monitor so it survives logout:  
   ```bash
   sbatch_longrun --detached  \
     --time=01:00:00 --job-name=data_proc data_pipeline.sbatch
   # → prints “Monitor running in background PID: ”
   ```

---

### Example : Assignment 2

Assignment 2 is training an LLM over 1000 epochs. To showcase the resubmission feature, I set the walltime to 3 minutes.
Further, I sent a signal to the job 20 seconds before the walltime limit. I use the signal to save the state of the training run.

**Submission**

```sh
sbatch_longrun --signal=SIGTERM@20  example/assignment2_example/run_job.sbatch
```

using the following file:

```bash
# example/assignment2_example/run_job.sbatch

#!/bin/bash
#SBATCH --account=a-large-sc
#SBATCH --job-name=sbatch_longrun_example_assignment2
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --time=00:03:00
#SBATCH --output=run_example_assignment2.log
#SBATCH --error=run_example_assignment2.err
#SBATCH --partition=debug
#SBATCH --environment=/path/to/.../ngc_pt_jan.toml
#SBATCH --export=ALL

set -eo pipefail
echo "START TIME: $(date)"

srun bash -c "python $SLURM_SUBMIT_DIR/example/assignment2_example/assignment_2/train.py \
    --learning-rate 5e-5 \
    --training-steps 1000 \
    --batch-size 1 \
    --lr-warmup-steps 100"

echo "END TIME: $(date)"
```

**Checkpointing** in `train.py`:

```python
############################## LONGRUN : SAVE & RECOVER STATE ##############################
def store_state(
    filepath: str, epoch: int, model: torch.nn.Module, strip_dp: bool = True
) -> None:
    """Save the last completed epoch and model weights to disk."""
    state_dict = (
        model.module.state_dict()
        if strip_dp and hasattr(model, "module")
        else model.state_dict()
    )
    torch.save({"epoch": epoch, "model_state_dict": state_dict}, filepath)


def recover_state(
    filepath: str, device: str = "cpu"
) -> Tuple[int, Dict[str, torch.Tensor]]:
    """Load and return (last_epoch, model_state_dict) from a checkpoint."""
    if not os.path.exists(filepath):
        return 0, None
    ckpt = torch.load(filepath, map_location=device)
    return ckpt["epoch"], ckpt["model_state_dict"]

STATE_PATH = f"{os.environ.get("SLURM_SUBMIT_DIR", ".")}/state-{os.environ.get("SLURM_LONGRUN_INITIAL_JOB_ID", os.environ.get("SLURM_JOB_ID", ""))}.json"
############################## END LONGRUN : SAVE & RECOVER STATE ##########################

def train(args):
    ...
    ############################## END LONGRUN : SAVE & RECOVER STATE ##########################
    with set_default_dtype(model_dtype):
        model = Transformer(model_config)
        ############################## LONGRUN : RECOVER STATE ##############################
        train_step, model_state_dict = recover_state(STATE_PATH, device)
        if model_state_dict is not None:
            model.load_state_dict(model_state_dict, strict=False)
            logger.info(f"Recovered model state from {STATE_PATH}")
        else:
            train_step = 0
            logger.info(f"Starting from scratch, no state found in {STATE_PATH}")
        del model_state_dict
        ############################## END LONGRUN : RECOVER STATE ##########################
        model = model.to(device)
    ############################ LONGRUN : SAVE STATE ON SIGTERM ########################
    def sigterm_handler(signum, frame):
        logger.info(f"[Received SIGTERM] : Saving state to {STATE_PATH}")
        store_state(STATE_PATH, train_step, model)
        logger.info(f"[Received SIGTERM] : Finished saving state.")

    signal.signal(
        signal.SIGTERM,
        sigterm_handler,
    )
    logger.info(f"Registered SIGTERM handler to save state to {STATE_PATH} on termination.")
    ############################ END LONGRUN : SAVE STATE ON SIGTERM ######################
    ...
```

**Logs** from monitoring the job (as we didn't run it in detached mode):

```
$sbatch_longrun --signal=SIGTERM@20  example/assignment2_example/run_job.sbatch
2025-05-21 11:31:10 | SUCCESS  : Job submitted with ID: 454600
2025-05-21 11:31:10 | INFO     : Monitoring job 454600 (submission 1/999)
2025-05-21 11:35:51 | INFO     : Job 454600 reached final state: TIMEOUT
2025-05-21 11:35:52 | SUCCESS  : Resubmitted based on status=TIMEOUT job with ID: 454609
2025-05-21 11:35:52 | INFO     : Monitoring job 454609 (submission 2/999)
2025-05-21 11:40:02 | INFO     : Job 454609 reached final state: TIMEOUT
...
2025-05-21 11:52:04 | SUCCESS  : Resubmitted based on status=TIMEOUT job with ID: 454644
2025-05-21 11:52:04 | INFO     : Monitoring job 454644 (submission 6/999)
2025-05-21 11:55:04 | INFO     : Job 454644 reached final state: COMPLETED
2025-05-21 11:55:04 | SUCCESS  : Job completed successfully.
```

**Logs** outputted by the job script:

```
2025-05-21 11:31:55,595 - root - INFO - Setting up DataLoaders...
2025-05-21 11:31:57,838 - root - INFO - Setting up Model...
2025-05-21 11:32:31,846 - root - INFO - Starting from scratch, no state found in /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json
2025-05-21 11:32:33,519 - root - INFO - Registered SIGTERM handler to save state to /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json on termination.
2025-05-21 11:32:33,521 - root - INFO - Starting training!
2025-05-21 11:32:34,982 - root - INFO - Step: 1 | Loss: 12.03 | Tokens per second: 2884.67 | Training tokens per second (%): 19.38 | MFU (%): 15.03 | TFLOPs: 148.68
...
2025-05-21 11:33:40,533 - root - INFO - Step: 120 | Loss: 7.89 | Tokens per second: 7542.89 | Training tokens per second (%): 26.43 | MFU (%): 39.31 | TFLOPs: 388.77
slurmstepd: error: *** STEP 454600.0 ON nid006459 CANCELLED AT 2025-05-21T11:33:42 ***
2025-05-21 11:33:43,079 - root - INFO - [Received SIGTERM] : Saving state to /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json
2025-05-21 11:33:54,977 - root - INFO - [Received SIGTERM] : Finished saving state.
2025-05-21 11:33:55,081 - root - INFO - Step: 125 | Loss: 8.12 | Tokens per second: 1411.76 | Training tokens per second (%): 24.73 | MFU (%): 7.36 | TFLOPs: 72.76
...
slurmstepd: error: *** JOB 454600 ON nid006459 CANCELLED AT 2025-05-21T11:34:48 DUE TO TIME LIMIT ***
srun: forcing job termination

2025-05-21 11:36:33,182 - root - INFO - Setting up DataLoaders...
2025-05-21 11:36:35,357 - root - INFO - Setting up Model...
2025-05-21 11:37:16,360 - root - INFO - Recovered model state from /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json
2025-05-21 11:37:16,626 - root - INFO - Registered SIGTERM handler to save state to /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json on termination.
2025-05-21 11:37:16,628 - root - INFO - Starting training!
2025-05-21 11:37:18,498 - root - INFO - Step: 225 | Loss: 7.56 | Tokens per second: 2238.88 | Training tokens per second (%): 19.38 | MFU (%): 11.67 | TFLOPs: 115.39
2025-05-21 11:37:21,168 - root - INFO - Step: 230 | Loss: 7.29 | Tokens per second: 7789.90 | Training tokens per second (%): 13.66 | MFU (%): 40.60 | TFLOPs: 401.50
2025-05-21 11:37:23,877 - root - INFO - Step: 235 | Loss: 7.63 | Tokens per second: 7677.60 | Training tokens per second (%): 22.45 | MFU (%): 40.01 | TFLOPs: 395.71
...
slurmstepd: error: *** JOB 454609 ON nid006455 CANCELLED AT 2025-05-21T11:39:18 DUE TO TIME LIMIT ***
srun: Job step aborted: Waiting up to 32 seconds for job step to finish.
srun: forcing job termination
srun: got SIGCONT
2025-05-21 11:39:18,023 - root - INFO - [Received SIGTERM] : Saving state to /iopsstor/scratch/cscs/athillen/example_slurmlongrun/state-454600.json
....
....
2025-05-21 11:53:53,561 - root - INFO - Step: 995 | Loss: 4.38 | Tokens per second: 7647.01 | Training tokens per second (%): 10.83 | MFU (%): 39.85 | TFLOPs: 394.14
2025-05-21 11:53:56,307 - root - INFO - Step: 1000 | Loss: 4.74 | Tokens per second: 7571.65 | Training tokens per second (%): 16.73 | MFU (%): 39.46 | TFLOPs: 390.25
2025-05-21 11:53:56,307 - root - INFO - Training completed
```


## How It Works

1. **Submit**  
   Calls `sbatch` with your arguments; parses the returned job ID.  
2. **Monitor**  
   - Polls `sacct` + `scontrol` until the job reaches a terminal state.  
   - If `JobStatus.should_resubmit` and you haven’t exceeded `--max-restarts`, it immediately resubmits with `--open-mode=append` to preserve logs.  
3. **Detach** (optional)  
   If `--detached` is passed, the process forks twice, detaches from the terminal (`setsid`), redirects stdio to `/dev/null`, and continues monitoring in background.  

`JobStatus.should_resubmit` holds for jobs that exit due to `TIMEOUT`, `DEADLINE`, `PREEMPTED`, `NODE_FAIL`, or `REVOKED`.

---

## Environment Variables

`SLURM_LONGRUN_INITIAL_JOB_ID`  
- Set internally to the first submission’s job ID.  
- You can read it in your job script (e.g., to name checkpoints).

---

## Dependencies

- click  
- loguru  

These are installed automatically via pip.

---

## Summary of CLI Options

| Option                       | Default         | Description                                                  |
| ---------------------------- | --------------- | ------------------------------------------------------------ |
| `--use-verbosity`            | DEFAULT         | Logging verbosity: DEFAULT (INFO), VERBOSE, SILENT (WARNING) |
| `--detached / --no-detached` | `--no-detached` | Detach monitoring loop into background process               |
| `--max-restarts `            | 999             | Max auto-resubmissions on TIMEOUT                            |
| `[SBATCH_ARGS…]`             | /               | All subsequent flags passed directly to `sbatch`             |
