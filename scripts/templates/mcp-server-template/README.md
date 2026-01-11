# MCP Server Template

This is a template for creating new MCP (Model Context Protocol) servers. It provides a clean, robust scaffold that follows the repository's standards for configuration, error handling, and structure.

## Purpose

This template provides:
- Directory layout for new servers
- Minimal placeholder files wired to use the config framework (`ServerConfig`, `validate_config_or_raise`)
- Example client and tool implementations
- Test structure with minimal examples

## How to Use This Template

### Copy the Template

Copy this template to create a new server:

```bash
cp -r scripts/templates/mcp-server-template servers/<domain>/new-server-name-mcp/
```

### Update Configuration

Edit `config.py`:
- Rename `TemplateServerConfig` to `YourServerConfig`
- Update configuration fields to match your server's needs
- Update the `validate()` method to check your specific requirements

### Update Server Entry Point

Edit `server.py`:
- Update the server name and description
- Implement your actual tools in `src/tools/`
- Implement your actual clients in `src/clients/`
- Register your tools in `list_tools()` and `call_tool()` handlers

### Implement Clients

Edit `src/clients/example_client.py` or create new client files:
- Rename `ExampleClient` to your client name
- Implement actual HTTP calls to your upstream API
- Add proper error handling using `common.errors.map_upstream_error`

### Implement Tools

Edit `src/tools/example_tool.py` or create new tool files:
- Rename `example_tool` to your tool name
- Implement your actual tool logic
- Add schema-based validation using `common.validation.validate_tool_input`
- Add proper error handling using `common.errors`

### Update Tests

Edit `tests/test_clients.py` and `tests/test_tools.py`:
- Update tests to match your actual implementations
- Add comprehensive tests for your specific use cases

### Update Environment Variables

Edit `.env.example`:
- Update variable names to match your server's configuration
- Update `requirements.txt` with your specific dependencies

## Configuration Framework

This template uses the standardized configuration framework from `common.config`:

### TemplateServerConfig

The `config.py` file defines `TemplateServerConfig` which extends `ServerConfig`:
- Define configuration fields as instance attributes
- Override `validate()` to check required and optional fields
- Return a list of `ConfigIssue` objects for any problems found

### validate_config_or_raise

The `server.py` file demonstrates how to use `validate_config_or_raise()`:

**Fail-Fast Mode** (default):
- Raises `ConfigValidationError` if critical config is missing
- Server refuses to start
- Use for production deployments

**Fail-Soft Mode**:
- Returns `(False, error_payload)` if critical config is missing
- Server starts but tools return `SERVICE_NOT_CONFIGURED` errors
- Use for development or graceful degradation

Example:
```python
config = TemplateServerConfig(
    base_url=os.getenv("TEMPLATE_BASE_URL"),
    api_key=os.getenv("TEMPLATE_API_KEY"),
)

ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)

if not ok:
    # Store error_payload for tools to use
    # Tools should check this and return error_payload when called
    _config_error_payload = error_payload
else:
    # Configuration is valid - initialize client
    _client = ExampleClient(base_url=config.base_url, api_key=config.api_key)
```

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

## See Also

- `common/config.py` - Configuration framework documentation
- `docs/CONFIGURATION_PATTERNS.md` - Detailed configuration patterns
- Existing servers in `servers/` for real-world examples
