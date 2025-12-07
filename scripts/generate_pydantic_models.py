#!/usr/bin/env python3
"""
Generate Pydantic models from JSON Schema files.

This script reads JSON Schema files from the schemas/ directory and generates
corresponding Pydantic models. The generated models can be used for type-safe
validation and serialization.

Usage:
    python scripts/generate_pydantic_models.py [--output-dir OUTPUT_DIR] [--schema-dir SCHEMA_DIR]

Options:
    --output-dir: Directory to write generated models (default: generated_models/)
    --schema-dir: Directory containing JSON schemas (default: schemas/)
    --include-output: Also generate models for output schemas (default: True)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from datamodel_code_generator import InputFileType, generate
    DATAMODEL_CODE_GENERATOR_AVAILABLE = True
except ImportError:
    DATAMODEL_CODE_GENERATOR_AVAILABLE = False

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    # Replace underscores and hyphens with spaces, then title case
    name = re.sub(r"[-_]", " ", name)
    # Title case and remove spaces
    return "".join(word.capitalize() for word in name.split())


def to_snake_case(name: str) -> str:
    """Convert PascalCase or kebab-case to snake_case."""
    # Insert underscore before uppercase letters (except first)
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return name.lower()


def generate_pydantic_model_from_schema(
    schema: Dict[str, Any],
    class_name: str,
    output_path: Path,
    use_datamodel_code_generator: bool = True,
) -> None:
    """
    Generate a Pydantic model from a JSON schema.

    Args:
        schema: JSON schema dictionary
        class_name: Name for the generated Pydantic class
        output_path: Path to write the generated model
        use_datamodel_code_generator: Whether to use datamodel-code-generator (if available)
    """
    if use_datamodel_code_generator and DATAMODEL_CODE_GENERATOR_AVAILABLE:
        # Use datamodel-code-generator for better schema support
        try:
            import tempfile

            # Write schema to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(schema, f, indent=2)
                temp_schema_path = Path(f.name)

            try:
                # Generate model
                generate(
                    input_=temp_schema_path,
                    input_file_type=InputFileType.JsonSchema,
                    output=output_path,
                    class_name=class_name,
                    use_annotated=True,
                    use_standard_collections=True,
                    use_generic_container_types=True,
                )
            finally:
                # Clean up temp file
                temp_schema_path.unlink()

            return
        except Exception as e:
            print(f"Warning: datamodel-code-generator failed: {e}", file=sys.stderr)
            print("Falling back to manual generation...", file=sys.stderr)

    # Fallback: Manual generation (simplified)
    generate_simple_pydantic_model(schema, class_name, output_path)


def generate_simple_pydantic_model(
    schema: Dict[str, Any], class_name: str, output_path: Path
) -> None:
    """
    Generate a simple Pydantic model manually (fallback method).

    This is a simplified generator that handles common schema patterns.
    For complex schemas, use datamodel-code-generator.
    """
    lines = [
        '"""',
        f"Auto-generated Pydantic model from JSON Schema: {output_path.stem}",
        '"""',
        "",
        "from typing import Any, Dict, List, Optional",
        "from pydantic import BaseModel, Field",
        "",
        "",
        f"class {class_name}(BaseModel):",
        '    """',
        f"    {schema.get('description', 'Generated from JSON Schema')}",
        '    """',
        "",
    ]

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    for prop_name, prop_schema in properties.items():
        prop_type = infer_python_type(prop_schema)
        is_required = prop_name in required

        # Field definition
        field_def = f"    {prop_name}: {prop_type}"
        if not is_required:
            field_def = f"    {prop_name}: Optional[{prop_type}] = None"

        # Add description if available
        description = prop_schema.get("description", "")
        if description:
            field_def += f'  # {description}'

        lines.append(field_def)
        lines.append("")

    # Add model config
    lines.append("    class Config:")
    lines.append("        extra = 'allow'  # Allow additional properties")
    lines.append("")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def infer_python_type(prop_schema: Dict[str, Any]) -> str:
    """Infer Python type from JSON Schema property."""
    prop_type = prop_schema.get("type")
    enum = prop_schema.get("enum")

    if enum:
        # Use Literal for enums
        enum_values = ", ".join(repr(v) for v in enum)
        return f"Literal[{enum_values}]"

    if prop_type == "string":
        return "str"
    elif prop_type == "integer":
        return "int"
    elif prop_type == "number":
        return "float"
    elif prop_type == "boolean":
        return "bool"
    elif prop_type == "array":
        items = prop_schema.get("items", {})
        item_type = infer_python_type(items) if items else "Any"
        return f"List[{item_type}]"
    elif prop_type == "object":
        return "Dict[str, Any]"
    else:
        return "Any"


def process_schema_file(
    schema_path: Path,
    output_dir: Path,
    include_output: bool = True,
) -> List[Path]:
    """
    Process a single schema file and generate Pydantic models.

    Args:
        schema_path: Path to schema file
        output_dir: Directory to write generated models
        include_output: Whether to process output schemas

    Returns:
        List of generated file paths
    """
    generated_files = []

    # Skip output schemas if not including them
    if not include_output and "_output" in schema_path.stem:
        return generated_files

    # Load schema
    with open(schema_path, "r") as f:
        schema = json.load(f)

    # Determine class name from schema file name
    schema_name = schema_path.stem
    class_name = to_pascal_case(schema_name)

    # Generate model
    output_path = output_dir / f"{schema_name}.py"
    try:
        generate_pydantic_model_from_schema(schema, class_name, output_path)
        generated_files.append(output_path)
        print(f"Generated: {output_path}")
    except Exception as e:
        print(f"Error generating model for {schema_path}: {e}", file=sys.stderr)
        raise

    return generated_files


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Pydantic models from JSON Schema files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated_models"),
        help="Directory to write generated models (default: generated_models/)",
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=Path("schemas"),
        help="Directory containing JSON schemas (default: schemas/)",
    )
    parser.add_argument(
        "--include-output",
        action="store_true",
        default=True,
        help="Also generate models for output schemas (default: True)",
    )
    parser.add_argument(
        "--no-include-output",
        dest="include_output",
        action="store_false",
        help="Skip output schemas",
    )

    args = parser.parse_args()

    # Check dependencies
    if not JSONSCHEMA_AVAILABLE:
        print("Error: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
        sys.exit(1)

    if not DATAMODEL_CODE_GENERATOR_AVAILABLE:
        print(
            "Warning: datamodel-code-generator not available. Install with: pip install datamodel-code-generator",
            file=sys.stderr,
        )
        print("Falling back to simplified generation...", file=sys.stderr)

    # Find all schema files
    schema_dir = args.schema_dir
    if not schema_dir.exists():
        print(f"Error: Schema directory not found: {schema_dir}", file=sys.stderr)
        sys.exit(1)

    schema_files = list(schema_dir.rglob("*.json"))
    if not schema_files:
        print(f"Warning: No JSON schema files found in {schema_dir}", file=sys.stderr)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate __init__.py
    init_file = args.output_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write('"""Auto-generated Pydantic models from JSON schemas."""\n\n')

    # Process each schema file
    generated_files = []
    for schema_file in schema_files:
        try:
            files = process_schema_file(schema_file, args.output_dir, args.include_output)
            generated_files.extend(files)
        except Exception as e:
            print(f"Failed to process {schema_file}: {e}", file=sys.stderr)
            continue

    # Update __init__.py with imports
    if generated_files:
        with open(init_file, "a") as f:
            for gen_file in generated_files:
                module_name = gen_file.stem
                class_name = to_pascal_case(module_name)
                f.write(f"from .{module_name} import {class_name}\n")
            f.write("\n__all__ = [\n")
            for gen_file in generated_files:
                class_name = to_pascal_case(gen_file.stem)
                f.write(f'    "{class_name}",\n')
            f.write("]\n")

    print(f"\nGenerated {len(generated_files)} Pydantic models in {args.output_dir}")


if __name__ == "__main__":
    main()
