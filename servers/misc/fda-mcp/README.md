# OpenFDA MCP Server

**Source**: Cloned from [Augmented-Nature/OpenFDA-MCP-Server](https://github.com/Augmented-Nature/OpenFDA-MCP-Server)  
**Version**: 0.1.0  
**Status**: Production-ready

## Overview

A comprehensive Model Context Protocol (MCP) server that provides access to the U.S. Food and Drug Administration's public datasets through the openFDA API. This server enables querying of drug adverse events, product labeling, recalls, approvals, shortages, NDC directory information, and medical device regulatory data.

**Developed by**: [Augmented Nature](https://augmentednature.ai)

## Tools

This server exposes 10 MCP tools:

### Drug Tools (6 tools)

1. **`search_drug_adverse_events`** - Search FDA Adverse Event Reporting System (FAERS) data
2. **`search_drug_labels`** - Search drug product labeling information
3. **`search_drug_ndc`** - Query the National Drug Code (NDC) directory
4. **`search_drug_recalls`** - Find drug recall enforcement reports
5. **`search_drugs_fda`** - Search the Drugs@FDA database for approved products
6. **`search_drug_shortages`** - Query current drug shortages

### Device Tools (4 tools)

7. **`search_device_510k`** - Search FDA 510(k) device clearances
8. **`search_device_classifications`** - Search FDA device classifications
9. **`search_device_adverse_events`** - Search FDA device adverse events (MDR)
10. **`search_device_recalls`** - Search FDA device recall enforcement reports

## Setup

### Prerequisites

- Node.js >= 20.0.0
- npm (comes with Node.js)
- **FDA API Key** (optional but recommended for higher rate limits)

### Installation

The server is already cloned and built in this directory. To rebuild:

```bash
cd servers/misc/fda-mcp
npm install
npm run build
```

### Configuration

#### Environment Variables

- **`FDA_API_KEY`** (optional): Your FDA API key for higher rate limits
  - Get one at: https://open.fda.gov/apis/authentication/
  - Without an API key: 1,000 requests/hour
  - With an API key: 120,000 requests/hour

#### MCP Client Configuration

Add to your MCP client settings:

```json
{
  "mcpServers": {
    "fda-server": {
      "command": "node",
      "args": ["servers/misc/fda-mcp/build/index.js"],
      "env": {
        "FDA_API_KEY": "YOUR_FDA_API_KEY_HERE"
      }
    }
  }
}
```

## Testing

### Start the Server

The server runs on stdio transport by default:

```bash
cd servers/misc/fda-mcp
node build/index.js
```

### Test with MCP Inspector

```bash
cd servers/misc/fda-mcp
npm run inspector
```

## API Key Requirements

- **FDA API Key**: Optional but recommended
  - Without key: 1,000 requests/hour rate limit
  - With key: 120,000 requests/hour rate limit
  - Get one at: https://open.fda.gov/apis/authentication/

## Search Parameters

All tools support comprehensive search parameters including:
- Drug/device names (brand, generic, manufacturer)
- Date ranges (YYYYMMDD format)
- Geographic filters (country, state)
- Classification filters
- Pagination (limit, skip)
- Counting/grouping options

See the original README.md in this directory for detailed parameter documentation for each tool.

## Architecture

- **Language**: TypeScript
- **Framework**: Model Context Protocol SDK v0.6.0
- **API**: openFDA API (https://open.fda.gov/)
- **Transport**: stdio
- **HTTP Client**: Axios

## Rate Limiting

The server automatically handles rate limit errors and provides helpful messages. Rate limits are enforced by the FDA API:
- **Without API Key**: 1,000 requests per hour
- **With API Key**: 120,000 requests per hour

## Documentation

For detailed tool documentation and search parameters, see:
- Original repository: https://github.com/Augmented-Nature/OpenFDA-MCP-Server
- FDA API documentation: https://open.fda.gov/apis/

## License

Open source (see original repository for license details)

## Important Note

This MCP server provides access to public FDA datasets. Always consult healthcare professionals for medical decisions and drug information.
