# utils.py
import re
import subprocess
import time
from typing import List, Optional, Dict
from loguru import logger

def run_command(cmd: List[str]) -> str:
    """
    Execute a shell command and return its stdout.
    
    Args:
        cmd: List of command-and-args, e.g. ["ls", "-la"].
    Raises:
        subprocess.CalledProcessError on nonzero exit.
    Returns:
        The captured stdout as a string.
    """
    logger.debug("Running command: {}", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Command failed: {}\nstdout: {}\nstderr: {}", e, e.stdout.strip(), e.stderr.strip())
        raise e
    logger.debug("Command output: {}", proc.stdout.strip())
    return proc.stdout

def run_sbatch(args: List[str]) -> Optional[str]:
    """
    Submit an sbatch job and extract its JobID.
    
    Args:
        args: Arguments to sbatch, including script path.
    Returns:
        The job ID string, or None if parsing failed.
    """
    output = run_command(["sbatch"] + args)
    match = re.search(r"Submitted batch job (\d+)", output)
    if not match:
        logger.warning("Could not parse sbatch output: {}", output)
        return None
    job_id = match.group(1)
    time.sleep(5)  # give Slurm time to register
    return job_id

def get_scontrol_show_job_details(job_id: str) -> Dict[str, str]:
    """
    Query `scontrol show job <job_id>` and parse key=value tokens.

    Args:
        job_id: The Slurm job ID.
    Returns:
        A dict of fields, e.g. {"TimeLimit":"00:10:00", ...}
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
    Run `sacct -j <job_id>` and parse pipe‐separated output into dicts.
    
    Args:
        job_id: The Slurm job ID.
    Returns:
        A list of dicts-one per step-containing fields like State, Elapsed, etc.
    """
    headers = ["JobID","JobName","State","ExitCode","Reason","Comment","Elapsed"]
    cmd = ["sacct", "-j", job_id, f"--format={','.join(headers)}", "--noheader", "-P"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = proc.stdout.strip()
    if not out:
        return []
    results = []
    for line in out.splitlines():
        parts = line.split("|")
        # pad or truncate to len(headers)
        parts = (parts + [""]*len(headers))[:len(headers)]
        results.append(dict(zip(headers, parts)))
    return results

def time_to_seconds(timestr: str) -> int:
    """
    Convert "D-HH:MM:SS" or "HH:MM:SS" to total seconds.
    
    Definition:
      D = days, HH = hours, MM = minutes, SS = seconds.
    Args:
        timestr: e.g. "1-02:30:00" or "00:15:20"
    Returns:
        Total seconds as int.
    """
    days = 0
    if "-" in timestr:
        days_part, rest = timestr.split("-", 1)
        days = int(days_part)
    else:
        rest = timestr
    h, m, s = map(int, rest.split(":"))
    total = days*86400 + h*3600 + m*60 + s
    logger.trace("Parsed {} → {}s", timestr, total)
    return total
