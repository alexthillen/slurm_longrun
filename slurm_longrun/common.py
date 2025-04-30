# common.py
from enum import Enum, unique
from loguru import logger

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
    UNKNOWN = "UNKNOWN"


    @classmethod
    def is_final(cls, status: str) -> bool:
        """Returns True if status is a terminal state."""
        TERMINAL_STATES = {
            cls.COMPLETED, cls.FAILED, cls.TIMEOUT, cls.PREEMPTED, cls.STOPPED, cls.CANCELLED,
            cls.BOOT_FAIL, cls.NODE_FAIL, cls.DEADLINE, cls.OUT_OF_MEMORY, cls.SPECIAL_EXIT, cls.REVOKED, cls.UNKNOWN
        }
        st = cls(status)
        res = st in TERMINAL_STATES
        logger.debug("is_final({}) = {}", status, res)
        return res
    
    @classmethod
    def is_success(cls, status: str) -> bool:
        """Returns True if status is a success state."""
        SUCCESS_STATES = {cls.COMPLETED, cls.TIMEOUT}
        st = cls(status)
        res = st in SUCCESS_STATES
        logger.debug("is_success({}) = {}", status, res)
        return res
