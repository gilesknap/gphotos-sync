import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# add a trace level for logging all API calls to Google
# this will be filtered into a separate file
TRACE_API_NUM = 9
TRACE_API = "TRACE"


class MaxLevelFilter(logging.Filter):
    """Filters (lets through) all messages with level < LEVEL"""

    def __init__(self, level: int, allow_trace: bool):
        self.level = level
        self.allow_trace = allow_trace

    def filter(self, record):
        result = self.allow_trace or record.levelno != TRACE_API_NUM
        result &= record.levelno < self.level
        return result


def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_API_NUM):
        self._log(TRACE_API_NUM, message, args, **kwargs)


setattr(logging.Logger, "trace", trace)


def setup_logging(log_level: str, log_filename: Path, folder: Path):
    # add out custom trace level logging
    logging.addLevelName(TRACE_API_NUM, TRACE_API)

    # if we are debugging requests library is too noisy
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # determine the numeric log level from the string argument
    if log_level.upper() == TRACE_API.upper():
        # todo - i would expect addLevelName to do this for us?
        numeric_level: Optional[Any] = TRACE_API_NUM
    else:
        numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % log_level)

    # configure the log files locations
    if log_filename:
        log_file = folder / log_filename
        if log_file.is_dir():
            log_file = log_file / "gphotos{}.log".format(
                datetime.now().strftime("%y%m%d_%H%M%S")
            )
    else:
        log_file = folder / "gphotos.log"
    trace_file = log_file.with_suffix(".trace")

    # define handler for the trace file
    log_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    log_handler.setLevel(logging.DEBUG)

    # define handler for the trace file
    trace_handler = logging.FileHandler(trace_file, mode="w", encoding="utf-8")
    trace_handler.setLevel(TRACE_API_NUM)
    trace_handler.addFilter(MaxLevelFilter(logging.DEBUG, True))

    # set format for files
    formatter = logging.Formatter(
        "%(asctime)s %(name)-12s %(levelname)-8s " "%(message)s",
        datefmt="%m-%d %H:%M:%S",
    )
    log_handler.setFormatter(formatter)
    trace_handler.setFormatter(formatter)

    # define handlers for std out and std err
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    # std error prints error and higher
    stderr_handler.setLevel(max(numeric_level, logging.ERROR))
    # std out prints everything below error (but always filters out trace)
    stdout_handler.setLevel(numeric_level)
    stdout_handler.addFilter(MaxLevelFilter(logging.ERROR, False))

    # set a format which is simpler for console use
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(message)s ", datefmt="%m-%d %H:%M:%S"
    )
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # add the handlers to the root logger
    logging.getLogger().addHandler(stdout_handler)
    logging.getLogger().addHandler(stderr_handler)
    logging.getLogger().addHandler(log_handler)
    logging.getLogger().addHandler(trace_handler)
    # set logging level for root logger
    # always do debug for the log file, drop to trace if requested
    logging.getLogger().setLevel(min(numeric_level, logging.DEBUG))
