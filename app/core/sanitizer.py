"""Input sanitization and validation utilities."""

import re
import html
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SanitizationResult:
    """Result of sanitization operation."""

    is_valid: bool
    sanitized_value: Any
    error_message: Optional[str] = None


class Sanitizer:
    """
    Input sanitization utilities for security.

    Provides methods to sanitize various types of user input
    to prevent injection attacks and ensure data integrity.
    """

    # Dangerous patterns for SQL injection (basic detection)
    SQL_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(--|\#|\/\*|\*\/)",  # SQL comments
        r"(\bor\b.*\b1\s*=\s*1\b)",
        r"(\band\b.*\b1\s*=\s*1\b)",
    ]

    # HTML/XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
    ]

    @classmethod
    def sanitize_string(
        cls,
        value: str,
        max_length: int = 10000,
        strip_html: bool = True,
        allow_newlines: bool = True,
    ) -> SanitizationResult:
        """
        Sanitize a string input.

        Args:
            value: Input string
            max_length: Maximum allowed length
            strip_html: Whether to strip HTML tags
            allow_newlines: Whether to allow newlines

        Returns:
            SanitizationResult with sanitized value
        """
        if not isinstance(value, str):
            return SanitizationResult(
                is_valid=False,
                sanitized_value="",
                error_message="Input must be a string",
            )

        # Check length
        if len(value) > max_length:
            return SanitizationResult(
                is_valid=False,
                sanitized_value="",
                error_message=f"Input exceeds maximum length of {max_length}",
            )

        # Strip HTML if requested
        if strip_html:
            value = cls._strip_html(value)

        # Escape HTML entities
        value = html.escape(value)

        # Handle newlines
        if not allow_newlines:
            value = value.replace("\n", " ").replace("\r", "")

        # Trim whitespace
        value = value.strip()

        return SanitizationResult(is_valid=True, sanitized_value=value)

    @classmethod
    def sanitize_filename(cls, filename: str) -> SanitizationResult:
        """
        Sanitize a filename for safe storage.

        Args:
            filename: Input filename

        Returns:
            SanitizationResult with sanitized filename
        """
        if not filename:
            return SanitizationResult(
                is_valid=False,
                sanitized_value="",
                error_message="Filename cannot be empty",
            )

        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Remove dangerous characters
        filename = re.sub(r"[^\w\s\-\.]", "", filename)

        # Limit length
        max_name = 255
        if len(filename) > max_name:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = (
                name[: max_name - len(ext) - 1] + "." + ext if ext else name[:max_name]
            )

        # Ensure not empty
        if not filename:
            return SanitizationResult(
                is_valid=False,
                sanitized_value="",
                error_message="Invalid filename after sanitization",
            )

        return SanitizationResult(is_valid=True, sanitized_value=filename)

    @classmethod
    def sanitize_sql(cls, value: str) -> SanitizationResult:
        """
        Check for potential SQL injection patterns.

        Args:
            value: Input string to check

        Returns:
            SanitizationResult with validation status
        """
        if not isinstance(value, str):
            return SanitizationResult(is_valid=True, sanitized_value=value)

        value_lower = value.lower()

        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:50]}...")
                return SanitizationResult(
                    is_valid=False,
                    sanitized_value="",
                    error_message="Input contains potentially dangerous SQL patterns",
                )

        return SanitizationResult(is_valid=True, sanitized_value=value)

    @classmethod
    def sanitize_xss(cls, value: str) -> SanitizationResult:
        """
        Check for potential XSS attack patterns.

        Args:
            value: Input string to check

        Returns:
            SanitizationResult with validation status
        """
        if not isinstance(value, str):
            return SanitizationResult(is_valid=True, sanitized_value=value)

        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {value[:50]}...")
                return SanitizationResult(
                    is_valid=False,
                    sanitized_value="",
                    error_message="Input contains potentially dangerous HTML/JS patterns",
                )

        return SanitizationResult(is_valid=True, sanitized_value=value)

    @classmethod
    def sanitize_url(cls, url: str) -> SanitizationResult:
        """
        Validate and sanitize a URL.

        Args:
            url: Input URL

        Returns:
            SanitizationResult with sanitized URL
        """
        try:
            parsed = urlparse(url)

            # Only allow http and https
            if parsed.scheme not in ("http", "https"):
                return SanitizationResult(
                    is_valid=False,
                    sanitized_value="",
                    error_message="Only HTTP and HTTPS URLs are allowed",
                )

            # Block dangerous schemes
            if parsed.scheme in ("javascript", "data", "vbscript"):
                return SanitizationResult(
                    is_valid=False,
                    sanitized_value="",
                    error_message="Dangerous URL scheme not allowed",
                )

            return SanitizationResult(is_valid=True, sanitized_value=url)
        except Exception as e:
            return SanitizationResult(
                is_valid=False, sanitized_value="", error_message=f"Invalid URL: {e}"
            )

    @classmethod
    def sanitize_dict(
        cls, data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sanitize a dictionary based on a schema.

        Args:
            data: Input dictionary
            schema: Schema with field definitions

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for field_name, field_schema in schema.items():
            value = data.get(field_name)
            field_type = field_schema.get("type", "string")
            required = field_schema.get("required", False)
            max_length = field_schema.get("max_length")

            # Handle missing required fields
            if value is None or value == "":
                if required:
                    sanitized[field_name] = None
                continue

            # Type-specific sanitization
            if field_type == "string":
                result = cls.sanitize_string(
                    value,
                    max_length=max_length,
                    strip_html=field_schema.get("strip_html", True),
                    allow_newlines=field_schema.get("allow_newlines", True),
                )
                sanitized[field_name] = (
                    result.sanitized_value if result.is_valid else ""
                )

            elif field_type == "filename":
                result = cls.sanitize_filename(value)
                sanitized[field_name] = (
                    result.sanitized_value if result.is_valid else ""
                )

            elif field_type == "url":
                result = cls.sanitize_url(value)
                sanitized[field_name] = (
                    result.sanitized_value if result.is_valid else ""
                )

            elif field_type == "int":
                try:
                    sanitized[field_name] = int(value)
                except (ValueError, TypeError):
                    sanitized[field_name] = 0

            elif field_type == "float":
                try:
                    sanitized[field_name] = float(value)
                except (ValueError, TypeError):
                    sanitized[field_name] = 0.0

            elif field_type == "bool":
                sanitized[field_name] = bool(value)

            else:
                sanitized[field_name] = value

        return sanitized

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        # Remove script and style elements
        text = re.sub(
            r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE
        )
        text = re.sub(
            r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE
        )

        # Remove all HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        return text


# ===================
# Validation Utilities
# ===================


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format."""
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(pattern, uuid_str.lower()))


def validate_workspace_name(name: str) -> bool:
    """
    Validate workspace name.

    Rules:
    - 1-255 characters
    - Alphanumeric, spaces, hyphens, underscores
    - Must start with alphanumeric
    """
    if not name or len(name) > 255:
        return False
    return bool(re.match(r"^[a-zA-Z0-9][\w\s\-]*$", name))


def validate_file_type(extension: str, allowed: Optional[List[str]] = None) -> bool:
    """
    Validate file extension.

    Args:
        extension: File extension (with or without dot)
        allowed: List of allowed extensions

    Returns:
        True if valid
    """
    # Normalize extension
    ext = extension.lower().lstrip(".")

    # Default allowed types
    if allowed is None:
        from app.core.constants import FileTypes

        allowed = FileTypes.ALLOWED_EXTENSIONS

    return ext in [a.lower().lstrip(".") for a in allowed]
