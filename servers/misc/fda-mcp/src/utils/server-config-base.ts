/**
 * @fileoverview Base configuration validation framework for TypeScript MCP servers.
 * 
 * Shared base classes and utilities (copied from pubmed-mcp for consistency).
 */

/**
 * Represents a configuration validation issue.
 */
export interface ConfigIssue {
  /** The name of the configuration field with the issue */
  field: string;
  /** Human-readable description of the issue */
  message: string;
  /** Whether this issue prevents the service from functioning (default: true) */
  critical?: boolean;
}

/**
 * Base class for MCP server configuration.
 */
export abstract class ServerConfig {
  validate(): ConfigIssue[] {
    return [];
  }

  isValid(): boolean {
    const issues = this.validate();
    return !issues.some(issue => issue.critical !== false);
  }
}

/**
 * Exception raised when configuration validation fails in fail-fast mode.
 */
export class ConfigValidationError extends Error {
  public readonly issues: ConfigIssue[];

  constructor(issues: ConfigIssue[]) {
    super(ConfigValidationError.formatMessage(issues));
    this.issues = issues;
    this.name = 'ConfigValidationError';
    Object.setPrototypeOf(this, ConfigValidationError.prototype);
  }

  private static formatMessage(issues: ConfigIssue[]): string {
    if (issues.length === 0) {
      return "Configuration validation failed (no details available)";
    }

    const criticalIssues = issues.filter(issue => issue.critical !== false);
    const nonCriticalIssues = issues.filter(issue => issue.critical === false);

    const parts = ["Configuration validation failed:"];

    if (criticalIssues.length > 0) {
      parts.push("\nCritical issues (must be fixed):");
      for (const issue of criticalIssues) {
        parts.push(`  - ${issue.field}: ${issue.message}`);
      }
    }

    if (nonCriticalIssues.length > 0) {
      parts.push("\nNon-critical issues (warnings):");
      for (const issue of nonCriticalIssues) {
        parts.push(`  - ${issue.field}: ${issue.message}`);
      }
    }

    return parts.join("\n");
  }
}

/**
 * Error payload structure for fail-soft validation mode.
 */
export interface ConfigErrorPayload {
  error_code: string;
  message: string;
  issues: Array<{
    field: string;
    message: string;
    critical: boolean;
  }>;
}

/**
 * Validate configuration with configurable failure strategy.
 */
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
