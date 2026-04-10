"""Custom exception classes for specific error handling."""

from typing import Optional, Any, Dict
from functools import wraps
import time
import requests

from app.core.logger import get_logger

logger = get_logger(__name__)


# ===================
# Base Exceptions
# ===================


class AppError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the error.

        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ===================
# Database Exceptions
# ===================


class DatabaseError(AppError):
    """Raised when a database operation fails."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection cannot be established."""

    pass


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""

    pass


class MigrationError(DatabaseError):
    """Raised when database migration fails."""

    pass


# ===================
# ChromaDB Exceptions
# ===================


class ChromaError(AppError):
    """Raised when Chroma vector store operations fail."""

    pass


class ChromaConnectionError(ChromaError):
    """Raised when ChromaDB connection fails."""

    pass


class ChromaCollectionError(ChromaError):
    """Raised when ChromaDB collection operations fail."""

    pass


class EmbeddingError(ChromaError):
    """Raised when embedding generation fails."""

    pass


# ===================
# LLM Exceptions
# ===================


class LLMError(AppError):
    """Raised when LLM/RAG chain operations fail."""

    pass


class LLMConnectionError(LLMError):
    """Raised when LLM API connection fails."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    pass


class LLMResponseError(LLMError):
    """Raised when LLM returns an invalid or unexpected response."""

    pass


class RateLimitError(LLMError):
    """Raised when API rate limit is exceeded."""

    pass


# ===================
# File Exceptions
# ===================


class FileProcessingError(AppError):
    """Raised when file loading or processing fails."""

    pass


class FileNotFoundError(FileProcessingError):
    """Raised when a file is not found."""

    pass


class InvalidFileTypeError(FileProcessingError):
    """Raised when file type is not allowed."""

    pass


class FileTooLargeError(FileProcessingError):
    """Raised when file exceeds size limit."""

    pass


class FileCorruptedError(FileProcessingError):
    """Raised when file appears to be corrupted."""

    pass


# ===================
# Workspace Exceptions
# ===================


class WorkspaceError(AppError):
    """Base class for workspace-related errors."""

    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when workspace is not found."""

    pass


class WorkspaceExistsError(WorkspaceError):
    """Raised when attempting to create duplicate workspace."""

    pass


# ===================
# Configuration Exceptions
# ===================


class ConfigurationError(AppError):
    """Raised when there is a configuration-related issue."""

    pass


class EnvironmentVariableError(ConfigurationError):
    """Raised when required environment variable is missing."""

    pass


class ValidationError(AppError):
    """Raised when input validation fails."""

    pass


# ===================
# Retry Decorator
# ===================


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch

    Returns:
        Decorated function

    Example:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        def call_api():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator


def retry_llm_call(max_attempts: int = 3):
    """
    Specialized retry decorator for LLM API calls.

    Args:
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorated function
    """
    return retry(
        max_attempts=max_attempts,
        delay=2.0,
        backoff=2.0,
        exceptions=(
            LLMConnectionError,
            LLMTimeoutError,
            RateLimitError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ),
    )
