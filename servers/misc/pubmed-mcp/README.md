# PubMed MCP Server

**Source**: Cloned from [cyanheads/pubmed-mcp-server](https://github.com/cyanheads/pubmed-mcp-server)  
**Version**: 1.4.4  
**Status**: Production-ready

## Overview

A production-grade Model Context Protocol (MCP) server that provides comprehensive access to PubMed's biomedical literature database via NCBI E-utilities. This server enables AI agents and research tools to search, retrieve, analyze, and visualize scientific literature.

## Tools

This server exposes 5 MCP tools:

1. **`pubmed_search_articles`** - Search PubMed for articles using query terms, filters, and date ranges
2. **`pubmed_fetch_contents`** - Retrieve detailed article information using PMIDs or search history
3. **`pubmed_article_connections`** - Find related articles, citations, and references for a given PMID
4. **`pubmed_research_agent`** - Generate structured research plans with literature search strategies
5. **`pubmed_generate_chart`** - Create customizable PNG charts from structured publication data

## Setup

### Prerequisites

- Node.js >= 20.0.0
- npm (comes with Node.js)
- **NCBI API Key** (optional but recommended for higher rate limits)

### Installation

The server is already cloned and built in this directory. To rebuild:

```bash
cd servers/misc/pubmed-mcp
npm install
npm run build
```

### Configuration

#### Environment Variables

- **`NCBI_API_KEY`** (optional): Your NCBI API key for higher rate limits
  - Get one at: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
  - Without an API key, you're limited to 3 requests/second
  - With an API key, you get 10 requests/second

- **`MCP_TRANSPORT_TYPE`**: `stdio` (default) or `http`
- **`MCP_HTTP_PORT`**: Port for HTTP server (default: 3017)
- **`MCP_LOG_LEVEL`**: Logging level (default: `debug`)

#### MCP Client Configuration

Add to your MCP client settings:

```json
{
  "mcpServers": {
    "pubmed-mcp-server": {
      "command": "node",
      "args": ["servers/misc/pubmed-mcp/dist/index.js"],
      "env": {
        "NCBI_API_KEY": "YOUR_NCBI_API_KEY_HERE"
      }
    }
  }
}
```

## Testing

### Start the Server

```bash
# Using stdio (default)
cd servers/misc/pubmed-mcp
npm start

# Using HTTP transport
npm run start:http
```

### Test with MCP Inspector

```bash
cd servers/misc/pubmed-mcp
npm run inspector
```

## API Key Requirements

- **NCBI API Key**: Optional but recommended
  - Without key: 3 requests/second rate limit
  - With key: 10 requests/second rate limit
  - Get one at: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

## Architecture

- **Language**: TypeScript
- **Framework**: Model Context Protocol SDK
- **API**: NCBI E-utilities (ESearch, EFetch, ELink, ESummary)
- **Transport**: stdio (default) or HTTP

## Documentation

For detailed tool documentation and examples, see the original repository:
- GitHub: https://github.com/cyanheads/pubmed-mcp-server
- Examples: See `examples/` directory in the cloned repository

## License

Apache License 2.0
