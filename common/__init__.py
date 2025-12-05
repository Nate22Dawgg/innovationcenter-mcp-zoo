"""
Common utilities for MCP servers.

Provides standardized logging, error handling, metrics, rate limiting,
circuit breakers, and health checks across all MCP servers.
"""

from .errors import (
    McpError,
    ApiError,
    ValidationError,
    RateLimitError,
    CircuitBreakerError,
    ErrorCode,
    format_error_response,
    create_error_response,
)
from .logging import (
    get_logger,
    setup_logging,
    log_request,
    log_response,
    log_error,
    request_context,
)
from .metrics import MetricsCollector, get_metrics_collector
from .rate_limit import (
    RateLimiter,
    TokenBucket,
    get_rate_limiter,
    exponential_backoff,
    retry_with_backoff,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerManager,
    get_circuit_breaker_manager,
)
from .health import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
    create_health_check_response,
)

__all__ = [
    # Errors
    "McpError",
    "ApiError",
    "ValidationError",
    "RateLimitError",
    "CircuitBreakerError",
    "ErrorCode",
    "format_error_response",
    "create_error_response",
    # Logging
    "get_logger",
    "setup_logging",
    "log_request",
    "log_response",
    "log_error",
    "request_context",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    # Rate Limiting
    "RateLimiter",
    "TokenBucket",
    "get_rate_limiter",
    "exponential_backoff",
    "retry_with_backoff",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerManager",
    "get_circuit_breaker_manager",
    # Health Checks
    "HealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    "create_health_check_response",
]

