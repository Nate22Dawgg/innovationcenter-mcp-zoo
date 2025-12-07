# Configuration Patterns

This document explains how to use the configuration framework in MCP servers, including patterns for fail-fast and fail-soft validation, error handling, and best practices.

## Overview

All MCP servers should use the standardized configuration framework from `common.config`:

- `ServerConfig`: Base class for server-specific configuration
- `ConfigIssue`: Represents configuration validation issues
- `ConfigValidationError`: Exception raised in fail-fast mode
- `validate_config_or_raise()`: Validates config with configurable failure strategy

## Basic Usage

### Step 1: Define Your Config Class

Create a config class that extends `ServerConfig`:

```python
from dataclasses import dataclass
from typing import List, Optional
from common.config import ServerConfig, ConfigIssue

@dataclass
class YourServerConfig(ServerConfig):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    def validate(self) -> List[ConfigIssue]:
        issues: List[ConfigIssue] = []
        
        # Required field
        if not self.api_key:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY is required for this service",
                critical=True
            ))
        
        # Optional field with validation
        if self.base_url and not self.base_url.startswith("http"):
            issues.append(ConfigIssue(
                field="base_url",
                message="BASE_URL must start with http:// or https://",
                critical=False  # Warning, not critical
            ))
        
        return issues
```

### Step 2: Load and Validate Configuration

In your `server.py`:

```python
import os
from common.config import validate_config_or_raise, ConfigValidationError

# Load from environment
config = YourServerConfig(
    base_url=os.getenv("YOUR_BASE_URL"),
    api_key=os.getenv("YOUR_API_KEY")
)

# Validate (fail-fast by default)
try:
    ok, error_payload = validate_config_or_raise(config, fail_fast=True)
    # If we get here, config is valid
    client = YourClient(base_url=config.base_url, api_key=config.api_key)
except ConfigValidationError as e:
    # Configuration is invalid - server won't start
    print(f"Configuration error: {e}")
    sys.exit(1)
```

## Validation Strategies

### Fail-Fast (Recommended for Production)

**When to use**: Production deployments, CI/CD pipelines, containers

**Behavior**: Server refuses to start if configuration is invalid

**Example**:

```python
# Fail-fast validation
config = YourServerConfig(...)
ok, error_payload = validate_config_or_raise(config, fail_fast=True)
# If invalid, raises ConfigValidationError immediately

# Only reached if config is valid
client = YourClient(...)
```

**Benefits**:
- Immediate failure on misconfiguration
- Clear error messages at startup
- Prevents partial functionality
- Better for automated deployments

**When to use**:
- Production environments
- Docker containers
- CI/CD pipelines
- When misconfiguration should be fatal

### Fail-Soft (Useful for Development)

**When to use**: Development, graceful degradation, optional services

**Behavior**: Server starts even with invalid config, but tools return `SERVICE_NOT_CONFIGURED` errors

**Example**:

```python
# Fail-soft validation
config = YourServerConfig(...)
ok, error_payload = validate_config_or_raise(config, fail_fast=False)

if not ok:
    # Store error payload for tools to use
    _config_error_payload = error_payload
    print("Warning: Server starting with invalid configuration")
else:
    # Config is valid - initialize client
    client = YourClient(...)

# In tool handlers:
def your_tool(...):
    if _config_error_payload is not None:
        return _config_error_payload  # Returns SERVICE_NOT_CONFIGURED
    
    # Normal tool execution
    return client.do_something()
```

**Benefits**:
- Server starts even with missing config
- Useful for development/testing
- Allows graceful degradation
- Tools can check config and return clear errors

**When to use**:
- Development environments
- Optional services
- When you want graceful degradation
- Testing scenarios

### Environment Variable Control

Control fail-fast behavior via environment variable:

```python
# In server.py
fail_fast = os.getenv("YOUR_SERVER_FAIL_FAST", "true").lower() == "true"
ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
```

In `.env`:
```bash
# Fail-fast (production)
YOUR_SERVER_FAIL_FAST=true

# Fail-soft (development)
YOUR_SERVER_FAIL_FAST=false
```

## SERVICE_NOT_CONFIGURED Error Code

The `SERVICE_NOT_CONFIGURED` error code is used when:
- Configuration is invalid (fail-soft mode)
- Required environment variables are missing
- Tools are called but service cannot function

### Error Payload Structure

```python
{
    "error_code": "SERVICE_NOT_CONFIGURED",
    "message": "Service configuration is incomplete or invalid.",
    "issues": [
        {
            "field": "api_key",
            "message": "API_KEY is required",
            "critical": true
        }
    ]
}
```

### Using in Tools

```python
from common.errors import ErrorCode

def your_tool(client, config_error_payload, ...):
    # Check if service is configured
    if config_error_payload is not None:
        return config_error_payload  # Returns SERVICE_NOT_CONFIGURED
    
    # Service is configured - proceed normally
    return client.do_something()
```

## Configuration Validation Patterns

### Required Fields

```python
def validate(self) -> List[ConfigIssue]:
    issues = []
    
    if not self.api_key:
        issues.append(ConfigIssue(
            field="api_key",
            message="API_KEY is required",
            critical=True  # Critical = required
        ))
    
    return issues
```

### Optional Fields with Defaults

```python
def validate(self) -> List[ConfigIssue]:
    issues = []
    
    if not self.base_url:
        # Set default if not provided
        self.base_url = "https://api.default.com"
        issues.append(ConfigIssue(
            field="base_url",
            message="BASE_URL not set, using default",
            critical=False  # Non-critical = optional
        ))
    
    return issues
```

### Format Validation

```python
def validate(self) -> List[ConfigIssue]:
    issues = []
    
    if self.api_key and len(self.api_key) < 10:
        issues.append(ConfigIssue(
            field="api_key",
            message="API_KEY appears to be invalid (too short)",
            critical=True
        ))
    
    if self.base_url and not self.base_url.startswith("http"):
        issues.append(ConfigIssue(
            field="base_url",
            message="BASE_URL must start with http:// or https://",
            critical=True
        ))
    
    return issues
```

### Conditional Validation

```python
def validate(self) -> List[ConfigIssue]:
    issues = []
    
    # If using OAuth, client_secret is required
    if self.auth_method == "oauth" and not self.client_secret:
        issues.append(ConfigIssue(
            field="client_secret",
            message="CLIENT_SECRET is required when using OAuth",
            critical=True
        ))
    
    return issues
```

## Environment Variable Naming Conventions

### Recommended Pattern

Use uppercase with underscores, prefixed by server name:

```bash
# Pattern: {SERVER_NAME}_{CONFIG_NAME}
BIOTECH_MARKETS_API_KEY=...
BIOTECH_MARKETS_BASE_URL=...
HOSPITAL_PRICES_API_KEY=...
SEC_EDGAR_API_KEY=...
```

### Examples

```bash
# Good
PUBMED_API_KEY=abc123
TURQUOISE_API_KEY=xyz789
CLINICAL_TRIALS_BASE_URL=https://clinicaltrials.gov

# Bad (not prefixed)
API_KEY=abc123  # Which server?
BASE_URL=https://...  # Ambiguous
```

### Template Server

For the template server, use `TEMPLATE_` prefix:

```bash
TEMPLATE_BASE_URL=https://api.example.com
TEMPLATE_API_KEY=your-key-here
TEMPLATE_FAIL_FAST=true
```

When scaffolding a new server, these will be replaced with the server-specific prefix.

## Configuration Loading Pattern

### Pattern 1: Direct Environment Variables

```python
config = YourServerConfig(
    base_url=os.getenv("YOUR_BASE_URL"),
    api_key=os.getenv("YOUR_API_KEY")
)
```

### Pattern 2: With Defaults

```python
config = YourServerConfig(
    base_url=os.getenv("YOUR_BASE_URL", "https://api.default.com"),
    api_key=os.getenv("YOUR_API_KEY")  # No default = required
)
```

### Pattern 3: Using python-dotenv

```python
from dotenv import load_dotenv

load_dotenv()  # Load .env file

config = YourServerConfig(
    base_url=os.getenv("YOUR_BASE_URL"),
    api_key=os.getenv("YOUR_API_KEY")
)
```

## Error Handling Patterns

### Pattern 1: Fail-Fast at Startup

```python
def create_server():
    config = YourServerConfig(...)
    
    try:
        ok, _ = validate_config_or_raise(config, fail_fast=True)
    except ConfigValidationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Config is valid
    client = YourClient(...)
    return Server(...)
```

### Pattern 2: Fail-Soft with Tool Checks

```python
_config_error_payload = None

def create_server():
    global _config_error_payload
    
    config = YourServerConfig(...)
    ok, error_payload = validate_config_or_raise(config, fail_fast=False)
    
    if not ok:
        _config_error_payload = error_payload
    else:
        _client = YourClient(...)

def your_tool(...):
    if _config_error_payload is not None:
        return _config_error_payload
    return _client.do_something()
```

### Pattern 3: Hybrid (Recommended)

```python
# Check environment for fail-fast preference
fail_fast = os.getenv("YOUR_SERVER_FAIL_FAST", "true").lower() == "true"

try:
    ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
    if not ok:
        _config_error_payload = error_payload
    else:
        _client = YourClient(...)
except ConfigValidationError:
    # Fail-fast mode - exit
    sys.exit(1)
```

## Best Practices

### 1. Always Validate

```python
# ✅ Good - Always validate
config = YourServerConfig(...)
ok, _ = validate_config_or_raise(config, fail_fast=True)

# ❌ Bad - No validation
config = YourServerConfig(...)
client = YourClient(config.api_key)  # api_key might be None!
```

### 2. Use Descriptive Messages

```python
# ✅ Good - Clear message
issues.append(ConfigIssue(
    field="api_key",
    message="API_KEY is required for authentication",
    critical=True
))

# ❌ Bad - Vague message
issues.append(ConfigIssue(
    field="api_key",
    message="Missing",
    critical=True
))
```

### 3. Mark Critical Issues Correctly

```python
# ✅ Good - Critical for required fields
if not self.api_key:
    issues.append(ConfigIssue(
        field="api_key",
        message="API_KEY is required",
        critical=True  # Cannot function without this
    ))

# ✅ Good - Non-critical for optional fields
if not self.base_url:
    self.base_url = "https://default.com"
    issues.append(ConfigIssue(
        field="base_url",
        message="Using default BASE_URL",
        critical=False  # Can function with default
    ))
```

### 4. Set Defaults When Appropriate

```python
# ✅ Good - Set default in validate()
if not self.base_url:
    self.base_url = "https://api.default.com"

# ❌ Bad - Leave None if default exists
if not self.base_url:
    issues.append(...)  # Should set default instead
```

### 5. Validate Format When Possible

```python
# ✅ Good - Validate format
if self.api_key and len(self.api_key) < 10:
    issues.append(ConfigIssue(
        field="api_key",
        message="API_KEY appears invalid (too short)",
        critical=True
    ))

# ✅ Good - Validate URL format
if self.base_url and not self.base_url.startswith("http"):
    issues.append(ConfigIssue(
        field="base_url",
        message="BASE_URL must be a valid HTTP(S) URL",
        critical=True
    ))
```

## Complete Example

```python
# config.py
from dataclasses import dataclass
from typing import List, Optional
from common.config import ServerConfig, ConfigIssue

@dataclass
class ExampleServerConfig(ServerConfig):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    def validate(self) -> List[ConfigIssue]:
        issues = []
        
        # Required field
        if not self.api_key:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY is required",
                critical=True
            ))
        elif len(self.api_key) < 10:
            issues.append(ConfigIssue(
                field="api_key",
                message="API_KEY appears invalid (too short)",
                critical=True
            ))
        
        # Optional field with default
        if not self.base_url:
            self.base_url = "https://api.example.com"
            issues.append(ConfigIssue(
                field="base_url",
                message="BASE_URL not set, using default",
                critical=False
            ))
        elif not self.base_url.startswith("http"):
            issues.append(ConfigIssue(
                field="base_url",
                message="BASE_URL must be a valid HTTP(S) URL",
                critical=True
            ))
        
        return issues
```

```python
# server.py
import os
from common.config import validate_config_or_raise, ConfigValidationError

config = ExampleServerConfig(
    base_url=os.getenv("EXAMPLE_BASE_URL"),
    api_key=os.getenv("EXAMPLE_API_KEY")
)

fail_fast = os.getenv("EXAMPLE_FAIL_FAST", "true").lower() == "true"

try:
    ok, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
    if not ok:
        _config_error_payload = error_payload
    else:
        _client = ExampleClient(config.base_url, config.api_key)
except ConfigValidationError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

## Summary

- **Always use `ServerConfig`**: Extend `ServerConfig` for all server configs
- **Validate in `validate()` method**: Return list of `ConfigIssue` objects
- **Use fail-fast for production**: Prevents partial functionality
- **Use fail-soft for development**: Allows graceful degradation
- **Mark critical issues correctly**: `critical=True` for required fields
- **Follow naming conventions**: `{SERVER_NAME}_{CONFIG_NAME}` for env vars
- **Handle SERVICE_NOT_CONFIGURED**: Check `_config_error_payload` in tools
- **Provide clear error messages**: Help users understand what's wrong
