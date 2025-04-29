#!/usr/bin/env python3

import os
import sys
import time

import click

from slurm_longrun import utils
from slurm_longrun.common import JobStatus


def get_job_information(job_id):
    """
    Retrieves job information using sacct and scontrol commands.

    Args:
        job_id (str): The Slurm job ID.

    Returns:
        dict: A dictionary containing job information.
    """
    sacct_info = next(
        (x for x in utils.get_sacct_job_details(job_id) if x.get("JobID") == job_id),
        None,
    )
    scontrol_info = utils.get_scontrol_show_job_details(job_id)
    return {**sacct_info, **scontrol_info}


def remaining_time(info):
    """
    Calculate the remaining time in seconds based on the run time and time limit.
    Args:
        info (dict): A dictionary containing job information with 'RunTime' and 'TimeLimit' keys.
    Returns:
        int: Remaining time in seconds.
    """
    run_time_str = info.get("RunTime", "00:00:00")
    time_limit_str = info.get("TimeLimit", "00:00:00")

    def time_to_seconds(time_str):
        days = 0
        if "-" in time_str:
            days, time_str = time_str.split("-")
            days = int(days)
        hours, minutes, seconds = map(int, time_str.split(":"))
        return days * 24 * 3600 + hours * 3600 + minutes * 60 + seconds

    run_time_seconds = time_to_seconds(run_time_str)
    time_limit_seconds = time_to_seconds(time_limit_str)
    remaining_seconds = time_limit_seconds - run_time_seconds
    print(f"Remaining time: {remaining_seconds} seconds")
    return max(0, remaining_seconds)


def run_till_completed(sbatch_args, max_restarts=10):  # CHANGE THIS
    # Prepare Arguments
    sbatch_args_list = list(sbatch_args)
    # sbatch_args_list = utils.patch_sbatch_args(sbatch_args_list)
    # options_cli : dict = utils.parse_sbatch_cli_options(sbatch_args_list)
    # options_file : dict = utils.parse_sbatch_file_options(options_cli.get("filename"))
    # options_unified = {**options_file, **options_cli} # CLI > File
    if True:  # verbose
        click.echo("Verbose mode enabled.")
        click.echo(f"sbatch args: {sbatch_args_list}")

    # Run sbatch
    job_id = utils.run_sbatch(sbatch_args_list)
    os.environ["SLURM_LONGRUN_INITIAL_JOB_ID"] = job_id
    sbatch_args_list = ["--open-mode=append"] + sbatch_args_list

    # Parse Job Information
    initial_info = get_job_information(job_id)
    click.echo(f"Initial job information: {initial_info}")

    for _ in range(max_restarts):
        info = get_job_information(job_id)
        while JobStatus.is_final(info.get("State")) is False:
            # Wait for a while before checking again
            expected_runtime = remaining_time(info)
            bounded_expected_runtime = max(min(5 * 60, expected_runtime), 5)

            print(f"Sleep for", bounded_expected_runtime, "seconds.")
            time.sleep(bounded_expected_runtime)
            info = get_job_information(job_id)
        if JobStatus(info.get("State")) == JobStatus.TIMEOUT:
            click.echo("Job has timed out. Attempting to resubmit...")
            # Resubmit the job
            job_id = utils.run_sbatch(sbatch_args_list)
            info = get_job_information(job_id)
            click.echo(f"New job information: {info}")
        else:
            print("The current job has reached it's final state.", info.get("State"))
            break


if __name__ == "__main__":
    run_till_completed(["./example/run_job.sbatch"])
