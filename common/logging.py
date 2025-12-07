"""
Structured logging utilities for MCP servers.

Provides JSON-formatted structured logging with request tracking,
error logging, and performance metrics.
"""

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, Callable

try:
    from .phi import redact_phi
except ImportError:
    # Fallback if phi module not available
    def redact_phi(payload: Any) -> Any:
        return payload

# Configure JSON logging formatter
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add standard fields from record
        for key in [
            "server_name", "tool_name", "request_id", "trace_id", "correlation_id",
            "duration_ms", "status_code", "upstream", "upstream_error_code"
        ]:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data)


def setup_logging(
    server_name: str,
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Set up structured logging for an MCP server.

    Args:
        server_name: Name of the MCP server
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ("json" or "text")
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(server_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(server_name: str) -> logging.Logger:
    """
    Get or create a logger for an MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        Logger instance
    """
    logger = logging.getLogger(server_name)
    if not logger.handlers:
        # If logger hasn't been configured, set up with defaults
        logger = setup_logging(server_name)
    return logger


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for request tracking.

    Returns:
        UUID string formatted as correlation ID
    """
    return str(uuid.uuid4())


def log_request(
    logger: logging.Logger,
    tool_name: str,
    server_name: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    input_params: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """
    Log a tool request with structured data.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being called
        server_name: Name of the MCP server
        request_id: Optional request ID for tracking (generated if not provided)
        trace_id: Optional trace ID for distributed tracing
        correlation_id: Optional correlation ID (generated if not provided)
        input_params: Optional input parameters (will be sanitized)
        **kwargs: Additional fields to include in log
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    if request_id is None:
        request_id = correlation_id

    extra = {
        "tool_name": tool_name,
        "event_type": "request_start",
        "correlation_id": correlation_id,
        "request_id": request_id,
    }
    if server_name:
        extra["server_name"] = server_name
    if trace_id:
        extra["trace_id"] = trace_id
    if input_params:
        # Sanitize and redact PHI from input params
        sanitized = _sanitize_params(input_params)
        extra["input_params"] = redact_phi(sanitized)
    else:
        extra["input_params"] = None
    
    # Redact PHI from all kwargs
    redacted_kwargs = redact_phi(kwargs) if kwargs else {}
    extra.update(redacted_kwargs)

    logger.info(f"Tool request: {tool_name}", extra={"extra_fields": extra})


def log_response(
    logger: logging.Logger,
    tool_name: str,
    duration_ms: float,
    status: str = "success",
    server_name: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    upstream: Optional[str] = None,
    upstream_error_code: Optional[str] = None,
    **kwargs,
):
    """
    Log a tool response with structured data.

    Args:
        logger: Logger instance
        tool_name: Name of the tool
        duration_ms: Request duration in milliseconds
        status: Response status ("success", "error", "timeout", etc.)
        server_name: Name of the MCP server
        request_id: Optional request ID for tracking
        trace_id: Optional trace ID for distributed tracing
        correlation_id: Optional correlation ID
        upstream: Optional upstream service name (if error from upstream)
        upstream_error_code: Optional upstream error code
        **kwargs: Additional fields to include in log
    """
    extra = {
        "tool_name": tool_name,
        "duration_ms": round(duration_ms, 2),
        "status": status,
        "event_type": "request_complete",
    }
    if server_name:
        extra["server_name"] = server_name
    if request_id:
        extra["request_id"] = request_id
    if trace_id:
        extra["trace_id"] = trace_id
    if correlation_id:
        extra["correlation_id"] = correlation_id
    if upstream:
        extra["upstream"] = upstream
    if upstream_error_code:
        extra["upstream_error_code"] = upstream_error_code
    
    # Redact PHI from all kwargs before adding to extra
    redacted_kwargs = redact_phi(kwargs) if kwargs else {}
    extra.update(redacted_kwargs)
    
    # Redact PHI from the entire extra dict
    extra = redact_phi(extra)

    level = logging.INFO if status == "success" else logging.ERROR
    logger.log(level, f"Tool response: {tool_name}", extra={"extra_fields": extra})


def log_error(
    logger: logging.Logger,
    error: Exception,
    tool_name: Optional[str] = None,
    server_name: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    upstream: Optional[str] = None,
    upstream_error_code: Optional[str] = None,
    **kwargs,
):
    """
    Log an error with structured data.

    Args:
        logger: Logger instance
        error: Exception to log
        tool_name: Optional tool name
        server_name: Name of the MCP server
        request_id: Optional request ID
        trace_id: Optional trace ID for distributed tracing
        correlation_id: Optional correlation ID
        upstream: Optional upstream service name (if error from upstream)
        upstream_error_code: Optional upstream error code
        **kwargs: Additional fields to include in log
    """
    extra = {
        "event_type": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if tool_name:
        extra["tool_name"] = tool_name
    if server_name:
        extra["server_name"] = server_name
    if request_id:
        extra["request_id"] = request_id
    if trace_id:
        extra["trace_id"] = trace_id
    if correlation_id:
        extra["correlation_id"] = correlation_id
    if upstream:
        extra["upstream"] = upstream
    if upstream_error_code:
        extra["upstream_error_code"] = upstream_error_code
    
    # Redact PHI from all kwargs
    redacted_kwargs = redact_phi(kwargs) if kwargs else {}
    extra.update(redacted_kwargs)
    
    # Redact PHI from the entire extra dict
    extra = redact_phi(extra)

    logger.error(f"Error in {tool_name or 'unknown'}: {error}", extra={"extra_fields": extra}, exc_info=True)


@contextmanager
def request_context(
    logger: logging.Logger,
    tool_name: str,
    server_name: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    log_input: bool = True,
    **input_params,
):
    """
    Context manager for tracking request execution with full observability.

    Args:
        logger: Logger instance
        tool_name: Name of the tool
        server_name: Name of the MCP server
        request_id: Optional request ID (generated if not provided)
        trace_id: Optional trace ID for distributed tracing
        correlation_id: Optional correlation ID (generated if not provided)
        log_input: Whether to log input parameters
        **input_params: Input parameters to log

    Yields:
        Context dictionary with request metadata including correlation_id, trace_id, etc.
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    if request_id is None:
        request_id = correlation_id

    start_time = time.time()
    context = {
        "tool_name": tool_name,
        "server_name": server_name,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "start_time": start_time,
    }

    if log_input and input_params:
        # Sanitize input for logging (remove sensitive data and PHI)
        sanitized_params = _sanitize_params(input_params)
        # Apply PHI redaction after sanitization
        sanitized_params = redact_phi(sanitized_params)
        log_request(
            logger, tool_name, server_name=server_name,
            request_id=request_id, trace_id=trace_id, correlation_id=correlation_id,
            input_params=sanitized_params
        )
    else:
        log_request(
            logger, tool_name, server_name=server_name,
            request_id=request_id, trace_id=trace_id, correlation_id=correlation_id
        )

    try:
        yield context
        duration_ms = (time.time() - start_time) * 1000
        log_response(
            logger, tool_name, duration_ms, "success",
            server_name=server_name, request_id=request_id,
            trace_id=trace_id, correlation_id=correlation_id
        )
        context["duration_ms"] = duration_ms
        context["status"] = "success"
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        # Extract upstream error info if it's an ApiError
        upstream = None
        upstream_error_code = None
        if hasattr(e, "details") and isinstance(e.details, dict):
            upstream = e.details.get("upstream")
            upstream_error_code = e.details.get("status_code") or e.details.get("error_code")
        
        log_error(
            logger, e, tool_name, server_name=server_name,
            request_id=request_id, trace_id=trace_id, correlation_id=correlation_id,
            upstream=upstream, upstream_error_code=str(upstream_error_code) if upstream_error_code else None
        )
        log_response(
            logger, tool_name, duration_ms, "error",
            server_name=server_name, request_id=request_id,
            trace_id=trace_id, correlation_id=correlation_id,
            upstream=upstream, upstream_error_code=str(upstream_error_code) if upstream_error_code else None,
            error=str(e)
        )
        context["duration_ms"] = duration_ms
        context["status"] = "error"
        context["error"] = str(e)
        raise


def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from parameters."""
    sensitive_keys = {"api_key", "password", "token", "secret", "authorization"}
    sanitized = {}
    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_params(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [_sanitize_params(item) for item in value]
        else:
            sanitized[key] = value
    return sanitized


def log_tool_call(func: Callable) -> Callable:
    """
    Decorator to automatically log tool calls.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to get logger from function's module or use default
        logger_name = func.__module__ or "mcp_server"
        logger = get_logger(logger_name)

        tool_name = func.__name__
        with request_context(logger, tool_name, **kwargs):
            return await func(*args, **kwargs)

    return wrapper

