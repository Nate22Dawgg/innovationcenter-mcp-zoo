# Architecture Overview

## High-Level Goal

This repository (`innovationcenter-mcp-zoo`) is a **registry and collection of MCP servers and tools** that power a multi-domain analytics engine. It provides a catalog ("zoo") of MCP tools that can be consumed by other applications (like the Fin pharmaceutical analytics pipeline).

## Key Principles

1. **Separation of Concerns**: This repo is the MCP/tool layer. It is NOT the Fin app; Fin is a separate repo that consumes tools from here as "connectors".

2. **Modularity**: The architecture must scale to **hundreds of tools** while remaining maintainable.

3. **Clear Structure**: Tools are organized by domain, with clear boundaries between registry (metadata), schemas (contracts), and implementations (servers).

## Repository Structure

```
innovationcenter-mcp-zoo/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md           # This file
│   └── REGISTRY_FORMAT.md        # Registry schema documentation
│
├── registry/                      # Tool metadata and taxonomy
│   ├── tools_registry.json       # Master catalog of all tools
│   └── domains_taxonomy.json     # Domain definitions and hierarchy
│
├── schemas/                       # JSON Schema definitions
│   ├── clinical_trials_search.json
│   ├── markets_timeseries.json
│   └── hospital_prices_search.json
│
├── servers/                       # MCP server implementations
│   ├── clinical/
│   │   └── clinical-mcp/         # Clinical trials MCP server
│   ├── markets/
│   │   └── markets-mcp/          # Financial markets MCP server
│   ├── pricing/
│   │   └── hospital-prices-mcp/  # Hospital pricing MCP server
│   └── misc/                     # External/experimental MCP servers
│
├── scripts/                       # Management scripts
│   ├── validate_registry.py      # Validate registry structure and content
│   └── sync_github_mcps.py       # Sync external MCP repos from GitHub
│
├── README.md                      # Project overview
├── .gitignore                    # Git ignore rules
└── pyproject.toml                # Python project configuration
```

## Components

### Registry (`registry/`)

- **`tools_registry.json`**: The master catalog of all tools, with metadata about each tool (domain, status, auth, schemas, capabilities).
- **`domains_taxonomy.json`**: Definitions of domains and subdomains for organizing tools.

### Schemas (`schemas/`)

JSON Schema files that define the input and output contracts for tools. These enable:
- Validation before/after tool execution
- Documentation generation
- Type safety in consuming applications

### Servers (`servers/`)

MCP server implementations organized by domain. Each server folder contains:
- Server code (language-agnostic; could be Python, TypeScript, etc.)
- Configuration files
- README with setup instructions

### Scripts (`scripts/`)

Python scripts for managing the zoo:
- **`validate_registry.py`**: Ensures registry integrity and consistency
- **`sync_github_mcps.py`**: Clones/updates external MCP servers from GitHub

## Design Decisions

### Why JSON for the Registry?

- Human-readable and editable
- Easy to validate with JSON Schema
- Language-agnostic (can be consumed by any stack)
- Git-friendly (easy to diff and review)

### Why Separate Schemas?

- Reusability: Same schema can be referenced by multiple tools
- Versioning: Schemas can evolve independently
- Tool-agnostic: Schemas define contracts, not implementations

### Why Domain-Based Organization?

- Clear categorization for hundreds of tools
- Easy navigation and discovery
- Supports domain-specific conventions and patterns
- Aligns with multi-domain analytics use case

## Current State

This is a **scaffolding repository**. Most tools are stubs with TODO comments. The focus is on:
1. Establishing the structure
2. Defining the registry format
3. Creating validation tooling
4. Documenting the architecture

## Future Expansion

As the zoo grows:
- Add more domains and tools to the registry
- Implement real MCP servers
- Add more sophisticated validation (e.g., schema validation)
- Build tool discovery and search capabilities
- Add CI/CD for registry validation
- Create documentation generation from schemas

## Integration with Fin

The Fin pharmaceutical analytics pipeline will:
1. Read `registry/tools_registry.json`
2. Filter tools by domain (e.g., `clinical`, `pricing`)
3. Load MCP servers from `servers/` paths
4. Use schemas from `schemas/` for validation
5. Consume tools as "connectors" in a config-driven pipeline

The separation ensures:
- Fin focuses on analytics logic, not tool implementations
- Tools can be reused by other applications
- Registry can evolve independently

