"""
Comprehensive observability wrapper for MCP tool calls.

Provides a unified decorator/wrapper that automatically handles:
- Metrics collection (mcp_tool_calls_total, mcp_tool_latency_ms, mcp_tool_upstream_errors_total)
- Structured logging with correlation IDs and trace IDs
- Error tracking with upstream error codes
- Trace ID propagation

Usage:
    from common.observability import observe_tool_call

    @observe_tool_call(server_name="my-mcp-server")
    async def my_tool(**kwargs):
        # Your tool implementation
        pass
"""

import functools
import time
from typing import Any, Callable, Dict, Optional

from .errors import ApiError, ErrorCode
from .logging import (
    get_logger,
    request_context,
    generate_correlation_id,
)
from .metrics import get_metrics_collector
from .tracing import (
    get_trace_id,
    get_correlation_id,
    propagate_trace_context,
    generate_trace_id,
)


def observe_tool_call(
    server_name: str,
    tool_name: Optional[str] = None,
    log_input: bool = True,
):
    """
    Decorator for MCP tool functions that provides comprehensive observability.

    Automatically:
    - Generates correlation IDs and trace IDs
    - Logs requests/responses with structured data
    - Records metrics (calls, latency, errors)
    - Tracks upstream errors
    - Propagates trace context

    Args:
        server_name: Name of the MCP server
        tool_name: Optional tool name (defaults to function name)
        log_input: Whether to log input parameters

    Returns:
        Decorated function with observability

    Example:
        @observe_tool_call(server_name="claims-edi-mcp")
        async def claims_parse_edi_837(edi_content: str):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        actual_tool_name = tool_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create trace context
            trace_id = get_trace_id()
            correlation_id = get_correlation_id()
            
            if correlation_id is None:
                correlation_id = generate_correlation_id()
            
            if trace_id is None:
                trace_id = generate_trace_id()
            
            # Set in context
            propagate_trace_context(trace_id=trace_id, correlation_id=correlation_id)

            # Get logger and metrics collector
            logger = get_logger(server_name)
            metrics = get_metrics_collector()

            # Track execution
            start_time = time.time()
            status = "success"
            upstream = None
            upstream_error_code = None

            with request_context(
                logger=logger,
                tool_name=actual_tool_name,
                server_name=server_name,
                trace_id=trace_id,
                correlation_id=correlation_id,
                log_input=log_input,
                **kwargs,
            ):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except ApiError as e:
                    # Extract upstream error information
                    status = "error"
                    upstream = e.details.get("upstream") if hasattr(e, "details") else None
                    upstream_error_code = str(e.details.get("status_code") or e.code.value) if hasattr(e, "details") else str(e.code.value)
                    
                    # Record upstream error metric
                    if upstream:
                        metrics.record_upstream_error(
                            server=server_name,
                            tool=actual_tool_name,
                            upstream=upstream,
                            code=upstream_error_code,
                        )
                    
                    raise
                except Exception as e:
                    status = "error"
                    # Try to extract upstream info from exception
                    if hasattr(e, "details") and isinstance(e.details, dict):
                        upstream = e.details.get("upstream")
                        upstream_error_code = e.details.get("status_code") or e.details.get("error_code")
                        if upstream:
                            metrics.record_upstream_error(
                                server=server_name,
                                tool=actual_tool_name,
                                upstream=upstream,
                                code=str(upstream_error_code) if upstream_error_code else "unknown",
                            )
                    raise
                finally:
                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    metrics.record_mcp_tool_call(
                        server=server_name,
                        tool=actual_tool_name,
                        status=status,
                        duration_ms=duration_ms,
                    )

        return wrapper
    return decorator


def observe_tool_call_sync(
    server_name: str,
    tool_name: Optional[str] = None,
    log_input: bool = True,
):
    """
    Synchronous version of observe_tool_call decorator.

    Same functionality as observe_tool_call but for synchronous functions.

    Args:
        server_name: Name of the MCP server
        tool_name: Optional tool name (defaults to function name)
        log_input: Whether to log input parameters

    Returns:
        Decorated function with observability
    """
    def decorator(func: Callable) -> Callable:
        actual_tool_name = tool_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create trace context
            trace_id = get_trace_id()
            correlation_id = get_correlation_id()
            
            if correlation_id is None:
                correlation_id = generate_correlation_id()
            
            if trace_id is None:
                trace_id = generate_trace_id()
            
            # Set in context
            propagate_trace_context(trace_id=trace_id, correlation_id=correlation_id)

            # Get logger and metrics collector
            logger = get_logger(server_name)
            metrics = get_metrics_collector()

            # Track execution
            start_time = time.time()
            status = "success"
            upstream = None
            upstream_error_code = None

            with request_context(
                logger=logger,
                tool_name=actual_tool_name,
                server_name=server_name,
                trace_id=trace_id,
                correlation_id=correlation_id,
                log_input=log_input,
                **kwargs,
            ):
                try:
                    result = func(*args, **kwargs)
                    return result
                except ApiError as e:
                    # Extract upstream error information
                    status = "error"
                    upstream = e.details.get("upstream") if hasattr(e, "details") else None
                    upstream_error_code = str(e.details.get("status_code") or e.code.value) if hasattr(e, "details") else str(e.code.value)
                    
                    # Record upstream error metric
                    if upstream:
                        metrics.record_upstream_error(
                            server=server_name,
                            tool=actual_tool_name,
                            upstream=upstream,
                            code=upstream_error_code,
                        )
                    
                    raise
                except Exception as e:
                    status = "error"
                    # Try to extract upstream info from exception
                    if hasattr(e, "details") and isinstance(e.details, dict):
                        upstream = e.details.get("upstream")
                        upstream_error_code = e.details.get("status_code") or e.details.get("error_code")
                        if upstream:
                            metrics.record_upstream_error(
                                server=server_name,
                                tool=actual_tool_name,
                                upstream=upstream,
                                code=str(upstream_error_code) if upstream_error_code else "unknown",
                            )
                    raise
                finally:
                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    metrics.record_mcp_tool_call(
                        server=server_name,
                        tool=actual_tool_name,
                        status=status,
                        duration_ms=duration_ms,
                    )

        return wrapper
    return decorator


def create_observable_tool_wrapper(
    server_name: str,
    tool_func: Callable,
    tool_name: Optional[str] = None,
) -> Callable:
    """
    Create an observable wrapper for a tool function without using decorator syntax.

    Useful when you need to wrap existing functions or when decorator syntax
    is not convenient.

    Args:
        server_name: Name of the MCP server
        tool_func: The tool function to wrap
        tool_name: Optional tool name (defaults to function name)

    Returns:
        Wrapped function with observability

    Example:
        wrapped_func = create_observable_tool_wrapper(
            server_name="claims-edi-mcp",
            tool_func=claims_parse_edi_837
        )
    """
    if tool_name is None:
        tool_name = tool_func.__name__

    if asyncio.iscoroutinefunction(tool_func):
        return observe_tool_call(server_name, tool_name)(tool_func)
    else:
        return observe_tool_call_sync(server_name, tool_name)(tool_func)
