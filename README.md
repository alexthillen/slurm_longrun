## Slurm Longrun

Slurm Longrun is a Python package that wraps Slurm’s `sbatch` command to automatically resubmit jobs that time out, allowing you to run workloads that exceed a single‐job walltime without manual intervention. It supports optional terminal detachment (so your monitor survives after you log out), configurable retry limits, and built-in logging via Loguru.

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
 Maximum number of resubmissions on `TIMEOUT`. Default: 99.  
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

## How It Works

1. **Submit**  
   Calls `sbatch` with your arguments; parses the returned job ID.  
2. **Monitor**  
   - Polls `sacct` + `scontrol` until the job reaches a terminal state.  
   - If `TIMEOUT` and you haven’t exceeded `--max-restarts`, it immediately resubmits with `--open-mode=append` to preserve logs.  
3. **Detach** (optional)  
   If `--detached` is passed, the process forks twice, detaches from the terminal (`setsid`), redirects stdio to `/dev/null`, and continues monitoring in background.  

---

## Environment Variables

SLURM_LONGRUN_INITIAL_JOB_ID  
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
| `--max-restarts `            | 99              | Max auto-resubmissions on TIMEOUT                            |
| `[SBATCH_ARGS…]`             | /               | All subsequent flags passed directly to `sbatch`             |
