# slurm_longrun/common.py

from enum import Enum, unique


@unique
class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    COMPLETING = "COMPLETING"
    CONFIGURING = "CONFIGURING"
    RESIZING = "RESIZING"
    REQUEUED = "REQUEUED"
    # terminal
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    PREEMPTED = "PREEMPTED"
    STOPPED = "STOPPED"
    CANCELLED = "CANCELLED"
    BOOT_FAIL = "BOOT_FAIL"
    NODE_FAIL = "NODE_FAIL"
    DEADLINE = "DEADLINE"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    SPECIAL_EXIT = "SPECIAL_EXIT"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"

    @property
    def is_final(self) -> bool:
        """
        True if this status is a terminal (no-further-progress) state.
        """
        return self in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.PREEMPTED,
            JobStatus.STOPPED,
            JobStatus.CANCELLED,
            JobStatus.BOOT_FAIL,
            JobStatus.NODE_FAIL,
            JobStatus.DEADLINE,
            JobStatus.OUT_OF_MEMORY,
            JobStatus.SPECIAL_EXIT,
            JobStatus.REVOKED,
            JobStatus.UNKNOWN,
        }

    @property
    def is_success(self) -> bool:
        """
        True if this status counts as a success for our purposes.
        We treat TIMEOUT as a “successful” endpoint (to trigger resubmit).
        """
        return self in {JobStatus.COMPLETED}

    @property
    def should_resubmit(self) -> bool:
        """
        True if this status should trigger a resubmission.
        """
        return self in {
            JobStatus.TIMEOUT,
            JobStatus.DEADLINE,
            JobStatus.PREEMPTED,
            JobStatus.NODE_FAIL,
            JobStatus.REVOKED,
        }
