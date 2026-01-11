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
 *   import { sendDCAPSemanticDiscover, sendDCAPPerfUpdate, withDCAP } from './dcap/index.js';
 *
 *   // On server startup - announce tools
 *   sendDCAPSemanticDiscover({
 *     serverId: 'pubmed-mcp',
 *     toolName: 'search_articles',
 *     description: 'Search PubMed for articles',
 *     triggers: ['pubmed', 'medical literature', 'research articles'],
 *     signature: { input: 'SearchQuery', output: 'Maybe<ArticleList>', cost: 0 }
 *   });
 *
 *   // After tool execution - report metrics (or use withDCAP wrapper)
 *   sendDCAPPerfUpdate({
 *     serverId: 'pubmed-mcp',
 *     toolName: 'search_articles',
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
 */
export interface ToolSignature {
  input: string;
  output: string;
  cost: number;
}

/**
 * DCAP v3.1 connector for tool invocation.
 */
export interface Connector {
  transport: 'stdio' | 'sse' | 'http';
  protocol: 'mcp' | 'rest' | 'graphql';
  command?: string;
  url?: string;
  authType?: string;
  headers?: Record<string, string>;
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
      // Fail silently
    });

    return true;
  } catch {
    return false;
  }
}

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
    const isSensitive = [...sensitiveKeys].some(sens => keyLower.includes(sens));

    if (isSensitive) {
      sanitized[key] = '***REDACTED***';
    } else if (typeof value === 'string' && value.length > 100) {
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
