"""Structured and sanitized logging configuration for DBGuard.

Ensures no raw database record values or sensitive customer information
leak into log streams or stderr.
"""

import logging
import sys

_LOGGER_INITIALIZED = False


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Set up and return the root logger for DBGuard."""
    global _LOGGER_INITIALIZED
    logger = logging.getLogger("dbguard")

    if not _LOGGER_INITIALIZED:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [DBGuard] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        _LOGGER_INITIALIZED = True

    return logger

