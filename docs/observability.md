# Observability Layer

This document describes the standardized observability layer implemented across all MCP servers in the innovationcenter-mcp-zoo repository.

## Overview

The observability layer provides:
- **Structured Logging**: JSON-formatted logs with request tracking
- **Error Handling**: Standardized error responses with error codes
- **Metrics Collection**: Performance metrics (latency, cache hit rates, API call stats)
- **Rate Limiting**: Token bucket rate limiting with configurable limits
- **Circuit Breakers**: Fail-fast behavior after repeated failures
- **Health Checks**: Standardized health check endpoints

## Architecture

All observability utilities are located in the `common/` directory:

```
common/
├── __init__.py           # Public API exports
├── errors.py             # Error classes and formatting
├── logging.py            # Structured logging
├── metrics.py            # Metrics collection
├── rate_limit.py         # Rate limiting and retry logic
├── circuit_breaker.py    # Circuit breaker pattern
└── health.py             # Health check utilities
```

## Usage

### Importing Utilities

```python
from common import (
    # Error handling
    McpError, ApiError, ValidationError, RateLimitError,
    format_error_response, ErrorCode,
    
    # Logging
    get_logger, setup_logging, request_context,
    
    # Metrics
    get_metrics_collector,
    
    # Rate limiting
    get_rate_limiter, exponential_backoff, retry_with_backoff,
    
    # Circuit breaker
    get_circuit_breaker_manager,
    
    # Health checks
    HealthChecker, HealthStatus,
)
```

### Structured Logging

```python
from common import get_logger, setup_logging, request_context

# Setup logging for your server
logger = setup_logging(
    server_name="my-mcp-server",
    log_level="INFO",
    log_format="json"
)

# Or get existing logger
logger = get_logger("my-mcp-server")

# Use request context for automatic logging
async def my_tool_function(**params):
    with request_context(logger, "my_tool", **params):
        # Your tool logic here
        result = await do_work()
        return result
```

**Log Format**:
```json
{
  "timestamp": "2024-12-05 15:30:45",
  "level": "INFO",
  "logger": "my-mcp-server",
  "message": "Tool request: my_tool",
  "tool_name": "my_tool",
  "request_id": "req-123",
  "duration_ms": 245.5,
  "status": "success"
}
```

### Error Handling

```python
from common import ApiError, ValidationError, format_error_response

# Raise structured errors
if not valid_input:
    raise ValidationError(
        message="Invalid input parameter",
        field="param_name"
    )

# Handle API errors
try:
    response = await api_call()
except requests.HTTPError as e:
    raise ApiError(
        message="API call failed",
        status_code=e.response.status_code,
        response_body=e.response.text
    )

# Format errors in responses
try:
    result = await tool_function()
except Exception as e:
    error_response = format_error_response(e, include_traceback=False)
    return error_response
```

**Standard Error Response Format**:
```json
{
  "error": {
    "code": "API_RATE_LIMIT",
    "message": "ClinicalTrials.gov rate limit exceeded",
    "retry_after": 60,
    "docs_url": "https://docs.example.com/errors/API_RATE_LIMIT",
    "details": {
      "status_code": 429
    }
  }
}
```

### Metrics Collection

```python
from common import get_metrics_collector
import time

metrics = get_metrics_collector()

async def api_call():
    start_time = time.time()
    try:
        response = await make_api_request()
        duration_ms = (time.time() - start_time) * 1000
        
        metrics.record_api_call(
            api_name="clinical_trials",
            duration_ms=duration_ms,
            status_code=response.status_code,
            error=False
        )
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call(
            api_name="clinical_trials",
            duration_ms=duration_ms,
            error=True
        )
        raise

# Record cache hits/misses
if cached_data:
    metrics.record_cache_hit("api_cache", hit=True)
else:
    metrics.record_cache_hit("api_cache", hit=False)
```

**Metrics Available**:
- Request counts and error rates
- Latency histograms (p50, p95, p99)
- Cache hit rates
- API call statistics

### Rate Limiting

```python
from common import get_rate_limiter, RateLimitError

rate_limiter = get_rate_limiter()

# Configure rate limits
rate_limiter.configure(
    name="clinical_trials_api",
    max_requests=10,
    window_seconds=60  # 10 requests per minute
)

# Check rate limit before API call
error = rate_limiter.check_rate_limit("clinical_trials_api")
if error:
    raise error

# Or wait if needed
wait_time = rate_limiter.wait_if_needed("clinical_trials_api")
```

### Exponential Backoff and Retries

```python
from common import retry_with_backoff, exponential_backoff

# Retry with exponential backoff
result = retry_with_backoff(
    func=lambda: api_call(),
    max_attempts=3,
    backoff_fn=exponential_backoff(base_delay=1.0, max_delay=60.0),
    retry_on=lambda e: isinstance(e, (ConnectionError, TimeoutError))
)
```

### Circuit Breakers

```python
from common import get_circuit_breaker_manager

breaker_manager = get_circuit_breaker_manager()

# Get circuit breaker for an API
breaker = breaker_manager.get_breaker(
    name="clinical_trials_api",
    failure_threshold=5,      # Open after 5 failures
    timeout_seconds=60,        # Try half-open after 60s
    success_threshold=2        # Close after 2 successes
)

# Use circuit breaker to protect API calls
try:
    result = breaker.call(lambda: api_call())
except CircuitBreakerError as e:
    # Circuit is open, fail fast
    logger.warning(f"Circuit breaker open: {e}")
    raise
```

**Circuit Breaker States**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Failing, requests rejected immediately
- **HALF_OPEN**: Testing if service recovered

### Health Checks

```python
from common import HealthChecker, HealthStatus

# Create health checker
health = HealthChecker(server_name="my-mcp-server")

# Add basic checks (metrics, circuit breakers)
health.add_basic_checks()

# Add custom health check
def check_external_api():
    try:
        response = await api_client.ping()
        if response.ok:
            return HealthCheckResult(
                name="external_api",
                status=HealthStatus.HEALTHY
            )
        else:
            return HealthCheckResult(
                name="external_api",
                status=HealthStatus.DEGRADED,
                message="API responding slowly"
            )
    except Exception as e:
        return HealthCheckResult(
            name="external_api",
            status=HealthStatus.UNHEALTHY,
            message=f"API unavailable: {e}"
        )

health.register_check("external_api", check_external_api)

# Get health status
health_status = health.check_all()
```

**Health Check Response**:
```json
{
  "status": "healthy",
  "server": "my-mcp-server",
  "timestamp": 1701792045.123,
  "checks": [
    {
      "name": "metrics",
      "status": "healthy",
      "details": {
        "error_rate": 0.01,
        "total_requests": 1000
      }
    },
    {
      "name": "circuit_breakers",
      "status": "healthy",
      "details": {
        "total_breakers": 2,
        "open_breakers": 0
      }
    }
  ]
}
```

## Server Integration

### Example: Complete Server Implementation

```python
import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server

from common import (
    setup_logging, get_logger, request_context,
    format_error_response,
    get_metrics_collector,
    get_rate_limiter,
    get_circuit_breaker_manager,
    HealthChecker, create_health_check_response,
)

# Setup observability
logger = setup_logging("my-server", log_level="INFO")
metrics = get_metrics_collector()
rate_limiter = get_rate_limiter()
breaker_manager = get_circuit_breaker_manager()

# Configure rate limiting
rate_limiter.configure("api_calls", max_requests=10, window_seconds=60)

# Get circuit breaker
api_breaker = breaker_manager.get_breaker("api_calls")

# Setup health checker
health_checker = HealthChecker("my-server")
health_checker.add_basic_checks()

# Create MCP server
server = Server("my-server")

@server.list_tools()
async def list_tools():
    return [Tool(name="my_tool", ...)]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(f"Tool call: {name}", extra={"arguments": arguments})
    
    try:
        with request_context(logger, name, **arguments):
            # Check rate limit
            rate_error = rate_limiter.check_rate_limit("api_calls")
            if rate_error:
                raise rate_error
            
            # Execute with circuit breaker
            result = api_breaker.call(
                lambda: execute_tool(name, arguments)
            )
            
            return [TextContent(type="text", text=json.dumps(result))]
            
    except Exception as e:
        logger.error(f"Tool error: {name}", exc_info=True)
        error_response = format_error_response(e)
        return [TextContent(type="text", text=json.dumps(error_response))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ...)

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Codes

Standard error codes defined in `ErrorCode` enum:

**API Errors**:
- `API_ERROR`: General API error
- `API_TIMEOUT`: Request timeout
- `API_RATE_LIMIT`: Rate limit exceeded (includes `retry_after`)
- `API_UNAUTHORIZED`: 401 Unauthorized
- `API_FORBIDDEN`: 403 Forbidden
- `API_NOT_FOUND`: 404 Not Found
- `API_SERVER_ERROR`: 5xx server errors

**Validation Errors**:
- `VALIDATION_ERROR`: General validation error
- `INVALID_INPUT`: Invalid input format
- `MISSING_REQUIRED_FIELD`: Required field missing

**System Errors**:
- `CIRCUIT_BREAKER_OPEN`: Circuit breaker is open
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `INTERNAL_ERROR`: Internal server error
- `SERVICE_UNAVAILABLE`: Service unavailable

**Data Errors**:
- `DATA_NOT_FOUND`: Requested data not found
- `DATA_PARSE_ERROR`: Error parsing data
- `CACHE_ERROR`: Cache operation failed

## Best Practices

1. **Always use structured logging**: Use `request_context` for automatic request/response logging
2. **Handle errors gracefully**: Use `format_error_response` for consistent error responses
3. **Track metrics**: Record API calls, cache hits, and latency for monitoring
4. **Configure rate limits**: Prevent API abuse with appropriate rate limits
5. **Use circuit breakers**: Protect against cascading failures
6. **Implement health checks**: Enable monitoring and alerting
7. **Sanitize logs**: Sensitive data (API keys, passwords) is automatically redacted

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Log format ("json" or "text")
- `LOG_FILE`: Optional log file path

### Default Settings

- **Logging**: INFO level, JSON format
- **Rate Limiting**: No limits by default (must be configured)
- **Circuit Breaker**: 5 failures threshold, 60s timeout
- **Metrics**: In-memory storage (1000 samples per metric)

## Monitoring Integration

Metrics can be exported for integration with monitoring systems:

```python
metrics = get_metrics_collector()
all_metrics = metrics.get_all_metrics()

# Export to Prometheus, Datadog, etc.
# Metrics include:
# - counters: request counts, error counts
# - gauges: current values
# - histograms: latency distributions with percentiles
```

## Troubleshooting

### High Error Rates

1. Check circuit breaker status: `breaker.get_stats()`
2. Review error logs for patterns
3. Check rate limit configurations
4. Verify external API status

### Performance Issues

1. Review latency histograms: `metrics.get_histogram_stats("api_latency_ms")`
2. Check cache hit rates: `metrics.get_cache_hit_rate("cache_name")`
3. Monitor request counts and error rates

### Circuit Breaker Stuck Open

1. Check failure threshold configuration
2. Verify external service is actually recovering
3. Manually reset if needed: `breaker.reset()`

## Further Reading

- [Error Handling Guide](./errors.md) (to be created)
- [Logging Best Practices](./logging.md) (to be created)
- [Metrics and Monitoring](./metrics.md) (to be created)

