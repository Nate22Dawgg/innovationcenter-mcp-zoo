# Schema-First Validation Guide

This guide explains how to use the schema-first validation system for MCP servers. The validation system provides runtime validation of tool inputs and outputs against JSON Schema definitions, ensuring type safety and catching errors early.

## Overview

The validation system provides:

1. **Input Validation**: Validates tool arguments against JSON Schema before execution
2. **Output Validation**: Optionally validates tool responses (gated by environment variable)
3. **Machine-Readable Errors**: Returns structured validation errors with detailed field-level information
4. **Type Generation**: Scripts to generate Pydantic models from JSON schemas

## Quick Start

### 1. Import Validation Utilities

```python
from common.validation import validate_tool_input, validate_tool_output
from common.errors import ValidationError, format_error_response
```

### 2. Validate in Tool Handler

```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with schema validation."""
    try:
        # Validate input against JSON schema
        validate_tool_input(name, arguments)
        
        # Execute tool
        if name == "my_tool":
            result = await my_tool(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Validate output (only if strict mode enabled)
        if isinstance(result, dict):
            validate_tool_output(name, result)
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    except ValidationError as ve:
        # Return properly formatted validation error
        error_response = format_error_response(ve)
        return [TextContent(
            type="text",
            text=json.dumps(error_response, indent=2)
        )]
```

## Schema Naming Convention

The validation system infers schema names from tool names:

- **Input Schema**: `{tool_name}.json` (e.g., `claims_parse_edi_837.json`)
- **Output Schema**: `{tool_name}_output.json` (e.g., `claims_parse_edi_837_output.json`)

Schemas should be located in the `schemas/` directory at the project root.

## Error Format

When validation fails, a `ValidationError` is raised with:

- **Code**: `BAD_REQUEST` (from `ErrorCode` enum)
- **Message**: Human-readable error message
- **Details**: Contains:
  - `validation_errors`: List of machine-readable validation errors
  - `schema`: Schema name that failed validation
  - `tool`: Tool name

### Example Error Response

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Input validation failed for tool 'claims_parse_edi_837': 'edi_content' is a required property",
    "details": {
      "validation_errors": [
        {
          "message": "'edi_content' is a required property",
          "path": [],
          "schema_path": ["required"],
          "validator": "required",
          "instance": {}
        }
      ],
      "schema": "claims_parse_edi_837",
      "tool": "claims_parse_edi_837"
    }
  }
}
```

## Output Validation

Output validation is **disabled by default** to avoid performance overhead in production. To enable it:

```bash
export MCP_STRICT_OUTPUT_VALIDATION=true
```

When enabled, output validation runs but **does not fail requests** - it only logs warnings. This allows you to catch output shape drift during development and testing without breaking production.

## Using the Decorator

For simpler integration, you can use the `@validated_tool` decorator:

```python
from common.validation import validated_tool

@validated_tool(
    input_schema="claims_parse_edi_837",
    output_schema="claims_parse_edi_837_output"
)
async def claims_parse_edi_837(edi_content: str) -> Dict[str, Any]:
    """Parse EDI 837 file."""
    # Your implementation here
    return result
```

**Note**: The decorator works best when tool functions accept arguments as `**kwargs`. For more complex cases, use explicit validation in the tool handler.

## Generating Pydantic Models

Generate type-safe Pydantic models from JSON schemas:

```bash
python scripts/generate_pydantic_models.py
```

This will:
1. Read all JSON schemas from `schemas/`
2. Generate corresponding Pydantic models in `generated_models/`
3. Create an `__init__.py` with all exports

### Options

```bash
# Specify output directory
python scripts/generate_pydantic_models.py --output-dir my_models/

# Specify schema directory
python scripts/generate_pydantic_models.py --schema-dir custom_schemas/

# Skip output schemas
python scripts/generate_pydantic_models.py --no-include-output
```

### Using Generated Models

```python
from generated_models import ClaimsParseEdi837, ClaimsParseEdi837Output

# Use as type hints
async def claims_parse_edi_837(
    input_data: ClaimsParseEdi837
) -> ClaimsParseEdi837Output:
    ...
```

## Advanced Usage

### Custom Validator Instance

If you need a custom validator (e.g., different schema path):

```python
from common.validation import SchemaValidator

validator = SchemaValidator(schema_base_path=Path("/custom/schemas"))
validator.validate_input(data, "my_schema", tool_name="my_tool")
```

### Manual Schema Loading

```python
from common.validation import get_validator

validator = get_validator()
schema = validator.load_schema("claims_parse_edi_837")
validator_instance = validator.get_validator("claims_parse_edi_837")
```

## Best Practices

1. **Always validate inputs**: Input validation should never be skipped in production
2. **Gate output validation**: Use environment variable to enable output validation only in dev/test
3. **Use descriptive schema names**: Follow the `{tool_name}` and `{tool_name}_output` convention
4. **Keep schemas in sync**: Update schemas when tool signatures change
5. **Generate types**: Use generated Pydantic models for type hints and IDE support
6. **Handle ValidationError**: Always catch and format `ValidationError` properly

## Troubleshooting

### Schema Not Found

If you see `FileNotFoundError: Schema file not found`, check:
1. Schema file exists in `schemas/` directory
2. Schema name matches tool name (or is explicitly specified)
3. Schema file has `.json` extension

### Validation Always Fails

1. Check schema file is valid JSON
2. Verify schema follows JSON Schema Draft 7
3. Use `validator.load_schema()` to inspect loaded schema
4. Check validation errors in `details.validation_errors`

### Performance Issues

1. Output validation is disabled by default - only enable in dev/test
2. Validators are cached - first call may be slower
3. Consider validating only required fields in hot paths

## Integration Checklist

- [ ] Import validation utilities
- [ ] Add `validate_tool_input()` in tool handler
- [ ] Add `validate_tool_output()` (optional, gated by env var)
- [ ] Handle `ValidationError` exceptions
- [ ] Ensure schemas exist for all tools
- [ ] Test with invalid inputs
- [ ] Enable output validation in test environment
- [ ] Generate Pydantic models (optional but recommended)

## Examples

See `servers/claims/claims-edi-mcp/server.py` and `servers/pricing/hospital-prices-mcp/server.py` for complete examples.
