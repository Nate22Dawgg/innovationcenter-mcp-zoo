"""
Schema validation tests.

Validates all schemas/*.json as correct JSON Schema and ensures
tools_registry.json refers only to existing schemas.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List, Set
import jsonschema
from jsonschema import validate, Draft7Validator, ValidationError as JSONSchemaValidationError

pytestmark = [pytest.mark.schema, pytest.mark.python]


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def schemas_dir(project_root: Path) -> Path:
    """Return the schemas directory."""
    return project_root / "schemas"


@pytest.fixture(scope="session")
def registry_file(project_root: Path) -> Path:
    """Return the tools registry file."""
    return project_root / "registry" / "tools_registry.json"


@pytest.fixture(scope="session")
def all_schema_files(schemas_dir: Path) -> List[Path]:
    """Get all JSON schema files recursively."""
    schema_files = []
    for pattern in ["**/*.json"]:
        schema_files.extend(schemas_dir.glob(pattern))
    return sorted(schema_files)


@pytest.fixture(scope="session")
def tools_registry(registry_file: Path) -> Dict[str, Any]:
    """Load and return the tools registry."""
    with open(registry_file, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema_paths_from_registry(tools_registry: Dict[str, Any], project_root: Path) -> Set[str]:
    """Extract all schema paths referenced in the registry."""
    schema_paths = set()
    
    for tool in tools_registry.get("tools", []):
        input_schema = tool.get("input_schema")
        output_schema = tool.get("output_schema")
        
        if input_schema:
            schema_paths.add(str(project_root / input_schema))
        if output_schema:
            schema_paths.add(str(project_root / output_schema))
    
    return schema_paths


class TestSchemaValidation:
    """Test that all schemas are valid JSON Schema."""
    
    def test_all_schemas_are_valid_json(self, all_schema_files: List[Path]):
        """Test that all schema files are valid JSON."""
        for schema_file in all_schema_files:
            with open(schema_file, "r") as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {schema_file}: {e}")
    
    def test_all_schemas_are_valid_json_schema(self, all_schema_files: List[Path]):
        """Test that all schema files are valid JSON Schema (Draft 7)."""
        for schema_file in all_schema_files:
            with open(schema_file, "r") as f:
                schema = json.load(f)
            
            # Skip if it's not a JSON Schema (doesn't have $schema or type)
            if "$schema" not in schema and "type" not in schema:
                # Might be a data file, not a schema - skip it
                continue
            
            try:
                # Validate as JSON Schema Draft 7
                Draft7Validator.check_schema(schema)
            except JSONSchemaValidationError as e:
                pytest.fail(
                    f"Invalid JSON Schema in {schema_file}: {e.message}\n"
                    f"Path: {'.'.join(str(p) for p in e.path)}"
                )
    
    def test_schema_structure(self, all_schema_files: List[Path]):
        """Test that schemas have expected structure."""
        for schema_file in all_schema_files:
            with open(schema_file, "r") as f:
                schema = json.load(f)
            
            # Skip non-schema files
            if "$schema" not in schema and "type" not in schema:
                continue
            
            # If it has $schema, it should be a valid schema reference
            if "$schema" in schema:
                assert schema["$schema"].startswith("http://json-schema.org/"), \
                    f"{schema_file}: $schema should reference JSON Schema spec"
            
            # Should have type property
            if "type" in schema:
                valid_types = ["object", "array", "string", "number", "integer", "boolean", "null"]
                assert schema["type"] in valid_types or isinstance(schema["type"], list), \
                    f"{schema_file}: type should be one of {valid_types} or a list"
    
    def test_registry_schema_references_exist(
        self,
        schema_paths_from_registry: Set[str],
        project_root: Path
    ):
        """Test that all schema paths in registry point to existing files."""
        missing_schemas = []
        
        for schema_path in schema_paths_from_registry:
            full_path = Path(schema_path)
            if not full_path.exists():
                # Try relative path from project root
                rel_path = project_root / schema_path.replace(str(project_root), "").lstrip("/")
                if not rel_path.exists():
                    missing_schemas.append(schema_path)
        
        if missing_schemas:
            pytest.fail(
                f"Registry references non-existent schema files:\n"
                + "\n".join(f"  - {path}" for path in sorted(missing_schemas))
            )
    
    def test_registry_schema_references_are_valid_json(
        self,
        schema_paths_from_registry: Set[str],
        project_root: Path
    ):
        """Test that all referenced schemas are valid JSON."""
        invalid_schemas = []
        
        for schema_path in schema_paths_from_registry:
            full_path = Path(schema_path)
            if not full_path.exists():
                full_path = project_root / schema_path.replace(str(project_root), "").lstrip("/")
            
            if full_path.exists():
                try:
                    with open(full_path, "r") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    invalid_schemas.append((schema_path, str(e)))
        
        if invalid_schemas:
            error_msg = "Registry references invalid JSON files:\n"
            for path, error in invalid_schemas:
                error_msg += f"  - {path}: {error}\n"
            pytest.fail(error_msg)
    
    def test_registry_schema_references_are_valid_json_schema(
        self,
        schema_paths_from_registry: Set[str],
        project_root: Path
    ):
        """Test that all referenced schemas are valid JSON Schema."""
        invalid_schemas = []
        
        for schema_path in schema_paths_from_registry:
            full_path = Path(schema_path)
            if not full_path.exists():
                full_path = project_root / schema_path.replace(str(project_root), "").lstrip("/")
            
            if full_path.exists():
                try:
                    with open(full_path, "r") as f:
                        schema = json.load(f)
                    
                    # Skip if not a schema
                    if "$schema" not in schema and "type" not in schema:
                        continue
                    
                    Draft7Validator.check_schema(schema)
                except JSONSchemaValidationError as e:
                    invalid_schemas.append((schema_path, e.message))
        
        if invalid_schemas:
            error_msg = "Registry references invalid JSON Schema files:\n"
            for path, error in invalid_schemas:
                error_msg += f"  - {path}: {error}\n"
            pytest.fail(error_msg)
    
    def test_registry_consistency(self, tools_registry: Dict[str, Any]):
        """Test that registry structure is consistent."""
        assert "version" in tools_registry, "Registry should have version"
        assert "tools" in tools_registry, "Registry should have tools array"
        assert isinstance(tools_registry["tools"], list), "tools should be a list"
        
        # Check each tool has required fields
        required_fields = ["id", "name", "description", "domain", "status"]
        for tool in tools_registry["tools"]:
            for field in required_fields:
                assert field in tool, f"Tool {tool.get('id', 'unknown')} missing required field: {field}"
    
    def test_schema_property_types(self, all_schema_files: List[Path]):
        """Test that schema properties have correct types."""
        for schema_file in all_schema_files:
            with open(schema_file, "r") as f:
                schema = json.load(f)
            
            # Skip non-schema files
            if "$schema" not in schema and "type" not in schema:
                continue
            
            # If it's an object schema with properties, validate property definitions
            if schema.get("type") == "object" and "properties" in schema:
                for prop_name, prop_def in schema["properties"].items():
                    assert isinstance(prop_def, dict), \
                        f"{schema_file}: Property '{prop_name}' definition should be an object"
                    
                    if "type" in prop_def:
                        valid_types = ["object", "array", "string", "number", "integer", "boolean", "null"]
                        assert prop_def["type"] in valid_types or isinstance(prop_def["type"], list), \
                            f"{schema_file}: Property '{prop_name}' has invalid type"
                    
                    # If enum is present, it should be a list
                    if "enum" in prop_def:
                        assert isinstance(prop_def["enum"], list), \
                            f"{schema_file}: Property '{prop_name}' enum should be a list"
                        assert len(prop_def["enum"]) > 0, \
                            f"{schema_file}: Property '{prop_name}' enum should not be empty"
                    
                    # If default is present, it should match the type
                    if "default" in prop_def and "type" in prop_def:
                        default_type = type(prop_def["default"]).__name__
                        schema_type = prop_def["type"]
                        # Basic type checking (can be enhanced)
                        if schema_type == "string":
                            assert isinstance(prop_def["default"], str), \
                                f"{schema_file}: Property '{prop_name}' default should be string"
                        elif schema_type == "integer":
                            assert isinstance(prop_def["default"], int), \
                                f"{schema_file}: Property '{prop_name}' default should be integer"
                        elif schema_type == "number":
                            assert isinstance(prop_def["default"], (int, float)), \
                                f"{schema_file}: Property '{prop_name}' default should be number"
                        elif schema_type == "boolean":
                            assert isinstance(prop_def["default"], bool), \
                                f"{schema_file}: Property '{prop_name}' default should be boolean"
                        elif schema_type == "array":
                            assert isinstance(prop_def["default"], list), \
                                f"{schema_file}: Property '{prop_name}' default should be array"
                        elif schema_type == "object":
                            assert isinstance(prop_def["default"], dict), \
                                f"{schema_file}: Property '{prop_name}' default should be object"
