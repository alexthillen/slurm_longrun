# logger.py
import sys
from loguru import logger
from enum import Enum, auto

class Verbosity(Enum):
    DEFAULT = "DEFAULT"
    VERBOSE = "VERBOSE"
    SILENT = "SILENT"

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level:<8}</level> : {message}"

def setup_logger(verbosity: Verbosity = Verbosity.DEFAULT) -> None:
    """
    Configures the loguru logger based on desired verbosity.
    """
    # Remove any pre-existing handlers
    logger.remove()

    level_map = {
        Verbosity.DEFAULT: "INFO",
        Verbosity.VERBOSE: "DEBUG",
        Verbosity.SILENT: "WARNING",
    }
    level = level_map[verbosity]

    # Add stdout handler
    logger.add(
        sys.stdout,
        level=level,
        format=LOG_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

setup_logger()