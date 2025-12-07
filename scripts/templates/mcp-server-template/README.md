# MCP Server Template

This is a template for creating new MCP (Model Context Protocol) servers. It provides a clean, robust scaffold that follows the repository's standards for configuration, error handling, and structure.

## Purpose

This template provides:
- Directory layout for new servers
- Minimal placeholder files wired to use the config framework (`ServerConfig`, `validate_config_or_raise`)
- Example client and tool implementations demonstrating best practices
- Test structure with comprehensive examples
- Documentation and patterns for robust server development

## How to Use This Template

### Option 1: Use the Scaffolding Script (Recommended)

Use the automated scaffolding script to create a new server:

```bash
python scripts/create_mcp_server.py
```

The script will:
- Prompt for server name, domain, description, and config variables
- Copy the template and replace placeholders automatically
- Create the server structure under `servers/<domain>/`
- Generate properly named configuration classes and environment variables

**Example**:
```bash
$ python scripts/create_mcp_server.py
Server name (must end with '-mcp'): my-new-server-mcp
Domain: clinical
Short description: My new clinical data server
...
```

### Option 2: Manual Copy

If you prefer to copy manually:

```bash
cp -r scripts/templates/mcp-server-template servers/<domain>/new-server-name-mcp/
```

### 2. Update Configuration

Edit `config.py`:
- Rename `TemplateServerConfig` to `YourServerConfig`
- Update configuration fields to match your server's needs
- Update the `validate()` method to check your specific requirements

### 3. Update Server Entry Point

Edit `server.py`:
- Update the server name and description
- Implement your actual tools in `src/tools/`
- Implement your actual clients in `src/clients/`
- Register your tools in `list_tools()` and `call_tool()` handlers

### 4. Implement Clients

Edit `src/clients/example_client.py` or create new client files:
- Rename `ExampleClient` to your client name
- Implement actual HTTP calls to your upstream API
- Add proper error handling using `common.errors.map_upstream_error`

### 5. Implement Tools

Edit `src/tools/example_tool.py` or create new tool files:
- Rename `example_tool` to your tool name
- Implement your actual tool logic
- Add schema-based validation using `common.validation.validate_tool_input`
- Add proper error handling using `common.errors`

### 6. Update Tests

Edit `tests/test_clients.py` and `tests/test_tools.py`:
- Update tests to match your actual implementations
- Add comprehensive tests for your specific use cases

### 7. Update Environment Variables

Edit `.env.example`:
- Update variable names to match your server's configuration
- Update `requirements.txt` with your specific dependencies

## Key Features

This template integrates all Phase 1 features for robust MCP server development:

### Configuration Framework

This template uses the standardized configuration framework from `common.config`:

- **Fail-Fast Mode**: Server refuses to start if critical config is missing (production default)
- **Fail-Soft Mode**: Server starts but tools return `SERVICE_NOT_CONFIGURED` errors (development)
- **Structured Validation**: Uses `ConfigIssue` objects for clear error messages
- **Environment Variable Management**: Follows naming conventions (`{SERVER_NAME}_{CONFIG_NAME}`)

**See**: [`docs/CONFIGURATION_PATTERNS.md`](../../docs/CONFIGURATION_PATTERNS.md) for detailed documentation

### Caching

The template demonstrates caching integration:

- **In-Memory Cache**: Simple cache with TTL support via `common.cache`
- **Cache Key Building**: Standardized cache key generation
- **Automatic TTL Management**: Expired entries are automatically cleaned up

**See**: [`PHASE1_INTEGRATION.md`](./PHASE1_INTEGRATION.md) for caching examples

### Error Handling

All tools and clients use standardized error handling:

- **Upstream Errors**: Mapped to standardized error codes via `map_upstream_error()`
- **Configuration Errors**: `SERVICE_NOT_CONFIGURED` for invalid/missing config
- **Input Validation**: Structured validation errors with clear messages
- **Structured Responses**: Consistent error response format

**See**: `common/errors.py` for error handling utilities

### HTTP Client Integration

Clients use the shared HTTP wrapper (`common.http`):

- **Retries**: Automatic retries with exponential backoff (for idempotent operations)
- **Circuit Breaker**: Per-upstream circuit breaker to prevent cascading failures
- **Timeouts**: Configurable timeouts (default 10s)
- **Error Mapping**: Automatic mapping to standardized error codes

**See**: `common/http.py` for HTTP client utilities

### Schema Validation

The template supports schema-first validation:

- **Input Validation**: Validate tool arguments against JSON schemas
- **Output Validation**: Optional output validation (gated by `MCP_STRICT_OUTPUT_VALIDATION`)
- **Schema Caching**: Schemas are cached for performance
- **Machine-Readable Errors**: Structured validation error responses

**See**: [`PHASE1_INTEGRATION.md`](./PHASE1_INTEGRATION.md) and [`docs/VALIDATION.md`](../../docs/VALIDATION.md)

### Observability

Optional observability decorators provide automatic:

- **Metrics Collection**: Tool calls, latency, upstream errors
- **Structured Logging**: With correlation IDs and trace IDs
- **Error Tracking**: Upstream error code tracking
- **Trace Propagation**: Distributed tracing support

**See**: [`PHASE1_INTEGRATION.md`](./PHASE1_INTEGRATION.md) and [`docs/observability-guide.md`](../../docs/observability-guide.md)

### Domain Boundaries

Follow domain taxonomy when creating servers:

- `clinical`: Clinical trials, biomedical research, healthcare data
- `markets`: Financial markets, company data, SEC filings
- `pricing`: Price transparency, fee schedules
- `claims`: Insurance claims, EDI processing
- `real-estate`: Property data, real estate markets
- `misc`: General-purpose, cross-domain tools

**See**: [`docs/DOMAIN_BOUNDARIES.md`](../../docs/DOMAIN_BOUNDARIES.md) for scoping guidelines

## Directory Structure

```
mcp-server-template/
├── src/
│   ├── __init__.py
│   ├── tools/           # Tool implementations
│   │   ├── __init__.py
│   │   └── example_tool.py
│   ├── clients/         # Upstream API clients
│   │   ├── __init__.py
│   │   └── example_client.py
│   └── schemas/         # JSON schemas for tool inputs/outputs
│       └── .gitkeep
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_clients.py
├── server.py            # MCP server entry point
├── config.py            # Server configuration
├── requirements.txt    # Python dependencies
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Running Tests

Run the template tests to verify everything works:

```bash
cd scripts/templates/mcp-server-template
python -m pytest tests/ -v
```

Or run tests individually:

```bash
python tests/test_clients.py
python tests/test_tools.py
```

## Next Steps

After copying and customizing this template:

1. Add JSON schemas to `src/schemas/` for your tool inputs/outputs
2. Implement schema validation in your tools using `common.validation.validate_tool_input`
3. Add comprehensive error handling using `common.errors`
4. Add logging using `common.logging`
5. Add metrics using `common.metrics`
6. Update documentation with your server's specific information

## Testing

The template includes comprehensive test examples:

### Running Tests

```bash
# Run all tests
cd scripts/templates/mcp-server-template
python -m pytest tests/ -v

# Run specific test files
python tests/test_clients.py
python tests/test_tools.py
```

### Test Coverage

The example tests demonstrate:
- Client initialization and methods
- Error handling and retries
- Tool execution with valid/invalid config
- Input validation
- `SERVICE_NOT_CONFIGURED` scenarios

## Next Steps

After creating your server (via scaffolding script or manual copy):

1. **Update Configuration** (`config.py`):
   - Rename config class (if manual copy)
   - Update fields for your server's needs
   - Implement validation logic
   - Test fail-fast and fail-soft modes

2. **Implement Clients** (`src/clients/`):
   - Create clients for your upstream APIs
   - Use `common.http` for HTTP requests (automatic retries, circuit breakers)
   - Handle errors with `map_upstream_error()`
   - Optionally add caching for expensive operations

3. **Implement Tools** (`src/tools/`):
   - Create tool functions
   - Add input validation (schema-based if schemas available)
   - Add caching for expensive operations (optional)
   - Add observability decorators (optional but recommended)
   - Handle `SERVICE_NOT_CONFIGURED`
   - Register tools in `server.py`

4. **Add JSON Schemas** (`src/schemas/` or `schemas/`):
   - Create input schemas for each tool (e.g., `example_tool.json`)
   - Create output schemas (e.g., `example_tool_output.json`)
   - Enable validation in tools using `validate_tool_input()`

5. **Add Tests** (`tests/`):
   - Update tests for your implementations
   - Test happy paths and error cases
   - Test configuration scenarios (fail-fast vs fail-soft)
   - Test caching behavior
   - Test validation errors

6. **Update Environment Variables** (`.env.example`):
   - Update variable names (if manual copy)
   - Document required vs optional vars
   - Add `MCP_STRICT_OUTPUT_VALIDATION=true` for development (optional)

7. **Register Server**:
   - Update `registry/tools_registry.json`
   - See `docs/REGISTRY_FORMAT.md` for details

8. **Enable Observability** (Optional but Recommended):
   - Add `@observe_tool_call_sync()` decorators to tools
   - Configure metrics collection
   - Set up distributed tracing if needed

## Documentation

### Template-Specific

- **[Phase 1 Integration Guide](./PHASE1_INTEGRATION.md)**: Comprehensive guide on using Phase 1 features (config, cache, validation, observability)

### Repository Documentation

- **[Configuration Patterns](../../docs/CONFIGURATION_PATTERNS.md)**: Detailed guide on using the config framework
- **[Domain Boundaries](../../docs/DOMAIN_BOUNDARIES.md)**: Guidelines for scoping servers correctly
- **[Registry Format](../../docs/REGISTRY_FORMAT.md)**: How to register servers in the registry
- **[Architecture](../../docs/ARCHITECTURE.md)**: Repository architecture overview
- **[Validation Guide](../../docs/VALIDATION.md)**: Schema validation implementation
- **[Observability Guide](../../docs/observability-guide.md)**: Observability and metrics guide

## Common Utilities Reference

### Core Utilities (Phase 1)

- **`common/config.py`** - Configuration framework
  - `ServerConfig` - Base class for server configuration
  - `validate_config_or_raise()` - Fail-fast/fail-soft validation
  - `ConfigIssue` - Structured configuration issues
  - `ConfigValidationError` - Exception for invalid config

- **`common/errors.py`** - Error handling
  - `ErrorCode` - Standardized error codes enum
  - `map_upstream_error()` - Map upstream errors to MCP errors
  - `format_error_response()` - Format structured error responses
  - `McpError`, `ApiError`, `ValidationError` - Error classes

- **`common/http.py`** - HTTP client wrapper
  - `call_upstream()` / `call_upstream_async()` - Unified HTTP calls
  - `get()`, `post()`, `get_async()`, `post_async()` - Convenience functions
  - `CallOptions` - Request configuration
  - Features: timeouts, retries, circuit breakers, error mapping

- **`common/cache.py`** - Caching utilities
  - `Cache` - In-memory cache with TTL
  - `get_cache()` - Get global cache instance
  - `build_cache_key()` - Build cache keys from tool arguments
  - `build_cache_key_simple()` - Simple cache key builder

- **`common/validation.py`** - Schema validation
  - `SchemaValidator` - JSON Schema validator with caching
  - `validate_tool_input()` - Validate tool arguments
  - `validate_tool_output()` - Validate tool responses (gated by env var)
  - `validated_tool()` - Decorator for automatic validation

- **`common/logging.py`** - Logging utilities
  - `get_logger()` - Get logger instance
  - `setup_logging()` - Configure logging
  - `request_context()` - Context manager for request logging
  - `generate_correlation_id()` - Generate correlation IDs

- **`common/observability.py`** - Observability decorators
  - `observe_tool_call()` - Async decorator for metrics/logging/tracing
  - `observe_tool_call_sync()` - Sync decorator for metrics/logging/tracing
  - `create_observable_tool_wrapper()` - Wrapper function (non-decorator)

- **`common/metrics.py`** - Metrics collection
  - `MetricsCollector` - Metrics collector interface
  - `get_metrics_collector()` - Get global metrics instance
  - Tracks: tool calls, latency, upstream errors, cache hits/misses

- **`common/tracing.py`** - Distributed tracing
  - `generate_trace_id()` - Generate trace IDs
  - `get_trace_id()`, `set_trace_id()` - Get/set trace ID
  - `propagate_trace_context()` - Propagate trace context
  - `inject_trace_headers()` - Inject trace headers for HTTP calls

### Additional Utilities

- **`common/circuit_breaker.py`** - Circuit breaker pattern
- **`common/rate_limit.py`** - Rate limiting
- **`common/health.py`** - Health check utilities
- **`common/phi.py`** - PHI (Protected Health Information) handling

## See Also

- Existing servers in `servers/` for real-world examples
- `scripts/create_mcp_server.py` - Automated server scaffolding
- `templates/mcp-server-template/` - This template directory
