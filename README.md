# Slurm Longrun

## Overview

Slurm Longrun is a `python` package that provides a simple command line interface (CLI) for submitting long-running jobs, that exceed the `walltime`, to a Slurm workload manager.

## Usage
To use Slurm Longrun, you need to have `python` and `pip` installed on your system. You can install the package using pip:

```bash
pip install slurm-longrun
```

## Command Line Interface (CLI)

The Slurm Longrun CLI provides a simple way to submit long-running jobs to a Slurm workload manager. The basic usage is as follows:

```bash
sbatch_longrun [OPTIONS] [SBATCH_ARGS ...]
```

Where `OPTIONS` are the options for the Slurm Longrun CLI and `SBATCH_ARGS` are the arguments for the `sbatch` command.

For example, assume the walltime is set to 30 minutes, but your job takes more than that. You can submit your job using the following command:

```bash
sbatch_longrun --time=30:00 --job-name=my_job my_script.sbatch
```

This will restart your job every 30 minutes until it completes.

## Graceful Timeout

`slurm_longrun` also provides a simple way to register signal handlers, which can be used to checkpoint your model weights or save any progress upon receiving `SIGTERM` signal.

```py
import slurm_longrun

slurm_longrun.register_signal_handler(
    signal.SIGTERM,
    save_checkpoint,
)
```

The type and time of signal slurm sends can be configured using the `--signal` option. 
For example `--signal=SIGUSR1@90` will send `SIGUSR1` signal 90 seconds before the job is terminated, similar to `--signal=SIGTERM@90`.