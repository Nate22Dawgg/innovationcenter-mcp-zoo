# TypeScript MCP Server Configuration Alignment

## Overview

This document describes the TypeScript configuration validation pattern aligned with Python's `common/config.py`. The goal is **conceptual parity**, not line-by-line porting.

## Pattern Summary

TypeScript MCP servers should implement:

1. **ConfigIssue interface** - Represents configuration validation issues
2. **ServerConfig abstract class** - Base class for server-specific configs
3. **ConfigValidationError class** - Exception for fail-fast mode
4. **validateConfigOrRaise function** - Validates with fail-fast/fail-soft strategies
5. **ErrorCode.SERVICE_NOT_CONFIGURED** - Standard error code for misconfiguration

## Core Components

### 1. ConfigIssue Interface

```typescript
export interface ConfigIssue {
  /** The name of the configuration field with the issue */
  field: string;
  /** Human-readable description of the issue */
  message: string;
  /** Whether this issue prevents the service from functioning (default: true) */
  critical?: boolean;
}
```

### 2. ServerConfig Abstract Class

```typescript
export abstract class ServerConfig {
  /**
   * Validate configuration and return a list of issues.
   * @returns List of ConfigIssue objects. Empty list means configuration is valid.
   */
  abstract validate(): ConfigIssue[];

  /**
   * Check if configuration is valid (no critical issues).
   */
  isValid(): boolean {
    const issues = this.validate();
    return !issues.some(issue => issue.critical !== false);
  }
}
```

### 3. ConfigValidationError Class

```typescript
export class ConfigValidationError extends Error {
  public readonly issues: ConfigIssue[];

  constructor(issues: ConfigIssue[]) {
    super(ConfigValidationError.formatMessage(issues));
    this.issues = issues;
    this.name = 'ConfigValidationError';
    Object.setPrototypeOf(this, ConfigValidationError.prototype);
  }

  private static formatMessage(issues: ConfigIssue[]): string {
    // Format error message with critical/non-critical issues
    // (See implementation in reference server)
  }
}
```

### 4. validateConfigOrRaise Function

```typescript
export interface ConfigErrorPayload {
  error_code: string;  // "SERVICE_NOT_CONFIGURED"
  message: string;
  issues: Array<{
    field: string;
    message: string;
    critical: boolean;
  }>;
}

export function validateConfigOrRaise(
  config: ServerConfig,
  failFast: boolean = true
): [boolean, ConfigErrorPayload | null] {
  const issues = config.validate();
  const criticalIssues = issues.filter(issue => issue.critical !== false);

  if (criticalIssues.length === 0) {
    return [true, null];
  }

  if (failFast) {
    throw new ConfigValidationError(issues);
  }

  const errorPayload: ConfigErrorPayload = {
    error_code: "SERVICE_NOT_CONFIGURED",
    message: "Service configuration is incomplete or invalid.",
    issues: issues.map(issue => ({
      field: issue.field,
      message: issue.message,
      critical: issue.critical !== false,
    })),
  };

  return [false, errorPayload];
}
```

## Implementation Pattern

### Step 1: Define Your Config Class

```typescript
import { ServerConfig, ConfigIssue } from './utils/config/server-config.js';

export class YourServerConfig extends ServerConfig {
  apiKey?: string;
  baseUrl: string = 'https://api.example.com';

  constructor() {
    super();
    this.apiKey = process.env.YOUR_API_KEY;
    this.baseUrl = process.env.YOUR_BASE_URL || 'https://api.example.com';
  }

  validate(): ConfigIssue[] {
    const issues: ConfigIssue[] = [];

    // Required field
    if (!this.apiKey) {
      issues.push({
        field: 'apiKey',
        message: 'YOUR_API_KEY is required for this service',
        critical: true,
      });
    }

    // Optional field validation
    if (!this.baseUrl.startsWith('http://') && !this.baseUrl.startsWith('https://')) {
      issues.push({
        field: 'baseUrl',
        message: 'YOUR_BASE_URL must start with http:// or https://',
        critical: false,  // Warning, not critical
      });
    }

    return issues;
  }
}
```

### Step 2: Load and Validate in Server Startup

```typescript
import { validateConfigOrRaise, ConfigValidationError } from './utils/config/server-config.js';

// In your server initialization
let _config: YourServerConfig | null = null;
let _configErrorPayload: ConfigErrorPayload | null = null;

export function getConfig(failFast: boolean = false): {
  config: YourServerConfig | null;
  errorPayload: ConfigErrorPayload | null;
} {
  if (_config === null && _configErrorPayload === null) {
    const config = new YourServerConfig();
    const [isValid, errorPayload] = validateConfigOrRaise(config, failFast);

    if (isValid) {
      _config = config;
    } else {
      _configErrorPayload = errorPayload;
    }
  }

  return { config: _config, errorPayload: _configErrorPayload };
}

// In server.ts or index.ts
async function createServer(failFast: boolean = true) {
  try {
    const { config, errorPayload } = getConfig(failFast);

    if (errorPayload) {
      if (failFast) {
        // This should not happen (validateConfigOrRaise throws in fail-fast mode)
        throw new Error('Configuration validation failed in fail-fast mode');
      } else {
        // Fail-soft: server starts but tools will return errors
        console.warn('Server starting with invalid configuration. Tools will return SERVICE_NOT_CONFIGURED errors.');
      }
    } else {
      // Configuration is valid - initialize client
      console.info('Configuration validated successfully');
      // Initialize your API client here
    }
  } catch (error) {
    if (error instanceof ConfigValidationError) {
      // Fail-fast: configuration is invalid, don't start server
      console.error(`Configuration validation failed: ${error.message}`);
      process.exit(1);
    }
    throw error;
  }
}
```

### Step 3: Use in Tool Handlers

```typescript
import { getConfig } from '../utils/config.js';

export async function yourTool(args: any) {
  // Check if service is configured
  const { config, errorPayload } = getConfig();
  
  if (errorPayload) {
    // Return SERVICE_NOT_CONFIGURED error
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ error: errorPayload }, null, 2)
      }],
      isError: true
    };
  }

  // Service is configured - proceed normally
  // Use config.apiKey, etc.
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({ result: 'success' }, null, 2)
    }]
  };
}
```

## Validation Strategies

### Fail-Fast (Recommended for Production)

**When to use**: Production deployments, CI/CD pipelines, containers

**Behavior**: Server refuses to start if configuration is invalid

```typescript
const { config, errorPayload } = getConfig(failFast: true);
// If invalid, throws ConfigValidationError immediately
```

**Benefits**:
- Immediate failure on misconfiguration
- Clear error messages at startup
- Prevents partial functionality

### Fail-Soft (Useful for Development)

**When to use**: Development environments, optional services, graceful degradation

**Behavior**: Server starts, but tools return SERVICE_NOT_CONFIGURED errors

```typescript
const { config, errorPayload } = getConfig(failFast: false);
// Server starts, but tools check errorPayload and return errors
```

**Benefits**:
- Useful for development/testing
- Allows graceful degradation
- Tools can check config and return clear errors

## Error Code Integration

Ensure your error codes enum includes:

```typescript
export enum ErrorCode {
  // ... other codes
  SERVICE_NOT_CONFIGURED = "SERVICE_NOT_CONFIGURED",
}
```

The `validateConfigOrRaise` function returns error payloads with `error_code: "SERVICE_NOT_CONFIGURED"` which should align with your error handling system.

## Differences from Python

1. **Type System**: TypeScript uses interfaces and abstract classes instead of dataclasses
2. **Naming**: camelCase instead of snake_case (TypeScript convention)
3. **Error Handling**: TypeScript uses Error classes with prototype setting for instanceof checks
4. **Optional Fields**: TypeScript uses `?` syntax; default values via constructor
5. **No Shared Module**: Each TypeScript server is independent; copy the pattern rather than importing from a shared package

## Alignment Checklist

For each TypeScript MCP server:

- [ ] Implements `ConfigIssue` interface
- [ ] Extends `ServerConfig` abstract class
- [ ] Implements `ConfigValidationError` class
- [ ] Implements `validateConfigOrRaise` function
- [ ] Uses `ErrorCode.SERVICE_NOT_CONFIGURED`
- [ ] Tools check `errorPayload` and return errors when misconfigured
- [ ] Server startup validates config (fail-fast or fail-soft)
- [ ] Configuration loaded from environment variables
- [ ] Required vs optional fields clearly marked (critical vs non-critical)

## Reference Implementation

See the following files in `servers/misc/pubmed-mcp` for the reference implementation:

- **Base pattern**: `src/utils/config/server-config.ts` - Core ServerConfig pattern
- **Service config example**: `src/utils/config/ncbi-server-config.ts` - NCBI service config extending ServerConfig
- **Config loader**: `src/utils/config/config-loader.ts` - Pattern for loading and caching configs

### Example Tool Handler

```typescript
import { getNCBIConfig } from '../utils/config/config-loader.js';

export async function yourTool(args: any) {
  // Check if service is configured
  const { config, errorPayload } = getNCBIConfig();
  
  if (errorPayload) {
    // Return SERVICE_NOT_CONFIGURED error
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ error: errorPayload }, null, 2)
      }],
      isError: true
    };
  }

  // Service is configured - proceed normally
  // Use config.ncbiApiKey, config.ncbiBaseUrl, etc.
  // ...
}
```

## Integration Notes

**Important**: The ServerConfig pattern is designed for **service-specific API configuration** (API keys, endpoints, etc.), not infrastructure configuration (transport, logging, etc.).

For pubmed-mcp:
- **Infrastructure config** (`src/config/index.ts`): Uses Zod for server setup (transport, logging, auth)
- **Service config** (`src/utils/config/ncbi-server-config.ts`): Uses ServerConfig pattern for NCBI API configuration

This separation allows:
1. Infrastructure config to be validated at startup (fail-fast)
2. Service configs to be validated with fail-fast/fail-soft options
3. Tools to check service config and return clear errors when misconfigured
