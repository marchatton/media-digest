"""Logging configuration for Media Digest."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: str | Path | None = None, level: int = logging.INFO) -> None:
    """Set up logging with both file and console handlers.

    Args:
        log_file: Path to log file
        level: Logging level
    """
    if log_file is None:
        # Deferred import avoids circular dependency during config initialization
        from src.config import config  # pylint: disable=import-outside-toplevel

        log_path = config.logs_dir / "digest.log"
    else:
        log_path = Path(log_file)

    # Create logs directory if it doesn't exist
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(str(log_path), maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
