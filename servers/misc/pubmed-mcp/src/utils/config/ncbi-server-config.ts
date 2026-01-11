/**
 * @fileoverview NCBI API service configuration using ServerConfig pattern.
 * 
 * Reference implementation demonstrating alignment with Python common/config.py pattern.
 * This shows how to use ServerConfig for service-specific API configuration.
 */

import { ServerConfig, ConfigIssue } from './server-config.js';

/**
 * Configuration for NCBI E-utilities API service.
 * 
 * This extends ServerConfig to validate NCBI-specific configuration.
 */
export class NCBIServerConfig extends ServerConfig {
  /** NCBI API key (optional but recommended for higher rate limits) */
  ncbiApiKey?: string;
  
  /** Base URL for NCBI E-utilities */
  ncbiBaseUrl: string = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils';
  
  /** Tool identifier for NCBI requests */
  ncbiToolIdentifier?: string;
  
  /** Admin email for NCBI requests */
  ncbiAdminEmail?: string;
  
  /** Request delay in milliseconds (lower with API key) */
  requestDelayMs: number = 334;
  
  /** Maximum number of retries for failed requests */
  maxRetries: number = 3;

  constructor() {
    super();
    
    // Load from environment variables
    this.ncbiApiKey = process.env.NCBI_API_KEY;
    this.ncbiBaseUrl = process.env.NCBI_BASE_URL || 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils';
    this.ncbiToolIdentifier = process.env.NCBI_TOOL_IDENTIFIER;
    this.ncbiAdminEmail = process.env.NCBI_ADMIN_EMAIL;
    
    if (process.env.NCBI_REQUEST_DELAY_MS) {
      const delay = parseInt(process.env.NCBI_REQUEST_DELAY_MS, 10);
      if (!isNaN(delay) && delay > 0) {
        this.requestDelayMs = delay;
      }
    }
    
    if (process.env.NCBI_MAX_RETRIES) {
      const retries = parseInt(process.env.NCBI_MAX_RETRIES, 10);
      if (!isNaN(retries) && retries >= 0) {
        this.maxRetries = retries;
      }
    }
  }

  validate(): ConfigIssue[] {
    const issues: ConfigIssue[] = [];

    // NCBI API key is optional but recommended
    // No critical validation needed - API works without key (lower rate limits)

    // Validate base URL format
    if (!this.ncbiBaseUrl.startsWith('http://') && !this.ncbiBaseUrl.startsWith('https://')) {
      issues.push({
        field: 'ncbiBaseUrl',
        message: 'NCBI_BASE_URL must start with http:// or https://',
        critical: false,  // Warning, not critical
      });
    }

    // Validate request delay
    if (this.requestDelayMs < 100) {
      issues.push({
        field: 'requestDelayMs',
        message: 'NCBI_REQUEST_DELAY_MS should be at least 100ms for API compliance',
        critical: false,  // Warning
      });
    }

    // Validate retries
    if (this.maxRetries < 0 || this.maxRetries > 10) {
      issues.push({
        field: 'maxRetries',
        message: 'NCBI_MAX_RETRIES should be between 0 and 10',
        critical: false,  // Warning
      });
    }

    // Validate email format if provided
    if (this.ncbiAdminEmail && !this.ncbiAdminEmail.includes('@')) {
      issues.push({
        field: 'ncbiAdminEmail',
        message: 'NCBI_ADMIN_EMAIL should be a valid email address',
        critical: false,  // Warning
      });
    }

    return issues;
  }
}
