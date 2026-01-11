/**
 * @fileoverview Configuration validation framework for TypeScript MCP servers.
 * 
 * This module provides a base class and utilities for validating server configuration,
 * supporting both fail-fast and fail-soft validation strategies.
 * 
 * ServerConfig is a base class for server-specific configs (env vars, base URLs, API keys, etc.).
 * Subclasses should implement validate() to check required and optional fields and return
 * ConfigIssue objects.
 * 
 * validateConfigOrRaise() provides two validation strategies:
 * - fail-fast: throw ConfigValidationError and typically abort server startup
 * - fail-soft: allow server to start, but tools should surface SERVICE_NOT_CONFIGURED with issue details
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
 * 
 * Responsibilities:
 * - Load config (e.g., from env vars)
 * - Validate required/optional fields
 * - Provide structured validation results
 * 
 * Subclasses should:
 * 1. Define configuration fields as instance attributes
 * 2. Override validate() to check required and optional fields
 * 3. Return a list of ConfigIssue objects for any problems found
 */
export abstract class ServerConfig {
  /**
   * Validate configuration and return a list of issues.
   * 
   * @returns List of ConfigIssue objects. Empty list means configuration is valid.
   *          Issues marked as critical=true indicate the service cannot function.
   */
  validate(): ConfigIssue[] {
    return [];
  }

  /**
   * Check if configuration is valid (no critical issues).
   * 
   * @returns True if there are no critical issues, False otherwise.
   */
  isValid(): boolean {
    const issues = this.validate();
    return !issues.some(issue => issue.critical !== false);
  }
}

/**
 * Exception raised when configuration validation fails in fail-fast mode.
 * 
 * This exception contains structured information about all configuration issues
 * found during validation.
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
 * 
 * @param config - ServerConfig instance to validate
 * @param failFast - If true, throw ConfigValidationError on critical issues.
 *                   If false, return (false, error_payload) for critical issues.
 * @returns Tuple of (is_valid, error_payload):
 *          - (true, null) if configuration is valid (no critical issues)
 *          - (false, error_payload) if failFast=false and there are critical issues.
 *            error_payload contains SERVICE_NOT_CONFIGURED error code and issue details.
 * @throws ConfigValidationError - If failFast=true and there are critical issues.
 */
export function validateConfigOrRaise(
  config: ServerConfig,
  failFast: boolean = true
): [boolean, ConfigErrorPayload | null] {
  const issues = config.validate();
  const criticalIssues = issues.filter(issue => issue.critical !== false);

  // If no critical issues, configuration is valid
  if (criticalIssues.length === 0) {
    return [true, null];
  }

  // If failFast, throw exception
  if (failFast) {
    throw new ConfigValidationError(issues);
  }

  // Otherwise, return error payload for fail-soft behavior
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
