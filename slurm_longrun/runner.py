# slurm_longrun/runner.py

import os
import time
from typing import List

from loguru import logger

from slurm_longrun.common import JobStatus
from slurm_longrun.utils import (
    detach_terminal,
    get_sacct_job_details,
    get_scontrol_show_job_details,
    run_sbatch,
    time_to_seconds,
)


class SlurmRunner:
    """
    Encapsulates sbatch submission + (optional) terminal detachment + monitoring
    with automatic resubmission on TIMEOUT.
    """

    def __init__(
        self, sbatch_args: List[str], max_restarts: int = 99, detached: bool = False
    ):
        self.base_args = list(sbatch_args)
        self.max_restarts = max_restarts
        self.detached = detached

    def submit(self) -> str:
        """
        Submit the sbatch job and return its job ID.
        Raises RuntimeError on failure.
        """
        job_id = run_sbatch(self.base_args)
        if not job_id:
            logger.error("sbatch submission failed.")
            raise RuntimeError("sbatch submission failed")
        logger.success("Job submitted with ID: {}", job_id)
        return job_id

    def fetch_info(self, job_id: str) -> dict:
        """
        Merge sacct details + scontrol details into one dict.
        """
        sacct_list = get_sacct_job_details(job_id)
        sacct = next((j for j in sacct_list if j.get("JobID") == job_id), {})
        sctrl = get_scontrol_show_job_details(job_id)
        info = {**sacct, **sctrl}
        logger.trace("Fetched info for {}: {}", job_id, info)
        return info

    def parse_status(self, info: dict) -> JobStatus:
        """
        Extract and normalize Slurm job state → JobStatus enum.
        """
        raw = info.get("JobState") or info.get("State", "").split(maxsplit=1)[0]
        try:
            return JobStatus(raw)
        except ValueError:
            logger.warning("Unknown job state {!r}, default to UNKNOWN.", raw)
            return JobStatus.UNKNOWN

    def monitor(self, job_id: str) -> JobStatus:
        """
        Poll Slurm until job reaches a terminal state.
        On TIMEOUT and if attempts remain, automatically resubmit.
        Returns the final JobStatus.
        """
        attempt = 1
        retry_args = ["--open-mode=append", *self.base_args]

        while True:
            logger.info(
                "Monitoring job {} (submission {}/{})", job_id, attempt, self.max_restarts
            )
            info = self.fetch_info(job_id)
            status = self.parse_status(info)

            # Poll until final
            while not status.is_final:
                # compute remaining time
                limit = info.get("TimeLimit", "00:00:00")
                runtime = info.get("RunTime", "00:00:00")
                rem = time_to_seconds(limit) - time_to_seconds(runtime)
                wait = max(5, min(rem, 300))
                logger.debug("Sleeping {}s (remaining {}s)", wait, rem)
                time.sleep(wait)
                info = self.fetch_info(job_id)
                status = self.parse_status(info)

            logger.info("Job {} reached final state: {}", job_id, status.value)

            # TIMEOUT, NODE_FAIL, ... → resubmit if allowed
            if status.should_resubmit and attempt < self.max_restarts:
                attempt += 1
                new_id = run_sbatch(retry_args)
                if not new_id:
                    logger.error("Resubmission failed.")
                    return status
                job_id = new_id
                logger.success(f"Resubmitted based on status={status.value} job with ID: {job_id}")
                continue

            # final outcome
            if status.is_success:
                logger.success("Job completed successfully.")
            else:
                logger.warning("Job finished with state: {}", status.value)
            return status

    def run(self) -> None:
        """
        Submit → optional detach → monitor.
        """
        initial = self.submit()
        os.environ["SLURM_LONGRUN_INITIAL_JOB_ID"] = initial

        if self.detached:
            logger.info("Detaching terminal output (monitor runs in background)…")
            detach_terminal()

        self.monitor(initial)
