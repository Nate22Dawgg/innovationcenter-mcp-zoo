# Security and PHI Handling

This document describes the security features implemented across MCP servers, with special focus on PHI (Protected Health Information) handling for healthcare-related services.

## Overview

The security layer provides:
- **PHI Redaction**: Automatic redaction of Protected Health Information in logs
- **Configurable Persistence**: Clear separation between "ephemeral" and "stored" data
- **Secrets Management**: Secure API key handling with fail-closed behavior

## PHI Redaction

### Central Helper: `redact_phi()`

The `common/phi.py` module provides a central `redact_phi(payload)` function that automatically identifies and redacts PHI from data structures before logging.

### PHI Fields Detected

The redaction system identifies PHI through:

1. **Field Name Patterns**: Common PHI field names (case-insensitive):
   - Names: `name`, `first_name`, `last_name`, `patient_name`, `member_name`
   - Identifiers: `ssn`, `social_security_number`, `member_id`, `patient_id`, `medical_record_number`
   - Dates: `dob`, `date_of_birth`, `birth_date`
   - Addresses: `address`, `street`, `city`, `state`, `zip_code`
   - Contact: `phone`, `phone_number`, `email`, `email_address`
   - Medical: `diagnosis`, `diagnosis_code`, `procedure_code`, `cpt_code`, `hcpcs_code`

2. **Value Patterns**: Regex patterns to detect PHI in values:
   - SSN: `XXX-XX-XXXX` format
   - Phone: `XXX-XXX-XXXX` format
   - Email: Standard email format
   - ZIP codes: 5 or 9 digit postal codes

### Usage

```python
from common import redact_phi

# Automatically redacts PHI from data structure
data = {
    "patient": {
        "name": "John Doe",
        "ssn": "123-45-6789",
        "dob": "1980-01-01"
    }
}

redacted = redact_phi(data)
# Result: {"patient": {"name": "[REDACTED]", "ssn": "[REDACTED]", "dob": "[REDACTED]"}}
```

### Integration with Logging

PHI redaction is automatically applied in the logging system:

- `log_request()`: Redacts PHI from input parameters
- `log_response()`: Redacts PHI from response data
- `log_error()`: Redacts PHI from error context
- `request_context()`: Automatically redacts PHI in request/response logging

## Configurable Persistence

### Ephemeral vs Stored Data

The system clearly separates data that should not be persisted ("ephemeral") from data that can be stored ("stored").

#### Ephemeral Data

By default, **all PHI-containing data is marked as ephemeral** and should not be persisted beyond the request scope.

```python
from common import mark_ephemeral, is_ephemeral

# Mark data as ephemeral
data = mark_ephemeral({
    "patient": {"name": "John Doe"},
    "claim": {...}
}, reason="Contains PHI")

# Check if data is ephemeral
if is_ephemeral(data):
    # Do not persist this data
    pass
```

#### Stored Data

Data that is safe to persist can be explicitly marked:

```python
from common import mark_stored, should_persist

# Mark data as safe to store
data = mark_stored({
    "aggregate_stats": {...},
    "summary": {...}
}, reason="Aggregate data, no PHI")

# Check if data should be persisted
if should_persist(data):
    # Safe to store
    pass
```

### Default Behavior

- **PHI data**: Automatically marked as ephemeral
- **Non-PHI data**: Can be marked as stored if needed
- **Unmarked data**: Treated as ephemeral by default (fail-safe)

## Secrets Handling

### API Key Management

All API keys must be provided via environment variables. The system implements **fail-closed behavior**: if a required API key is missing, the service will fail with a clear error message rather than attempting to function with partial functionality.

### Supported Services

1. **Turquoise Health** (`TURQUOISE_API_KEY`)
   - Required for hospital pricing data
   - Fail-closed: Service will not start without key

2. **BatchData.io** (`BATCHDATA_API_KEY`)
   - Required for real estate property data
   - Fail-closed: Service will not start without key

3. **S&P Global Market Intelligence** (`SP_GLOBAL_API_KEY`)
   - Required for company financial data
   - Fail-closed: Service will not start without key

### Fail-Closed Behavior

When an API key is missing, the service will:

1. **Raise a clear error** immediately during initialization
2. **Not attempt partial functionality** - no degraded mode
3. **Provide explicit instructions** on how to set the required key

Example error message:
```
ValueError: TURQUOISE_API_KEY environment variable is required. 
This is a required configuration - the service will not function without it. 
Please set TURQUOISE_API_KEY in your environment or configuration.
```

### Best Practices

1. **Never hardcode API keys** in source code
2. **Use environment variables** or secure vaults (AWS Secrets Manager, HashiCorp Vault, etc.)
3. **Rotate keys periodically**
4. **Use separate keys** for development and production
5. **Never commit keys** to version control

### Environment Variable Setup

```bash
# Set API keys in your environment
export TURQUOISE_API_KEY="your-turquoise-key"
export BATCHDATA_API_KEY="your-batchdata-key"
export SP_GLOBAL_API_KEY="your-sp-global-key"

# Or use a .env file (make sure it's in .gitignore)
# .env
TURQUOISE_API_KEY=your-turquoise-key
BATCHDATA_API_KEY=your-batchdata-key
SP_GLOBAL_API_KEY=your-sp-global-key
```

## Implementation in Claims-EDI-MCP

The `claims-edi-mcp` server demonstrates all security features:

1. **PHI Redaction**: All parsed EDI data is automatically redacted before logging
2. **Ephemeral Marking**: Parsed claims are marked as ephemeral by default
3. **Secure Logging**: Uses `request_context()` for automatic PHI redaction

Example:
```python
# EDI parser automatically marks data as ephemeral
result = parse_edi_837(edi_file_path)
# Result includes: {"_persistence": {"type": "ephemeral", "should_persist": False}}

# Logging automatically redacts PHI
with request_context(logger, "claims_parse_edi_837", edi_file_path=path):
    result = parse_edi_837(path)
    # PHI is redacted in logs automatically
```

## Compliance Considerations

### HIPAA Compliance

For HIPAA-covered entities:
- PHI is automatically redacted from logs
- PHI data is marked as ephemeral and should not be persisted
- Clear audit trail of data handling decisions

### Recommendations

1. **Review persistence policies**: Ensure ephemeral data is not being stored
2. **Audit logs regularly**: Verify PHI redaction is working correctly
3. **Monitor for PHI leakage**: Set up alerts for potential PHI in logs
4. **Document data flows**: Understand where PHI goes in your system
5. **Implement data retention policies**: Automatically purge ephemeral data

## Testing

To test PHI redaction:

```python
from common import redact_phi

test_data = {
    "patient_name": "John Doe",
    "ssn": "123-45-6789",
    "phone": "555-123-4567"
}

redacted = redact_phi(test_data)
assert redacted["patient_name"] == "[REDACTED]"
assert redacted["ssn"] == "[REDACTED]"
assert redacted["phone"] == "[REDACTED]"
```

## Additional Resources

- [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
