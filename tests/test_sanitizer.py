"""Unit tests for sanitization utilities."""

from app.core.sanitizer import (
    Sanitizer,
    validate_email,
    validate_file_type,
    validate_uuid,
    validate_workspace_name,
)


class TestSanitizer:
    """Tests for Sanitizer class."""

    # ===================
    # String Sanitization
    # ===================

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = Sanitizer.sanitize_string("Hello World")

        assert result.is_valid is True
        assert result.sanitized_value == "Hello World"

    def test_sanitize_string_strips_html(self):
        """Test HTML stripping."""
        result = Sanitizer.sanitize_string("<script>alert('xss')</script>Hello", strip_html=True)

        assert result.is_valid is True
        assert "<script>" not in result.sanitized_value

    def test_sanitize_string_max_length(self):
        """Test max length validation."""
        long_string = "x" * 15000
        result = Sanitizer.sanitize_string(long_string, max_length=10000)

        assert result.is_valid is False
        assert "exceeds maximum" in result.error_message

    def test_sanitize_string_escapes_html(self):
        """Test HTML entity escaping."""
        result = Sanitizer.sanitize_string("<div>Test</div>")

        assert result.is_valid is True
        assert "&lt;" in result.sanitized_value

    def test_sanitize_string_no_newlines(self):
        """Test newline handling."""
        result = Sanitizer.sanitize_string("Hello\nWorld", allow_newlines=False)

        assert "\n" not in result.sanitized_value

    # ===================
    # Filename Sanitization
    # ===================

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        result = Sanitizer.sanitize_filename("document.pdf")

        assert result.is_valid is True
        assert result.sanitized_value == "document.pdf"

    def test_sanitize_filename_removes_path(self):
        """Test path component removal."""
        result = Sanitizer.sanitize_filename("../../../etc/passwd")

        assert result.is_valid is True
        assert "/" not in result.sanitized_value
        assert ".." not in result.sanitized_value

    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test dangerous character removal."""
        result = Sanitizer.sanitize_filename("file<>:\"|?*.pdf")

        assert result.is_valid is True
        # Should only keep safe characters
        assert all(c.isalnum() or c in "._-" for c in result.sanitized_value)

    def test_sanitize_filename_empty(self):
        """Test empty filename."""
        result = Sanitizer.sanitize_filename("")

        assert result.is_valid is False

    # ===================
    # SQL Injection Detection
    # ===================

    def test_sanitize_sql_safe(self):
        """Test safe SQL input."""
        result = Sanitizer.sanitize_sql("SELECT * FROM users")

        # Note: This is just for detection, not prevention
        # Parameterized queries should always be used
        assert result.is_valid is True

    def test_sanitize_sql_union_injection(self):
        """Test UNION injection detection."""
        result = Sanitizer.sanitize_sql("1' UNION SELECT * FROM users--")

        assert result.is_valid is False
        assert "SQL" in result.error_message

    def test_sanitize_sql_comment_injection(self):
        """Test comment injection detection."""
        result = Sanitizer.sanitize_sql("admin'--")

        assert result.is_valid is False

    # ===================
    # XSS Detection
    # ===================

    def test_sanitize_xss_safe(self):
        """Test safe HTML input."""
        result = Sanitizer.sanitize_xss("<p>Hello World</p>")

        assert result.is_valid is True

    def test_sanitize_xss_script_tag(self):
        """Test script tag detection."""
        result = Sanitizer.sanitize_xss("<script>alert('xss')</script>")

        assert result.is_valid is False
        assert "XSS" in result.error_message or "dangerous" in result.error_message.lower()

    def test_sanitize_xss_javascript_protocol(self):
        """Test javascript: protocol detection."""
        result = Sanitizer.sanitize_xss("javascript:alert('xss')")

        assert result.is_valid is False

    def test_sanitize_xss_event_handler(self):
        """Test event handler detection."""
        result = Sanitizer.sanitize_xss("<img onerror='alert(1)'>")

        assert result.is_valid is False

    # ===================
    # URL Sanitization
    # ===================

    def test_sanitize_url_valid_http(self):
        """Test valid HTTP URL."""
        result = Sanitizer.sanitize_url("http://example.com")

        assert result.is_valid is True
        assert result.sanitized_value == "http://example.com"

    def test_sanitize_url_valid_https(self):
        """Test valid HTTPS URL."""
        result = Sanitizer.sanitize_url("https://example.com/path?query=1")

        assert result.is_valid is True

    def test_sanitize_url_invalid_scheme(self):
        """Test invalid URL scheme."""
        result = Sanitizer.sanitize_url("ftp://example.com")

        assert result.is_valid is False
        assert "HTTP" in result.error_message

    def test_sanitize_url_javascript_scheme(self):
        """Test javascript: URL scheme."""
        result = Sanitizer.sanitize_url("javascript:alert('xss')")

        assert result.is_valid is False

    # ===================
    # Dict Sanitization
    # ===================

    def test_sanitize_dict_basic(self):
        """Test dictionary sanitization."""
        data = {
            "name": "Test",
            "age": "25",
            "active": "true"
        }
        schema = {
            "name": {"type": "string", "required": True},
            "age": {"type": "int"},
            "active": {"type": "bool"}
        }

        result = Sanitizer.sanitize_dict(data, schema)

        assert result["name"] == "Test"
        assert result["age"] == 25
        assert result["active"] is True

    def test_sanitize_dict_with_max_length(self):
        """Test dictionary with max length constraint."""
        data = {
            "description": "x" * 1000
        }
        schema = {
            "description": {"type": "string", "max_length": 100}
        }

        result = Sanitizer.sanitize_dict(data, schema)

        # Should be truncated or rejected based on implementation
        assert len(result["description"]) <= 100


class TestValidationFunctions:
    """Tests for validation utility functions."""

    def test_validate_email_valid(self):
        """Test valid email."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.org") is True

    def test_validate_email_invalid(self):
        """Test invalid email."""
        assert validate_email("not-an-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False

    def test_validate_uuid_valid(self):
        """Test valid UUID."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert validate_uuid("12345678-1234-5678-1234-567812345678") is True

    def test_validate_uuid_invalid(self):
        """Test invalid UUID."""
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("12345") is False

    def test_validate_workspace_name_valid(self):
        """Test valid workspace names."""
        assert validate_workspace_name("My Workspace") is True
        assert validate_workspace_name("workspace-1") is True
        assert validate_workspace_name("test_workspace") is True

    def test_validate_workspace_name_invalid(self):
        """Test invalid workspace names."""
        assert validate_workspace_name("") is False
        assert validate_workspace_name("x" * 300) is False  # Too long
        assert validate_workspace_name("123 workspace") is True  # Numbers allowed

    def test_validate_file_type_valid(self):
        """Test valid file types."""
        assert validate_file_type("pdf") is True
        assert validate_file_type(".pdf") is True
        assert validate_file_type("PDF") is True

    def test_validate_file_type_invalid(self):
        """Test invalid file types."""
        assert validate_file_type("exe") is False
        assert validate_file_type("bat") is False

    def test_validate_file_type_custom_allowed(self):
        """Test custom allowed file types."""
        assert validate_file_type("exe", allowed=["exe", "bat"]) is True
        assert validate_file_type("pdf", allowed=["exe", "bat"]) is False
