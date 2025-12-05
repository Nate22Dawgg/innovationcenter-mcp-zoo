#!/usr/bin/env python3
"""
Validate the tools registry for required fields, allowed values, and consistency.

Usage:
    python scripts/validate_registry.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("WARNING: jsonschema library not available. Schema validation will be skipped.", file=sys.stderr)


# Allowed values
ALLOWED_STATUS = ["stub", "in_development", "experimental", "testing", "active", "deprecated", "archived"]
ALLOWED_SAFETY_LEVELS = ["low", "medium", "high", "restricted"]

# Required fields for tool entries
REQUIRED_FIELDS = [
    "id",
    "name",
    "description",
    "domain",
    "status",
    "safety_level",
    "auth_required",
    "mcp_server_path",
]


def load_json_file(filepath: Path, exit_on_error: bool = True) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if exit_on_error:
            print(f"ERROR: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        return None
    except json.JSONDecodeError as e:
        if exit_on_error:
            print(f"ERROR: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            sys.exit(1)
        return None


def validate_json_schema_structure(schema_path: Path) -> tuple:
    """
    Validate that a file contains a valid JSON Schema structure.
    
    Returns:
        (is_valid, error_message)
    """
    if not JSONSCHEMA_AVAILABLE:
        return (True, None)  # Skip validation if library not available
    
    # Load the schema file
    schema_data = load_json_file(schema_path, exit_on_error=False)
    if schema_data is None:
        return (False, "File not found or invalid JSON")
    
    # Check that it's an object
    if not isinstance(schema_data, dict):
        return (False, "Schema must be a JSON object")
    
    # Try to create a validator (this validates the schema structure)
    try:
        Draft7Validator.check_schema(schema_data)
        return (True, None)
    except jsonschema.SchemaError as e:
        return (False, f"Invalid JSON Schema structure: {e.message}")
    except Exception as e:
        return (False, f"Schema validation error: {str(e)}")


def validate_registry() -> bool:
    """Validate the tools registry and return True if valid."""
    repo_root = Path(__file__).parent.parent
    registry_path = repo_root / "registry" / "tools_registry.json"
    taxonomy_path = repo_root / "registry" / "domains_taxonomy.json"

    print("Loading registry files...")
    registry = load_json_file(registry_path)
    taxonomy = load_json_file(taxonomy_path)

    # Extract valid domain IDs
    valid_domains = {domain["id"] for domain in taxonomy.get("domains", [])}

    print(f"\nValidating {len(registry.get('tools', []))} tool(s)...\n")

    errors = []
    warnings = []
    tool_counts_by_domain = defaultdict(int)
    tool_counts_by_status = defaultdict(int)

    # Validate each tool
    for tool in registry.get("tools", []):
        tool_id = tool.get("id", "<unknown>")

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in tool:
                errors.append(f"Tool '{tool_id}': Missing required field '{field}'")

        # Validate status
        status = tool.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(
                f"Tool '{tool_id}': Invalid status '{status}'. "
                f"Must be one of: {ALLOWED_STATUS}"
            )

        # Validate safety_level
        safety_level = tool.get("safety_level")
        if safety_level not in ALLOWED_SAFETY_LEVELS:
            errors.append(
                f"Tool '{tool_id}': Invalid safety_level '{safety_level}'. "
                f"Must be one of: {ALLOWED_SAFETY_LEVELS}"
            )

        # Validate domain
        domain = tool.get("domain")
        if domain not in valid_domains:
            errors.append(
                f"Tool '{tool_id}': Invalid domain '{domain}'. "
                f"Must be one of: {sorted(valid_domains)}"
            )

        # Validate auth_required consistency
        auth_required = tool.get("auth_required")
        auth_type = tool.get("auth_type")
        if auth_required and not auth_type:
            warnings.append(
                f"Tool '{tool_id}': auth_required is True but auth_type is null"
            )
        if not auth_required and auth_type:
            warnings.append(
                f"Tool '{tool_id}': auth_required is False but auth_type is set"
            )
        
        # Validate schema files exist and are valid JSON Schemas
        input_schema_path = tool.get("input_schema")
        output_schema_path = tool.get("output_schema")
        
        if input_schema_path:
            schema_file = repo_root / input_schema_path
            if not schema_file.exists():
                errors.append(
                    f"Tool '{tool_id}': Input schema file not found: {input_schema_path}"
                )
            else:
                is_valid, error_msg = validate_json_schema_structure(schema_file)
                if not is_valid:
                    errors.append(
                        f"Tool '{tool_id}': Invalid input schema '{input_schema_path}': {error_msg}"
                    )
        
        if output_schema_path:
            schema_file = repo_root / output_schema_path
            if not schema_file.exists():
                errors.append(
                    f"Tool '{tool_id}': Output schema file not found: {output_schema_path}"
                )
            else:
                is_valid, error_msg = validate_json_schema_structure(schema_file)
                if not is_valid:
                    errors.append(
                        f"Tool '{tool_id}': Invalid output schema '{output_schema_path}': {error_msg}"
                    )

        # Count statistics
        if domain:
            tool_counts_by_domain[domain] += 1
        if status:
            tool_counts_by_status[status] += 1

    # Print errors
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
        print()

    # Print warnings
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
        print()

    # Print summary statistics
    print("📊 SUMMARY:")
    print(f"  Total tools: {len(registry.get('tools', []))}")
    print()
    print("  By domain:")
    for domain in sorted(tool_counts_by_domain.keys()):
        print(f"    • {domain}: {tool_counts_by_domain[domain]}")
    print()
    print("  By status:")
    for status in sorted(tool_counts_by_status.keys()):
        print(f"    • {status}: {tool_counts_by_status[status]}")

    # Return success/failure
    if errors:
        print(f"\n❌ Validation failed with {len(errors)} error(s)")
        return False
    else:
        print("\n✅ Validation passed!")
        return True


if __name__ == "__main__":
    success = validate_registry()
    sys.exit(0 if success else 1)

