# Healthcare Equities Orchestrator MCP Server

Cross-domain orchestrator MCP server that coordinates multiple domain servers to provide comprehensive analysis of healthcare companies across markets and clinical domains.

## Purpose

This orchestrator provides higher-level analysis tools by composing multiple domain-specific MCP servers:

- **biotech-markets-mcp**: Company profiles, financials, and drug pipeline
- **sec-edgar-mcp**: SEC filings and company information
- **clinical-trials-mcp** or **biomcp-mcp**: Clinical trial data

## Tools

### `analyze_company_across_markets_and_clinical`

Analyzes a healthcare company across markets and clinical domains, orchestrating calls to multiple upstream MCP servers to provide:

- **Financials**: Market cap, revenue, cash on hand, burn rate, runway
- **Pipeline**: Drug pipeline with phases and trial counts
- **Clinical Exposure**: Clinical trials summary and active trials
- **SEC Data**: SEC filings and company information
- **Risk Flags**: Aggregated risk flags across all domains

**Input**: Company identifier (ticker, company_name, or cik) + options

**Output**: Strongly typed schema summarizing financials, pipeline, clinical exposure, and key risk flags

## Configuration

All configuration is optional - the orchestrator can work with default settings.

### Environment Variables

- `HEALTHCARE_EQUITIES_ORCHESTRATOR_BIOTECH_MARKETS_MCP_URL`: Optional URL for biotech-markets-mcp (if using HTTP transport)
- `HEALTHCARE_EQUITIES_ORCHESTRATOR_SEC_EDGAR_MCP_URL`: Optional URL for sec-edgar-mcp (if using HTTP transport)
- `HEALTHCARE_EQUITIES_ORCHESTRATOR_CLINICAL_TRIALS_MCP_URL`: Optional URL for clinical-trials-mcp (if using HTTP transport)
- `HEALTHCARE_EQUITIES_ORCHESTRATOR_CACHE_TTL_SECONDS`: Cache TTL in seconds (default: 300)
- `HEALTHCARE_EQUITIES_ORCHESTRATOR_FAIL_FAST`: Fail-fast mode (default: true)

See `.env.example` for details.

## Architecture

This orchestrator:

1. **Does not re-implement upstream logic** - Reuses other MCPs' abstractions
2. **Uses caching** - Avoids repeated calls when orchestrating multiple tools
3. **Handles partial failures gracefully** - If one upstream server fails, others can still succeed
4. **Provides strongly typed outputs** - Clear schemas that LLMs can act on

## Dependencies

This orchestrator depends on:

- `biotech-markets-mcp`: For company profiles and financials
- `sec-edgar-mcp`: For SEC filings (optional)
- `clinical-trials-mcp` or `biomcp-mcp`: For clinical trial data (optional)

## Usage

### Running the Server

```bash
cd servers/markets/healthcare-equities-orchestrator-mcp
python server.py
```

### Example Tool Call

```json
{
  "name": "analyze_company_across_markets_and_clinical",
  "arguments": {
    "identifier": {
      "company_name": "Moderna"
    },
    "include_financials": true,
    "include_clinical": true,
    "include_sec": true
  }
}
```

## Testing

Run tests:

```bash
cd servers/markets/healthcare-equities-orchestrator-mcp
python -m pytest tests/ -v
```

## See Also

- [Domain Boundaries](../../../docs/DOMAIN_BOUNDARIES.md) - Guidelines for orchestrator MCPs
- [Architecture](../../../docs/ARCHITECTURE.md) - Repository architecture overview
- [Configuration Patterns](../../../docs/CONFIGURATION_PATTERNS.md) - Configuration framework
