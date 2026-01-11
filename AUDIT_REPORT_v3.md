# Innovation Center MCP Zoo - Audit Report v3

**Date**: December 2024  
**Auditor**: Senior Architect & Codebase Auditor  
**Scope**: Read-only QC pass after robustness + macro-tool work, comparing to previous audits  
**Mode**: READ-ONLY inspection (no modifications)

---

## Executive Summary

This audit compares the current state to `AUDIT_REPORT_v2.md` (December 2024) and `AUDIT_REPORT.md` (earlier baseline). **No significant changes** have been detected since v2 - the repository state appears stable. The audit confirms the findings from v2 and adds deeper analysis of PHI handling, propose-vs-execute patterns, and CI/CD coverage.

**Key Findings:**
- **6 of 13 servers** use `ServerConfig` framework (unchanged from v2)
- **1 of 13 servers** uses `common.http` client (unchanged from v2)
- **PHI redaction** is properly implemented in `common/phi.py` and integrated into logging
- **Idempotency and dry-run** patterns exist in `playwright-mcp` but not widely adopted
- **CI/CD** runs registry validation, schema validation, and test suites

**Status**: 🟡 **Yellow** - Good foundation, but migration work (P0 items from v2) remains incomplete.

---

## 1. Global Scan & Baseline

### 1.1 Current Repository Structure

**Top-level directories:**
- `common/` - Shared utilities (config, errors, HTTP, cache, validation, observability, PHI handling)
- `servers/` - MCP server implementations organized by domain
- `scripts/` - Helper scripts including `create_mcp_server.py` and templates
- `docs/` - Architecture and configuration documentation
- `schemas/` - JSON schemas for tool inputs/outputs (100+ files)
- `registry/` - Centralized tool registry (`tools_registry.json`, `domains_taxonomy.json`)
- `tests/` - Test suite (unit, integration, e2e, contract, schema validation)
- `.github/workflows/` - CI/CD workflows (validate.yml, release.yml)

**MCP Servers (13 total across 6 domains):**

1. **biomcp-mcp** (`servers/clinical/biomcp-mcp/`) - ~35-40 tools
2. **clinical-trials-mcp** (`servers/clinical/clinical-trials-mcp/`) - 2 tools
3. **nhanes-mcp** (`servers/clinical/nhanes-mcp/`) - 5 tools
4. **pubmed-mcp** (`servers/misc/pubmed-mcp/`) - 5 tools (TypeScript)
5. **fda-mcp** (`servers/misc/fda-mcp/`) - 10 tools (TypeScript)
6. **biotech-markets-mcp** (`servers/markets/biotech-markets-mcp/`) - 8 tools
7. **sec-edgar-mcp** (`servers/markets/sec-edgar-mcp/`) - 6 tools
8. **sp-global-mcp** (`servers/markets/sp-global-mcp/`) - 4 tools
9. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`) - 1 tool
10. **hospital-prices-mcp** (`servers/pricing/hospital-prices-mcp/`) - 5 tools
11. **claims-edi-mcp** (`servers/claims/claims-edi-mcp/`) - 7 tools
12. **real-estate-mcp** (`servers/real-estate/real-estate-mcp/`) - 5+ tools
13. **playwright-mcp** (`servers/misc/playwright-mcp/`) - 10+ tools

### 1.2 Previous Audit Summaries

**AUDIT_REPORT.md (Baseline - December 2025):**
- Identified 13 servers across 5 domains
- Noted that only 6 servers were using new config template
- Highlighted missing macro tools in some domains
- Recommended migration to config framework for remaining servers

**AUDIT_REPORT_v2.md (December 2024 - Most Recent):**
- **Main conclusions:**
  - 6/13 servers use `ServerConfig` framework
  - Only 1 server (`hospital-prices-mcp`) uses `common.http`
  - 7 macro tools exist (dossier generation, claim analysis, orchestration)
  - Strong cross-MCP orchestration via `healthcare-equities-orchestrator-mcp`
  - Shared identifier schemas exist (ticker, CIK, NCT ID)
  - Good test coverage for `biomcp-mcp`, gaps elsewhere
  - PHI handling implemented in `common/phi.py`
  
- **P0 items listed:**
  1. Migrate remaining servers to config framework (7 servers)
  2. Migrate HTTP clients to `common.http` (8 servers)
  3. Add E2E tests for orchestrator workflows
  4. Create shared identifier normalization utilities
  5. Add tests for macro tools

- **P1 items listed:**
  6. Migrate all servers to `common.cache`
  7. Implement Patient Out-of-Pocket Estimate macro tool
  8. Implement Clinical Trial Matching tool
  9. Add comprehensive error mapping
  10. Add tests for servers without coverage

**Delta from v2 to v3:**
- **No changes detected** - Repository state appears unchanged since v2 audit
- All P0/P1 items from v2 remain open
- This audit adds deeper analysis of PHI handling, propose-vs-execute patterns, and CI/CD

---

## 2. Robustness & Config Framework Adoption

### 2.1 Server-by-Server Config Framework Status

| Server | Uses `ServerConfig`? | Fail-Fast/Fail-Soft | Uses `SERVICE_NOT_CONFIGURED`? | Config File Path |
|--------|---------------------|---------------------|-------------------------------|------------------|
| **biomcp-mcp** | ❌ No | N/A | ❌ No | N/A (custom config) |
| **clinical-trials-mcp** | ❌ No | N/A | ❌ No | N/A |
| **nhanes-mcp** | ❌ No | N/A | ❌ No | N/A |
| **pubmed-mcp** | ❌ No (TS) | N/A | ❌ No | N/A (TypeScript) |
| **fda-mcp** | ❌ No (TS) | N/A | ❌ No | N/A (TypeScript) |
| **biotech-markets-mcp** | ✅ Yes | Fail-soft (env var) | ⚠️ Partial | `config.py` |
| **sec-edgar-mcp** | ❌ No | N/A | ❌ No | N/A |
| **sp-global-mcp** | ❌ No | N/A | ❌ No | N/A |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | Fail-fast (default) | ✅ Yes | `config.py` |
| **hospital-prices-mcp** | ✅ Yes | Fail-fast | ✅ Yes | `config.py` |
| **claims-edi-mcp** | ✅ Yes | N/A (all optional) | ⚠️ Partial | `config.py` |
| **real-estate-mcp** | ✅ Yes | Fail-fast | ⚠️ Partial | `config.py` |
| **playwright-mcp** | ✅ Yes | Fail-fast | ✅ Yes | `config.py` |

**Summary:**
- **6/13 servers** (46%) use `ServerConfig` framework
- **7/13 servers** (54%) still need migration
- **Fail-fast by default**: 4 servers (healthcare-equities-orchestrator-mcp, hospital-prices-mcp, real-estate-mcp, playwright-mcp)
- **Fail-soft configurable**: 1 server (biotech-markets-mcp via `BIOTECH_MARKETS_FAIL_FAST` env var)
- **SERVICE_NOT_CONFIGURED usage**: 3 servers explicitly use it (healthcare-equities-orchestrator-mcp, hospital-prices-mcp, playwright-mcp)

### 2.2 Config Framework Implementation Details

**Servers with `ServerConfig` (6):**

1. **biotech-markets-mcp** (`servers/markets/biotech-markets-mcp/config.py`)
   - `BiotechMarketsConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-soft behavior (configurable via env var)
   - All config optional (SEC_USER_AGENT, CACHE_TTL_HOURS)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

2. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/config.py`)
   - `HealthcareEquitiesOrchestratorConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast default
   - All config optional (upstream MCP URLs)
   - Uses `SERVICE_NOT_CONFIGURED` in fail-soft mode

3. **hospital-prices-mcp** (`servers/pricing/hospital-prices-mcp/config.py`)
   - `HospitalPricesConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - `TURQUOISE_API_KEY` is **required** (critical=True)
   - Uses `SERVICE_NOT_CONFIGURED` when API key missing

4. **claims-edi-mcp** (`servers/claims/claims-edi-mcp/config.py`)
   - `ClaimsEdiConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` (but all config optional)
   - Has `enable_phi_redaction` flag (defaults to True)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

5. **real-estate-mcp** (`servers/real-estate/real-estate-mcp/config.py`)
   - `RealEstateConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - `BATCHDATA_API_KEY` is required
   - Does NOT explicitly use `SERVICE_NOT_CONFIGURED` (but should)

6. **playwright-mcp** (`servers/misc/playwright-mcp/config.py`)
   - `PlaywrightServerConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - Has `default_dry_run` flag (defaults to True)
   - Uses `SERVICE_NOT_CONFIGURED` for missing config

**Servers needing migration (7):**

1. **biomcp-mcp** - Uses custom config pattern (likely env vars directly)
2. **clinical-trials-mcp** - No config.py found
3. **nhanes-mcp** - No config.py found
4. **sec-edgar-mcp** - No config.py found
5. **sp-global-mcp** - No config.py found
6. **pubmed-mcp** - TypeScript server, different pattern
7. **fda-mcp** - TypeScript server, different pattern

**Migration Recommendation:**
- Create `config.py` files for Python servers following the template in `scripts/templates/mcp-server-template/config.py`
- For TypeScript servers, document alignment strategy or create TypeScript equivalent

---

## 3. HTTP Client, Error Handling, PHI, Caching

### 3.1 HTTP Client Usage

| Server | HTTP Client Pattern | Retries? | Circuit Breaker? | Uses Shared Error Mapping? | Notes |
|--------|-------------------|----------|-----------------|---------------------------|-------|
| **biomcp-mcp** | Custom async httpx | ✅ Yes | ✅ Yes | ⚠️ Custom | Custom client with connection pooling |
| **clinical-trials-mcp** | Raw `requests` | ❌ No | ❌ No | ❌ No | `clinical_trials_api.py` uses `requests.get()` |
| **nhanes-mcp** | Raw `requests` (likely) | ❌ No | ❌ No | ❌ No | No HTTP client code reviewed |
| **pubmed-mcp** | Axios (TypeScript) | ⚠️ Partial | ❌ No | ❌ No | TypeScript server |
| **fda-mcp** | Axios (TypeScript) | ⚠️ Partial | ❌ No | ❌ No | TypeScript server |
| **biotech-markets-mcp** | Raw `requests` | ❌ No | ❌ No | ⚠️ Partial | `pubmed_client.py`, `sec_edgar_client.py`, `clinical_trials_client.py` |
| **sec-edgar-mcp** | Raw `requests` | ❌ No | ❌ No | ❌ No | `sec_edgar_client.py` uses `requests.get()` |
| **sp-global-mcp** | Raw `requests` | ❌ No | ❌ No | ❌ No | `sp_global_client.py` uses `requests` |
| **healthcare-equities-orchestrator-mcp** | MCP protocol | N/A | N/A | ✅ Yes | Calls other MCPs, not direct HTTP |
| **hospital-prices-mcp** | ✅ `common.http` | ✅ Yes | ✅ Yes | ✅ Yes | `turquoise_client.py` uses `common.http.get()` |
| **claims-edi-mcp** | N/A (file parsing) | N/A | N/A | ✅ Yes | No external HTTP |
| **real-estate-mcp** | Raw `requests` | ❌ No | ❌ No | ⚠️ Partial | `batchdata_client.py`, `redfin_client.py`, etc. |
| **playwright-mcp** | N/A (browser) | N/A | N/A | ⚠️ Partial | Browser automation, no direct HTTP |

**Summary:**
- **1/13 servers** (8%) use `common.http` client
- **8/13 servers** (62%) use raw `requests` library
- **2/13 servers** (15%) use TypeScript HTTP (Axios)
- **1/13 servers** (8%) use custom httpx client (biomcp-mcp)
- **1/13 servers** (8%) use MCP protocol (orchestrator)

**Servers that should migrate to `common.http`:**
1. biotech-markets-mcp (pubmed_client.py, sec_edgar_client.py, clinical_trials_client.py)
2. sec-edgar-mcp (sec_edgar_client.py)
3. sp-global-mcp (sp_global_client.py)
4. clinical-trials-mcp (clinical_trials_api.py)
5. nhanes-mcp (if it uses HTTP)
6. real-estate-mcp (batchdata_client.py, redfin_client.py, county_assessor_client.py, gis_client.py)

**Note on biomcp-mcp**: Uses custom async httpx client with connection pooling, circuit breakers, and rate limiting. Consider whether to migrate to `common.http` or document as acceptable alternative pattern.

### 3.2 Error Handling

**Servers using `map_upstream_error` (3/13):**
- ✅ **hospital-prices-mcp** - Uses `map_upstream_error` in `turquoise_client.py`
- ✅ **claims-edi-mcp** - Uses `map_upstream_error` in tool implementations
- ⚠️ **biotech-markets-mcp** - Uses error handling but not consistently `map_upstream_error`

**Servers with custom error handling:**
- ⚠️ **biomcp-mcp** - Custom `RequestError` pattern
- ⚠️ **healthcare-equities-orchestrator-mcp** - Uses `ErrorCode` directly

**Servers with minimal error handling:**
- ❌ Most other servers have basic try/except with string error messages

### 3.3 PHI & Sensitive Data Handling

**PHI Redaction Implementation:**

✅ **`common/phi.py`** provides:
- `redact_phi(payload)` - Recursively redacts PHI from data structures
- `is_phi_field(field_name)` - Checks if field name matches PHI patterns
- `mark_ephemeral(data, reason)` - Marks data as ephemeral (should not persist)
- `is_ephemeral(data)` - Checks if data is marked as ephemeral

**PHI Field Patterns Detected:**
- Names, SSN, DOB, addresses, phone, email
- Member IDs, medical record numbers
- Diagnosis codes, procedure codes (CPT/HCPCS)

**PHI Value Patterns Detected:**
- SSN: `XXX-XX-XXXX` format
- Phone: `XXX-XXX-XXXX` format
- Email: Standard email format
- ZIP codes: 5 or 9 digit postal codes

**Integration with Logging:**

✅ **`common/logging.py`** automatically applies PHI redaction:
- `log_request()` - Redacts PHI from input parameters (line 175: `extra["input_params"] = redact_phi(sanitized)`)
- `log_response()` - Redacts PHI from response data
- `log_error()` - Redacts PHI from error context
- `request_context()` - Redacts PHI before logging (line 348: `sanitized_params = redact_phi(sanitized_params)`)

**PHI Redaction Usage in Servers:**

✅ **claims-edi-mcp**:
- Imports `redact_phi` and `is_ephemeral` from `common.phi` (line 44)
- Uses `request_context()` which applies PHI redaction automatically
- `edi_parser.py` uses `mark_ephemeral()` to mark parsed EDI data as ephemeral (lines 119, 186)
- Has config flag `enable_phi_redaction` (defaults to True) in `config.py` (line 96)

**Config Flags for PHI Behavior:**

✅ **claims-edi-mcp** has `enable_phi_redaction` config flag:
- Environment variable: `ENABLE_PHI_REDACTION` (defaults to "true")
- Location: `servers/claims/claims-edi-mcp/config.py` line 96
- Default: `True` (PHI redaction enabled by default)

**Risky Patterns Identified:**

⚠️ **Potential risks:**
- Some servers may log raw EDI segments before parsing (need to verify)
- TypeScript servers (pubmed-mcp, fda-mcp) may not have PHI redaction
- `biomcp-mcp` uses custom logging - need to verify PHI redaction integration

**Recommendation:**
- Verify all servers that handle PHI use `common.logging` functions or manually call `redact_phi()` before logging
- Add PHI redaction to TypeScript servers if they handle PHI
- Document PHI handling requirements in `common/SECURITY.md` (already exists)

### 3.4 Caching & Artifacts

**Shared Caching Infrastructure:**

✅ **`common/cache.py`** provides:
- `Cache` class: In-memory cache with TTL support
- `get_cache()`: Global singleton cache instance
- `build_cache_key()`: Standardized cache key generation

**Servers using `common.cache`:**
- ✅ **biotech-markets-mcp**: Uses `get_cache()` and `build_cache_key()` for timeseries data
- ✅ **sec-edgar-mcp** (via biotech-markets-mcp): Uses `common.cache` in `sec_edgar_client.py`

**Servers with custom caching:**
- ⚠️ **biomcp-mcp**: Custom caching with request/response caching
- ⚠️ **hospital-prices-mcp**: Local `Cache` class (similar to `common.cache`)
- ⚠️ **real-estate-mcp**: Local `Cache` class

**Servers without caching:**
- ❌ **clinical-trials-mcp**: No caching found
- ❌ **nhanes-mcp**: No caching found
- ❌ **sp-global-mcp**: No caching found

**Artifact Storage:**

✅ **biotech-markets-mcp** has `artifact_store.py`:
- Stores generated dossiers with unique IDs
- Supports retrieval by ID
- Used by `generate_biotech_company_dossier` and `refine_biotech_dossier`

**Expensive Operations Cached:**
- ✅ **biotech-markets-mcp**: Timeseries data (7 days for historical, 1 hour for recent)
- ✅ **biotech-markets-mcp**: CIK lookups (24 hours)
- ✅ **hospital-prices-mcp**: Procedure price searches (via local cache)
- ✅ **biomcp-mcp**: API responses (configurable TTL)

**Expensive Operations NOT Cached (but should be):**
- ❌ **clinical-trials-mcp**: Trial searches (no caching)
- ❌ **nhanes-mcp**: Dataset queries (no caching)
- ❌ **sp-global-mcp**: Company profiles (no caching)

---

## 4. Macro Tools & "Actionable Work"

### 4.1 Existing Macro Tools

| Tool Name | Server | Workflow Steps | IO Typing | Status |
|-----------|--------|---------------|-----------|--------|
| `generate_biotech_company_dossier` | `biotech-markets-mcp` | 1. Company identifier resolution<br>2. Company profile aggregation<br>3. Pipeline drugs from ClinicalTrials.gov<br>4. SEC filings and investors<br>5. PubMed publications<br>6. Financial timeseries<br>7. Risk flag calculation<br>8. Artifact storage | ✅ Strong (uses schemas) | ✅ Production-ready |
| `refine_biotech_dossier` | `biotech-markets-mcp` | 1. Load existing dossier<br>2. Extract insights by category<br>3. Answer new questions<br>4. Update dossier structure | ✅ Strong (structured I/O) | ✅ Production-ready |
| `analyze_company_across_markets_and_clinical` | `healthcare-equities-orchestrator-mcp` | 1. Company identifier resolution<br>2. Financial data (biotech-markets-mcp)<br>3. SEC filings (sec-edgar-mcp)<br>4. Clinical trials (clinical-trials-mcp)<br>5. Risk assessment<br>6. Cross-domain synthesis | ✅ Strong (uses shared schemas) | ✅ Production-ready |
| `claims_summarize_claim_with_risks` | `claims-edi-mcp` | 1. Parse EDI 837 (if needed)<br>2. Extract claim data<br>3. Analyze line items<br>4. Check for missing fields<br>5. Validate codes (CPT/HCPCS)<br>6. Generate risk flags<br>7. Build human-readable summary | ✅ Strong (structured output) | ✅ Production-ready |
| `claims_plan_claim_adjustments` | `claims-edi-mcp` | 1. Parse EDI 837 (if needed)<br>2. Analyze line items<br>3. Check payer rules<br>4. Identify issues<br>5. Suggest code changes<br>6. Generate structured plan | ✅ Strong (structured output) | ✅ Production-ready (read-only) |
| `generate_property_investment_brief` | `real-estate-mcp` | 1. Property lookup<br>2. Tax records<br>3. Recent sales<br>4. Market trends<br>5. Red flag calculation | ⚠️ Moderate | ⚠️ Needs schema verification |
| `biomcp.think` + research workflow | `biomcp-mcp` | 10-step sequential thinking process | ✅ Strong (structured) | ✅ Production-ready |

**Total: 7 macro tools**

### 4.2 Propose vs Execute Patterns

**Idempotency & Dry-Run Implementation:**

✅ **playwright-mcp** implements propose-vs-execute patterns:
- **Dry-run mode**: Defaults to `dry_run=True` for safety
- **Idempotency keys**: Uses `idempotency_store.py` to prevent duplicate executions
- **Confirmation required**: Non-dry-run operations require explicit confirmation phrase
- **Location**: `servers/misc/playwright-mcp/server.py` and `idempotency_store.py`

**Dry-Run Implementation Details:**
- Config flag: `default_dry_run` (defaults to `True`) in `PlaywrightServerConfig`
- Tools: `submit_regulatory_form` and `update_tracker_sheet` support `dry_run` parameter
- Behavior: When `dry_run=True`, returns preview without executing
- Confirmation: When `dry_run=False`, requires `confirm` parameter matching `REQUIRED_CONFIRMATION_PHRASE`

**Idempotency Implementation Details:**
- Store: `IdempotencyStore` class in `idempotency_store.py`
- Key format: `idempotency:tool:key:hash` (combines idempotency_key, tool_name, and parameter hash)
- TTL: 7 days default
- Behavior: Returns previous result if same idempotency_key + parameters used

**Other Servers with Propose-vs-Execute:**
- ⚠️ **claims-edi-mcp**: `claims_plan_claim_adjustments` is read-only (propose only, no execute)
- ❌ **biotech-markets-mcp**: Dossier tools are read-only (no execute phase)
- ❌ **healthcare-equities-orchestrator-mcp**: Analysis tool is read-only

**Recommendation:**
- Document propose-vs-execute pattern in `docs/` for future write tools
- Consider adding dry-run support to other write-capable tools
- Add idempotency support to tools that modify external state

### 4.3 Missing Macro Tools (Prioritized)

**P0 (Must-Do):**
1. **Patient Out-of-Pocket Estimate Tool** - Combine pricing + claims data
2. **Clinical Trial Matching Tool** - Patient condition → trial matches

**P1 (High Value):**
3. **Drug Pipeline Competitive Analysis** - Target disease → competitive landscape
4. **Claim Risk Flagging Tool** - Enhanced version of existing `claims_summarize_claim_with_risks`

**P2 (Nice-to-Have):**
5. **Property Investment Portfolio Analysis** - Batch processing of investment briefs
6. **Biomedical Literature Review Generator** - Leverage `biomcp.think` workflow

---

## 5. Cross-MCP Orchestration & Shared Identifiers

### 5.1 Orchestrator MCPs

**Identified Orchestrators:**

1. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`)
   - **Calls**: `biotech-markets-mcp`, `sec-edgar-mcp`, `clinical-trials-mcp`
   - **Workflows**: Cross-domain company analysis (markets + clinical)
   - **Tool**: `analyze_company_across_markets_and_clinical`
   - **Partial failure handling**: Returns partial results if some upstream MCPs fail
   - **Status**: ✅ Implemented, uses shared identifier schemas

2. **biotech-markets-mcp** (partial orchestration)
   - **Calls**: ClinicalTrials.gov API, SEC EDGAR API, PubMed API (direct, not via MCP)
   - **Workflows**: Company dossier generation, pipeline aggregation
   - **Status**: ✅ Implemented, but uses direct API calls (not MCP protocol)

### 5.2 Shared Identifier Schemas

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

**Gaps in Shared Identifier Normalization:**
- ❌ **NPI (National Provider Identifier)**: No shared schema found (used in claims-edi-mcp)
- ❌ **CPT/HCPCS codes**: No shared schema found (used in claims-edi-mcp, hospital-prices-mcp)
- ❌ **Address normalization**: No shared schema/utility found
- ⚠️ **Drug identifiers**: No shared schema found

**Local Normalization Functions (not shared):**
- `biotech-markets-mcp/company_aggregator.py`: `_normalize_company_name()`
- `sec-edgar-mcp/sec_edgar_client.py`: CIK zero-padding logic
- `claims-edi-mcp/edi_parser.py`: CPT/HCPCS code extraction

**Recommendation**: Create `common/identifiers.py` with shared normalization utilities.

---

## 6. Tests & CI

### 6.1 Test Layout

**Test directories:**
- `tests/unit/` - Unit tests per server
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end MCP protocol tests
- `tests/contract/` - API contract tests
- `tests/schema/` - Schema validation tests
- `servers/*/tests/` - Server-specific tests

### 6.2 Server-by-Server Test Coverage

| Server | Unit Tests | Integration Tests | E2E Tests | Macro Tools Tested? |
|--------|------------|-------------------|-----------|-------------------|
| **biomcp-mcp** | ✅ Yes (extensive) | ✅ Yes | ⚠️ Partial | N/A |
| **biotech-markets-mcp** | ⚠️ Partial | ❌ No | ❌ No | ❌ No |
| **clinical-trials-mcp** | ✅ Yes | ❌ No | ✅ Yes | N/A |
| **nhanes-mcp** | ✅ Yes | ❌ No | ❌ No | N/A |
| **sec-edgar-mcp** | ❌ No | ❌ No | ❌ No | N/A |
| **sp-global-mcp** | ❌ No | ❌ No | ❌ No | N/A |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **hospital-prices-mcp** | ✅ Yes | ❌ No | ❌ No | N/A |
| **claims-edi-mcp** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **real-estate-mcp** | ✅ Yes | ❌ No | ❌ No | N/A |
| **playwright-mcp** | ✅ Yes | ❌ No | ❌ No | ✅ Yes (idempotency) |
| **pubmed-mcp** | ❌ No | ❌ No | ❌ No | N/A |
| **fda-mcp** | ❌ No | ❌ No | ❌ No | N/A |

### 6.3 CI/CD Coverage

**GitHub Actions Workflows:**

✅ **`.github/workflows/validate.yml`** runs:
- **Registry validation**: Validates `tools_registry.json`
- **Schema validation**: Validates all JSON schema files
- **Python tests**: Runs `pytest tests/` on Python 3.8-3.11
- **TypeScript tests**: Runs `npm test` for TypeScript servers
- **Link checking**: Validates markdown links (continue-on-error)

✅ **`.github/workflows/release.yml`** (not reviewed in detail)

**Test Execution in CI:**
- ✅ Registry validation runs on every push/PR
- ✅ Schema validation runs on every push/PR
- ✅ Python tests run on every push/PR (multiple Python versions)
- ✅ TypeScript tests run on every push/PR
- ⚠️ Unclear if E2E tests run in CI

**Test Gaps:**
- ❌ Macro tools lack dedicated tests (`generate_biotech_company_dossier`, `refine_biotech_dossier`, `claims_summarize_claim_with_risks`)
- ❌ Orchestrator workflows lack E2E tests (`analyze_company_across_markets_and_clinical`)
- ❌ Missing negative/edge case tests (config missing, upstream failures)
- ❌ 4 servers have no tests (sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp)

---

## 7. QC Scorecard & Next Steps

### 7.1 QC Scorecard

| Category | Status | Justification |
|----------|--------|---------------|
| **Config & fail-soft/fail-fast** | 🟡 Yellow | 6/13 servers use `ServerConfig`. 7 servers need migration. Fail-fast/fail-soft behavior is inconsistent. |
| **Standardized HTTP + error handling** | 🟡 Yellow | Only 1 server (`hospital-prices-mcp`) uses `common.http`. Most use raw `requests`. Error mapping is inconsistent. |
| **Actionable workflow tools** | 🟢 Green | 7 macro tools exist, including strong dossier generation and orchestration. Some domains still need macro tools. |
| **Cross-MCP orchestration** | 🟢 Green | Orchestrator exists (`healthcare-equities-orchestrator-mcp`). Shared identifier schemas exist (ticker, CIK, NCT ID). |
| **Caching & artifacts** | 🟡 Yellow | `common.cache` exists but not widely adopted. Some servers use local caching. Artifact storage only in biotech-markets-mcp. |
| **Tests & CI** | 🟡 Yellow | Good coverage for biomcp-mcp, but many servers lack tests. Macro tools and orchestrators lack E2E tests. CI runs tests but E2E coverage unclear. |
| **PHI & sensitive data** | 🟢 Green | `common.phi` module exists and is integrated into logging. `claims-edi-mcp` uses PHI redaction. Config flag exists for enabling/disabling. |
| **TypeScript/JS alignment** | 🟡 Yellow | TypeScript servers (pubmed-mcp, fda-mcp, playwright-mcp) don't use Python config framework. Alignment needed. |

**Overall Health: 🟡 Yellow** - Good foundation, but migration work (P0 items from v2) remains incomplete.

### 7.2 Delta vs Previous Audits

**What improved since v2:**
- ❌ **No changes detected** - Repository state appears unchanged since v2 audit

**Which P0/P1 items from v2 are now done:**
- ❌ **None** - All P0/P1 items from v2 remain open

**Which are still open:**
- ✅ **All P0 items from v2** remain open:
  1. Migrate remaining servers to config framework (7 servers)
  2. Migrate HTTP clients to `common.http` (8 servers)
  3. Add E2E tests for orchestrator workflows
  4. Create shared identifier normalization utilities
  5. Add tests for macro tools

- ✅ **All P1 items from v2** remain open:
  6. Migrate all servers to `common.cache`
  7. Implement Patient Out-of-Pocket Estimate macro tool
  8. Implement Clinical Trial Matching tool
  9. Add comprehensive error mapping
  10. Add tests for servers without coverage

**New findings in v3:**
- ✅ PHI redaction is properly implemented and integrated into logging
- ✅ Idempotency and dry-run patterns exist in `playwright-mcp` but not widely adopted
- ✅ CI/CD runs comprehensive test suites (registry, schema, Python, TypeScript)
- ⚠️ E2E test coverage for orchestrators is unclear

### 7.3 Prioritized Roadmap (12 items)

#### P0 (Must-Do / Highest Risk or Leverage)

1. **Migrate remaining Python servers to config framework**
   - **Target**: biomcp-mcp, clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp
   - **Outcome**: All Python servers use `ServerConfig` with `validate_config_or_raise()`
   - **Why**: Consistency, fail-fast/fail-soft behavior, SERVICE_NOT_CONFIGURED support
   - **Risk if skipped**: Configuration errors go undetected, inconsistent startup behavior

2. **Migrate HTTP clients to `common.http`**
   - **Target**: biotech-markets-mcp, sec-edgar-mcp, sp-global-mcp, clinical-trials-mcp, nhanes-mcp, real-estate-mcp
   - **Outcome**: All servers use `common.http` for standardized timeouts, retries, circuit breakers
   - **Why**: Reduces upstream failures, improves resilience, consistent error handling
   - **Risk if skipped**: Inconsistent timeout/retry behavior, no circuit breaker protection

3. **Add E2E tests for orchestrator workflows**
   - **Target**: `healthcare-equities-orchestrator-mcp.analyze_company_across_markets_and_clinical`
   - **Outcome**: E2E test that verifies cross-MCP calls work end-to-end
   - **Why**: Orchestrators are high-risk (multiple dependencies)
   - **Risk if skipped**: Integration issues discovered in production

4. **Create shared identifier normalization utilities**
   - **Target**: `common/identifiers.py`
   - **Outcome**: `normalize_ticker()`, `normalize_cik()`, `normalize_nct_id()`, `normalize_cpt_code()`, `normalize_npi()`
   - **Why**: Prevents identifier mismatches in orchestration
   - **Risk if skipped**: Cross-MCP integration bugs from identifier format mismatches

5. **Add tests for macro tools**
   - **Target**: `generate_biotech_company_dossier`, `refine_biotech_dossier`, `claims_summarize_claim_with_risks`
   - **Outcome**: Dedicated unit/integration tests for each macro tool
   - **Why**: Macro tools are high-value and complex
   - **Risk if skipped**: Regressions in key workflows go undetected

#### P1 (High Value)

6. **Migrate all servers to `common.cache`**
   - **Target**: hospital-prices-mcp, real-estate-mcp, clinical-trials-mcp, nhanes-mcp, sp-global-mcp
   - **Outcome**: All servers use `common.cache` for consistency
   - **Why**: Better cache hit rates, easier cache debugging, centralized cache management
   - **Risk if skipped**: Inconsistent caching behavior, harder to optimize cache performance

7. **Implement Patient Out-of-Pocket Estimate macro tool**
   - **Target**: New tool combining `hospital-prices-mcp` and `claims-edi-mcp`
   - **Outcome**: Tool that estimates patient OOP costs using pricing + claims data
   - **Why**: High-value use case combining multiple domains
   - **Risk if skipped**: Missing actionable workflow for end users

8. **Implement Clinical Trial Matching tool**
   - **Target**: New tool in `clinical-trials-mcp` or new server
   - **Outcome**: Tool that matches patient condition/demographics to trials
   - **Why**: Actionable workflow vs. just search
   - **Risk if skipped**: Poor user experience for clinical trial discovery

9. **Add comprehensive error mapping**
   - **Target**: All servers using raw `requests`
   - **Outcome**: All servers use `map_upstream_error` for consistent error codes
   - **Why**: Consistent error codes across servers, better LLM error handling
   - **Risk if skipped**: Inconsistent error handling, harder to debug upstream failures

10. **Add tests for servers without coverage**
    - **Target**: sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp
    - **Outcome**: Unit tests for each server
    - **Why**: Prevents regressions
    - **Risk if skipped**: Bugs go undetected, lower confidence in deployments

#### P2 (Nice-to-Have)

11. **Create shared address normalization utility**
    - **Target**: `common/identifiers.py`
    - **Outcome**: `normalize_address()` function
    - **Why**: Addresses used across multiple servers (real-estate, hospital-prices)
    - **Risk if skipped**: Location-based matching issues

12. **Document propose-vs-execute pattern**
    - **Target**: `docs/` directory
    - **Outcome**: Documentation of dry-run and idempotency patterns (based on playwright-mcp)
    - **Why**: Guide for future write tools
    - **Risk if skipped**: Inconsistent patterns across write tools

### 7.4 "If You Only Do Three Things Next..."

**Top 3 Most Leveraged Next Actions:**

1. **Migrate HTTP clients to `common.http`** (P0)
   - **Impact**: Immediately improves resilience for 8 servers
   - **Effort**: Medium (requires updating client code in each server)
   - **Risk reduction**: Prevents upstream failures from cascading, adds circuit breaker protection

2. **Migrate remaining Python servers to config framework** (P0)
   - **Impact**: Standardizes configuration across all Python servers
   - **Effort**: Medium (requires creating config.py files and updating server.py)
   - **Risk reduction**: Catches configuration errors at startup, enables fail-fast/fail-soft behavior

3. **Add E2E tests for orchestrator workflows** (P0)
   - **Impact**: Validates cross-MCP integration works end-to-end
   - **Effort**: Low (single E2E test for orchestrator)
   - **Risk reduction**: Catches integration issues before production deployment

**Rationale**: These three items address the highest-risk areas (upstream failures, configuration errors, integration bugs) with manageable effort.

---

## 8. Owner-Friendly Synopsis

**For Tech Lead Planning Doc:**

- **Status**: 🟡 Yellow - Good foundation, but migration work remains incomplete
- **Config Framework**: 6/13 servers migrated, 7 remaining (biomcp-mcp, clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp)
- **HTTP Client**: Only 1/13 servers use `common.http`, 8 use raw `requests` (should migrate)
- **Macro Tools**: 7 macro tools exist and are production-ready (dossier generation, claim analysis, orchestration)
- **PHI Handling**: ✅ Properly implemented in `common/phi.py` and integrated into logging; `claims-edi-mcp` has config flag
- **Propose-vs-Execute**: ✅ Implemented in `playwright-mcp` (dry-run + idempotency), not widely adopted elsewhere
- **Tests**: Good coverage for `biomcp-mcp`, gaps for macro tools and orchestrators; 4 servers have no tests
- **CI/CD**: ✅ Runs registry validation, schema validation, Python tests (3.8-3.11), TypeScript tests
- **Top 3 Next Actions**: (1) Migrate HTTP clients to `common.http`, (2) Migrate remaining servers to config framework, (3) Add E2E tests for orchestrators
- **No changes since v2**: Repository state appears unchanged; all P0/P1 items from v2 remain open

---

**Report Generated**: December 2024  
**Compared Against**: AUDIT_REPORT_v2.md (December 2024), AUDIT_REPORT.md (baseline)  
**Next Review**: After P0 items completed

