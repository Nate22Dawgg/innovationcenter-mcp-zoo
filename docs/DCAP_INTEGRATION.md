# DCAP Integration for innovationcenter-mcp-zoo

This document describes how the MCP Zoo integrates with [DCAP (Dynamic Capability Acquisition Protocol)](https://github.com/boorich/dcap), enabling dynamic tool discovery for AI agents.

## Overview

The MCP Zoo now broadcasts tool capabilities to the DCAP network, allowing AI agents to dynamically discover and use tools without pre-configuration. This integration follows **DCAP v3.1 specification**.

### What is DCAP?

DCAP is a decentralized protocol for AI agents to:
- **Discover** tools at runtime via semantic search
- **Evaluate** tool capabilities based on typed signatures
- **Acquire** tools by invoking them through standardized connectors
- **Monitor** tool performance through execution metrics

### Public Relay

The default DCAP relay is hosted at:
- **UDP**: `159.89.110.236:10191` (for sending messages)
- **WebSocket**: `ws://159.89.110.236:10191` (for receiving broadcasts)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     innovationcenter-mcp-zoo                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ clinical-trials  │  │ biotech-markets  │  │   fda-mcp     │  │
│  │      -mcp        │  │      -mcp        │  │  (TypeScript) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘  │
│           │                     │                     │          │
│           └─────────────────────┴─────────────────────┘          │
│                               │                                  │
│                    ┌──────────▼──────────┐                       │
│                    │   common/dcap.py    │                       │
│                    │   (DCAP v3.1 SDK)   │                       │
│                    └──────────┬──────────┘                       │
│                               │                                  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                         UDP Broadcast
                                │
                    ┌───────────▼───────────┐
                    │    DCAP Relay         │
                    │ 159.89.110.236:10191  │
                    └───────────┬───────────┘
                                │
                    WebSocket Broadcast
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      ┌───────▼───────┐ ┌───────▼───────┐ ┌──────▼──────┐
      │   AI Agent    │ │   AI Agent    │ │  Dashboard  │
      │    (Claude)   │ │   (Custom)    │ │  (Monitor)  │
      └───────────────┘ └───────────────┘ └─────────────┘
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DCAP_ENABLED` | `true` | Master toggle - enable/disable all DCAP broadcasting |
| `DCAP_RELAY_HOST` | `159.89.110.236` | DCAP relay hostname or IP |
| `DCAP_RELAY_PORT` | `10191` | DCAP relay UDP port |
| `DCAP_SERVER_ID` | (per-server) | Override the server identifier in broadcasts |

### Toggling DCAP On/Off

**To disable DCAP completely:**
```bash
export DCAP_ENABLED=false
```

**To enable DCAP (default):**
```bash
export DCAP_ENABLED=true
```

**To use a different relay:**
```bash
export DCAP_RELAY_HOST=your-relay.example.com
export DCAP_RELAY_PORT=10191
```

---

## DCAP Message Types

### 1. semantic_discover (sent on server startup)

Announces tool capabilities to the network:

```json
{
  "v": 3,
  "t": "semantic_discover",
  "ts": 1736600000,
  "sid": "clinical-trials-mcp",
  "tool": "clinical_trials_search",
  "does": "Search for clinical trials by condition, intervention, location",
  "when": ["clinical trials", "find trials", "NCT", "medical research"],
  "signature": {
    "input": "SearchQuery",
    "output": "Maybe<TrialList>",
    "cost": 0
  },
  "connector": {
    "transport": "stdio",
    "protocol": "mcp",
    "command": "python servers/clinical/clinical-trials-mcp/server.py"
  }
}
```

### 2. perf_update (sent after each tool execution)

Reports execution metrics:

```json
{
  "v": 3,
  "t": "perf_update",
  "ts": 1736600042,
  "sid": "clinical-trials-mcp",
  "tool": "clinical_trials_search",
  "exec_ms": 1234,
  "success": true,
  "cost_paid": 0,
  "ctx": {
    "caller": "unknown-agent",
    "args": {"condition": "diabetes"}
  }
}
```

---

## Integrated MCP Servers

### Python Servers (9)

| Server | Tools | Description |
|--------|-------|-------------|
| `clinical-trials-mcp` | 3 | ClinicalTrials.gov integration |
| `nhanes-mcp` | 5 | CDC NHANES health survey data |
| `biotech-markets-mcp` | 9 | Biotech company analytics |
| `sec-edgar-mcp` | 6 | SEC EDGAR filings |
| `sp-global-mcp` | 4 | S&P Global Capital IQ |
| `healthcare-equities-orchestrator-mcp` | 1 | Multi-MCP orchestrator |
| `hospital-prices-mcp` | 6 | Hospital price transparency |
| `real-estate-mcp` | 8 | Property data from multiple sources |
| `claims-edi-mcp` | 5 | EDI 837/835 parsing and CMS fee schedules |

### TypeScript Servers (2)

| Server | Tools | Description |
|--------|-------|-------------|
| `fda-mcp` | 10 | OpenFDA API (drugs, devices, recalls) |
| `pubmed-mcp` | 4 | PubMed/NCBI literature search |

**Total: 61 tools registered with DCAP**

---

## How It Works

### On Server Startup

Each server broadcasts `semantic_discover` messages for all its tools:

```python
# In server.py main() function
if DCAP_ENABLED:
    registered = register_tools_with_dcap(
        server_id="clinical-trials-mcp",
        tools=DCAP_TOOLS,
        base_command="python servers/clinical/clinical-trials-mcp/server.py"
    )
    print(f"DCAP: Registered {registered} tools with relay", file=sys.stderr)
```

### On Tool Execution

The `@observe_tool_call` decorator automatically broadcasts `perf_update` messages:

```python
# In common/observability.py
if DCAP_ENABLED:
    send_dcap_perf_update(
        server_id=server_name,
        tool_name=actual_tool_name,
        exec_ms=int(duration_ms),
        success=(status == "success"),
        cost_paid=dcap_cost,
        args=kwargs if log_input else None,
    )
```

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `common/dcap.py` | Core DCAP v3.1 Python module |
| `servers/misc/fda-mcp/src/utils/dcap.ts` | DCAP TypeScript module for FDA |
| `servers/misc/pubmed-mcp/src/utils/dcap/index.ts` | DCAP TypeScript module for PubMed |
| `tests/unit/test_dcap.py` | Unit tests (20 tests, all passing) |
| `scripts/validate_dcap_live.py` | Live validation script |
| `docs/DCAP_INTEGRATION.md` | This documentation |

### Modified Files

All 11 server `server.py`/`index.ts` files were updated to:
1. Import DCAP modules
2. Define `DCAP_TOOLS` metadata
3. Call `register_tools_with_dcap()` on startup

---

## Validation

### Run DCAP Tests

```bash
python3 -m pytest tests/unit/test_dcap.py -v --override-ini="addopts="
```

### Live Validation

```bash
# Basic connectivity test
python scripts/validate_dcap_live.py

# Broadcast all tools
python scripts/validate_dcap_live.py --broadcast-all

# Listen to WebSocket stream
python scripts/validate_dcap_live.py --websocket --duration 15
```

### Expected Output

```
============================================================
DCAP Live Validation
============================================================

Configuration:
  DCAP_ENABLED: True
  DCAP_RELAY_HOST: 159.89.110.236
  DCAP_RELAY_PORT: 10191

📡 Testing UDP connectivity to 159.89.110.236:10191...
   ✅ UDP packet sent successfully (98 bytes)

🔍 Sending semantic_discover message...
   ✅ semantic_discover message sent

📊 Sending perf_update message...
   ✅ perf_update message sent

============================================================
🎉 All validations passed! DCAP integration is working.
```

---

## Monitoring

### WebSocket Stream

Connect to the DCAP WebSocket to monitor all tool broadcasts:

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"[{data.get('sid')}] {data.get('t')} -> {data.get('tool')}")

ws = websocket.WebSocketApp(
    "ws://159.89.110.236:10191",
    on_message=on_message
)
ws.run_forever()
```

### Using wscat (command line)

```bash
npx wscat -c ws://159.89.110.236:10191
```

---

## Security Considerations

1. **Sensitive Data Redaction**: The `_sanitize_args()` function automatically redacts sensitive keys (password, token, api_key, secret, credential) before broadcasting.

2. **Fail-Silent Behavior**: All DCAP operations fail silently to never break tool execution.

3. **No Inbound Connections**: DCAP only sends UDP broadcasts - it does not accept incoming connections.

4. **Optional Integration**: DCAP can be completely disabled via `DCAP_ENABLED=false`.

---

## Troubleshooting

### DCAP messages not being sent

1. Check `DCAP_ENABLED` is not set to `false`
2. Verify network connectivity to `159.89.110.236:10191`
3. Run the validation script: `python scripts/validate_dcap_live.py`

### Server won't start

DCAP failures are always silent - they should never prevent server startup. If a server fails to start, the issue is unrelated to DCAP.

### Messages not appearing on WebSocket

UDP is fire-and-forget. If the relay is down or unreachable, messages are silently dropped. This is by design.

---

## References

- [DCAP Specification (GitHub)](https://github.com/boorich/dcap)
- [DCAP Discussion (GitHub MCP Community)](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/615)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
