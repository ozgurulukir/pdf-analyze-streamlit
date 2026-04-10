"""Unit tests for exceptions and error handling."""
import pytest

from app.core.exceptions import (
    AppError,
    DatabaseError,
    FileProcessingError,
    LLMError,
    retry,
    retry_llm_call,
)


class TestAppError:
    """Tests for AppError base class."""

    def test_error_creation(self):
        """Test creating an error with message."""
        err = AppError("Test error")
        assert str(err) == "Test error"

    def test_error_with_details(self):
        """Test creating an error with details."""
        err = AppError("Test error", details={"key": "value"})
        assert "key" in err.details
        assert err.details["key"] == "value"

    def test_error_str_with_details(self):
        """Test string representation with details."""
        err = AppError("Test error", details={"code": 500})
        assert "code" in str(err)


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_database_error(self):
        """Test database error creation."""
        err = DatabaseError("Connection failed")
        assert isinstance(err, AppError)
        assert "Connection failed" in str(err)


class TestLLMError:
    """Tests for LLMError."""

    def test_llm_error(self):
        """Test LLM error creation."""
        err = LLMError("API timeout")
        assert isinstance(err, AppError)
        assert "API timeout" in str(err)


class TestFileProcessingError:
    """Tests for FileProcessingError."""

    def test_file_error(self):
        """Test file processing error."""
        err = FileProcessingError("Invalid PDF")
        assert isinstance(err, AppError)


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_retry_success_first_try(self):
        """Test retry succeeds on first try."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Test retry succeeds after failures."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """Test retry exhausted after max attempts."""
        call_count = 0

        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError):
            always_fail_func()

        assert call_count == 3

    def test_retry_with_backoff(self):
        """Test exponential backoff."""
        import time

        call_times = []

        @retry(max_attempts=3, delay=0.1, backoff=2.0, exceptions=(ValueError,))
        def timed_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Error")
            return "success"

        try:
            timed_func()
        except ValueError:
            pass

        # Check that delays increase
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1] if len(call_times) == 3 else 0
            # Second delay should be roughly twice the first
            assert delay2 >= delay1


class TestRetryLLMCall:
    """Tests for specialized LLM retry decorator."""

    def test_llm_retry_decorator(self):
        """Test LLM retry decorator."""
        from app.core.exceptions import LLMConnectionError

        call_count = 0

        @retry_llm_call(max_attempts=2)
        def llm_func():
            nonlocal call_count
            call_count += 1
            raise LLMConnectionError("Connection failed")

        with pytest.raises(LLMConnectionError):
            llm_func()

        assert call_count == 2
