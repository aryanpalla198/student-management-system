"""
Logging configuration for the Student Management System.
Logs application activity, database transactions, errors, and authentication events.
"""

import logging
import sys
from app.config import LOG_DIR, LOG_FILE

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = None

def get_logger(name: str = "sms") -> logging.Logger:
    """Return a configured logger singleton with both file and console handlers."""
    global _logger
    if _logger is not None:
        return logging.getLogger(name)

    logger = logging.getLogger("sms")
    logger.setLevel(logging.DEBUG)

    # Formatters
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler (UTF-8 encoded)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return logging.getLogger(name)
