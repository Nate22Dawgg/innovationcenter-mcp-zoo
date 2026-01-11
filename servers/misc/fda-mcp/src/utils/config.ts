/**
 * @fileoverview Configuration validation framework for FDA MCP server.
 * 
 * Aligned with Python common/config.py ServerConfig pattern.
 */

import { ServerConfig, ConfigIssue, validateConfigOrRaise, ConfigErrorPayload } from './server-config.js';

/**
 * Configuration for FDA MCP server.
 */
export class FDAServerConfig extends ServerConfig {
  // API configuration
  fdaApiKey?: string;
  fdaApiBaseUrl: string = 'https://api.fda.gov';
  
  // Request settings
  requestTimeout: number = 30000; // milliseconds
  maxLimit: number = 100;
  defaultLimit: number = 10;

  constructor() {
    super();
    
    // Load from environment variables
    this.fdaApiKey = process.env.FDA_API_KEY;
    this.fdaApiBaseUrl = process.env.FDA_API_BASE_URL || 'https://api.fda.gov';
    
    if (process.env.FDA_REQUEST_TIMEOUT) {
      this.requestTimeout = parseInt(process.env.FDA_REQUEST_TIMEOUT, 10);
    }
    
    if (process.env.FDA_MAX_LIMIT) {
      this.maxLimit = parseInt(process.env.FDA_MAX_LIMIT, 10);
    }
    
    if (process.env.FDA_DEFAULT_LIMIT) {
      this.defaultLimit = parseInt(process.env.FDA_DEFAULT_LIMIT, 10);
    }
  }

  validate(): ConfigIssue[] {
    const issues: ConfigIssue[] = [];
    
    // FDA API key is optional but recommended for higher rate limits
    // No critical validation needed - API works without key
    
    // Validate timeout
    if (this.requestTimeout < 1000) {
      issues.push({
        field: 'requestTimeout',
        message: 'requestTimeout must be at least 1000ms',
        critical: false
      });
    }
    
    // Validate limits
    if (this.maxLimit < 1 || this.maxLimit > 100) {
      issues.push({
        field: 'maxLimit',
        message: 'maxLimit must be between 1 and 100',
        critical: false
      });
    }
    
    if (this.defaultLimit < 1 || this.defaultLimit > this.maxLimit) {
      issues.push({
        field: 'defaultLimit',
        message: `defaultLimit must be between 1 and ${this.maxLimit}`,
        critical: false
      });
    }
    
    // Validate base URL format
    if (!this.fdaApiBaseUrl.startsWith('http://') && !this.fdaApiBaseUrl.startsWith('https://')) {
      issues.push({
        field: 'fdaApiBaseUrl',
        message: 'fdaApiBaseUrl must start with http:// or https://',
        critical: false
      });
    }
    
    return issues;
  }
}

// Global config instance
let _config: FDAServerConfig | null = null;
let _configErrorPayload: ConfigErrorPayload | null = null;

/**
 * Get the FDA server configuration.
 * Validates on first access.
 */
export function getConfig(failFast: boolean = false): { config: FDAServerConfig | null; errorPayload: ConfigErrorPayload | null } {
  if (_config === null && _configErrorPayload === null) {
    const config = new FDAServerConfig();
    const [isValid, errorPayload] = validateConfigOrRaise(config, failFast);
    
    if (isValid) {
      _config = config;
    } else {
      _configErrorPayload = errorPayload;
    }
  }
  
  return { config: _config, errorPayload: _configErrorPayload };
}
