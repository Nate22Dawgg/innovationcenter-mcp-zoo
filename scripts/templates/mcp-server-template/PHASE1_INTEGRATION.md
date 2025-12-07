# Phase 1 Integration Guide

This document explains how the MCP server template integrates with Phase 1 features (core robustness, config, caching, validation, observability).

## Overview

Phase 1 introduced standardized utilities in the `common/` directory that all MCP servers should use:

1. **Configuration Framework** (`common/config.py`)
2. **Caching** (`common/cache.py`)
3. **Schema Validation** (`common/validation.py`)
4. **HTTP Client** (`common/http.py`)
5. **Error Handling** (`common/errors.py`)
6. **Logging** (`common/logging.py`)
7. **Observability** (`common/observability.py`)
8. **Metrics** (`common/metrics.py`)
9. **Tracing** (`common/tracing.py`)

## Template Integration

The template demonstrates all Phase 1 features:

### 1. Configuration Framework

**File**: `config.py`

```python
from common.config import ServerConfig, ConfigIssue, validate_config_or_raise

@dataclass
class TemplateServerConfig(ServerConfig):
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def validate(self) -> List[ConfigIssue]:
        issues = []
        if not self.api_key:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY is required",
                critical=True
            ))
        return issues
```

**Usage in `server.py`**:
- Fail-fast mode: Server refuses to start if critical config missing
- Fail-soft mode: Server starts but tools return `SERVICE_NOT_CONFIGURED`

### 2. Caching

**File**: `src/tools/example_tool.py`

```python
from common.cache import get_cache, build_cache_key

# Check cache first
cache = get_cache()
cache_key = build_cache_key("template-mcp-server", "example_get_data", {"resource_id": resource_id})
cached_result = cache.get(cache_key)
if cached_result is not None:
    return cached_result

# Fetch from API and cache
result = client.get_data(resource_id)
cache.set(cache_key, result, ttl_seconds=300)
```

**Benefits**:
- Reduces API calls
- Improves response time
- Automatic TTL management

### 3. Schema Validation

**File**: `src/tools/example_tool.py`

```python
from common.validation import validate_tool_input, validate_tool_output

# Validate input
validate_tool_input("example_tool", {"message": message})

# Validate output (only in strict mode)
validate_tool_output("example_tool", result)
```

**Schema Files**: Place JSON schemas in `schemas/` directory:
- `example_tool.json` - Input schema
- `example_tool_output.json` - Output schema

**Output Validation**: Gated by `MCP_STRICT_OUTPUT_VALIDATION` environment variable (default: disabled)

### 4. HTTP Client

**File**: `src/clients/example_client.py`

```python
from common.http import get, post, CallOptions

# Simple GET request
response = get(
    url=f"{self.base_url}/ping",
    upstream="example",
    timeout=10.0,
    headers=self._headers
)

# With retries and circuit breaker (automatic)
response = get(
    url=f"{self.base_url}/data/{resource_id}",
    upstream="example",
    timeout=10.0,
    allow_retries=True,
    max_retries=3
)
```

**Features**:
- Automatic retries with exponential backoff
- Circuit breaker per upstream
- Timeout handling
- Error mapping to standardized codes

### 5. Error Handling

**File**: `src/tools/example_tool.py`

```python
from common.errors import ErrorCode, map_upstream_error, format_error_response

try:
    result = client.get_data(resource_id)
except Exception as e:
    mcp_error = map_upstream_error(e)
    return format_error_response(error=mcp_error)["error"]
```

**Standardized Error Codes**:
- `BAD_REQUEST` - Invalid input
- `NOT_FOUND` - Resource not found
- `UPSTREAM_UNAVAILABLE` - Upstream API unavailable
- `SERVICE_NOT_CONFIGURED` - Configuration missing/invalid
- `API_TIMEOUT` - Request timeout
- `INTERNAL_ERROR` - Unexpected error

### 6. Logging

**File**: `server.py`, `src/tools/example_tool.py`

```python
from common.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing message: {message}", message=message)
logger.error("Tool execution failed: {error}", error=str(e))
```

**Features**:
- Structured logging
- Correlation IDs
- Request context

### 7. Observability

**File**: `src/tools/example_tool.py` (optional decorator)

```python
from common.observability import observe_tool_call_sync

@observe_tool_call_sync(server_name="template-mcp-server")
def example_tool(client, config_error_payload, message):
    # Tool implementation
    pass
```

**What it provides**:
- Automatic metrics collection (calls, latency, errors)
- Structured logging with trace IDs
- Upstream error tracking
- Correlation ID propagation

### 8. Metrics

**Automatic via observability decorators**, or manual:

```python
from common.metrics import get_metrics_collector

metrics = get_metrics_collector()
metrics.record_mcp_tool_call(
    server="template-mcp-server",
    tool="example_tool",
    status="success",
    duration_ms=150.5
)
```

**Metrics tracked**:
- `mcp_tool_calls_total` - Total tool calls
- `mcp_tool_latency_ms` - Tool execution latency
- `mcp_tool_upstream_errors_total` - Upstream API errors

### 9. Tracing

**Automatic via observability decorators**, or manual:

```python
from common.tracing import generate_trace_id, propagate_trace_context

trace_id = generate_trace_id()
propagate_trace_context(trace_id=trace_id, correlation_id=correlation_id)
```

## Best Practices

1. **Always use `common.http`** for HTTP requests (don't use `requests` directly)
2. **Add caching** for expensive read operations
3. **Validate inputs** using JSON schemas when available
4. **Use observability decorators** for automatic metrics/logging
5. **Handle `SERVICE_NOT_CONFIGURED`** in all tools (fail-soft behavior)
6. **Map upstream errors** using `map_upstream_error()`
7. **Use structured logging** via `get_logger()`

## Migration Checklist

When creating a new server from this template:

- [ ] Update `config.py` with your server's configuration needs
- [ ] Implement clients using `common.http`
- [ ] Add caching for expensive operations
- [ ] Create JSON schemas for tool inputs/outputs
- [ ] Add input validation in tools
- [ ] Add observability decorators (optional but recommended)
- [ ] Test fail-fast and fail-soft configuration modes
- [ ] Update `.env.example` with your config variables

## See Also

- [`docs/CONFIGURATION_PATTERNS.md`](../../docs/CONFIGURATION_PATTERNS.md) - Configuration framework details
- [`docs/VALIDATION.md`](../../docs/VALIDATION.md) - Schema validation guide
- [`docs/observability-guide.md`](../../docs/observability-guide.md) - Observability guide
- [`common/__init__.py`](../../common/__init__.py) - All available utilities
