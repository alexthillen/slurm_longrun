# slurm_longrun/logger.py

import sys
from enum import Enum

from loguru import logger


class Verbosity(Enum):
    DEFAULT = "INFO"
    VERBOSE = "DEBUG"
    SILENT = "WARNING"


LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level:<8}</level> : {message}"


def setup_logger(verbosity: Verbosity = Verbosity.DEFAULT) -> None:
    """
    Configure Loguru root logger with a single stdout sink.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        level=verbosity.value,
        format=LOG_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
