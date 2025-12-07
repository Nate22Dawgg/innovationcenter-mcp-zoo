"""
Tests for schema validation system.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

try:
    from common.validation import (
        SchemaValidator,
        validate_tool_input,
        validate_tool_output,
        get_validator,
    )
    from common.errors import ValidationError, ErrorCode
    VALIDATION_AVAILABLE = True
except ImportError as e:
    VALIDATION_AVAILABLE = False
    pytest.skip(f"Validation module not available: {e}", allow_module_level=True)


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_load_schema(self):
        """Test loading a schema file."""
        validator = SchemaValidator()
        schema = validator.load_schema("claims_parse_edi_837")
        
        assert schema is not None
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_load_schema_caching(self):
        """Test that schemas are cached."""
        validator = SchemaValidator()
        schema1 = validator.load_schema("claims_parse_edi_837")
        schema2 = validator.load_schema("claims_parse_edi_837")
        
        # Should be the same object (cached)
        assert schema1 is schema2

    def test_get_validator(self):
        """Test getting a validator instance."""
        validator = SchemaValidator()
        validator_instance = validator.get_validator("claims_parse_edi_837")
        
        assert validator_instance is not None

    def test_validate_input_success(self):
        """Test successful input validation."""
        validator = SchemaValidator()
        data = {"edi_content": "ISA*00*..."}
        
        # Should not raise
        validator.validate_input(data, "claims_parse_edi_837", tool_name="claims_parse_edi_837")

    def test_validate_input_failure(self):
        """Test input validation failure."""
        validator = SchemaValidator()
        data = {"invalid_field": "value"}
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_input(data, "claims_parse_edi_837", tool_name="claims_parse_edi_837")
        
        error = exc_info.value
        assert error.code == ErrorCode.BAD_REQUEST
        assert "validation_errors" in error.details
        assert len(error.details["validation_errors"]) > 0

    def test_validate_output_disabled_by_default(self):
        """Test that output validation is disabled by default."""
        validator = SchemaValidator()
        data = {"invalid": "data"}
        
        # Should not raise (output validation disabled)
        with patch.dict(os.environ, {}, clear=True):
            validator.validate_output(data, "claims_parse_edi_837_output", tool_name="claims_parse_edi_837")

    def test_validate_output_enabled(self):
        """Test output validation when enabled."""
        validator = SchemaValidator()
        data = {"invalid": "data"}
        
        # Should raise when enabled
        with patch.dict(os.environ, {"MCP_STRICT_OUTPUT_VALIDATION": "true"}):
            with pytest.raises(ValidationError):
                validator.validate_output(data, "claims_parse_edi_837_output", tool_name="claims_parse_edi_837")

    def test_format_validation_errors(self):
        """Test formatting validation errors."""
        validator = SchemaValidator()
        validator_instance = validator.get_validator("claims_parse_edi_837")
        
        data = {"invalid": "data"}
        errors = list(validator_instance.iter_errors(data))
        formatted = validator.format_validation_errors(errors)
        
        assert len(formatted) > 0
        assert "message" in formatted[0]
        assert "path" in formatted[0]
        assert "schema_path" in formatted[0]


class TestValidationHelpers:
    """Test validation helper functions."""

    def test_validate_tool_input_success(self):
        """Test validate_tool_input helper."""
        data = {"cpt_code": "99213"}
        # Should not raise
        validate_tool_input("claims_lookup_cpt_price", data)

    def test_validate_tool_input_failure(self):
        """Test validate_tool_input with invalid data."""
        data = {"invalid": "data"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_tool_input("claims_lookup_cpt_price", data)
        
        error = exc_info.value
        assert error.code == ErrorCode.BAD_REQUEST
        assert "validation_errors" in error.details

    def test_validate_tool_output_disabled(self):
        """Test validate_tool_output is disabled by default."""
        data = {"invalid": "data"}
        
        # Should not raise
        with patch.dict(os.environ, {}, clear=True):
            validate_tool_output("claims_lookup_cpt_price", data)

    def test_get_validator_singleton(self):
        """Test that get_validator returns singleton."""
        validator1 = get_validator()
        validator2 = get_validator()
        
        assert validator1 is validator2


class TestErrorFormatting:
    """Test error formatting and structure."""

    def test_validation_error_structure(self):
        """Test ValidationError structure."""
        validator = SchemaValidator()
        data = {"invalid": "data"}
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_input(data, "claims_parse_edi_837", tool_name="test_tool")
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        assert error_dict["code"] == ErrorCode.BAD_REQUEST.value
        assert "message" in error_dict
        assert "details" in error_dict
        assert "validation_errors" in error_dict["details"]
        
        # Check validation_errors structure
        validation_errors = error_dict["details"]["validation_errors"]
        assert len(validation_errors) > 0
        assert "message" in validation_errors[0]
        assert "path" in validation_errors[0]
        assert "schema_path" in validation_errors[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
