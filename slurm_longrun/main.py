#!/usr/bin/env python3
import os
import time
import multiprocessing
from typing import Any, Dict

import click

from slurm_longrun.logger import setup_logger, Verbosity, logger
from slurm_longrun import utils
from slurm_longrun.common import JobStatus

# 1) Tell Click to let unknown flags slip by and collect them at the end
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
    help="Logging verbosity",
)
@click.option(
    "--use-detached/--no-detached",
    default=False,
    show_default=True,
    help="Run in detached mode",
)
@click.option(
    "--max-restarts",
    default=99,
    show_default=True,
    help="Number of times to resubmit on TIMEOUT",
)
@click.argument(
  "sbatch_args",
  nargs=-1,
  type=click.UNPROCESSED,
  metavar="[SBATCH ARGS] script.sbatch [SCRIPT ARGS]",
)
@click.pass_context
def cli(ctx, use_verbosity, use_detached, max_restarts, sbatch_args):
    """
    Wrapper that takes any sbatch flags *after* your wrapper-options,
    e.g.:
      "sbatch_longrun --time=00:02:00 --job-name=my_job example/run_job.sbatch"
      or
      "sbatch_longrun --use-verbosity VERBOSE --job-name=my_job example/run_job.sbatch"
    """
    setup_logger(Verbosity[use_verbosity])
    logger.debug("Starting with verbosity={}", use_verbosity)
    if use_detached:
        # print pid of this process
        logger.info("Running in detached mode")
        logger.info("This process PID: {}", os.getpid())
        pid = utils._run_detached(run_until, sbatch_args, use_detached, max_restarts)
        logger.info("Detached process started with PID: {}", pid)
        time.sleep(2)  
        return
    else:
        run_until(sbatch_args, use_verbosity, use_detached, max_restarts)


def run_until(sbatch_args, use_detached, max_restarts):
    logger.debug("sbatch_args={}", sbatch_args)

    # Submit initial job
    sbatch_list = list(sbatch_args)
    job_id = utils.run_sbatch(sbatch_list)
    if use_detached:
        utils.detach_terminal()
    if not job_id:
        logger.error("Initial sbatch submission failed.")
        return
    logger.success("Initial job submitted with ID: {}", job_id)

    os.environ["SLURM_LONGRUN_INITIAL_JOB_ID"] = job_id
    sbatch_list.insert(0, "--open-mode=append")

    for attempt in range(1, max_restarts + 1):
        logger.info("Monitoring job {} (attempt {}/{})", job_id, attempt, max_restarts)
        info = _fetch_info(job_id)

        # Poll until we hit a final state
        while not JobStatus.is_final(extract_job_status(info)):
            logger.debug("Job {} in state: {}", job_id, info.get("State"))
            rem = utils.time_to_seconds(info.get("TimeLimit", "00:00:00")) \
                - utils.time_to_seconds(info.get("RunTime", "00:00:00"))
            sleep_secs = max(5, min(rem, 5 * 60))
            logger.debug("Sleeping {}s (remaining {}s)", sleep_secs, rem)
            time.sleep(sleep_secs)
            info = _fetch_info(job_id)

        state = info.get("State")
        logger.info("Job {} entered final state: {}", job_id, state)

        # If TIMEOUT and we still have retries, resubmit
        if state == JobStatus.TIMEOUT.value and attempt < max_restarts:
            job_id = utils.run_sbatch(sbatch_list)
            if not job_id:
                logger.error("Resubmission failed.")
                break
            logger.success("Job timed out → resubmitted job with ID: {}", job_id)
        else:
            if JobStatus.is_success(state):
                logger.success("Job completed successfully.")
            else:
                logger.warning("Job finished with state: {}", state)
            break

def extract_job_status(info: Dict[str, Any]) -> JobStatus:
    """
    Extract the job status from a Slurm‐style info dictionary.

    1. Try 'JobState' key.
    2. Fallback to the first word of 'State' if present.
    3. Validate against JobStatus, default to UNKNOWN on failure.

    Returns:
        A JobStatus enum member.
    """
    try:
        raw = info.get("JobState") or info.get("State", "").split(maxsplit=1)[0]
        status = JobStatus(raw)
    except (ValueError, IndexError):
        logger.warning(f"Unknown job state: {raw!r}. Defaulting to UNKNOWN.")
        status = JobStatus.UNKNOWN
    return status.value

def _fetch_info(job_id: str) -> dict:
    sacct = next(
        (x for x in utils.get_sacct_job_details(job_id) if x["JobID"] == job_id),
        {}
    )
    sctrl = utils.get_scontrol_show_job_details(job_id)
    merged = {**sacct, **sctrl}
    logger.debug("Fetched info for {}: {}", job_id, merged)
    return merged


