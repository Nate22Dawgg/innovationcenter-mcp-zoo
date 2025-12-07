# Observability Guide for MCP Servers

This guide explains how to use the comprehensive observability features in MCP servers, including metrics, logging, and distributed tracing.

## Overview

The observability layer provides:

1. **Standardized Metrics**: `mcp_tool_calls_total`, `mcp_tool_latency_ms`, `mcp_tool_upstream_errors_total`
2. **Structured Logging**: JSON-formatted logs with correlation IDs, trace IDs, and sanitized parameters
3. **Distributed Tracing**: Trace ID propagation across MCP servers and upstream services

## Quick Start

The easiest way to add observability to your MCP tool is using the `@observe_tool_call` decorator:

```python
from common import observe_tool_call

@observe_tool_call(server_name="my-mcp-server")
async def my_tool(param1: str, param2: int):
    # Your tool implementation
    result = do_something(param1, param2)
    return result
```

This automatically:
- Generates correlation IDs and trace IDs
- Logs requests/responses with structured data
- Records metrics (calls, latency, errors)
- Tracks upstream errors
- Propagates trace context

## Metrics

### Standardized MCP Metrics

The following metrics are automatically emitted:

#### `mcp_tool_calls_total{server, tool, status}`
Counter tracking total tool invocations by server, tool name, and status (success/error/timeout).

#### `mcp_tool_latency_ms{server, tool}`
Histogram tracking tool execution latency in milliseconds.

#### `mcp_tool_upstream_errors_total{server, tool, upstream, code}`
Counter tracking upstream service errors, including the upstream service name and error code.

### Using Metrics Directly

```python
from common import get_metrics_collector

metrics = get_metrics_collector()

# Record a tool call
metrics.record_mcp_tool_call(
    server="my-mcp-server",
    tool="my_tool",
    status="success",
    duration_ms=150.5
)

# Record an upstream error
metrics.record_upstream_error(
    server="my-mcp-server",
    tool="my_tool",
    upstream="pubmed-api",
    code="500"
)
```

## Logging

### Structured Logging with Correlation IDs

All logs include:
- **correlation_id**: Unique ID for request tracking
- **trace_id**: Distributed trace ID (if available)
- **server_name**: MCP server name
- **tool_name**: Tool name
- **input_params**: Sanitized input parameters (PHI/API keys redacted)
- **upstream**: Upstream service name (on errors)
- **upstream_error_code**: Upstream error code (on errors)

### Example Log Output

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "claims-edi-mcp",
  "message": "Tool request: claims_parse_edi_837",
  "event_type": "request_start",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "660e8400-e29b-41d4-a716-446655440001",
  "server_name": "claims-edi-mcp",
  "tool_name": "claims_parse_edi_837",
  "input_params": {
    "edi_file_path": "/path/to/file.txt"
  }
}
```

### Using Logging Directly

```python
from common import (
    get_logger,
    request_context,
    generate_correlation_id,
)

logger = get_logger("my-mcp-server")

# Manual logging with context
correlation_id = generate_correlation_id()
with request_context(
    logger=logger,
    tool_name="my_tool",
    server_name="my-mcp-server",
    correlation_id=correlation_id,
    **kwargs
):
    result = await my_tool_implementation(**kwargs)
```

## Distributed Tracing

### Trace ID Propagation

Trace IDs are automatically propagated to upstream services when making HTTP calls:

```python
from common import inject_trace_headers
import httpx

# When making upstream API calls
headers = inject_trace_headers()
response = await httpx.get(
    "https://api.example.com/data",
    headers=headers
)
```

This injects `X-Trace-Id` and `X-Correlation-Id` headers, allowing you to trace requests across:
- MCP server → Upstream API
- MCP server → Another MCP server (e.g., biotech-markets-mcp → sec-edgar-mcp)

### Extracting Trace Context

When receiving requests from other services:

```python
from common import extract_trace_headers, propagate_trace_context

# Extract from incoming request headers
trace_context = extract_trace_headers(request.headers)

# Propagate to current context
propagate_trace_context(
    trace_id=trace_context["trace_id"],
    correlation_id=trace_context["correlation_id"]
)
```

## Advanced Usage

### Manual Observability

If you need more control than the decorator provides:

```python
from common import (
    get_logger,
    get_metrics_collector,
    request_context,
    propagate_trace_context,
    generate_trace_id,
    generate_correlation_id,
)

logger = get_logger("my-mcp-server")
metrics = get_metrics_collector()

async def my_tool(**kwargs):
    # Set up trace context
    trace_id = generate_trace_id()
    correlation_id = generate_correlation_id()
    propagate_trace_context(trace_id=trace_id, correlation_id=correlation_id)
    
    start_time = time.time()
    status = "success"
    
    with request_context(
        logger=logger,
        tool_name="my_tool",
        server_name="my-mcp-server",
        trace_id=trace_id,
        correlation_id=correlation_id,
        **kwargs
    ):
        try:
            result = await do_work(**kwargs)
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_mcp_tool_call(
                server="my-mcp-server",
                tool="my_tool",
                status=status,
                duration_ms=duration_ms
            )
```

### Upstream Error Tracking

When calling upstream services, capture error information:

```python
from common import ApiError, ErrorCode

try:
    response = await httpx.get("https://api.example.com/data")
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    # Wrap in ApiError with upstream information
    raise ApiError(
        message="Upstream API error",
        status_code=e.response.status_code,
        details={
            "upstream": "example-api",
            "status_code": e.response.status_code,
        }
    )
```

This automatically:
- Records `mcp_tool_upstream_errors_total` metric
- Logs upstream error information
- Includes upstream details in error logs

## Integration Examples

### Example 1: Simple Tool

```python
from common import observe_tool_call

@observe_tool_call(server_name="claims-edi-mcp")
async def claims_parse_edi_837(edi_content: str):
    # Parse EDI content
    result = parse_edi(edi_content)
    return result
```

### Example 2: Tool with Upstream Calls

```python
from common import observe_tool_call, inject_trace_headers, ApiError
import httpx

@observe_tool_call(server_name="biotech-markets-mcp")
async def get_company_filings(ticker: str):
    # Propagate trace IDs to upstream service
    headers = inject_trace_headers()
    
    try:
        response = await httpx.get(
            f"https://api.sec.gov/companies/{ticker}/filings",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise ApiError(
            message="SEC EDGAR API error",
            status_code=e.response.status_code,
            details={
                "upstream": "sec-edgar-api",
                "status_code": e.response.status_code,
            }
        )
```

### Example 3: Tool Calling Another MCP Server

```python
from common import observe_tool_call, inject_trace_headers
import httpx

@observe_tool_call(server_name="biotech-markets-mcp")
async def get_combined_data(ticker: str):
    # Call another MCP server with trace propagation
    headers = inject_trace_headers()
    
    # Call sec-edgar-mcp
    sec_response = await httpx.post(
        "http://sec-edgar-mcp:8000/tools/get_filings",
        json={"ticker": ticker},
        headers=headers
    )
    
    # Call pubmed-mcp with same trace ID
    pubmed_response = await httpx.post(
        "http://pubmed-mcp:8000/tools/search",
        json={"query": ticker},
        headers=headers  # Same trace ID propagated
    )
    
    return {
        "sec_data": sec_response.json(),
        "pubmed_data": pubmed_response.json()
    }
```

## Best Practices

1. **Always use `@observe_tool_call`**: It provides comprehensive observability with minimal code.

2. **Propagate trace IDs**: When calling upstream services, use `inject_trace_headers()` to maintain trace continuity.

3. **Include upstream information**: When wrapping upstream errors, include `upstream` and `status_code` in error details.

4. **Use correlation IDs**: They're automatically generated, but you can pass them explicitly for cross-service correlation.

5. **Sanitize sensitive data**: The logging system automatically redacts API keys and PHI, but be mindful of what you log.

## Metrics Export

Metrics can be exported for monitoring systems (Prometheus, etc.):

```python
from common import get_metrics_collector

metrics = get_metrics_collector()
all_metrics = metrics.get_all_metrics()

# Export to Prometheus format or your monitoring system
```

## Troubleshooting

### Missing Trace IDs

If trace IDs are not propagating:
- Ensure you're using `inject_trace_headers()` when making HTTP calls
- Check that upstream services extract headers using `extract_trace_headers()`

### Metrics Not Recording

- Verify the decorator is applied: `@observe_tool_call(server_name="...")`
- Check that `get_metrics_collector()` returns a valid instance

### Logs Missing Fields

- Ensure you're using `request_context` or the `@observe_tool_call` decorator
- Verify server_name is provided in the decorator or context
