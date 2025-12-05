# Registry Format Documentation

This document describes the structure and format of `registry/tools_registry.json`.

## Overview

The tools registry is a JSON file that catalogs all MCP tools available in this zoo. Each tool entry describes its capabilities, requirements, and metadata.

## Registry Structure

```json
{
  "version": "string",
  "last_updated": "ISO8601 datetime",
  "tools": [
    {
      // Tool entries (see below)
    }
  ]
}
```

## Tool Entry Fields

### Required Fields

- **`id`** (string): Unique identifier for the tool (e.g., `clinical_trials.search`)
- **`name`** (string): Human-readable name
- **`description`** (string): What the tool does
- **`domain`** (string): Primary domain (must match a domain in `domains_taxonomy.json`)
- **`status`** (string): Current status (see allowed values below)
- **`safety_level`** (string): Safety/risk classification (see allowed values below)
- **`auth_required`** (boolean): Whether authentication is needed
- **`mcp_server_path`** (string): Relative path to the MCP server implementation

### Optional Fields

- **`auth_type`** (string | null): Type of authentication if required (e.g., `"api_key"`, `"oauth"`, `"bearer"`)
- **`input_schema`** (string | null): Path to JSON Schema for input validation
- **`output_schema`** (string | null): Path to JSON Schema for output validation
- **`capabilities`** (array of strings): List of capabilities (e.g., `["search", "filter", "pagination"]`)
- **`tags`** (array of strings): Tags for categorization and search
- **`external_source`** (string | null): URL or reference to external source if cloned
- **`notes`** (string | null): Implementation notes, TODOs, or warnings

## Allowed Values

### Status

- **`stub`**: Placeholder with no real implementation yet
- **`in_development`**: Under active development
- **`experimental`**: Functional implementation, but still being refined and tested
- **`testing`**: Being tested before production
- **`active`**: Production-ready and available
- **`deprecated`**: Still available but not recommended for new use
- **`archived`**: No longer maintained but kept for reference

### Safety Level

- **`low`**: Read-only operations, public data, no sensitive information
- **`medium`**: May access semi-sensitive data, requires authentication
- **`high`**: Accesses sensitive or protected data, requires strong auth and audit
- **`restricted`**: Special access required, additional approval needed

## Example Entry

```json
{
  "id": "clinical_trials.search",
  "name": "Clinical Trials Search",
  "description": "Search for clinical trials by condition, intervention, location, and other criteria",
  "domain": "clinical",
  "status": "stub",
  "safety_level": "low",
  "auth_required": false,
  "auth_type": null,
  "mcp_server_path": "servers/clinical/clinical-mcp",
  "input_schema": "schemas/clinical_trials_search.json",
  "output_schema": "schemas/clinical_trials_search_output.json",
  "capabilities": ["search", "filter", "pagination"],
  "tags": ["clinical-trials", "research", "medical"],
  "external_source": null,
  "notes": "TODO: Implement connection to ClinicalTrials.gov API or similar data source"
}
```

## Validation

Run `scripts/validate_registry.py` to check that:
- All required fields are present
- Status values are from the allowed list
- Safety level values are from the allowed list
- Domain references exist in `domains_taxonomy.json`
- Paths reference valid files/directories (if they exist)

