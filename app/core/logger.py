"""Logging utility for the application."""

import json
import logging
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

# Import config to check environment
try:
    from app.core.config import AppConfig

    _config = AppConfig()
    DEBUG_MODE = _config.DEBUG
except Exception:
    DEBUG_MODE = False


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "pdf_analyzer",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a standardized logger with console and optional file output.

    Args:
        name: Name of the logger
        level: Logging level (defaults to DEBUG if in development mode)
        log_file: Optional path to log file

    Returns:
        logging.Logger: Configured logger instance
    """
    if level is None:
        level = logging.DEBUG if DEBUG_MODE else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Avoid duplicate handlers

    # Console formatter (colored)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler (JSON for production, text for development)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    if log_file is None:
        log_file = str(log_dir / "app.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_execution(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time and results.

    Usage:
        @log_execution(logger)
        def my_function():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            logger.debug(f"Executing {func.__name__} with args={args}, kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator


# Global logger instance
logger = setup_logger()


# Named loggers for different modules
def get_module_logger(module_name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(f"pdf_analyzer.{module_name}")
