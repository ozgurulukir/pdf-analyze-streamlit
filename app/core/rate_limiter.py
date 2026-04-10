"""Rate limiting utilities for API calls."""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
from functools import wraps

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    enable_burst: bool = True


@dataclass
class RateLimitInfo:
    """Information about rate limit status."""

    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[float] = None
    message: str = ""


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

    Features:
    - Smooth rate limiting
    - Burst handling
    - Sliding window
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second
            capacity: Maximum token capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_available(self) -> float:
        """Get number of available tokens."""
        with self._lock:
            self._refill()
            return self.tokens


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    Tracks requests in a sliding time window for more accurate limiting.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_requests(self, key: str) -> None:
        """Remove requests outside the window."""
        cutoff = time.time() - self.window_seconds
        self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]

    def is_allowed(self, key: str = "default") -> tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            key: Identifier for rate limit (e.g., user ID, IP)

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        with self._lock:
            self._cleanup_old_requests(key)

            current_count = len(self.requests[key])

            if current_count < self.max_requests:
                self.requests[key].append(time.time())
                remaining = self.max_requests - current_count - 1
                return True, max(0, remaining)

            return False, 0

    def get_reset_time(self, key: str = "default") -> datetime:
        """Get time when rate limit resets."""
        with self._lock:
            if not self.requests[key]:
                return datetime.now()

            oldest = min(self.requests[key])
            return datetime.fromtimestamp(oldest + self.window_seconds)

    def reset(self, key: str = "default") -> None:
        """Reset rate limit for a key."""
        with self._lock:
            if key in self.requests:
                del self.requests[key]


class RateLimiter:
    """
    Combined rate limiter using token bucket and sliding window.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()

        # Per-minute limiter
        self.minute_limiter = SlidingWindowRateLimiter(
            max_requests=self.config.requests_per_minute, window_seconds=60
        )

        # Per-hour limiter
        self.hour_limiter = SlidingWindowRateLimiter(
            max_requests=self.config.requests_per_hour, window_seconds=3600
        )

        # Burst limiter
        self.bucket = TokenBucket(
            rate=self.config.requests_per_minute / 60, capacity=self.config.burst_limit
        )

    def check(self, key: str = "default") -> RateLimitInfo:
        """
        Check if request is allowed.

        Args:
            key: Identifier for rate limit

        Returns:
            RateLimitInfo with result
        """
        # Check burst first
        if self.config.enable_burst:
            if not self.bucket.consume():
                reset_at = datetime.now() + timedelta(seconds=1)
                return RateLimitInfo(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=1.0,
                    message="Burst limit exceeded",
                )

        # Check per-minute
        minute_allowed, minute_remaining = self.minute_limiter.is_allowed(
            f"{key}_minute"
        )
        if not minute_allowed:
            reset_at = self.minute_limiter.get_reset_time(f"{key}_minute")
            retry_after = (reset_at - datetime.now()).total_seconds()
            return RateLimitInfo(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
                message="Minute rate limit exceeded",
            )

        # Check per-hour
        hour_allowed, hour_remaining = self.hour_limiter.is_allowed(f"{key}_hour")
        if not hour_allowed:
            reset_at = self.hour_limiter.get_reset_time(f"{key}_hour")
            retry_after = (reset_at - datetime.now()).total_seconds()
            return RateLimitInfo(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
                message="Hourly rate limit exceeded",
            )

        return RateLimitInfo(
            allowed=True,
            remaining=min(minute_remaining, hour_remaining),
            reset_at=datetime.now() + timedelta(minutes=1),
            message="Request allowed",
        )

    def reset(self, key: str = "default") -> None:
        """Reset rate limits for a key."""
        self.minute_limiter.reset(f"{key}_minute")
        self.hour_limiter.reset(f"{key}_hour")


# ===================
# Global Rate Limiter
# ===================

_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _global_limiter
    if _global_limiter is None:
        from app.core.config import AppConfig

        config = AppConfig()

        rate_config = RateLimitConfig(
            requests_per_minute=config.RATE_LIMIT_RPM,
            requests_per_hour=config.RATE_LIMIT_RPM * 60,
            burst_limit=config.RATE_LIMIT_RPM // 6,
            enable_burst=config.RATE_LIMIT_ENABLED,
        )
        _global_limiter = RateLimiter(rate_config)

    return _global_limiter


def rate_limit(key_func: Optional[callable] = None):
    """
    Decorator to apply rate limiting to a function.

    Args:
        key_func: Function to generate rate limit key from args

    Usage:
        @rate_limit()
        def call_api():
            ...

        @rate_limit(key_func=lambda user_id: f"user_{user_id}")
        def call_api_for_user(user_id):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Generate key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__

            # Check rate limit
            info = limiter.check(key)

            if not info.allowed:
                logger.warning(f"Rate limit exceeded for {key}: {info.message}")
                raise RateLimitExceededError(
                    f"Rate limit exceeded: {info.message}",
                    retry_after=info.retry_after,
                    reset_at=info.reset_at,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        reset_at: Optional[datetime] = None,
    ):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after
        self.reset_at = reset_at


# ===================
# LLM-specific Rate Limiter
# ===================


class LLMRateLimiter:
    """
    Specialized rate limiter for LLM API calls.

    Features:
    - Per-model rate limiting
    - Per-workspace rate limiting
    - Token usage tracking (approximate)
    """

    def __init__(self):
        """Initialize LLM rate limiter."""
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = Lock()

    def get_limiter(self, model: str) -> RateLimiter:
        """Get or create rate limiter for a model."""
        with self._lock:
            if model not in self._limiters:
                # Different limits based on model
                # Smaller models can have higher limits
                if "mini" in model.lower() or "small" in model.lower():
                    config = RateLimitConfig(
                        requests_per_minute=120, requests_per_hour=5000, burst_limit=20
                    )
                else:
                    config = RateLimitConfig(
                        requests_per_minute=60, requests_per_hour=2000, burst_limit=10
                    )
                self._limiters[model] = RateLimiter(config)
            return self._limiters[model]

    def check(self, model: str, key: str = "default") -> RateLimitInfo:
        """Check if LLM request is allowed."""
        limiter = self.get_limiter(model)
        return limiter.check(f"{model}:{key}")

    def reset(self, model: str, key: str = "default") -> None:
        """Reset rate limit for a model/key."""
        limiter = self.get_limiter(model)
        limiter.reset(f"{model}:{key}")


# Global LLM rate limiter
_llm_limiter: Optional[LLMRateLimiter] = None


def get_llm_limiter() -> LLMRateLimiter:
    """Get the global LLM rate limiter."""
    global _llm_limiter
    if _llm_limiter is None:
        _llm_limiter = LLMRateLimiter()
    return _llm_limiter
