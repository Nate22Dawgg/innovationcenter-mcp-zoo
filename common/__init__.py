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
    map_upstream_error,
    handle_mcp_tool_error,
)
from .logging import (
    get_logger,
    setup_logging,
    log_request,
    log_response,
    log_error,
    request_context,
    generate_correlation_id,
)
from .metrics import MetricsCollector, get_metrics_collector
from .tracing import (
    generate_trace_id,
    get_trace_id,
    set_trace_id,
    get_correlation_id,
    set_correlation_id,
    get_trace_context,
    inject_trace_headers,
    extract_trace_headers,
    propagate_trace_context,
)
from .observability import (
    observe_tool_call,
    observe_tool_call_sync,
    create_observable_tool_wrapper,
)
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
from .http import (
    CallOptions,
    call_upstream,
    call_upstream_async,
    get,
    get_async,
    post,
    post_async,
)
try:
    from .validation import (
        SchemaValidator,
        get_validator,
        validate_tool_input,
        validate_tool_output,
        validated_tool,
    )
except ImportError:
    # Validation module may not exist in all installations
    pass
from .phi import (
    redact_phi,
    is_phi_field,
    mark_ephemeral,
    mark_stored,
    is_ephemeral,
    should_persist,
)
from .config import (
    ConfigIssue,
    ServerConfig,
    ConfigValidationError,
    validate_config_or_raise,
)
from .cache import (
    Cache,
    CacheEntry,
    get_cache,
    build_cache_key,
    build_cache_key_simple,
)
from .dcap import (
    DCAPConfig,
    ToolSignature,
    Connector,
    ToolMetadata,
    send_dcap_semantic_discover,
    send_dcap_perf_update,
    dcap_tool_wrapper,
    register_tools_with_dcap,
    DCAP_ENABLED,
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
    "map_upstream_error",
    "handle_mcp_tool_error",
    # Logging
    "get_logger",
    "setup_logging",
    "log_request",
    "log_response",
    "log_error",
    "request_context",
    "generate_correlation_id",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    # Tracing
    "generate_trace_id",
    "get_trace_id",
    "set_trace_id",
    "get_correlation_id",
    "set_correlation_id",
    "get_trace_context",
    "inject_trace_headers",
    "extract_trace_headers",
    "propagate_trace_context",
    # Observability
    "observe_tool_call",
    "observe_tool_call_sync",
    "create_observable_tool_wrapper",
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
    # HTTP Client
    "CallOptions",
    "call_upstream",
    "call_upstream_async",
    "get",
    "get_async",
    "post",
    "post_async",
    # Validation
    "SchemaValidator",
    "get_validator",
    "validate_tool_input",
    "validate_tool_output",
    "validated_tool",
    # Configuration
    "ConfigIssue",
    "ServerConfig",
    "ConfigValidationError",
    "validate_config_or_raise",
    # Cache
    "Cache",
    "CacheEntry",
    "get_cache",
    "build_cache_key",
    "build_cache_key_simple",
    # PHI Handling
    "redact_phi",
    "is_phi_field",
    "mark_ephemeral",
    "mark_stored",
    "is_ephemeral",
    "should_persist",
    # DCAP (Dynamic Capability Acquisition Protocol)
    "DCAPConfig",
    "ToolSignature",
    "Connector",
    "ToolMetadata",
    "send_dcap_semantic_discover",
    "send_dcap_perf_update",
    "dcap_tool_wrapper",
    "register_tools_with_dcap",
    "DCAP_ENABLED",
]

