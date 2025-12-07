"""
PHI (Protected Health Information) handling utilities.

Provides functions for redacting PHI from data structures before logging
and managing data persistence policies.
"""

import re
from typing import Any, Dict, List, Optional, Union, Set
from copy import deepcopy


# Common PHI field patterns (case-insensitive)
PHI_FIELD_PATTERNS = {
    # Direct field name matches
    'name': ['name', 'first_name', 'last_name', 'firstname', 'lastname', 
             'patient_name', 'member_name', 'subscriber_name', 'provider_name'],
    'ssn': ['ssn', 'social_security', 'social_security_number', 'tax_id', 'tax_id_number'],
    'dob': ['dob', 'date_of_birth', 'birth_date', 'birthdate'],
    'address': ['address', 'street', 'street_address', 'city', 'state', 'zip', 'zip_code', 
                'postal_code', 'address_line_1', 'address_line_2'],
    'phone': ['phone', 'phone_number', 'telephone', 'mobile', 'cell'],
    'email': ['email', 'email_address'],
    'member_id': ['member_id', 'member_number', 'subscriber_id', 'patient_id', 
                  'patient_number', 'account_number', 'policy_number'],
    'medical_record': ['medical_record_number', 'mrn', 'record_number'],
    'insurance': ['insurance_id', 'group_number', 'policy_id'],
    'diagnosis': ['diagnosis', 'diagnosis_code', 'icd_code', 'icd10', 'icd9'],
    'procedure': ['procedure', 'procedure_code', 'cpt_code', 'hcpcs_code'],
}


# Patterns for detecting PHI in values (not just field names)
PHI_VALUE_PATTERNS = {
    'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),  # SSN format: XXX-XX-XXXX
    'phone': re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # Phone: XXX-XXX-XXXX
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'zip': re.compile(r'\b\d{5}(-\d{4})?\b'),  # ZIP code
}


# Redaction placeholder
REDACTED_PLACEHOLDER = "[REDACTED]"


def redact_phi(payload: Any, field_patterns: Optional[Dict[str, List[str]]] = None) -> Any:
    """
    Redact PHI (Protected Health Information) from a data structure.
    
    This function recursively traverses dictionaries, lists, and other data structures
    to identify and redact PHI fields before logging or storage.
    
    Args:
        payload: Data structure to redact (dict, list, str, etc.)
        field_patterns: Optional custom field patterns dict (defaults to PHI_FIELD_PATTERNS)
    
    Returns:
        Deep copy of payload with PHI fields redacted
    
    Examples:
        >>> data = {"patient": {"name": "John Doe", "ssn": "123-45-6789"}}
        >>> redact_phi(data)
        {"patient": {"name": "[REDACTED]", "ssn": "[REDACTED]"}}
    """
    if field_patterns is None:
        field_patterns = PHI_FIELD_PATTERNS
    
    # Create a flattened set of all PHI field names for quick lookup
    phi_fields: Set[str] = set()
    for pattern_list in field_patterns.values():
        phi_fields.update(pattern_list)
    
    def _is_phi_field(key: str) -> bool:
        """Check if a field name matches PHI patterns."""
        key_lower = str(key).lower()
        return any(
            pattern.lower() in key_lower or key_lower in pattern.lower()
            for pattern in phi_fields
        )
    
    def _redact_value(value: str) -> str:
        """Redact PHI patterns in string values."""
        if not isinstance(value, str):
            return value
        
        redacted = value
        # Check for SSN pattern
        if PHI_VALUE_PATTERNS['ssn'].search(redacted):
            redacted = PHI_VALUE_PATTERNS['ssn'].sub(REDACTED_PLACEHOLDER, redacted)
        # Check for phone pattern
        if PHI_VALUE_PATTERNS['phone'].search(redacted):
            redacted = PHI_VALUE_PATTERNS['phone'].sub(REDACTED_PLACEHOLDER, redacted)
        # Check for email pattern
        if PHI_VALUE_PATTERNS['email'].search(redacted):
            redacted = PHI_VALUE_PATTERNS['email'].sub(REDACTED_PLACEHOLDER, redacted)
        
        return redacted
    
    def _redact_recursive(obj: Any) -> Any:
        """Recursively redact PHI from data structure."""
        if isinstance(obj, dict):
            redacted = {}
            for key, value in obj.items():
                if _is_phi_field(key):
                    # Redact the entire value
                    redacted[key] = REDACTED_PLACEHOLDER
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    redacted[key] = _redact_recursive(value)
                elif isinstance(value, str):
                    # Check for PHI patterns in string values
                    redacted[key] = _redact_value(value)
                else:
                    redacted[key] = value
            return redacted
        elif isinstance(obj, list):
            return [_redact_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return _redact_value(obj)
        else:
            return obj
    
    # Create deep copy to avoid modifying original
    payload_copy = deepcopy(payload)
    return _redact_recursive(payload_copy)


def is_phi_field(field_name: str, field_patterns: Optional[Dict[str, List[str]]] = None) -> bool:
    """
    Check if a field name matches PHI patterns.
    
    Args:
        field_name: Field name to check
        field_patterns: Optional custom field patterns dict
    
    Returns:
        True if field matches PHI patterns, False otherwise
    """
    if field_patterns is None:
        field_patterns = PHI_FIELD_PATTERNS
    
    phi_fields: Set[str] = set()
    for pattern_list in field_patterns.values():
        phi_fields.update(pattern_list)
    
    field_lower = str(field_name).lower()
    return any(
        pattern.lower() in field_lower or field_lower in pattern.lower()
        for pattern in phi_fields
    )


def mark_ephemeral(data: Dict[str, Any], reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark data as ephemeral (should not be persisted beyond request scope).
    
    Args:
        data: Data dictionary to mark
        reason: Optional reason for ephemeral marking
    
    Returns:
        Data dictionary with ephemeral metadata
    """
    if not isinstance(data, dict):
        data = {"_data": data}
    
    data["_persistence"] = {
        "type": "ephemeral",
        "reason": reason or "Contains PHI or sensitive data",
        "should_persist": False
    }
    return data


def mark_stored(data: Dict[str, Any], reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark data as stored (can be persisted).
    
    Args:
        data: Data dictionary to mark
        reason: Optional reason for stored marking
    
    Returns:
        Data dictionary with persistence metadata
    """
    if not isinstance(data, dict):
        data = {"_data": data}
    
    data["_persistence"] = {
        "type": "stored",
        "reason": reason or "Safe to persist",
        "should_persist": True
    }
    return data


def is_ephemeral(data: Dict[str, Any]) -> bool:
    """
    Check if data is marked as ephemeral.
    
    Args:
        data: Data dictionary to check
    
    Returns:
        True if data is marked as ephemeral, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    persistence = data.get("_persistence", {})
    return persistence.get("type") == "ephemeral" or not persistence.get("should_persist", False)


def should_persist(data: Dict[str, Any]) -> bool:
    """
    Check if data should be persisted.
    
    Args:
        data: Data dictionary to check
    
    Returns:
        True if data should be persisted, False if ephemeral
    """
    return not is_ephemeral(data)
