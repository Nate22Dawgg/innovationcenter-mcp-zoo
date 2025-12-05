# Innovation Center MCP Zoo

[![Validate](https://github.com/OWNER/innovationcenter-mcp-zoo/actions/workflows/validate.yml/badge.svg)](https://github.com/OWNER/innovationcenter-mcp-zoo/actions/workflows/validate.yml)
[![Release](https://github.com/OWNER/innovationcenter-mcp-zoo/actions/workflows/release.yml/badge.svg)](https://github.com/OWNER/innovationcenter-mcp-zoo/actions/workflows/release.yml)

A **registry and collection of MCP (Model Context Protocol) servers and tools** that power a multi-domain analytics engine.

## What This Is

This repository is a **catalog ("zoo") of MCP tools** that provides:

- A **registry** describing each tool (domains, capabilities, auth, safety, schemas)
- A **collection** of first-party and cloned/open-source MCP servers
- **Scripts** to sync/clone external MCP servers from GitHub and update the registry

## What This Is NOT

- This is **NOT** a single application
- This is **NOT** the Fin pharmaceutical analytics pipeline (that's a separate repo)
- This repo is the MCP/tool layer; Fin consumes tools from this repo as "connectors"

## Structure

```
innovationcenter-mcp-zoo/
├── docs/                    # Architecture and registry format documentation
├── registry/                # Tools registry and domain taxonomy
├── schemas/                 # JSON Schema files for tool input/output
├── servers/                 # MCP server implementations
│   ├── clinical/           # Clinical trials, NHANES, and medical data tools
│   ├── markets/            # Financial markets and biotech market tools
│   ├── pricing/            # Healthcare pricing tools
│   ├── claims/             # Insurance claims and EDI processing tools
│   ├── real-estate/        # Real estate property and market data tools
│   └── misc/               # External/experimental MCP servers (PubMed, FDA)
└── scripts/                # Management and validation scripts
```

## Quick Start

1. **View the registry**: `registry/tools_registry.json`
2. **View registry summary**: `docs/REGISTRY_SUMMARY.md` (comprehensive statistics and tool listing)
3. **Validate the registry**: `python3 scripts/validate_registry.py`
4. **Read the docs**: Start with `docs/ARCHITECTURE.md`

## Registry Statistics

- **Total Tools**: 44 tools across 8 servers
- **Active Tools**: 43 (97.7%)
- **Stub Tools**: 1 (2.3%)
- **Domains**: 6 (clinical, markets, pricing, claims, real_estate, misc)

See [Registry Summary](./docs/REGISTRY_SUMMARY.md) for detailed statistics and tool listings.

## Goals

- Modular, scalable architecture for **hundreds of tools**
- Clear separation between tool definitions and implementations
- JSON Schema-based tool descriptions
- Extensible domain taxonomy

---

**Status**: The registry includes 44 production-ready tools across 8 MCP servers. Most tools are active and ready for use.

