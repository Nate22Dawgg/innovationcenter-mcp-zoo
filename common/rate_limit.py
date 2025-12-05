"""
Rate limiting utilities for MCP servers.

Provides token bucket rate limiting with exponential backoff for retries.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Callable, Optional, TypeVar, Any

from .errors import RateLimitError, ErrorCode

T = TypeVar("T")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int
    window_seconds: int
    name: Optional[str] = None


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, max_tokens: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            max_tokens: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = float(max_tokens)
        self.last_refill = time.time()
        self._lock = Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens are available
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0

            needed = tokens - self.tokens
            return needed / self.refill_rate

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


class RateLimiter:
    """Rate limiter with configurable limits per operation."""

    def __init__(self):
        """Initialize rate limiter."""
        self._buckets: dict[str, TokenBucket] = {}
        self._configs: dict[str, RateLimitConfig] = {}
        self._lock = Lock()

    def configure(
        self,
        name: str,
        max_requests: int,
        window_seconds: int,
    ):
        """
        Configure rate limit for an operation.

        Args:
            name: Operation name
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        with self._lock:
            refill_rate = max_requests / window_seconds
            self._buckets[name] = TokenBucket(max_requests, refill_rate)
            self._configs[name] = RateLimitConfig(
                max_requests=max_requests,
                window_seconds=window_seconds,
                name=name,
            )

    def acquire(self, name: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens for an operation.

        Args:
            name: Operation name
            tokens: Number of tokens needed

        Returns:
            True if acquired, False if rate limited
        """
        with self._lock:
            bucket = self._buckets.get(name)
            if bucket is None:
                # No rate limit configured, allow
                return True

            return bucket.acquire(tokens)

    def wait_if_needed(self, name: str, tokens: int = 1) -> float:
        """
        Wait if needed to respect rate limit.

        Args:
            name: Operation name
            tokens: Number of tokens needed

        Returns:
            Seconds waited (0 if not needed)
        """
        with self._lock:
            bucket = self._buckets.get(name)
            if bucket is None:
                return 0.0

            wait_time = bucket.time_until_available(tokens)
            if wait_time > 0:
                time.sleep(wait_time)
            return wait_time

    def check_rate_limit(self, name: str, tokens: int = 1) -> Optional[RateLimitError]:
        """
        Check if rate limit is exceeded, return error if so.

        Args:
            name: Operation name
            tokens: Number of tokens needed

        Returns:
            RateLimitError if exceeded, None otherwise
        """
        if not self.acquire(name, tokens):
            config = self._configs.get(name)
            wait_time = self.time_until_available(name, tokens)

            return RateLimitError(
                message=f"Rate limit exceeded for '{name}'. Retry after {int(wait_time)} seconds.",
                retry_after=int(wait_time),
            )
        return None

    def time_until_available(self, name: str, tokens: int = 1) -> float:
        """Get time until tokens are available."""
        with self._lock:
            bucket = self._buckets.get(name)
            if bucket is None:
                return 0.0
            return bucket.time_until_available(tokens)


def exponential_backoff(
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
    jitter: bool = True,
) -> Callable[[int], float]:
    """
    Create exponential backoff function.

    Args:
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Backoff multiplier
        jitter: Whether to add random jitter

    Returns:
        Function that takes attempt number and returns delay
    """
    import random

    def backoff(attempt: int) -> float:
        delay = min(base_delay * (multiplier ** attempt), max_delay)
        if jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay

    return backoff


def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    backoff_fn: Optional[Callable[[int], float]] = None,
    retry_on: Optional[Callable[[Exception], bool]] = None,
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        backoff_fn: Backoff function (attempt -> delay)
        retry_on: Function to determine if exception should be retried

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    if backoff_fn is None:
        backoff_fn = exponential_backoff()

    last_exception = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e

            # Check if we should retry this exception
            if retry_on and not retry_on(e):
                raise

            # Don't retry on last attempt
            if attempt < max_attempts - 1:
                delay = backoff_fn(attempt)
                time.sleep(delay)
            else:
                raise

    raise last_exception


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

