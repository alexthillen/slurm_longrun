from enum import Enum


class JobStatus(Enum):
    # Non-final states
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    COMPLETING = "COMPLETING"
    CONFIGURING = "CONFIGURING"
    RESIZING = "RESIZING"
    REQUEUED = "REQUEUED"

    # Final states
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

    @classmethod
    def is_final(cls, status):
        """Returns whether this is a final (terminal) state."""
        res = JobStatus(status) not in {
            cls.PENDING,
            cls.RUNNING,
            cls.SUSPENDED,
            cls.COMPLETING,
            cls.CONFIGURING,
            cls.RESIZING,
            cls.REQUEUED,
        }
        print(f"JobStatus.is_final({status}) = {res}")
        return res
