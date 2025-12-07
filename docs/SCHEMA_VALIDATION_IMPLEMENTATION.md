# Schema-First Validation Implementation Summary

This document summarizes the schema-first validation system implementation for making MCPs more robust.

## What Was Implemented

### 1. Enhanced Error Handling (`common/errors.py`)

- **Added `BAD_REQUEST` error code** to `ErrorCode` enum
- **Enhanced `ValidationError` class** with:
  - `validation_errors` field for machine-readable error details
  - Better error formatting with field-level information

### 2. Schema Validation Module (`common/validation.py`)

A comprehensive validation system with:

- **`SchemaValidator` class**: Core validator with schema caching
  - Loads JSON schemas from `schemas/` directory
  - Caches schemas and validators for performance
  - Formats validation errors into machine-readable structure

- **Helper functions**:
  - `validate_tool_input()`: Validates tool arguments
  - `validate_tool_output()`: Validates tool responses (gated by env var)
  - `get_validator()`: Gets singleton validator instance
  - `validated_tool()`: Decorator for automatic validation

- **Output validation gating**: Controlled by `MCP_STRICT_OUTPUT_VALIDATION` environment variable
  - Default: disabled (no performance impact in production)
  - Enabled: validates outputs but only logs warnings (doesn't fail requests)

### 3. Pydantic Model Generation (`scripts/generate_pydantic_models.py`)

Script to generate type-safe Pydantic models from JSON schemas:

- Reads all JSON schemas from `schemas/` directory
- Generates corresponding Pydantic models
- Creates `__init__.py` with all exports
- Supports both `datamodel-code-generator` (preferred) and fallback manual generation

### 4. Updated Example Servers

- **`servers/claims/claims-edi-mcp/server.py`**: Integrated validation
- **`servers/pricing/hospital-prices-mcp/server.py`**: Integrated validation

Both servers now:
- Validate inputs before tool execution
- Return structured validation errors with `validation_errors` field
- Optionally validate outputs (when strict mode enabled)
- Handle `ValidationError` exceptions properly

### 5. Documentation

- **`docs/VALIDATION.md`**: Comprehensive guide on using the validation system
- **`tests/test_validation.py`**: Test suite for validation functionality

## Key Features

### Input Validation (Always On)

```python
validate_tool_input(tool_name, arguments)
```

- Validates tool arguments against JSON Schema
- Raises `ValidationError` with `BAD_REQUEST` code
- Returns machine-readable `validation_errors` in error details

### Output Validation (Gated)

```python
validate_tool_output(tool_name, result)
```

- Only runs when `MCP_STRICT_OUTPUT_VALIDATION=true`
- Logs warnings but doesn't fail requests
- Useful for catching shape drift in dev/test

### Error Format

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Input validation failed for tool 'claims_parse_edi_837': ...",
    "details": {
      "validation_errors": [
        {
          "message": "'edi_content' is a required property",
          "path": [],
          "schema_path": ["required"],
          "validator": "required"
        }
      ],
      "schema": "claims_parse_edi_837",
      "tool": "claims_parse_edi_837"
    }
  }
}
```

## Usage Pattern

```python
from common.validation import validate_tool_input, validate_tool_output
from common.errors import ValidationError, format_error_response

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        # Validate input
        validate_tool_input(name, arguments)
        
        # Execute tool
        result = await execute_tool(name, **arguments)
        
        # Validate output (optional)
        if isinstance(result, dict):
            validate_tool_output(name, result)
        
        return [TextContent(type="text", text=json.dumps(result))]
    except ValidationError as ve:
        error_response = format_error_response(ve)
        return [TextContent(type="text", text=json.dumps(error_response))]
```

## Schema Naming Convention

- **Input schemas**: `{tool_name}.json` (e.g., `claims_parse_edi_837.json`)
- **Output schemas**: `{tool_name}_output.json` (e.g., `claims_parse_edi_837_output.json`)
- **Location**: `schemas/` directory at project root

## Benefits

1. **Type Safety**: Catch errors at runtime before execution
2. **Machine-Readable Errors**: Structured validation errors for programmatic handling
3. **Performance**: Input validation always on, output validation gated
4. **Developer Experience**: Clear error messages with field-level details
5. **Consistency**: Standardized validation across all MCP servers
6. **Type Generation**: Generate Pydantic models for IDE support and type checking

## Next Steps

To integrate validation into other MCP servers:

1. Import validation utilities
2. Add `validate_tool_input()` in `call_tool()` handler
3. Add `validate_tool_output()` (optional, gated)
4. Handle `ValidationError` exceptions
5. Ensure schemas exist for all tools
6. (Optional) Generate Pydantic models

See `docs/VALIDATION.md` for detailed instructions.
