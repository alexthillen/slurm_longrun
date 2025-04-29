# common.py
from enum import Enum, unique

@unique
class JobStatus(Enum):
    PENDING      = "PENDING"
    RUNNING      = "RUNNING"
    SUSPENDED    = "SUSPENDED"
    COMPLETING   = "COMPLETING"
    CONFIGURING  = "CONFIGURING"
    RESIZING     = "RESIZING"
    REQUEUED     = "REQUEUED"

    # terminal states
    COMPLETED    = "COMPLETED"
    FAILED       = "FAILED"
    TIMEOUT      = "TIMEOUT"
    PREEMPTED    = "PREEMPTED"
    STOPPED      = "STOPPED"
    CANCELLED    = "CANCELLED"
    BOOT_FAIL    = "BOOT_FAIL"
    NODE_FAIL    = "NODE_FAIL"
    DEADLINE     = "DEADLINE"
    OUT_OF_MEMORY= "OUT_OF_MEMORY"
    SPECIAL_EXIT = "SPECIAL_EXIT"
    REVOKED      = "REVOKED"

    __terminal_states = {
        COMPLETED, FAILED, TIMEOUT, PREEMPTED, STOPPED, CANCELLED,
        BOOT_FAIL, NODE_FAIL, DEADLINE, OUT_OF_MEMORY, SPECIAL_EXIT, REVOKED
    }

    @classmethod
    def is_final(cls, status: str) -> bool:
        """Returns True if status is a terminal state."""
        try:
            st = cls(status)
        except ValueError:
            return False
        return st in cls.__terminal_states
