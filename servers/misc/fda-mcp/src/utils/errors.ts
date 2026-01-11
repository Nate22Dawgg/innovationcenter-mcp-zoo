/**
 * @fileoverview Standardized error codes for FDA MCP server.
 * 
 * Aligned with Python common/errors.py ErrorCode enum for consistency.
 */

/**
 * Format an exception as a standard error response.
 * 
 * @param error - Exception to format
 * @param includeTraceback - Whether to include traceback in response
 * @param docsBaseUrl - Base URL for documentation links
 * @returns Standardized error response dictionary
 */
export function formatErrorResponse(
  error: unknown,
  includeTraceback: boolean = false,
  docsBaseUrl?: string
): { error: Record<string, unknown> } {
  if (error instanceof McpError) {
    const errorDict = error.toDict(includeTraceback);
    
    // Add docs URL if base URL provided
    if (docsBaseUrl && !errorDict.docs_url) {
      errorDict.docs_url = `${docsBaseUrl}/errors/${error.code}`;
    }
    
    return { error: errorDict };
  } else {
    // Convert unknown exceptions to internal error
    const errorDict: Record<string, unknown> = {
      code: ErrorCode.INTERNAL_ERROR,
      message: error instanceof Error ? error.message : String(error) || "An unexpected error occurred",
    };

    if (includeTraceback && error instanceof Error) {
      errorDict.traceback = error.stack;
    }

    // Add docs URL if base URL provided
    if (docsBaseUrl) {
      errorDict.docs_url = `${docsBaseUrl}/errors/${ErrorCode.INTERNAL_ERROR}`;
    }

    return { error: errorDict };
  }
}

/**
 * Standard error codes for MCP servers.
 * 
 * Simplified error codes for LLM-friendly error handling:
 * - UPSTREAM_UNAVAILABLE: API down, timeout, 5xx errors
 * - BAD_REQUEST: Invalid arguments, schema validation failures
 * - RATE_LIMITED: Rate limit exceeded (from provider or internal limiter)
 * - NOT_FOUND: Resource not found
 * - INTERNAL_ERROR: Unexpected internal errors
 */
export enum ErrorCode {
  // Simplified error codes (primary)
  UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE",
  BAD_REQUEST = "BAD_REQUEST",
  RATE_LIMITED = "RATE_LIMITED",
  NOT_FOUND = "NOT_FOUND",
  INTERNAL_ERROR = "INTERNAL_ERROR",

  // Legacy/Detailed error codes (for backward compatibility)
  API_ERROR = "API_ERROR",
  API_TIMEOUT = "API_TIMEOUT",
  API_RATE_LIMIT = "API_RATE_LIMIT",
  API_UNAUTHORIZED = "API_UNAUTHORIZED",
  API_FORBIDDEN = "API_FORBIDDEN",
  API_NOT_FOUND = "API_NOT_FOUND",
  API_SERVER_ERROR = "API_SERVER_ERROR",

  // Validation Errors
  VALIDATION_ERROR = "VALIDATION_ERROR",
  INVALID_INPUT = "INVALID_INPUT",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",

  // System Errors
  CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN",
  RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED",
  SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",
  SERVICE_NOT_CONFIGURED = "SERVICE_NOT_CONFIGURED",

  // Data Errors
  DATA_NOT_FOUND = "DATA_NOT_FOUND",
  DATA_PARSE_ERROR = "DATA_PARSE_ERROR",
  CACHE_ERROR = "CACHE_ERROR",
}

/**
 * Base exception class for MCP server errors.
 */
export class McpError extends Error {
  public readonly code: ErrorCode;
  public readonly details?: Record<string, unknown>;
  public readonly retryAfter?: number;
  public readonly docsUrl?: string;
  public readonly originalError?: Error;

  constructor(
    code: ErrorCode,
    message: string,
    options?: {
      details?: Record<string, unknown>;
      retryAfter?: number;
      docsUrl?: string;
      originalError?: Error;
    }
  ) {
    super(message);
    this.code = code;
    this.details = options?.details;
    this.retryAfter = options?.retryAfter;
    this.docsUrl = options?.docsUrl;
    this.originalError = options?.originalError;
    this.name = "McpError";
    Object.setPrototypeOf(this, McpError.prototype);
  }

  toDict(includeTraceback: boolean = false): Record<string, unknown> {
    const errorDict: Record<string, unknown> = {
      code: this.code,
      message: this.message,
    };

    if (this.details) {
      errorDict.details = this.details;
    }

    if (this.retryAfter !== undefined) {
      errorDict.retry_after = this.retryAfter;
    }

    if (this.docsUrl) {
      errorDict.docs_url = this.docsUrl;
    }

    if (includeTraceback && this.originalError) {
      errorDict.traceback = this.originalError.stack;
    }

    return errorDict;
  }
}

/**
 * Map upstream errors (HTTP exceptions, timeouts, etc.) to standardized MCP errors.
 * 
 * This function categorizes common upstream errors into the simplified error codes
 * that LLMs can reason about.
 * 
 * @param error - The upstream exception to map
 * @returns McpError with appropriate error code
 */
export function mapUpstreamError(error: unknown): McpError {
  // Handle Axios errors
  if (error && typeof error === 'object' && 'isAxiosError' in error) {
    const axiosError = error as {
      isAxiosError: boolean;
      response?: { status: number; headers?: Record<string, string>; data?: unknown };
      code?: string;
      message: string;
    };

    if (axiosError.response) {
      const status = axiosError.response.status;
      const retryAfterHeader = axiosError.response.headers?.['retry-after'];
      let retryAfter: number | undefined;
      
      if (retryAfterHeader) {
        const parsed = parseInt(retryAfterHeader, 10);
        if (!isNaN(parsed)) {
          retryAfter = parsed;
        }
      }

      if (status === 404) {
        return new McpError(
          ErrorCode.NOT_FOUND,
          "Resource not found",
          {
            details: { status_code: status, error_type: "AxiosError" },
            originalError: error instanceof Error ? error : new Error(axiosError.message),
          }
        );
      } else if (status === 429) {
        return new McpError(
          ErrorCode.RATE_LIMITED,
          "Rate limit exceeded",
          {
            details: { status_code: status, error_type: "AxiosError" },
            retryAfter: retryAfter ?? 60,
            originalError: error instanceof Error ? error : new Error(axiosError.message),
          }
        );
      } else if (status >= 400 && status < 500) {
        return new McpError(
          ErrorCode.BAD_REQUEST,
          `Invalid request: ${axiosError.message}`,
          {
            details: { status_code: status, error_type: "AxiosError" },
            originalError: error instanceof Error ? error : new Error(axiosError.message),
          }
        );
      } else if (status >= 500) {
        return new McpError(
          ErrorCode.UPSTREAM_UNAVAILABLE,
          "Upstream service error",
          {
            details: { status_code: status, error_type: "AxiosError" },
            originalError: error instanceof Error ? error : new Error(axiosError.message),
          }
        );
      }
    } else if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ETIMEDOUT') {
      return new McpError(
        ErrorCode.UPSTREAM_UNAVAILABLE,
        "Request to upstream service timed out",
        {
          details: { error_type: "AxiosError", code: axiosError.code },
          originalError: error instanceof Error ? error : new Error(axiosError.message),
        }
      );
    } else if (axiosError.code === 'ECONNREFUSED' || axiosError.code === 'ENOTFOUND') {
      return new McpError(
        ErrorCode.UPSTREAM_UNAVAILABLE,
        "Unable to connect to upstream service",
        {
          details: { error_type: "AxiosError", code: axiosError.code },
          originalError: error instanceof Error ? error : new Error(axiosError.message),
        }
      );
    }
  }

  // Handle validation errors
  if (error instanceof TypeError || error instanceof ReferenceError) {
    return new McpError(
      ErrorCode.BAD_REQUEST,
      `Invalid input: ${error instanceof Error ? error.message : String(error)}`,
      {
        details: { error_type: error.constructor.name },
        originalError: error instanceof Error ? error : undefined,
      }
    );
  }

  // Handle known MCP errors (pass through)
  if (error instanceof McpError) {
    return error;
  }

  // Default to internal error for unknown exceptions
  return new McpError(
    ErrorCode.INTERNAL_ERROR,
    `An unexpected error occurred: ${error instanceof Error ? error.message : String(error)}`,
    {
      details: { error_type: error instanceof Error ? error.constructor.name : typeof error },
      originalError: error instanceof Error ? error : undefined,
    }
  );
}
