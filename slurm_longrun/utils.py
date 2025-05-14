# slurm_longrun/utils.py

import multiprocessing
import os
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional

from loguru import logger


def run_command(cmd: List[str]) -> str:
    """
    Execute a command and return its stdout.
    Raises CalledProcessError on non-zero exit.
    """
    logger.debug("Running command: {}", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Command failed: {}\nstdout: {}\nstderr: {}",
            e,
            e.stdout.strip(),
            e.stderr.strip(),
        )
        raise e
    logger.trace("Command stdout: {}", result.stdout.strip())
    return result.stdout.strip()


def run_sbatch(args: List[str]) -> Optional[str]:
    """
    Submit via sbatch and parse “Submitted batch job <ID>”.
    Returns the job ID or None on parse-failure.
    """
    try:
        out = run_command(["sbatch", *args])
    except subprocess.CalledProcessError:
        return None

    match = re.search(r"Submitted batch job (\d+)", out)
    if not match:
        logger.warning("Could not parse sbatch output: {}", out)
        return None

    job_id = match.group(1)
    return job_id


def get_scontrol_show_job_details(job_id: str) -> Dict[str, str]:
    """
    Run `scontrol show job <job_id>` → parse key=val tokens → dict.
    """
    try:
        out = run_command(["scontrol", "show", "job", job_id])
    except subprocess.CalledProcessError:
        return {}

    info: Dict[str, str] = {}
    for token in out.replace("\n", " ").split():
        if "=" in token:
            key, val = token.split("=", 1)
            info[key] = val
    return info


def get_sacct_job_details(job_id: str) -> List[Dict[str, str]]:
    """
    Run `sacct -j <job_id> --format=... -P` → parse pipe-separated lines.
    """
    headers = ["JobID", "JobName", "State", "ExitCode", "Reason", "Comment", "Elapsed"]
    cmd = ["sacct", "-j", job_id, f"--format={','.join(headers)}", "--noheader", "-P"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []

    out = result.stdout.strip()
    if not out:
        return []

    rows = []
    for line in out.splitlines():
        parts = line.split("|")
        # pad/truncate
        parts = (parts + [""] * len(headers))[: len(headers)]
        rows.append(dict(zip(headers, parts)))
    return rows


def time_to_seconds(timestr: str) -> int:
    """
    Convert "D-HH:MM:SS" or "HH:MM:SS" into total seconds.
    """
    if "-" in timestr:
        days_str, rest = timestr.split("-", 1)
        days = int(days_str)
    else:
        days, rest = 0, timestr

    h, m, s = map(int, rest.split(":"))
    total = days * 86400 + h * 3600 + m * 60 + s
    logger.trace("Parsed {} → {}s", timestr, total)
    return total


def run_detached(func, *args, **kwargs) -> int:
    """
    Fork+setsid a child to run func(*args, **kwargs), return its PID immediately.
    Not supported on Windows.
    """
    if os.name == "nt":
        raise RuntimeError("run_detached is not supported on Windows")

    def _wrapper(pid_queue: multiprocessing.Queue):
        # first fork
        pid = os.fork()
        if pid > 0:
            # In parent: send child-PID back and exit wrapper
            pid_queue.put(pid)
            return

        # In child: detach the session, then execute
        os.setsid()
        func(*args, **kwargs)
        os._exit(0)

    pid_q: multiprocessing.Queue = multiprocessing.Queue(1)
    worker = multiprocessing.Process(target=_wrapper, args=(pid_q,))
    worker.daemon = False
    worker.start()

    child_pid = pid_q.get()
    pid_q.close()
    return child_pid


def detach_terminal():
    """
    Redirect stdin, stdout, stderr to /dev/null.
    Useful after forking a detached monitor.
    """
    sys.stdout.flush()
    sys.stderr.flush()

    with open(os.devnull, "rb", 0) as devnull_in:
        os.dup2(devnull_in.fileno(), sys.stdin.fileno())
    with open(os.devnull, "ab", 0) as devnull_out:
        os.dup2(devnull_out.fileno(), sys.stdout.fileno())
        os.dup2(devnull_out.fileno(), sys.stderr.fileno())
