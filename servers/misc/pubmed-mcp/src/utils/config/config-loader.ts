/**
 * @fileoverview Configuration loader for service-specific configs.
 * 
 * Reference implementation showing how to load and validate service configs
 * using the ServerConfig pattern aligned with Python common/config.py.
 */

import { validateConfigOrRaise, ConfigErrorPayload } from './server-config.js';
import { NCBIServerConfig } from './ncbi-server-config.js';

// Global config instances
let _ncbiConfig: NCBIServerConfig | null = null;
let _ncbiConfigErrorPayload: ConfigErrorPayload | null = null;

/**
 * Get NCBI service configuration.
 * Validates on first access with fail-soft behavior by default.
 * 
 * @param failFast - If true, throws ConfigValidationError on critical issues.
 *                   If false, returns error payload for fail-soft behavior.
 * @returns Object with config and errorPayload (if any)
 */
export function getNCBIConfig(failFast: boolean = false): {
  config: NCBIServerConfig | null;
  errorPayload: ConfigErrorPayload | null;
} {
  if (_ncbiConfig === null && _ncbiConfigErrorPayload === null) {
    const config = new NCBIServerConfig();
    const [isValid, errorPayload] = validateConfigOrRaise(config, failFast);

    if (isValid) {
      _ncbiConfig = config;
    } else {
      _ncbiConfigErrorPayload = errorPayload;
    }
  }

  return {
    config: _ncbiConfig,
    errorPayload: _ncbiConfigErrorPayload,
  };
}

/**
 * Reset config cache (useful for testing).
 */
export function resetConfigCache(): void {
  _ncbiConfig = null;
  _ncbiConfigErrorPayload = null;
}
