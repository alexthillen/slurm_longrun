# slurm_longrun/cli.py

import os
import time
import click
from slurm_longrun.logger import setup_logger, Verbosity
from slurm_longrun.runner import SlurmRunner
from slurm_longrun.utils import _run_detached

@click.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
        "allow_interspersed_args": False,
    }
)
@click.option(
    "--use-verbosity",
    type=click.Choice([v.name for v in Verbosity]),
    default=Verbosity.DEFAULT.name,
    show_default=True,
    help="Logging verbosity",
)
@click.option(
    "--detached/--no-detached",
    default=False,
    show_default=True,
    help="Detach the monitoring loop from your terminal",
)
@click.option(
    "--max-restarts",
    default=99,
    show_default=True,
    help="Resubmit up to this many times on TIMEOUT",
)
@click.argument("sbatch_args", nargs=-1, type=click.UNPROCESSED)
def main(use_verbosity, detached, max_restarts, sbatch_args):
    """
    Wrapper for sbatch that auto-resubmits timed-out jobs.

    All unrecognized flags after these wrapper options are
    passed directly to sbatch.
    """
    setup_logger(Verbosity[use_verbosity])
    runner = SlurmRunner(
        sbatch_args=list(sbatch_args),
        max_restarts=max_restarts,
        detached=detached,
    )

    if detached:
        # click.echo(f"Starting detached monitor (parent PID: {os.getpid()})…")
        child_pid = _run_detached(runner.run)
        click.echo(f"Monitor running in background PID: {child_pid}")
        time.sleep(2) 
    else:
        runner.run()

if __name__ == "__main__":
    main()
