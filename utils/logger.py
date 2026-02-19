"""Logging configuration for convert-to-md."""

import logging
import sys


def get_logger(name: str = "convert-to-md", level: int = logging.INFO) -> logging.Logger:
    """Return a named logger with a consistent format.

    Args:
        name: Logger name (defaults to ``"convert-to-md"``).
        level: Logging level (defaults to ``logging.INFO``).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the logger is requested more than once.
    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
