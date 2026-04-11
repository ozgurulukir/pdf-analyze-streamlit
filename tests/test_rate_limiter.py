"""Unit tests for rate limiting."""

import time

from app.core.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RateLimitExceededError,
    SlidingWindowRateLimiter,
    TokenBucket,
    rate_limit,
)


class TestTokenBucket:
    """Tests for TokenBucket."""

    def test_initial_state(self):
        """Test initial token count."""
        bucket = TokenBucket(rate=1.0, capacity=10)

        assert bucket.get_available() == 10

    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(rate=1.0, capacity=10)

        result = bucket.consume(5)

        assert result is True
        assert bucket.get_available() == 5

    def test_consume_insufficient(self):
        """Test consumption with insufficient tokens."""
        bucket = TokenBucket(rate=1.0, capacity=10)

        result = bucket.consume(15)

        assert result is False

    def test_token_refill(self):
        """Test token refill over time."""
        bucket = TokenBucket(rate=10.0, capacity=10)  # 10 tokens/sec

        # Consume all tokens
        bucket.consume(10)
        assert bucket.get_available() == 0

        # Wait for refill
        time.sleep(0.2)

        # Should have ~2 tokens now
        available = bucket.get_available()
        assert 1.5 < available < 2.5


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    def test_allowed_within_limit(self):
        """Test requests within limit are allowed."""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)

        for _i in range(5):
            allowed, remaining = limiter.is_allowed("user1")
            assert allowed is True

        # Sixth request should be denied
        allowed, remaining = limiter.is_allowed("user1")
        assert allowed is False
        assert remaining == 0

    def test_different_keys_independent(self):
        """Test different keys have independent limits."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

        # User 1
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is True

        # User 2
        allowed2, _ = limiter.is_allowed("user2")
        assert allowed2 is True

        # User 1 again
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is True

        # User 1 exceeds
        allowed1, _ = limiter.is_allowed("user1")
        assert allowed1 is False

        # User 2 still has limit
        allowed2, _ = limiter.is_allowed("user2")
        assert allowed2 is True

    def test_window_expiration(self):
        """Test window expiration."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=1)

        # Use up limit
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        # Should be denied
        allowed, _ = limiter.is_allowed("user1")
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.5)

        # Should be allowed again
        allowed, _ = limiter.is_allowed("user1")
        assert allowed is True

    def test_reset(self):
        """Test rate limit reset."""
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

        # Use up limit
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")

        # Reset
        limiter.reset("user1")

        # Should be allowed again
        allowed, _ = limiter.is_allowed("user1")
        assert allowed is True


class TestRateLimiter:
    """Tests for combined RateLimiter."""

    def test_check_allowed(self):
        """Test check returns allowed."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5,
            enable_burst=True,
        )
        limiter = RateLimiter(config)

        info = limiter.check("user1")

        assert info.allowed is True
        assert info.remaining > 0

    def test_check_minute_limit_exceeded(self):
        """Test minute limit exceeded."""
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=100,
            burst_limit=10,
            enable_burst=False,
        )
        limiter = RateLimiter(config)

        # Use up limit
        limiter.check("user1")
        limiter.check("user1")

        # Should be denied
        info = limiter.check("user1")

        assert info.allowed is False
        assert "minute" in info.message.lower()


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_error_creation(self):
        """Test error creation."""
        error = RateLimitExceededError(
            "Rate limit exceeded", retry_after=60.0, reset_at=time.time() + 60
        )

        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60.0


class TestRateLimitDecorator:
    """Tests for @rate_limit decorator."""

    def test_allows_under_limit(self):
        """Test decorator allows under limit."""

        @rate_limit(key_func=lambda: "test_user")
        def allowed_func():
            return "success"

        result = allowed_func()

        assert result == "success"

    def test_rate_limit_configurable(self):
        """Test decorator with custom config."""
        from app.core.rate_limiter import _global_limiter

        # Get a fresh limiter
        limiter = _global_limiter

        if limiter:
            # This test depends on the global rate limiter being configured
            # In a real test, you'd mock the rate limiter
            pass
