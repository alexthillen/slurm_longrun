#!/usr/bin/env python3
"""
Wrapper script 'sbatch_longrun' for submitting Slurm batch jobs via 'sbatch'.

Enhanced with wrapper-specific options for chaining:
  --max_restarts: Max restarts for chaining (default 5).
  --verbose: Enable verbose wrapper output.

Other sbatch arguments (like --time, --job-name, --signal, the job script itself)
should be passed directly as sbatch arguments.

Syntax:
  sbatch_longrun [WRAPPER_OPTIONS] [SBATCH_ARGS ...]

Example:
  # Submit script.sl, allow up to 3 restarts if needed.
  # Assumes script.sl handles checkpoint/restart and has #SBATCH --time=...
  sbatch_longrun --max_restarts=3 --job-name=my_long_analysis --signal=USR1@120 script.sl

Uses Click for argument parsing and subprocess.run for execution and chaining.
"""

import click
import os
import sys
import subprocess
import re
import shlex # Use shlex for safer command display

CONTEXT_SETTINGS = dict(
    ignore_unknown_options=True,
    allow_interspersed_args=False  # Keep wrapper options before sbatch args
)

def parse_job_id(sbatch_output):
    """Parses sbatch output to find the submitted job ID."""
    match = re.search(r"Submitted batch job (\d+)", sbatch_output)
    if match:
        return match.group(1)
    return None

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--verbose', '-vvv',
    is_flag=True,
    help='Enable verbose output for the wrapper itself.'
)
@click.argument('sbatch_args', nargs=-1, type=click.UNPROCESSED)
def main(max_restarts, verbose, sbatch_args):
    """
    Submits a job using sbatch and chains subsequent jobs using dependencies
    up to max_restarts times. Assumes the job script handles checkpoint/restart.
    """
    sbatch_command = "sbatch"
    sbatch_args_list = list(sbatch_args)

    if not sbatch_args_list:
        click.echo("Error: No sbatch arguments or script provided.", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"  --verbose={verbose}", err=True)
        click.echo(f"sbatch_longrun: Base sbatch args: {' '.join(shlex.quote(a) for a in sbatch_args_list)}", err=True)
        click.echo("-" * 20, err=True)


    previous_job_id = None
    last_submitted_job_id = None

    # TODO

if __name__ == "__main__":
    main()
