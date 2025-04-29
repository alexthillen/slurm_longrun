import re
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


def run_command(command_args: List[str]) -> Optional[str]:
    """
    Executes a command using subprocess.run, prints command output and error details if any.
    Args:
        command_args: List of command arguments (e.g., ['ls', '-la']).
    Returns:
        The command output as a string if successful.
    Raises:
        subprocess.CalledProcessError: If the command fails.
    """
    print(f"Running command: {' '.join(command_args)}")
    try:
        process = subprocess.run(
            command_args, capture_output=True, text=True, check=True, encoding="utf-8"
        )
        print(f"Command output: {process.stdout}")
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Return code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"Standard output: '{e.stdout}'", file=sys.stderr)
        if e.stderr:
            print(f"Standard error: '{e.stderr}'", file=sys.stderr)
        raise e


def run_sbatch(sbatch_args_list: List[str]) -> Optional[str]:
    """
    Executes sbatch with given arguments and returns the Job ID.

    Args:
        sbatch_args_list: List of arguments for sbatch (e.g., ['script.sh']).

    Returns:
        The submitted Job ID as a string, or None if failed or not found.
    """
    # Execute command using subprocess
    command = ["sbatch"] + sbatch_args_list
    sbatch_output = run_command(command)
    match = re.search(r"Submitted batch job\s+(\d+)", sbatch_output, re.IGNORECASE)
    if match:
        time.sleep(5)
        return match.group(1)
    else:
        print(
            f"Warning: Job submitted but ID not found in output:\n{sbatch_output}",
            file=sys.stderr,
        )
        return None


import subprocess


def get_scontrol_show_job_details(job_id: int) -> dict:
    """
    Runs the 'scontrol show job <job_id>' command and parses the output into a dictionary.
    Args:
        job_id (int): The job ID to query.
    Returns:
        dict: Parsed job details as key-value pairs. E.g. : {"TimeLimit":"00:02:00", ...}
    """
    try:
        # Run the command and capture output
        output = run_command(["scontrol", "show", "job", str(job_id)])
    except subprocess.CalledProcessError as e:
        return {}
    lines = output.strip().split("\n")
    info = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                info[key] = value
    return info


def get_sacct_job_details(job_id) -> list:
    """
    Retrieves sacct output for a given job ID and parses it into a list of dictionaries.

    Args:
        job_id (int): The Slurm job ID.

    Returns:
        list: A list of dictionaries, where each dictionary represents a line (job step)
              from the sacct output containing job details.
              Returns None if there's an error running sacct or parsing the output.
    Example:
    [{'JobID': '389346', 'JobName': 'sbatch_longrun_example', 'State': 'TIMEOUT', 'ExitCode': '0:0',
    'Reason': 'None', 'Comment': ''}, ...]
    """
    headers = ["JobID", "JobName", "State", "ExitCode", "Reason", "Comment", "Elapsed"]
    command = [
        "sacct",
        "-j",
        str(job_id),
        f"--format={','.join(headers)}",
        "--noheader",  # Add --noheader to simplify parsing
        "-P",  # Use pipe separator for easier splitting
    ]
    process = subprocess.run(
        command, capture_output=True, text=True, check=True, encoding="utf-8"
    )
    output = process.stdout.strip()
    results = []
    if not output:
        return []

    for line in output.split("\n"):
        values = line.strip().split("|")  # Split by pipe
        num_values = len(values)
        if num_values < len(headers):
            values.extend([""] * (len(headers) - num_values))
        elif num_values > len(headers):
            values = values[: len(headers)]
        if len(values) == len(headers) and values[0]:
            results.append(dict(zip(headers, values)))
    return results

