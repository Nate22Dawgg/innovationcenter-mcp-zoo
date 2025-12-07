# MCP Server Robustness Guide

This guide outlines standards for making MCP servers robust and consistent across the codebase.

## Standardization Checklist

### 1. Error Handling

All servers should use the common error classes from `common.errors`:

```python
from common.errors import (
    ApiError,
    ValidationError,
    RateLimitError,
    CircuitBreakerError,
    format_error_response,
)

# Use standardized errors
try:
    result = api_call()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        raise RateLimitError("Rate limit exceeded", retry_after=60)
    elif e.response.status_code == 404:
        raise ApiError("Resource not found", status_code=404, code=ErrorCode.API_NOT_FOUND)
    else:
        raise ApiError("API error", status_code=e.response.status_code)
```

### 2. Input Validation

Validate all inputs using schemas and common utilities:

```python
from common.errors import ValidationError

def validate_input(data: Dict[str, Any], schema: Dict[str, Any]):
    """Validate input against schema."""
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data or data[field] is None:
            raise ValidationError(f"Missing required field: {field}", field=field)
    
    # Check types
    for field, value in data.items():
        if field in schema.get("properties", {}):
            prop_schema = schema["properties"][field]
            expected_type = prop_schema.get("type")
            if expected_type and not isinstance(value, _map_type(expected_type)):
                raise ValidationError(
                    f"Field {field} must be {expected_type}",
                    field=field
                )
```

### 3. Logging

Use the common logging utilities:

```python
from common.logging import get_logger, log_request, log_response, log_error

logger = get_logger("server-name")

@log_request
@log_response
async def my_tool(arg1: str):
    try:
        result = await do_work(arg1)
        return result
    except Exception as e:
        log_error(e, context={"tool": "my_tool", "arg1": arg1})
        raise
```

### 4. Rate Limiting

Apply rate limiting to all external API calls:

```python
from common.rate_limit import get_rate_limiter, retry_with_backoff

rate_limiter = get_rate_limiter()

@rate_limiter.limit(calls=10, period=60)  # 10 calls per minute
@retry_with_backoff(max_retries=3)
async def call_external_api(url: str):
    response = await requests.get(url)
    return response.json()
```

### 5. Circuit Breaker

Use circuit breakers for external dependencies:

```python
from common.circuit_breaker import get_circuit_breaker_manager

circuit_breaker = get_circuit_breaker_manager().get_breaker("api-name")

@circuit_breaker.protect
async def call_external_api(url: str):
    response = await requests.get(url)
    return response.json()
```

### 6. Metrics Collection

Collect metrics for monitoring:

```python
from common.metrics import get_metrics_collector

metrics = get_metrics_collector()

async def my_tool(arg1: str):
    start_time = time.time()
    try:
        result = await do_work(arg1)
        metrics.increment("tool.success", tags=["tool:my_tool"])
        metrics.timing("tool.duration", time.time() - start_time, tags=["tool:my_tool"])
        return result
    except Exception as e:
        metrics.increment("tool.error", tags=["tool:my_tool", f"error:{type(e).__name__}"])
        raise
```

### 7. Health Checks

Implement health checks:

```python
from common.health import HealthChecker, HealthStatus

health_checker = HealthChecker("server-name")

@health_checker.check("external-api")
async def check_external_api():
    try:
        response = await requests.get("https://api.example.com/health", timeout=5)
        if response.status_code == 200:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNHEALTHY
    except Exception:
        return HealthStatus.UNHEALTHY
```

## Edge Cases to Handle

### 1. Empty Results

Always return consistent structure for empty results:

```python
return {
    "total": 0,
    "count": 0,
    "offset": 0,
    "results": []
}
```

### 2. Huge Results

Implement pagination and limits:

```python
limit = min(limit or 20, 100)  # Cap at 100
offset = max(offset or 0, 0)

# Return paginated results
return {
    "total": total_count,
    "count": len(results),
    "offset": offset,
    "limit": limit,
    "results": results
}
```

### 3. Invalid Inputs

Validate and reject invalid inputs early:

```python
if limit is not None and (limit < 1 or limit > 100):
    raise ValidationError("limit must be between 1 and 100", field="limit")

if offset is not None and offset < 0:
    raise ValidationError("offset must be non-negative", field="offset")
```

### 4. Rate Limited Upstreams

Handle rate limits gracefully:

```python
try:
    result = await api_call()
except RateLimitError as e:
    # Return error with retry information
    return {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": str(e),
            "retry_after": e.retry_after
        }
    }
```

### 5. Network Errors

Handle network errors with retries:

```python
from common.rate_limit import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=2)
async def api_call_with_retry():
    return await api_call()
```

### 6. Timeouts

Set appropriate timeouts:

```python
response = await requests.get(url, timeout=10)  # 10 second timeout
```

### 7. Special Characters and Unicode

Handle special characters and unicode properly:

```python
# URL encode when necessary
from urllib.parse import quote

encoded_query = quote(query, safe='')

# Handle unicode in responses
response_text = response.text.encode('utf-8').decode('utf-8')
```

## Response Format Standards

### Success Response

```python
{
    "status": "success",
    "data": {...},
    "metadata": {
        "total": 100,
        "count": 20,
        "offset": 0
    }
}
```

### Error Response

```python
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": {
            "field": "limit"
        },
        "retry_after": null,
        "docs_url": "https://docs.example.com/errors/VALIDATION_ERROR"
    }
}
```

## Testing Requirements

### Unit Tests

- Test all edge cases (empty, huge, invalid inputs)
- Test error handling (rate limits, network errors, timeouts)
- Test input validation
- Mock external dependencies

### Integration Tests

- Test real API interactions (with VCR recording)
- Test error responses from upstream APIs
- Test rate limit handling
- Use fixtures for stable test data

### End-to-End Tests

- Test full request → response cycle
- Test MCP protocol compliance
- Test error mapping
- Test concurrent requests

## Common Patterns

### Tool Function Template

```python
from common.errors import ValidationError, ApiError, format_error_response
from common.logging import get_logger, log_request, log_response
from common.metrics import get_metrics_collector

logger = get_logger("server-name")
metrics = get_metrics_collector()

@log_request
@log_response
async def my_tool(
    required_param: str,
    optional_param: Optional[int] = None,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """Tool description."""
    try:
        # Validate inputs
        if not required_param:
            raise ValidationError("required_param is required", field="required_param")
        
        if limit is not None and (limit < 1 or limit > 100):
            raise ValidationError("limit must be between 1 and 100", field="limit")
        
        # Clamp values
        limit = min(limit or 20, 100)
        
        # Call external API with error handling
        try:
            result = await external_api_call(required_param, limit=limit)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded", retry_after=60)
            else:
                raise ApiError("API error", status_code=e.response.status_code)
        
        # Return standardized response
        return {
            "status": "success",
            "data": result,
            "total": result.get("total", 0),
            "count": len(result.get("items", []))
        }
    
    except ValidationError:
        raise  # Re-raise validation errors
    except (ApiError, RateLimitError):
        raise  # Re-raise API errors
    except Exception as e:
        logger.error("Unexpected error in my_tool", exc_info=e, extra={
            "required_param": required_param,
            "optional_param": optional_param
        })
        metrics.increment("tool.error", tags=["tool:my_tool"])
        raise ApiError("Internal error", original_error=e)
```

## Migration Guide

To migrate an existing server to follow these standards:

1. **Replace custom error handling** with `common.errors`
2. **Add input validation** using schemas
3. **Add logging** using `common.logging`
4. **Add rate limiting** using `common.rate_limit`
5. **Add circuit breakers** using `common.circuit_breaker`
6. **Add metrics** using `common.metrics`
7. **Add health checks** using `common.health`
8. **Update tests** to cover edge cases
9. **Update documentation** to reflect changes

## Resources

- [Common Utilities Documentation](../common/README.md)
- [Error Handling Guide](../common/errors.py)
- [Testing Guide](./README.md)
- [Schema Validation](../schemas/README.md)
