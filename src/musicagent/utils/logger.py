"""
Logging configuration and utilities.

This module provides comprehensive logging setup with file rotation,
structured output, and request/response tracking for the MusicAgent application.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pythonjsonlogger.json import JsonFormatter

try:
    from pythonjsonlogger.json import JsonFormatter
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


def setup_logger(
    name: str = "musicagent",
    log_level: str = "INFO",
    log_dir: Path = Path("logs"),
    log_file: str = "musicagent.log",
    error_log_file: str = "errors.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_format: str = "json",
) -> logging.Logger:
    """
    Set up comprehensive logging with file rotation.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_file: Main log file name
        error_log_file: Error log file name
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_format: Format type (json or text)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Ensure log directory exists
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Define formatters
    if log_format == "json" and HAS_JSON_LOGGER:
        formatter = JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (all logs)
    file_handler = RotatingFileHandler(
        log_dir / log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_handler = RotatingFileHandler(
        log_dir / error_log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


class RequestLogger:
    """Helper class for logging API requests and responses."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize request logger.

        Args:
            logger: Logger instance to use
        """
        self.logger = logger

    def log_request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Log API request details.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            request_id: Request correlation ID
        """
        self.logger.info(
            "API Request",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "params": params,
            },
        )

    def log_response(
        self,
        status_code: int,
        response_time: float,
        request_id: Optional[str] = None,
        size: Optional[int] = None,
    ) -> None:
        """
        Log API response details.

        Args:
            status_code: HTTP status code
            response_time: Response time in seconds
            request_id: Request correlation ID
            size: Response size in bytes
        """
        self.logger.info(
            "API Response",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "response_time_ms": response_time * 1000,
                "response_size_bytes": size,
            },
        )

    def log_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> None:
        """
        Log API error.

        Args:
            error: Exception that occurred
            request_id: Request correlation ID
            context: Additional error context
        """
        self.logger.error(
            f"API Error: {str(error)}",
            extra={
                "request_id": request_id,
                "error_type": type(error).__name__,
                "context": context,
            },
            exc_info=True,
        )
