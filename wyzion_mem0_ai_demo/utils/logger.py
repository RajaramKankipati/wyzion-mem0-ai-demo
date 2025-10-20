"""
Logging configuration for the Wyzion Mem0 AI Demo application.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging(name=__name__, log_level=None):
    """
    Configure application logging with both file and console handlers.

    Args:
        name: Logger name (usually __name__ from calling module)
        log_level: Optional log level override (defaults to LOG_LEVEL env var or INFO)

    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Log format with detailed information
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler - outputs to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)

    # File handler - rotating log files (10MB per file, keep 5 backups)
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10MB
    file_handler.setLevel(getattr(logging, log_level, logging.INFO))
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def configure_third_party_loggers():
    """Configure logging levels for third-party libraries"""
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name=__name__):
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__ from calling module)

    Returns:
        Configured logger instance
    """
    return setup_logging(name)
