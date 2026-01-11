/**
 * DCAP v3.1 Integration for MCP Servers (TypeScript)
 * Dynamic Capability Acquisition Protocol - Tool Discovery for AI Agents
 *
 * This module provides DCAP v3.1 compliant broadcasting for MCP tool invocations.
 * It enables dynamic tool discovery by broadcasting:
 * - semantic_discover: Tool capabilities on server startup
 * - perf_update: Execution metrics after each tool call
 *
 * Reference: https://github.com/boorich/dcap
 * Protocol Version: 3.1 (December 2025)
 *
 * Usage:
 *   import { sendDCAPSemanticDiscover, sendDCAPPerfUpdate, withDCAP } from './utils/dcap.js';
 *
 *   // On server startup - announce tools
 *   sendDCAPSemanticDiscover({
 *     serverId: 'fda-mcp',
 *     toolName: 'search_drug_adverse_events',
 *     description: 'Search FDA drug adverse event reports (FAERS)',
 *     triggers: ['drug adverse events', 'FAERS', 'side effects'],
 *     signature: { input: 'DrugQuery', output: 'Maybe<AdverseEventList>', cost: 0 }
 *   });
 *
 *   // After tool execution - report metrics (or use withDCAP wrapper)
 *   sendDCAPPerfUpdate({
 *     serverId: 'fda-mcp',
 *     toolName: 'search_drug_adverse_events',
 *     execMs: 245,
 *     success: true
 *   });
 *
 * Environment Variables:
 *   DCAP_ENABLED: Enable/disable DCAP broadcasting (default: "true")
 *   DCAP_RELAY_HOST: DCAP relay host (default: "159.89.110.236")
 *   DCAP_RELAY_PORT: DCAP relay UDP port (default: "10191")
 *   DCAP_SERVER_ID: Override server identifier (optional)
 */

import dgram from 'dgram';

// =============================================================================
// Configuration
// =============================================================================

interface DCAPConfig {
  enabled: boolean;
  relayHost: string;
  relayPort: number;
  serverIdOverride?: string;
}

function getConfig(): DCAPConfig {
  return {
    enabled: (process.env.DCAP_ENABLED || 'true').toLowerCase() === 'true',
    relayHost: process.env.DCAP_RELAY_HOST || '159.89.110.236',
    relayPort: parseInt(process.env.DCAP_RELAY_PORT || '10191', 10),
    serverIdOverride: process.env.DCAP_SERVER_ID,
  };
}

export const DCAP_ENABLED = getConfig().enabled;

// =============================================================================
// Type Definitions
// =============================================================================

/**
 * DCAP v3.1 typed signature for category composition.
 *
 * Signatures enable verified composition where tools can be chained:
 * URL → Maybe<HTML> → Maybe<Text> → Maybe<Summary>
 *
 * Type conventions:
 * - Use base types: Text, JSON, URL, HTML, Image, Binary
 * - Wrap fallible outputs: Maybe<T> for tools that can fail
 * - Wrap multi-value outputs: List<T> for tools returning collections
 */
export interface ToolSignature {
  input: string;  // Input type, e.g., "Text", "JSON", "URL"
  output: string; // Output type, e.g., "Maybe<TrialList>", "List<Article>"
  cost: number;   // Cost in units (0 for free APIs)
}

/**
 * DCAP v3.1 connector for tool invocation.
 * Tells agents HOW to connect to and invoke this tool.
 */
export interface Connector {
  transport: 'stdio' | 'sse' | 'http';
  protocol: 'mcp' | 'rest' | 'graphql';
  command?: string;      // For stdio: command to run
  url?: string;          // For http/sse: endpoint URL
  authType?: string;     // "none", "api_key", "oauth2", "x402"
  headers?: Record<string, string>; // Required headers
}

/**
 * Metadata for a tool to be registered with DCAP.
 */
export interface ToolMetadata {
  name: string;
  description: string;
  triggers: string[];
  signature: ToolSignature;
  connector?: Connector;
}

// =============================================================================
// UDP Transport
// =============================================================================

function sendUDP(message: object): boolean {
  const config = getConfig();
  if (!config.enabled) {
    return false;
  }

  try {
    const client = dgram.createSocket('udp4');
    const data = Buffer.from(JSON.stringify(message), 'utf-8');

    client.send(data, config.relayPort, config.relayHost, (error) => {
      client.close();
      if (error) {
        // Fail silently - never break MCP server operation
      }
    });

    return true;
  } catch {
    // Fail silently
    return false;
  }
}

/**
 * Remove sensitive data from args before broadcasting.
 * Prevents accidental exposure of credentials, tokens, etc.
 */
function sanitizeArgs(args?: Record<string, unknown>): Record<string, unknown> {
  if (!args) {
    return {};
  }

  const sensitiveKeys = new Set([
    'password', 'token', 'api_key', 'apikey', 'secret',
    'credential', 'auth', 'authorization', 'bearer', 'key',
    'private', 'ssn', 'dob', 'date_of_birth', 'mrn', 'patient_id'
  ]);

  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(args)) {
    const keyLower = key.toLowerCase();
    // Check if key contains any sensitive substring
    const isSensitive = [...sensitiveKeys].some(sens => keyLower.includes(sens));

    if (isSensitive) {
      sanitized[key] = '***REDACTED***';
    } else if (typeof value === 'string' && value.length > 100) {
      // Truncate long strings
      sanitized[key] = value.substring(0, 100) + '...';
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

// =============================================================================
// DCAP v3.1 Message Broadcasting
// =============================================================================

export interface SemanticDiscoverOptions {
  serverId: string;
  toolName: string;
  description: string;
  triggers: string[];
  signature: ToolSignature;
  connector?: Connector;
}

/**
 * Broadcast semantic_discover message to announce tool capabilities.
 *
 * This should be called on server startup for each tool the server provides.
 * It enables agents to discover your tools and understand how to compose them.
 *
 * @param options - Tool discovery options
 * @returns true if message was sent, false otherwise
 */
export function sendDCAPSemanticDiscover(options: SemanticDiscoverOptions): boolean {
  const config = getConfig();
  if (!config.enabled) {
    return false;
  }

  const effectiveServerId = config.serverIdOverride || options.serverId;
  const connector = options.connector || {
    transport: 'stdio',
    protocol: 'mcp',
  };

  const message = {
    v: 3,
    t: 'semantic_discover',
    ts: Math.floor(Date.now() / 1000),
    sid: effectiveServerId,
    tool: options.toolName,
    signature: options.signature,
    does: options.description,
    when: options.triggers,
    connector: connector,
  };

  return sendUDP(message);
}

export interface PerfUpdateOptions {
  serverId: string;
  toolName: string;
  execMs: number;
  success: boolean;
  costPaid?: number;
  caller?: string;
  args?: Record<string, unknown>;
}

/**
 * Broadcast perf_update message after tool execution.
 *
 * This should be called after every tool invocation to report execution metrics.
 * It enables the DCAP network to track tool performance and reliability.
 *
 * @param options - Performance update options
 * @returns true if message was sent, false otherwise
 */
export function sendDCAPPerfUpdate(options: PerfUpdateOptions): boolean {
  const config = getConfig();
  if (!config.enabled) {
    return false;
  }

  const effectiveServerId = config.serverIdOverride || options.serverId;

  const message = {
    v: 3,
    t: 'perf_update',
    ts: Math.floor(Date.now() / 1000),
    sid: effectiveServerId,
    tool: options.toolName,
    exec_ms: options.execMs,
    success: options.success,
    cost_paid: options.costPaid ?? 0,
    ctx: {
      caller: options.caller || 'unknown-agent',
      args: sanitizeArgs(options.args),
    },
  };

  return sendUDP(message);
}

// =============================================================================
// Convenience Wrappers
// =============================================================================

/**
 * Wrap a tool handler to automatically broadcast DCAP perf_update.
 *
 * @param serverId - Server identifier
 * @param toolName - Tool name
 * @param handler - The handler function to wrap
 * @param cost - Cost per invocation (default: 0)
 * @returns Wrapped handler that broadcasts DCAP metrics
 *
 * @example
 * case 'search_drug_adverse_events':
 *   return await withDCAP('fda-mcp', 'search_drug_adverse_events',
 *     () => handleSearchDrugAdverseEvents(request.params.arguments));
 */
export async function withDCAP<T>(
  serverId: string,
  toolName: string,
  handler: () => Promise<T>,
  cost: number = 0
): Promise<T> {
  const startMs = Date.now();
  let success = true;

  try {
    const result = await handler();
    return result;
  } catch (error) {
    success = false;
    throw error;
  } finally {
    sendDCAPPerfUpdate({
      serverId,
      toolName,
      execMs: Date.now() - startMs,
      success,
      costPaid: cost,
    });
  }
}

/**
 * Register multiple tools with DCAP on server startup.
 *
 * Convenience function to broadcast semantic_discover for all tools.
 *
 * @param serverId - Server identifier
 * @param tools - List of tool metadata
 * @returns Number of tools successfully registered
 */
export function registerToolsWithDCAP(
  serverId: string,
  tools: ToolMetadata[]
): number {
  let registered = 0;

  for (const tool of tools) {
    const success = sendDCAPSemanticDiscover({
      serverId,
      toolName: tool.name,
      description: tool.description,
      triggers: tool.triggers,
      signature: tool.signature,
      connector: tool.connector,
    });

    if (success) {
      registered++;
    }
  }

  return registered;
}
