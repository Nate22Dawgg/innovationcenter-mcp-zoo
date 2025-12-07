"""
Distributed tracing utilities for MCP servers.

Provides trace ID generation and propagation for distributed tracing across
MCP servers and upstream services.
"""

import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context variable for storing trace ID in async context
_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def generate_trace_id() -> str:
    """
    Generate a unique trace ID for distributed tracing.

    Returns:
        UUID string formatted as trace ID
    """
    return str(uuid.uuid4())


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from context.

    Returns:
        Current trace ID or None if not set
    """
    return _trace_id.get()


def set_trace_id(trace_id: Optional[str]) -> None:
    """
    Set the trace ID in the current context.

    Args:
        trace_id: Trace ID to set (None to clear)
    """
    _trace_id.set(trace_id)


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """
    Set the correlation ID in the current context.

    Args:
        correlation_id: Correlation ID to set (None to clear)
    """
    _correlation_id.set(correlation_id)


def get_trace_context() -> Dict[str, Optional[str]]:
    """
    Get the current trace context (trace_id and correlation_id).

    Returns:
        Dictionary with trace_id and correlation_id
    """
    return {
        "trace_id": get_trace_id(),
        "correlation_id": get_correlation_id(),
    }


def inject_trace_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Inject trace IDs into HTTP headers for upstream calls.

    This allows trace IDs to be propagated to upstream services
    (e.g., when biotech-markets-mcp calls sec-edgar-mcp or PubMed).

    Args:
        headers: Optional existing headers dictionary

    Returns:
        Headers dictionary with trace IDs injected
    """
    if headers is None:
        headers = {}

    trace_id = get_trace_id()
    correlation_id = get_correlation_id()

    if trace_id:
        headers["X-Trace-Id"] = trace_id
    if correlation_id:
        headers["X-Correlation-Id"] = correlation_id

    return headers


def extract_trace_headers(headers: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Extract trace IDs from HTTP headers.

    Used when receiving requests from other MCP servers or clients.

    Args:
        headers: HTTP headers dictionary

    Returns:
        Dictionary with trace_id and correlation_id extracted from headers
    """
    trace_id = headers.get("X-Trace-Id") or headers.get("trace-id")
    correlation_id = headers.get("X-Correlation-Id") or headers.get("correlation-id")

    return {
        "trace_id": trace_id,
        "correlation_id": correlation_id,
    }


def propagate_trace_context(
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    generate_new: bool = False,
) -> Dict[str, Optional[str]]:
    """
    Propagate trace context to a new operation.

    If trace_id/correlation_id are provided, they are used.
    If generate_new is True and IDs are not provided, new ones are generated.
    Otherwise, existing context IDs are used.

    Args:
        trace_id: Optional trace ID to use
        correlation_id: Optional correlation ID to use
        generate_new: Whether to generate new IDs if not provided

    Returns:
        Dictionary with trace_id and correlation_id
    """
    if trace_id is None:
        trace_id = get_trace_id()
        if trace_id is None and generate_new:
            trace_id = generate_trace_id()

    if correlation_id is None:
        correlation_id = get_correlation_id()
        if correlation_id is None and generate_new:
            from .logging import generate_correlation_id
            correlation_id = generate_correlation_id()

    # Set in context for this operation
    if trace_id:
        set_trace_id(trace_id)
    if correlation_id:
        set_correlation_id(correlation_id)

    return {
        "trace_id": trace_id,
        "correlation_id": correlation_id,
    }
