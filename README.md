# Innovation Center MCP Zoo

[![Validate](https://github.com/Nate22Dawgg/innovationcenter-mcp-zoo/actions/workflows/validate.yml/badge.svg)](https://github.com/Nate22Dawgg/innovationcenter-mcp-zoo/actions/workflows/validate.yml)
[![Release](https://github.com/Nate22Dawgg/innovationcenter-mcp-zoo/actions/workflows/release.yml/badge.svg)](https://github.com/Nate22Dawgg/innovationcenter-mcp-zoo/actions/workflows/release.yml)

A comprehensive **registry and collection of MCP (Model Context Protocol) servers** for healthcare, biotech, finance, and real estate domains.

## Overview

This repository is the **single source of truth** for all MCP tools, providing:

- **99 tools** across **13 MCP servers**
- Standardized registry with schemas, auth requirements, and safety levels
- Shared observability layer (logging, metrics, error handling)
- CI/CD pipeline for validation and releases

## Servers

### Clinical & Biomedical

| Server | Description | Tools |
|--------|-------------|-------|
| **biomcp-mcp** | Comprehensive biomedical research - clinical trials, variants, genes, drugs, OpenFDA | 40+ |
| **clinical-trials-mcp** | ClinicalTrials.gov search and retrieval | 2 |
| **nhanes-mcp** | CDC NHANES health survey data | 5 |
| **pubmed-mcp** | PubMed literature search with charts and citations | 5 |
| **fda-mcp** | OpenFDA drug and device data | 10 |

### Financial Markets

| Server | Description | Tools |
|--------|-------------|-------|
| **biotech-markets-mcp** | Biotech company analysis with SEC, trials, publications | 6 |
| **sec-edgar-mcp** | SEC EDGAR filings and company data | 6 |
| **sp-global-mcp** | S&P Global market intelligence | 4 |

### Healthcare Operations

| Server | Description | Tools |
|--------|-------------|-------|
| **hospital-prices-mcp** | Hospital price transparency via Turquoise Health | 4 |
| **claims-edi-mcp** | EDI 837/835 parsing and CMS fee schedules | 5 |

### Real Estate & Other

| Server | Description | Tools |
|--------|-------------|-------|
| **real-estate-mcp** | Property data via BatchData API | 5+ |
| **playwright-mcp** | Browser automation (Microsoft) | 10+ |

## Repository Structure

```
innovationcenter-mcp-zoo/
├── common/                 # Shared utilities (logging, errors, metrics)
├── docs/                   # Architecture and documentation
├── registry/               # Tools registry and domain taxonomy
│   ├── tools_registry.json
│   └── domains_taxonomy.json
├── schemas/                # JSON Schema files for tool I/O
├── servers/                # MCP server implementations
│   ├── clinical/          
│   │   ├── biomcp-mcp/    # Biomedical research platform
│   │   ├── clinical-trials-mcp/
│   │   └── nhanes-mcp/
│   ├── markets/           
│   │   ├── biotech-markets-mcp/
│   │   ├── sec-edgar-mcp/
│   │   └── sp-global-mcp/
│   ├── pricing/           
│   │   └── hospital-prices-mcp/
│   ├── claims/            
│   │   └── claims-edi-mcp/
│   ├── real-estate/       
│   │   └── real-estate-mcp/
│   └── misc/              
│       ├── pubmed-mcp/
│       ├── fda-mcp/
│       └── playwright-mcp/
├── scripts/                # Validation and management scripts
└── tests/                  # Test suite
```

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/Nate22Dawgg/innovationcenter-mcp-zoo.git
cd innovationcenter-mcp-zoo

# Install Python dependencies
pip install -e ".[dev]"

# Validate the registry
python scripts/validate_registry.py
```

### 2. Run a Server

**Python servers:**
```bash
cd servers/clinical/clinical-trials-mcp
pip install -r requirements.txt
python server.py
```

**TypeScript servers:**
```bash
cd servers/misc/pubmed-mcp
npm install
npm run build
npm start
```

### 3. View the Registry

- **Full registry**: `registry/tools_registry.json`
- **Summary**: `docs/REGISTRY_SUMMARY.md`
- **Architecture**: `docs/ARCHITECTURE.md`

## Observability

All servers can use the shared observability layer in `common/`:

```python
from common import (
    get_logger, setup_logging,      # Structured logging
    format_error_response,           # Standard error format
    get_metrics_collector,           # Performance metrics
    get_rate_limiter,               # Rate limiting
    get_circuit_breaker_manager,    # Circuit breakers
    HealthChecker,                  # Health checks
)
```

See [docs/observability.md](./docs/observability.md) for full documentation.

## CI/CD

- **Validation**: Runs on every push/PR - validates registry, schemas, and runs tests
- **Release**: Triggered by version tags (`v*`) - builds Docker images and creates GitHub releases

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on:
- Development setup
- Code style
- Testing requirements
- Registry updates

## API Keys

Some servers require API keys:

| Server | Required | Environment Variable |
|--------|----------|---------------------|
| hospital-prices-mcp | Yes | `TURQUOISE_API_KEY` |
| real-estate-mcp | Yes | `BATCHDATA_API_KEY` |
| sp-global-mcp | Yes | `SP_GLOBAL_API_KEY` |
| pubmed-mcp | Optional | `NCBI_API_KEY` |
| fda-mcp | Optional | `FDA_API_KEY` |
| biomcp-mcp | Optional | Various (see README) |

## License

Individual servers may have their own licenses. See each server's directory for details.

---

**Total**: 99 tools | 13 servers | 6 domains
