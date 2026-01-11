# Innovation Center MCP Zoo - Audit Report v2

**Date**: December 2024  
**Auditor**: Senior Architect & Codebase Auditor  
**Scope**: Full QC pass after recent robustness improvements (config framework, templates, macro tools, orchestration)  
**Mode**: READ-ONLY inspection (no modifications)

---

## Executive Summary

The repository has made significant progress in adopting standardized patterns for configuration, error handling, and HTTP clients. **6 of 13 servers** now use the new `ServerConfig` framework, and several have adopted the shared `common.http` client. However, **7 servers still need migration** to the config framework, and **most servers still use raw `requests`** instead of the shared HTTP client.

**Key Strengths:**
- Strong macro/workflow tools in biotech-markets-mcp (dossier generation, refinement)
- Cross-MCP orchestration via healthcare-equities-orchestrator-mcp
- Shared identifier schemas (ticker, CIK, NCT ID) in `schemas/`
- Comprehensive test coverage for biomcp-mcp
- Shared caching infrastructure (`common.cache`)

**Key Gaps:**
- 7 servers not using config framework (biomcp-mcp, clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp)
- Most servers use raw `requests` instead of `common.http`
- Limited E2E tests for orchestrator workflows
- Missing macro tools in claims and pricing domains
- Inconsistent error mapping across servers

---

## 1. Global Repo View

### 1.1 Repository Structure

**Top-level directories:**
- `common/` - Shared utilities (config, errors, HTTP, cache, validation, observability, PHI handling)
- `servers/` - MCP server implementations organized by domain
- `scripts/` - Helper scripts including `create_mcp_server.py` and templates
- `docs/` - Architecture and configuration documentation
- `schemas/` - JSON schemas for tool inputs/outputs (100+ files)
- `registry/` - Centralized tool registry (`tools_registry.json`, `domains_taxonomy.json`)
- `tests/` - Test suite (unit, integration, e2e, contract, schema validation)

### 1.2 MCP Servers Inventory

**Total: 13 MCP servers across 6 domains**

#### Clinical & Biomedical (5 servers)
1. **biomcp-mcp** (`servers/clinical/biomcp-mcp/`)
   - **Tools**: ~35-40 tools
   - **Language**: Python
   - **Domain**: Comprehensive biomedical research (trials, variants, genes, drugs, OpenFDA)
   - **HTTP Client**: Custom async httpx client (not using `common.http`)
   - **Config**: ❌ Not using `ServerConfig` framework

2. **clinical-trials-mcp** (`servers/clinical/clinical-trials-mcp/`)
   - **Tools**: 2 tools
   - **Language**: Python
   - **Domain**: ClinicalTrials.gov search and retrieval
   - **HTTP Client**: Raw `requests` library
   - **Config**: ❌ Not using `ServerConfig` framework

3. **nhanes-mcp** (`servers/clinical/nhanes-mcp/`)
   - **Tools**: 5 tools
   - **Language**: Python
   - **Domain**: CDC NHANES health survey data
   - **HTTP Client**: Raw `requests` library (likely)
   - **Config**: ❌ Not using `ServerConfig` framework

4. **pubmed-mcp** (`servers/misc/pubmed-mcp/`)
   - **Tools**: 5 tools
   - **Language**: TypeScript/JavaScript
   - **Domain**: PubMed literature search
   - **HTTP Client**: Axios (TypeScript)
   - **Config**: ❌ Not using `ServerConfig` framework (TypeScript server)

5. **fda-mcp** (`servers/misc/fda-mcp/`)
   - **Tools**: 10 tools
   - **Language**: TypeScript/JavaScript
   - **Domain**: OpenFDA drug and device data
   - **HTTP Client**: Axios (TypeScript)
   - **Config**: ❌ Not using `ServerConfig` framework (TypeScript server)

#### Financial Markets (4 servers)
6. **biotech-markets-mcp** (`servers/markets/biotech-markets-mcp/`)
   - **Tools**: 8 tools (including 2 macro tools: `generate_biotech_company_dossier`, `refine_biotech_dossier`)
   - **Language**: Python
   - **Domain**: Biotech company analysis with SEC, trials, publications
   - **HTTP Client**: Raw `requests` (in clients: `pubmed_client.py`, `sec_edgar_client.py`, `clinical_trials_client.py`)
   - **Config**: ✅ Using `ServerConfig` framework

7. **sec-edgar-mcp** (`servers/markets/sec-edgar-mcp/`)
   - **Tools**: 6 tools
   - **Language**: Python
   - **Domain**: SEC EDGAR filings and company data
   - **HTTP Client**: Raw `requests` library
   - **Config**: ❌ Not using `ServerConfig` framework

8. **sp-global-mcp** (`servers/markets/sp-global-mcp/`)
   - **Tools**: 4 tools
   - **Language**: Python
   - **Domain**: S&P Global market intelligence
   - **HTTP Client**: Raw `requests` library
   - **Config**: ❌ Not using `ServerConfig` framework

9. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`)
   - **Tools**: 1 macro tool (`analyze_company_across_markets_and_clinical`)
   - **Language**: Python
   - **Domain**: Cross-domain orchestration (markets + clinical)
   - **HTTP Client**: MCP protocol calls (not direct HTTP)
   - **Config**: ✅ Using `ServerConfig` framework

#### Healthcare Operations (2 servers)
10. **hospital-prices-mcp** (`servers/pricing/hospital-prices-mcp/`)
    - **Tools**: 5 tools
    - **Language**: Python
    - **Domain**: Hospital price transparency via Turquoise Health
    - **HTTP Client**: ✅ Using `common.http` (via `turquoise_client.py`)
    - **Config**: ✅ Using `ServerConfig` framework

11. **claims-edi-mcp** (`servers/claims/claims-edi-mcp/`)
    - **Tools**: 7 tools (including 2 macro tools: `claims_summarize_claim_with_risks`, `claims_plan_claim_adjustments`)
    - **Language**: Python
    - **Domain**: EDI 837/835 parsing and CMS fee schedules
    - **HTTP Client**: No external HTTP (file parsing only)
    - **Config**: ✅ Using `ServerConfig` framework

#### Real Estate & Other (2 servers)
12. **real-estate-mcp** (`servers/real-estate/real-estate-mcp/`)
    - **Tools**: 5+ tools (including 1 macro tool: `generate_property_investment_brief`)
    - **Language**: Python + TypeScript (hybrid)
    - **Domain**: Property data via BatchData API
    - **HTTP Client**: Raw `requests` library
    - **Config**: ✅ Using `ServerConfig` framework

13. **playwright-mcp** (`servers/misc/playwright-mcp/`)
    - **Tools**: 10+ tools
    - **Language**: TypeScript/JavaScript
    - **Domain**: Browser automation (Microsoft)
    - **HTTP Client**: N/A (browser automation)
    - **Config**: ✅ Using `ServerConfig` framework

---

## 2. Robustness & Config Framework Adoption

### 2.1 Server-by-Server Summary Table

| Server | Config Framework | Fail-Fast/Fail-Soft | SERVICE_NOT_CONFIGURED | HTTP Client | Error Mapping | Observability |
|--------|-----------------|---------------------|------------------------|-------------|---------------|---------------|
| **biomcp-mcp** | ❌ No | N/A | ❌ No | Custom httpx | Custom | ✅ Yes (metrics, logging) |
| **clinical-trials-mcp** | ❌ No | N/A | ❌ No | Raw `requests` | ❌ No | ❌ No |
| **nhanes-mcp** | ❌ No | N/A | ❌ No | Raw `requests` | ❌ No | ❌ No |
| **pubmed-mcp** | ❌ No (TS) | N/A | ❌ No | Axios | ❌ No | ❌ No |
| **fda-mcp** | ❌ No (TS) | N/A | ❌ No | Axios | ❌ No | ❌ No |
| **biotech-markets-mcp** | ✅ Yes | Fail-soft (env var) | ⚠️ Partial | Raw `requests` | ⚠️ Partial | ⚠️ Partial |
| **sec-edgar-mcp** | ❌ No | N/A | ❌ No | Raw `requests` | ❌ No | ❌ No |
| **sp-global-mcp** | ❌ No | N/A | ❌ No | Raw `requests` | ❌ No | ❌ No |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | Fail-fast (default) | ✅ Yes | MCP protocol | ✅ Yes | ✅ Yes |
| **hospital-prices-mcp** | ✅ Yes | Fail-fast | ✅ Yes | ✅ `common.http` | ✅ Yes | ⚠️ Partial |
| **claims-edi-mcp** | ✅ Yes | N/A (no required config) | ⚠️ Partial | N/A | ✅ Yes | ✅ Yes |
| **real-estate-mcp** | ✅ Yes | Fail-fast | ⚠️ Partial | Raw `requests` | ⚠️ Partial | ⚠️ Partial |
| **playwright-mcp** | ✅ Yes | Fail-fast | ✅ Yes | N/A | ⚠️ Partial | ⚠️ Partial |

**Legend:**
- ✅ = Fully implemented
- ⚠️ = Partially implemented
- ❌ = Not implemented
- N/A = Not applicable

### 2.2 Config Framework Details

**Servers using `ServerConfig` framework (6/13):**
1. ✅ **biotech-markets-mcp** - `BiotechMarketsConfig` extends `ServerConfig`
2. ✅ **healthcare-equities-orchestrator-mcp** - `HealthcareEquitiesOrchestratorConfig` extends `ServerConfig`
3. ✅ **hospital-prices-mcp** - `HospitalPricesConfig` extends `ServerConfig`
4. ✅ **claims-edi-mcp** - `ClaimsEdiConfig` extends `ServerConfig`
5. ✅ **real-estate-mcp** - `RealEstateConfig` extends `ServerConfig`
6. ✅ **playwright-mcp** - `PlaywrightServerConfig` extends `ServerConfig`

**Servers NOT using `ServerConfig` framework (7/13):**
1. ❌ **biomcp-mcp** - Uses custom config pattern
2. ❌ **clinical-trials-mcp** - No config.py found
3. ❌ **nhanes-mcp** - No config.py found
4. ❌ **sec-edgar-mcp** - No config.py found
5. ❌ **sp-global-mcp** - No config.py found
6. ❌ **pubmed-mcp** - TypeScript server, different pattern
7. ❌ **fda-mcp** - TypeScript server, different pattern

**Fail-Fast vs Fail-Soft Behavior:**
- **Fail-fast (default)**: `hospital-prices-mcp`, `healthcare-equities-orchestrator-mcp`, `real-estate-mcp`, `playwright-mcp`
- **Fail-soft (configurable)**: `biotech-markets-mcp` (via `BIOTECH_MARKETS_FAIL_FAST` env var)
- **No required config**: `claims-edi-mcp` (all config optional)

**SERVICE_NOT_CONFIGURED Usage:**
- ✅ **hospital-prices-mcp**: Uses `ErrorCode.SERVICE_NOT_CONFIGURED` when `TURQUOISE_API_KEY` missing
- ✅ **healthcare-equities-orchestrator-mcp**: Uses `SERVICE_NOT_CONFIGURED` in fail-soft mode
- ✅ **playwright-mcp**: Uses `SERVICE_NOT_CONFIGURED` for missing config
- ⚠️ **biotech-markets-mcp**: Has config validation but doesn't explicitly use `SERVICE_NOT_CONFIGURED`
- ⚠️ **claims-edi-mcp**: Uses error handling but doesn't use `SERVICE_NOT_CONFIGURED` (all config optional)

### 2.3 HTTP Client Usage

**Servers using `common.http` (1/13):**
- ✅ **hospital-prices-mcp** - `turquoise_client.py` uses `common.http.get()` and `call_upstream()`

**Servers using raw `requests` (8/13):**
- ❌ **biotech-markets-mcp** - `pubmed_client.py`, `sec_edgar_client.py`, `clinical_trials_client.py` use raw `requests.get()`
- ❌ **sec-edgar-mcp** - `sec_edgar_client.py` uses raw `requests.get()`
- ❌ **sp-global-mcp** - `sp_global_client.py` uses raw `requests`
- ❌ **clinical-trials-mcp** - `clinical_trials_api.py` uses raw `requests.get()`
- ❌ **nhanes-mcp** - Likely uses raw `requests`
- ❌ **real-estate-mcp** - `batchdata_client.py`, `redfin_client.py`, `county_assessor_client.py`, `gis_client.py` use raw `requests`
- ❌ **claims-edi-mcp** - `cms_fee_schedules.py` uses raw `requests` (for CMS data downloads)

**Servers using custom HTTP clients:**
- ⚠️ **biomcp-mcp** - Custom async httpx client with connection pooling, circuit breakers, rate limiting (not using `common.http`)

**Servers using TypeScript HTTP:**
- ⚠️ **pubmed-mcp** - Uses Axios (TypeScript)
- ⚠️ **fda-mcp** - Uses Axios (TypeScript)

**Servers not using HTTP:**
- N/A **healthcare-equities-orchestrator-mcp** - Uses MCP protocol calls
- N/A **playwright-mcp** - Browser automation, no direct HTTP

### 2.4 Error Mapping

**Servers using `map_upstream_error` (3/13):**
- ✅ **hospital-prices-mcp** - Uses `map_upstream_error` in `turquoise_client.py`
- ✅ **claims-edi-mcp** - Uses `map_upstream_error` in tool implementations
- ⚠️ **biotech-markets-mcp** - Uses error handling but not consistently `map_upstream_error`

**Servers with custom error handling:**
- ⚠️ **biomcp-mcp** - Custom `RequestError` pattern
- ⚠️ **healthcare-equities-orchestrator-mcp** - Uses `ErrorCode` directly

**Servers with minimal error handling:**
- ❌ **clinical-trials-mcp** - Basic try/except, no structured errors
- ❌ **nhanes-mcp** - Basic try/except
- ❌ **sec-edgar-mcp** - Basic try/except
- ❌ **sp-global-mcp** - Basic try/except
- ❌ **pubmed-mcp** - TypeScript, basic error handling
- ❌ **fda-mcp** - TypeScript, basic error handling
- ❌ **real-estate-mcp** - Basic try/except

### 2.5 Observability

**Servers with standardized observability:**
- ✅ **biomcp-mcp** - Comprehensive metrics, logging, tracing
- ✅ **claims-edi-mcp** - Uses `observe_tool_call` decorator, `request_context`
- ⚠️ **hospital-prices-mcp** - Has error handling but limited observability hooks
- ⚠️ **healthcare-equities-orchestrator-mcp** - Uses `get_logger` but limited metrics

**Servers with minimal observability:**
- ❌ Most other servers have basic logging but no standardized observability

---

## 3. Actionable "Macro" Tools & Workflows

### 3.1 Existing Macro Tools

| Tool Name | Server | Description | Workflow Steps | IO Typing |
|-----------|--------|-------------|----------------|-----------|
| `generate_biotech_company_dossier` | `biotech-markets-mcp` | Comprehensive biotech company dossier | 1. Company identifier resolution (ticker/CIK/name)<br>2. Company profile aggregation<br>3. Pipeline drugs from ClinicalTrials.gov<br>4. SEC filings and investors<br>5. PubMed publications<br>6. Financial timeseries<br>7. Risk flag calculation<br>8. Artifact storage | ✅ Strong (uses schemas, structured output) |
| `refine_biotech_dossier` | `biotech-markets-mcp` | Refine existing dossier with new questions | 1. Load existing dossier (from artifact store or provided)<br>2. Extract insights by category<br>3. Answer new questions<br>4. Update dossier structure<br>5. Return refined dossier | ✅ Strong (structured input/output) |
| `analyze_company_across_markets_and_clinical` | `healthcare-equities-orchestrator-mcp` | Cross-domain company analysis | 1. Company identifier resolution (ticker/CIK/name)<br>2. Financial data (biotech-markets-mcp)<br>3. SEC filings (sec-edgar-mcp)<br>4. Clinical trials (clinical-trials-mcp)<br>5. Risk assessment<br>6. Cross-domain synthesis | ✅ Strong (uses shared identifier schemas) |
| `claims_summarize_claim_with_risks` | `claims-edi-mcp` | Generate claim summary with risk flags | 1. Parse EDI 837 (if needed)<br>2. Extract claim data<br>3. Analyze line items<br>4. Check for missing fields<br>5. Validate codes (CPT/HCPCS)<br>6. Generate risk flags<br>7. Build human-readable summary | ✅ Strong (structured output) |
| `claims_plan_claim_adjustments` | `claims-edi-mcp` | Generate adjustment plan (read-only) | 1. Parse EDI 837 (if needed)<br>2. Analyze line items<br>3. Check payer rules<br>4. Identify issues<br>5. Suggest code changes<br>6. Generate structured plan | ✅ Strong (structured output) |
| `generate_property_investment_brief` | `real-estate-mcp` | Property investment analysis | 1. Property lookup<br>2. Tax records<br>3. Recent sales<br>4. Market trends<br>5. Red flag calculation | ⚠️ Moderate (needs schema verification) |
| `biomcp.think` + research workflow | `biomcp-mcp` | Sequential thinking for biomedical research | 10-step process: scoping → search → collection → quality assessment → extraction → synthesis → analysis → knowledge synthesis → reporting | ✅ Strong (structured thought process) |

**Total Macro Tools: 7**

### 3.2 Missing Macro Tools (Prioritized)

**P0 (Must-Do):**
1. **Patient Out-of-Pocket Estimate Tool**
   - **Domain**: Pricing + Claims
   - **Workflow**: 1) Patient demographics, 2) Insurance plan lookup, 3) Procedure CPT code, 4) Hospital price lookup, 5) CMS fee schedule, 6) Deductible/coinsurance calculation, 7) Final estimate
   - **Why**: High-value use case combining pricing and claims data. `hospital_prices_estimate_patient_out_of_pocket` exists but could be enhanced with claims data.

2. **Clinical Trial Matching Tool**
   - **Domain**: Clinical
   - **Workflow**: 1) Patient condition/demographics, 2) Search trials, 3) Filter by eligibility, 4) Location matching, 5) Generate match report
   - **Why**: Actionable workflow vs. just "search trials"

**P1 (High Value):**
3. **Claim Risk Flagging Tool** (partially exists as `claims_summarize_claim_with_risks`)
   - **Domain**: Claims
   - **Workflow**: 1) Parse EDI 837, 2) Extract procedure codes, 3) Compare to CMS fee schedules, 4) Flag anomalies, 5) Generate risk report
   - **Why**: Adds value beyond just parsing (already partially implemented)

4. **Drug Pipeline Competitive Analysis**
   - **Domain**: Markets + Clinical
   - **Workflow**: 1) Target disease/indication, 2) Find all companies in space, 3) Aggregate pipeline stages, 4) Compare timelines, 5) Generate competitive landscape
   - **Why**: Combines multiple data sources for actionable insight

**P2 (Nice-to-Have):**
5. **Property Investment Portfolio Analysis**
   - **Domain**: Real Estate
   - **Workflow**: 1) List of addresses, 2) Generate briefs for each, 3) Aggregate metrics, 4) Risk assessment, 5) Portfolio summary
   - **Why**: Batch processing of existing investment brief tool

6. **Biomedical Literature Review Generator**
   - **Domain**: Clinical
   - **Workflow**: 1) Research question, 2) PubMed search, 3) Quality filtering, 4) Evidence extraction, 5) Synthesis, 6) Report generation
   - **Why**: Could leverage `biomcp.think` workflow

### 3.3 Domains Still Mostly Read-Only

**Domains that are still mostly primitive (search/list/get):**
1. **Clinical Trials** - Only search and get detail (no matching, no eligibility checking)
2. **NHANES** - Only data querying (no analysis workflows)
3. **SEC EDGAR** - Only filing retrieval (no financial analysis workflows)
4. **S&P Global** - Only company/profile retrieval (no analysis workflows)

**Suggested macro tools for these domains:**
- **Clinical Trials**: Patient-trial matching tool (P0)
- **NHANES**: Population health analysis tool (P2)
- **SEC EDGAR**: Financial trend analysis tool (P1)
- **S&P Global**: Market intelligence brief generator (P1)

---

## 4. Cross-MCP Orchestration & Shared Identifiers

### 4.1 Orchestrator MCPs

**Identified Orchestrators:**
1. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`)
   - **Calls**: `biotech-markets-mcp`, `sec-edgar-mcp`, `clinical-trials-mcp`
   - **Workflows**: Cross-domain company analysis (markets + clinical)
   - **Tool**: `analyze_company_across_markets_and_clinical`
   - **Status**: ✅ Implemented, uses shared identifier schemas

2. **biotech-markets-mcp** (partial orchestration)
   - **Calls**: ClinicalTrials.gov API, SEC EDGAR API, PubMed API (direct, not via MCP)
   - **Workflows**: Company dossier generation, pipeline aggregation
   - **Status**: ✅ Implemented, but uses direct API calls (not MCP protocol)

### 4.2 Shared Identifier Schemas

**Identified in `schemas/`:**
1. **Ticker Identifier** (`schemas/ticker_identifier.json`)
   - Pattern: `^[A-Z0-9.-]+$`
   - Used in: `biotech-markets-mcp`, `healthcare-equities-orchestrator-mcp`, `sec-edgar-mcp`

2. **SEC CIK** (`schemas/sec_identifier.json`)
   - Pattern: `^\\d{10}$` (10-digit zero-padded)
   - Used in: `biotech-markets-mcp`, `healthcare-equities-orchestrator-mcp`, `sec-edgar-mcp`

3. **Clinical Trial Identifier** (`schemas/clinical_trial_identifier.json`)
   - Pattern: `^NCT[0-9]{8}$`
   - Used in: `clinical-trials-mcp`, `biomcp-mcp`

**Shared Identifier Usage:**
- ✅ **biotech-markets-mcp**: Uses ticker/CIK in `generate_biotech_company_dossier`
- ✅ **healthcare-equities-orchestrator-mcp**: Uses ticker/CIK/company_name in `analyze_company_across_markets_and_clinical`
- ✅ **sec-edgar-mcp**: Uses CIK for company lookups
- ⚠️ **biomcp-mcp**: Uses NCT ID but may have custom normalization

**Gaps in Shared Identifier Normalization:**
- ❌ **NPI (National Provider Identifier)**: No shared schema found (used in claims-edi-mcp)
- ❌ **CPT/HCPCS codes**: No shared schema found (used in claims-edi-mcp, hospital-prices-mcp)
- ❌ **Address normalization**: No shared schema/utility found (used across multiple servers)
- ⚠️ **Drug identifiers**: No shared schema found (used in biomcp-mcp, fda-mcp)

**Local Normalization Functions (not shared):**
- `biotech-markets-mcp/company_aggregator.py`: `_normalize_company_name()`
- `sec-edgar-mcp/sec_edgar_client.py`: CIK zero-padding logic
- `claims-edi-mcp/edi_parser.py`: CPT/HCPCS code extraction

**Recommendation**: Create shared identifier normalization utilities in `common/identifiers.py`:
- `normalize_ticker(ticker: str) -> str`
- `normalize_cik(cik: str) -> str`
- `normalize_nct_id(nct_id: str) -> str`
- `normalize_cpt_code(cpt_code: str) -> str`
- `normalize_npi(npi: str) -> str`

---

## 5. Caching & Artifacts

### 5.1 Shared Caching Infrastructure

**`common/cache.py` provides:**
- `Cache` class: In-memory cache with TTL support
- `get_cache()`: Global singleton cache instance
- `build_cache_key()`: Standardized cache key generation

**Servers using `common.cache`:**
- ✅ **biotech-markets-mcp**: Uses `get_cache()` and `build_cache_key()` for timeseries data
- ✅ **sec-edgar-mcp** (via biotech-markets-mcp): Uses `common.cache` in `sec_edgar_client.py`
- ⚠️ **hospital-prices-mcp**: Uses local `cache.py` (not `common.cache`)
- ⚠️ **real-estate-mcp**: Uses local `cache.py` (not `common.cache`)

**Servers with custom caching:**
- ⚠️ **biomcp-mcp**: Custom caching with request/response caching
- ⚠️ **hospital-prices-mcp**: Local `Cache` class (similar to `common.cache`)
- ⚠️ **real-estate-mcp**: Local `Cache` class

**Servers without caching:**
- ❌ **clinical-trials-mcp**: No caching found
- ❌ **nhanes-mcp**: No caching found
- ❌ **sec-edgar-mcp**: No caching (but used via biotech-markets-mcp)
- ❌ **sp-global-mcp**: No caching found

### 5.2 Artifact Storage

**Servers with artifact storage:**
- ✅ **biotech-markets-mcp**: `artifact_store.py` for storing dossiers
  - Stores generated dossiers with unique IDs
  - Supports retrieval by ID
  - Used by `generate_biotech_company_dossier` and `refine_biotech_dossier`

**Servers without artifact storage:**
- ❌ Most other servers don't store intermediate artifacts

### 5.3 Caching Analysis

**Expensive operations that ARE cached:**
- ✅ **biotech-markets-mcp**: Timeseries data (7 days for historical, 1 hour for recent)
- ✅ **biotech-markets-mcp**: CIK lookups (24 hours)
- ✅ **hospital-prices-mcp**: Procedure price searches (via local cache)
- ✅ **biomcp-mcp**: API responses (configurable TTL)

**Expensive operations that are NOT cached (but should be):**
- ❌ **clinical-trials-mcp**: Trial searches (no caching)
- ❌ **sec-edgar-mcp**: Company lookups (no caching, but used via biotech-markets-mcp which caches)
- ❌ **nhanes-mcp**: Dataset queries (no caching)
- ❌ **sp-global-mcp**: Company profiles (no caching)

**Recommendation**: Migrate all servers to use `common.cache` for consistency and centralized cache management.

---

## 6. Tests & CI Coverage

### 6.1 Test Structure

**Test directories:**
- `tests/unit/` - Unit tests per server
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end MCP protocol tests
- `tests/contract/` - API contract tests
- `tests/schema/` - Schema validation tests
- `servers/*/tests/` - Server-specific tests

### 6.2 Server-by-Server Test Coverage

| Server | Unit Tests | Integration Tests | E2E Tests | Notes |
|--------|------------|-------------------|-----------|-------|
| **biomcp-mcp** | ✅ Yes (extensive) | ✅ Yes | ⚠️ Partial | 50+ test files in `tests/tdd/` |
| **biotech-markets-mcp** | ⚠️ Partial | ❌ No | ❌ No | Only `test_timeseries.py` found |
| **clinical-trials-mcp** | ✅ Yes | ❌ No | ✅ Yes | `test_e2e_clinical_trials.py` |
| **nhanes-mcp** | ✅ Yes | ❌ No | ❌ No | `test_nhanes.py` |
| **sec-edgar-mcp** | ❌ No | ❌ No | ❌ No | No tests found |
| **sp-global-mcp** | ❌ No | ❌ No | ❌ No | No tests found |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | ❌ No | ❌ No | `test_orchestrator.py` |
| **hospital-prices-mcp** | ✅ Yes | ❌ No | ❌ No | `test_hospital_pricing.py` |
| **claims-edi-mcp** | ✅ Yes | ❌ No | ❌ No | `test_claims_edi.py` |
| **real-estate-mcp** | ✅ Yes | ❌ No | ❌ No | `test_real_estate.py` |
| **playwright-mcp** | ✅ Yes | ❌ No | ❌ No | TypeScript tests |
| **pubmed-mcp** | ❌ No | ❌ No | ❌ No | TypeScript server, no tests found |
| **fda-mcp** | ❌ No | ❌ No | ❌ No | TypeScript server, no tests found |

### 6.3 Test Gaps

**Missing Tests:**
1. **Macro tools without tests:**
   - ❌ `generate_biotech_company_dossier` - No dedicated test
   - ❌ `refine_biotech_dossier` - No dedicated test
   - ❌ `analyze_company_across_markets_and_clinical` - No E2E test
   - ❌ `claims_summarize_claim_with_risks` - No dedicated test
   - ❌ `claims_plan_claim_adjustments` - No dedicated test

2. **Orchestrator workflows without E2E tests:**
   - ❌ `healthcare-equities-orchestrator-mcp` - No E2E test for cross-MCP calls

3. **Missing negative/edge case tests:**
   - ❌ Config missing scenarios
   - ❌ Upstream API failure scenarios
   - ❌ Invalid identifier formats
   - ❌ Rate limiting scenarios

4. **Servers with no tests:**
   - ❌ `sec-edgar-mcp` - No tests found
   - ❌ `sp-global-mcp` - No tests found
   - ❌ `pubmed-mcp` - No tests found
   - ❌ `fda-mcp` - No tests found

### 6.4 CI/CD Coverage

**GitHub Actions workflows:**
- ✅ `.github/workflows/validate.yml` - Registry validation, schema validation
- ✅ `.github/workflows/release.yml` - Release automation

**Test execution in CI:**
- ⚠️ Validation workflow runs schema/registry checks
- ⚠️ Unclear if unit/integration tests run in CI

**Recommendation**: Ensure all test suites run in CI, especially for macro tools and orchestrators.

---

## 7. QC Scorecard

| Category | Status | Justification |
|----------|--------|---------------|
| **Config & fail-soft/fail-fast adoption** | 🟡 Yellow | 6/13 servers use `ServerConfig`. 7 servers need migration. Fail-fast/fail-soft behavior is inconsistent. |
| **Standardized HTTP + error handling** | 🟡 Yellow | Only 1 server (`hospital-prices-mcp`) uses `common.http`. Most use raw `requests`. Error mapping is inconsistent. |
| **Actionable workflow tools** | 🟢 Green | 7 macro tools exist, including strong dossier generation and orchestration. Some domains still need macro tools. |
| **Cross-MCP orchestration & shared identifiers** | 🟢 Green | Orchestrator exists (`healthcare-equities-orchestrator-mcp`). Shared identifier schemas exist (ticker, CIK, NCT ID). |
| **Caching & artifact handling** | 🟡 Yellow | `common.cache` exists but not widely adopted. Some servers use local caching. Artifact storage only in biotech-markets-mcp. |
| **Tests & CI around MCPs** | 🟡 Yellow | Good coverage for biomcp-mcp, but many servers lack tests. Macro tools and orchestrators lack E2E tests. |
| **PHI & sensitive data handling** | 🟢 Green | `common.phi` module exists. `claims-edi-mcp` uses PHI redaction. Observability includes PHI handling. |
| **TypeScript/JS server alignment** | 🟡 Yellow | TypeScript servers (pubmed-mcp, fda-mcp, playwright-mcp) don't use Python config framework. Alignment needed. |

**Overall Health: 🟡 Yellow (Good progress, but gaps remain)**

---

## 8. "What's Next" Roadmap

### P0 (Must-Do / Highest Risk or Leverage)

1. **Migrate remaining servers to config framework**
   - **Servers**: biomcp-mcp, clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp
   - **Why**: Consistency, fail-fast/fail-soft behavior, SERVICE_NOT_CONFIGURED support
   - **Impact**: Reduces configuration errors, improves startup reliability

2. **Migrate HTTP clients to `common.http`**
   - **Servers**: biotech-markets-mcp, sec-edgar-mcp, sp-global-mcp, clinical-trials-mcp, nhanes-mcp, real-estate-mcp
   - **Why**: Standardized timeouts, retries, circuit breakers, error handling
   - **Impact**: Reduces upstream failures, improves resilience

3. **Add E2E tests for orchestrator workflows**
   - **Focus**: `healthcare-equities-orchestrator-mcp.analyze_company_across_markets_and_clinical`
   - **Why**: Orchestrators are high-risk (multiple dependencies)
   - **Impact**: Catches integration issues early

4. **Create shared identifier normalization utilities**
   - **Location**: `common/identifiers.py`
   - **Functions**: `normalize_ticker()`, `normalize_cik()`, `normalize_nct_id()`, `normalize_cpt_code()`, `normalize_npi()`
   - **Why**: Prevents identifier mismatches in orchestration
   - **Impact**: Reduces cross-MCP integration bugs

5. **Add tests for macro tools**
   - **Focus**: `generate_biotech_company_dossier`, `refine_biotech_dossier`, `claims_summarize_claim_with_risks`
   - **Why**: Macro tools are high-value and complex
   - **Impact**: Ensures reliability of key workflows

### P1 (High Value)

6. **Migrate all servers to `common.cache`**
   - **Servers**: hospital-prices-mcp, real-estate-mcp, clinical-trials-mcp, nhanes-mcp, sp-global-mcp
   - **Why**: Consistency, centralized cache management
   - **Impact**: Better cache hit rates, easier cache debugging

7. **Implement Patient Out-of-Pocket Estimate macro tool**
   - **Domain**: Pricing + Claims
   - **Why**: High-value use case combining multiple domains
   - **Impact**: Actionable workflow for end users

8. **Implement Clinical Trial Matching tool**
   - **Domain**: Clinical
   - **Why**: Actionable workflow vs. just search
   - **Impact**: Better user experience for clinical trial discovery

9. **Add comprehensive error mapping**
   - **Servers**: All servers using raw `requests`
   - **Why**: Consistent error codes across servers
   - **Impact**: Better LLM error handling

10. **Add tests for servers without coverage**
    - **Servers**: sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp
    - **Why**: Prevents regressions
    - **Impact**: Higher confidence in deployments

### P2 (Nice-to-Have)

11. **Create shared address normalization utility**
    - **Location**: `common/identifiers.py`
    - **Why**: Addresses used across multiple servers (real-estate, hospital-prices)
    - **Impact**: Better location-based matching

12. **Implement Drug Pipeline Competitive Analysis macro tool**
    - **Domain**: Markets + Clinical
    - **Why**: Combines multiple data sources for actionable insight
    - **Impact**: Valuable for market research

13. **Add artifact storage to more servers**
    - **Servers**: healthcare-equities-orchestrator-mcp, claims-edi-mcp
    - **Why**: Store intermediate results for refinement
    - **Impact**: Better user experience for complex workflows

14. **Align TypeScript servers with Python patterns**
    - **Servers**: pubmed-mcp, fda-mcp
    - **Why**: Consistency across language boundaries
    - **Impact**: Easier maintenance, better developer experience

---

## 9. Risks & Gotchas

### 9.1 Configuration Risks

- **Inconsistent fail-fast behavior**: Some servers fail-fast, others fail-soft, making deployment behavior unpredictable
- **Missing SERVICE_NOT_CONFIGURED**: Servers without config framework may not surface configuration errors clearly
- **TypeScript servers**: Don't use Python config framework, need separate alignment strategy

### 9.2 HTTP Client Risks

- **No circuit breakers**: Servers using raw `requests` don't have circuit breaker protection
- **Inconsistent timeouts**: Different timeout values across servers (10s, 30s, etc.)
- **No retry logic**: Most servers don't retry on transient failures
- **biomcp-mcp custom client**: Uses custom httpx client, not aligned with `common.http` patterns

### 9.3 Orchestration Risks

- **Identifier mismatches**: Different normalization logic across servers could cause orchestration failures
- **No E2E tests**: Orchestrator workflows not tested end-to-end
- **Partial failures**: Orchestrators may not handle partial upstream failures gracefully

### 9.4 Testing Risks

- **Macro tools untested**: High-value macro tools lack dedicated tests
- **Missing negative tests**: Edge cases (config missing, upstream failures) not tested
- **No integration tests**: Cross-MCP calls not tested in integration environment

### 9.5 Caching Risks

- **Inconsistent caching**: Some servers use `common.cache`, others use local caching
- **Cache key collisions**: Different cache key formats could cause collisions
- **No cache invalidation strategy**: No clear strategy for cache invalidation across servers

---

## 10. Conclusion

The repository has made **significant progress** in adopting standardized patterns, with **6 of 13 servers** now using the config framework and **strong macro tools** in place. However, **7 servers still need migration** to the config framework, and **most servers still use raw HTTP** instead of the shared client.

**Priority actions:**
1. Migrate remaining servers to config framework (P0)
2. Migrate HTTP clients to `common.http` (P0)
3. Add E2E tests for orchestrators (P0)
4. Create shared identifier normalization (P0)
5. Add tests for macro tools (P0)

**Overall Assessment**: 🟡 **Yellow** - Good foundation, but gaps remain that should be addressed before scaling further.

---

**Report Generated**: December 2024  
**Next Review**: After P0 items completed

