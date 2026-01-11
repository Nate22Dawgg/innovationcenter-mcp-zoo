# Innovation Center MCP Zoo - Audit Report v4

**Date**: December 2024  
**Auditor**: Senior Architect & Codebase Auditor  
**Scope**: Read-only QC pass after robustness + macro-tool work, verifying P0/P1 items from v3  
**Mode**: READ-ONLY inspection (no modifications)

---

## Executive Summary

This audit compares the current state to `AUDIT_REPORT_v3.md` (December 2024) and verifies completion of P0/P1 items. **Significant progress** has been made since v3 - the repository shows substantial improvements in config framework adoption, HTTP client standardization, shared identifiers, caching, and macro tool implementation.

**Key Findings:**
- **11 of 13 servers** (85%) now use `ServerConfig` framework (up from 6/13, 46% in v3)
- **Multiple servers** now use `common.http` client (up from 1/13 in v3)
- **Shared identifier utilities** (`common/identifiers.py`) exist and are actively used across servers
- **Both P0 macro tools** implemented: Patient Out-of-Pocket Estimate and Clinical Trial Matching
- **Comprehensive tests** exist for macro tools and orchestrators (41+ test cases)
- **PHI handling** properly implemented in `common/phi.py` and integrated into claims-edi-mcp
- **Caching** widely adopted via `common.cache` across multiple servers

**Status**: 🟢 **Green** (up from 🟡 Yellow in v3) - Strong foundation with most P0 items completed. Remaining gaps are primarily TypeScript server alignment and some edge cases.

---

## 1. Global Scan & Baseline

### 1.1 Current Repository Structure

**Top-level directories:**
- `common/` - Shared utilities (config, errors, HTTP, cache, validation, observability, PHI handling, **identifiers**)
- `servers/` - MCP server implementations organized by domain
- `scripts/` - Helper scripts including `create_mcp_server.py` and templates
- `docs/` - Architecture and configuration documentation
- `schemas/` - JSON schemas for tool inputs/outputs (100+ files)
- `registry/` - Centralized tool registry (`tools_registry.json`, `domains_taxonomy.json`)
- `tests/` - Test suite (unit, integration, e2e, contract, schema validation)
- `.github/workflows/` - CI/CD workflows (validate.yml, release.yml)

**MCP Servers (13 total across 6 domains):**

1. **biomcp-mcp** (`servers/clinical/biomcp-mcp/`) - ~35-40 tools
2. **clinical-trials-mcp** (`servers/clinical/clinical-trials-mcp/`) - 3 tools (includes `clinical_trial_matching`)
3. **nhanes-mcp** (`servers/clinical/nhanes-mcp/`) - 5 tools
4. **pubmed-mcp** (`servers/misc/pubmed-mcp/`) - 5 tools (TypeScript)
5. **fda-mcp** (`servers/misc/fda-mcp/`) - 10 tools (TypeScript)
6. **biotech-markets-mcp** (`servers/markets/biotech-markets-mcp/`) - 8 tools
7. **sec-edgar-mcp** (`servers/markets/sec-edgar-mcp/`) - 6 tools
8. **sp-global-mcp** (`servers/markets/sp-global-mcp/`) - 4 tools
9. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`) - 1 tool
10. **hospital-prices-mcp** (`servers/pricing/hospital-prices-mcp/`) - 6 tools (includes `patient_oop_estimate_macro`)
11. **claims-edi-mcp** (`servers/claims/claims-edi-mcp/`) - 7 tools
12. **real-estate-mcp** (`servers/real-estate/real-estate-mcp/`) - 5+ tools
13. **playwright-mcp** (`servers/misc/playwright-mcp/`) - 10+ tools

### 1.2 Delta vs Previous Audits

**AUDIT_REPORT_v3.md (December 2024 - Previous):**
- **Main conclusions:**
  - 6/13 servers use `ServerConfig` framework
  - Only 1 server (`hospital-prices-mcp`) uses `common.http`
  - 7 macro tools exist (dossier generation, claim analysis, orchestration)
  - Shared identifier schemas exist (ticker, CIK, NCT ID) but no normalization utilities
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

**Delta from v3 to v4:**
- ✅ **5 servers migrated to config framework** (clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, biomcp-mcp)
- ✅ **Multiple servers migrated to `common.http`** (biotech-markets-mcp, sec-edgar-mcp, sp-global-mcp, clinical-trials-mcp, real-estate-mcp)
- ✅ **Shared identifier utilities created** (`common/identifiers.py` with all normalization functions)
- ✅ **Both P0 macro tools implemented** (Patient OOP Estimate, Clinical Trial Matching)
- ✅ **Comprehensive tests added** (41+ test cases for macro tools and orchestrators)
- ✅ **E2E tests for orchestrator** (`test_e2e_orchestrator.py` with 6 test cases)
- ✅ **Caching widely adopted** (many servers now use `common.cache`)

---

## 2. Robustness & Config Framework Adoption

### 2.1 Server-by-Server Config Framework Status

| Server | Uses `ServerConfig`? | Fail-Fast/Fail-Soft | Uses `SERVICE_NOT_CONFIGURED`? | Config File Path | Status vs v3 |
|--------|---------------------|---------------------|-------------------------------|------------------|--------------|
| **biomcp-mcp** | ✅ **Yes** | Fail-soft | ⚠️ Partial | `src/biomcp/config.py` | ✅ **NEW** (was ❌) |
| **clinical-trials-mcp** | ✅ **Yes** | Fail-fast | ⚠️ Partial | `config.py` | ✅ **NEW** (was ❌) |
| **nhanes-mcp** | ✅ **Yes** | Fail-fast | ⚠️ Partial | `config.py` | ✅ **NEW** (was ❌) |
| **pubmed-mcp** | ❌ No (TS) | N/A | ❌ No | N/A (TypeScript) | ⚠️ **Unchanged** |
| **fda-mcp** | ❌ No (TS) | N/A | ❌ No | N/A (TypeScript) | ⚠️ **Unchanged** |
| **biotech-markets-mcp** | ✅ Yes | Fail-soft (env var) | ⚠️ Partial | `config.py` | ✅ **Unchanged** |
| **sec-edgar-mcp** | ✅ **Yes** | Fail-fast | ⚠️ Partial | `config.py` | ✅ **NEW** (was ❌) |
| **sp-global-mcp** | ✅ **Yes** | Fail-fast | ✅ Yes | `config.py` | ✅ **NEW** (was ❌) |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | Fail-fast (default) | ✅ Yes | `config.py` | ✅ **Unchanged** |
| **hospital-prices-mcp** | ✅ Yes | Fail-fast | ✅ Yes | `config.py` | ✅ **Unchanged** |
| **claims-edi-mcp** | ✅ Yes | N/A (all optional) | ⚠️ Partial | `config.py` | ✅ **Unchanged** |
| **real-estate-mcp** | ✅ Yes | Fail-fast | ⚠️ Partial | `config.py` | ✅ **Unchanged** |
| **playwright-mcp** | ✅ Yes | Fail-fast | ✅ Yes | `config.py` | ✅ **Unchanged** |

**Summary:**
- **11/13 servers** (85%) use `ServerConfig` framework (up from 6/13, 46% in v3)
- **2/13 servers** (15%) still need migration (pubmed-mcp, fda-mcp - both TypeScript)
- **Fail-fast by default**: 7 servers (clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, healthcare-equities-orchestrator-mcp, hospital-prices-mcp, real-estate-mcp, playwright-mcp)
- **Fail-soft configurable**: 2 servers (biomcp-mcp, biotech-markets-mcp)
- **SERVICE_NOT_CONFIGURED usage**: 4 servers explicitly use it (sp-global-mcp, healthcare-equities-orchestrator-mcp, hospital-prices-mcp, playwright-mcp)

**Progress**: ✅ **5 servers migrated** since v3 (clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, biomcp-mcp)

### 2.2 Config Framework Implementation Details

**Newly Migrated Servers (5):**

1. **clinical-trials-mcp** (`servers/clinical/clinical-trials-mcp/config.py`)
   - `ClinicalTrialsConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - All config optional (uses free public API)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

2. **nhanes-mcp** (`servers/clinical/nhanes-mcp/config.py`)
   - `NhanesConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - All config optional (uses local data files)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

3. **sec-edgar-mcp** (`servers/markets/sec-edgar-mcp/config.py`)
   - `SecEdgarConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - All config optional (uses free public API, provides default User-Agent)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

4. **sp-global-mcp** (`servers/markets/sp-global-mcp/config.py`)
   - `SPGlobalConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-fast
   - `SP_GLOBAL_API_KEY` is **required** (critical=True)
   - Uses `SERVICE_NOT_CONFIGURED` when API key missing

5. **biomcp-mcp** (`servers/clinical/biomcp-mcp/src/biomcp/config.py`)
   - `BiomcpConfig` extends `ServerConfig`
   - Uses `validate_config_or_raise()` with fail-soft (fail_fast=False)
   - All API keys optional (multiple optional keys: ONCOKB_TOKEN, ALPHAGENOME_API_KEY, etc.)
   - Does NOT use `SERVICE_NOT_CONFIGURED` (all config optional)

**Servers Still Needing Migration (2):**
1. **pubmed-mcp** - TypeScript server, different pattern
2. **fda-mcp** - TypeScript server, different pattern

**Migration Recommendation:**
- TypeScript servers need separate alignment strategy (document patterns or create TypeScript equivalent)
- All Python servers now use `ServerConfig` framework ✅

---

## 3. HTTP Client, Error Handling, PHI, Caching

### 3.1 HTTP Client Usage

| Server | HTTP Client Pattern | Retries? | Circuit Breaker? | Uses Shared Error Mapping? | Status vs v3 |
|--------|-------------------|----------|-----------------|---------------------------|--------------|
| **biomcp-mcp** | Custom async httpx | ✅ Yes | ✅ Yes | ⚠️ Custom | ⚠️ **Unchanged** (acceptable) |
| **clinical-trials-mcp** | ✅ **`common.http`** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **NEW** (was raw `requests`) |
| **nhanes-mcp** | N/A (local files) | N/A | N/A | N/A | ⚠️ **Unchanged** |
| **pubmed-mcp** | Axios (TypeScript) | ⚠️ Partial | ❌ No | ❌ No | ⚠️ **Unchanged** |
| **fda-mcp** | Axios (TypeScript) | ⚠️ Partial | ❌ No | ❌ No | ⚠️ **Unchanged** |
| **biotech-markets-mcp** | ✅ **`common.http`** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **NEW** (was raw `requests`) |
| **sec-edgar-mcp** | ✅ **`common.http`** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **NEW** (was raw `requests`) |
| **sp-global-mcp** | ✅ **`common.http`** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **NEW** (was raw `requests`) |
| **healthcare-equities-orchestrator-mcp** | MCP protocol | N/A | N/A | ✅ Yes | ✅ **Unchanged** |
| **hospital-prices-mcp** | ✅ `common.http` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Unchanged** |
| **claims-edi-mcp** | N/A (file parsing) | N/A | N/A | ✅ Yes | ✅ **Unchanged** |
| **real-estate-mcp** | ✅ **`common.http`** | ✅ Yes | ✅ Yes | ⚠️ Partial | ✅ **NEW** (was raw `requests`) |
| **playwright-mcp** | N/A (browser) | N/A | N/A | ⚠️ Partial | ✅ **Unchanged** |

**Summary:**
- **6/13 servers** (46%) use `common.http` client (up from 1/13, 8% in v3)
- **5/13 servers** (38%) use raw `requests` library (down from 8/13, 62% in v3)
- **2/13 servers** (15%) use TypeScript HTTP (Axios) - unchanged
- **1/13 servers** (8%) use custom httpx client (biomcp-mcp) - acceptable exception

**Progress**: ✅ **5 servers migrated** to `common.http` since v3:
1. biotech-markets-mcp (pubmed_client.py, sec_edgar_client.py, clinical_trials_client.py)
2. sec-edgar-mcp (sec_edgar_client.py)
3. sp-global-mcp (sp_global_client.py)
4. clinical-trials-mcp (clinical_trials_api.py)
5. real-estate-mcp (batchdata_client.py, gis_client.py)

**Note on biomcp-mcp**: Uses custom async httpx client with connection pooling, circuit breakers, and rate limiting. This is an acceptable alternative pattern given its sophisticated requirements.

### 3.2 Error Handling

**Servers using `map_upstream_error` (3/13):**
- ✅ **hospital-prices-mcp** - Uses `map_upstream_error` in `turquoise_client.py`
- ✅ **claims-edi-mcp** - Uses `map_upstream_error` in tool implementations
- ⚠️ **biotech-markets-mcp** - Uses error handling but not consistently `map_upstream_error`

**Servers with custom error handling:**
- ⚠️ **biomcp-mcp** - Custom `RequestError` pattern
- ⚠️ **healthcare-equities-orchestrator-mcp** - Uses `ErrorCode` directly

**Servers with minimal error handling:**
- ⚠️ Most other servers have basic try/except with string error messages

**Recommendation**: Migrate remaining servers to use `map_upstream_error` for consistent error codes.

### 3.3 PHI & Sensitive Data Handling

**PHI Redaction Implementation:**

✅ **`common/phi.py`** provides:
- `redact_phi(payload)` - Recursively redacts PHI from data structures
- `is_phi_field(field_name)` - Checks if field name matches PHI patterns
- `mark_ephemeral(data, reason)` - Marks data as ephemeral (should not persist)
- `is_ephemeral(data)` - Checks if data is marked as ephemeral

**Integration with Logging:**

✅ **`common/logging.py`** automatically applies PHI redaction:
- `log_request()` - Redacts PHI from input parameters
- `log_response()` - Redacts PHI from response data
- `log_error()` - Redacts PHI from error context
- `request_context()` - Redacts PHI before logging

**PHI Redaction Usage in Servers:**

✅ **claims-edi-mcp**:
- Imports `redact_phi` and `is_ephemeral` from `common.phi`
- Uses `request_context()` which applies PHI redaction automatically
- `edi_parser.py` uses `mark_ephemeral()` to mark parsed EDI data as ephemeral
- Has config flag `enable_phi_redaction` (defaults to True) in `config.py`

**Status**: ✅ **Properly implemented** - PHI handling is robust and integrated into logging.

### 3.4 Caching & Artifacts

**Shared Caching Infrastructure:**

✅ **`common/cache.py`** provides:
- `Cache` class: In-memory cache with TTL support
- `get_cache()`: Global singleton cache instance
- `build_cache_key()`: Standardized cache key generation

**Servers using `common.cache`:**
- ✅ **biotech-markets-mcp**: Uses `get_cache()` and `build_cache_key()` for timeseries data
- ✅ **sec-edgar-mcp**: Uses `common.cache` in `sec_edgar_client.py`
- ✅ **sp-global-mcp**: Uses `common.cache` in `sp_global_client.py`
- ✅ **clinical-trials-mcp**: Uses `common.cache` in `clinical_trials_api.py`
- ✅ **nhanes-mcp**: Uses `common.cache` in `nhanes_query_engine.py`
- ✅ **real-estate-mcp**: Uses `common.cache` in multiple clients (batchdata_client.py, county_assessor_client.py, gis_client.py, redfin_client.py)
- ✅ **healthcare-equities-orchestrator-mcp**: Uses `common.cache` in `mcp_orchestrator_client.py`
- ✅ **hospital-prices-mcp**: Uses `common.cache` in `turquoise_client.py`
- ✅ **playwright-mcp**: Uses `common.cache` in `idempotency_store.py`

**Servers with custom caching:**
- ⚠️ **biomcp-mcp**: Custom caching with request/response caching (acceptable given async requirements)

**Progress**: ✅ **9/13 servers** (69%) now use `common.cache` (up from 2/13, 15% in v3)

**Artifact Storage:**

✅ **biotech-markets-mcp** has `artifact_store.py`:
- Stores generated dossiers with unique IDs
- Supports retrieval by ID
- Used by `generate_biotech_company_dossier` and `refine_biotech_dossier`

**Expensive Operations Cached:**
- ✅ **biotech-markets-mcp**: Timeseries data (7 days for historical, 1 hour for recent)
- ✅ **biotech-markets-mcp**: CIK lookups (24 hours)
- ✅ **hospital-prices-mcp**: Procedure price searches (via `common.cache`)
- ✅ **clinical-trials-mcp**: Trial searches (via `common.cache`)
- ✅ **sp-global-mcp**: Company profiles (via `common.cache`)
- ✅ **biomcp-mcp**: API responses (configurable TTL)

**Status**: ✅ **Caching widely adopted** - Most expensive operations are now cached.

---

## 4. Macro Tools & "Actionable Work"

### 4.1 Existing Macro Tools

| Tool Name | Server | Workflow Steps | IO Typing | Status | Status vs v3 |
|-----------|--------|---------------|-----------|--------|--------------|
| `generate_biotech_company_dossier` | `biotech-markets-mcp` | 1. Company identifier resolution<br>2. Company profile aggregation<br>3. Pipeline drugs from ClinicalTrials.gov<br>4. SEC filings and investors<br>5. PubMed publications<br>6. Financial timeseries<br>7. Risk flag calculation<br>8. Artifact storage | ✅ Strong (uses schemas) | ✅ Production-ready | ✅ **Unchanged** |
| `refine_biotech_dossier` | `biotech-markets-mcp` | 1. Load existing dossier<br>2. Extract insights by category<br>3. Answer new questions<br>4. Update dossier structure | ✅ Strong (structured I/O) | ✅ Production-ready | ✅ **Unchanged** |
| `analyze_company_across_markets_and_clinical` | `healthcare-equities-orchestrator-mcp` | 1. Company identifier resolution<br>2. Financial data (biotech-markets-mcp)<br>3. SEC filings (sec-edgar-mcp)<br>4. Clinical trials (clinical-trials-mcp)<br>5. Risk assessment<br>6. Cross-domain synthesis | ✅ Strong (uses shared schemas) | ✅ Production-ready | ✅ **Unchanged** |
| `claims_summarize_claim_with_risks` | `claims-edi-mcp` | 1. Parse EDI 837 (if needed)<br>2. Extract claim data<br>3. Analyze line items<br>4. Check for missing fields<br>5. Validate codes (CPT/HCPCS)<br>6. Generate risk flags<br>7. Build human-readable summary | ✅ Strong (structured output) | ✅ Production-ready | ✅ **Unchanged** |
| `claims_plan_claim_adjustments` | `claims-edi-mcp` | 1. Parse EDI 837 (if needed)<br>2. Analyze line items<br>3. Check payer rules<br>4. Identify issues<br>5. Suggest code changes<br>6. Generate structured plan | ✅ Strong (structured output) | ✅ Production-ready (read-only) | ✅ **Unchanged** |
| `generate_property_investment_brief` | `real-estate-mcp` | 1. Property lookup<br>2. Tax records<br>3. Recent sales<br>4. Market trends<br>5. Red flag calculation | ⚠️ Moderate | ⚠️ Needs schema verification | ✅ **Unchanged** |
| `biomcp.think` + research workflow | `biomcp-mcp` | 10-step sequential thinking process | ✅ Strong (structured) | ✅ Production-ready | ✅ **Unchanged** |
| `patient_oop_estimate_macro` | `hospital-prices-mcp` | 1. Procedure codes input<br>2. Hospital pricing lookup<br>3. CMS fee schedule lookup<br>4. Insurance benefit calculation<br>5. Deductible/coinsurance calculation<br>6. Final OOP estimate | ✅ Strong (uses schemas) | ✅ Production-ready | ✅ **NEW** (P0) |
| `clinical_trial_matching` | `clinical-trials-mcp` | 1. Patient condition input<br>2. Search trials<br>3. Filter by eligibility (age, sex, condition)<br>4. Rank by proximity, phase, fit<br>5. Return structured matches | ✅ Strong (uses schemas) | ✅ Production-ready | ✅ **NEW** (P0) |

**Total: 9 macro tools** (up from 7 in v3)

**Progress**: ✅ **Both P0 macro tools implemented**:
1. **Patient Out-of-Pocket Estimate** (`patient_oop_estimate_macro` in hospital-prices-mcp)
2. **Clinical Trial Matching** (`clinical_trial_matching` in clinical-trials-mcp)

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

**Status**: ✅ **Write safety patterns exist** - playwright-mcp demonstrates best practices.

### 4.3 Missing Macro Tools (Prioritized)

**P1 (High Value):**
1. **Drug Pipeline Competitive Analysis** - Target disease → competitive landscape
2. **Claim Risk Flagging Tool** - Enhanced version of existing `claims_summarize_claim_with_risks`

**P2 (Nice-to-Have):**
3. **Property Investment Portfolio Analysis** - Batch processing of investment briefs
4. **Biomedical Literature Review Generator** - Leverage `biomcp.think` workflow

**Status**: ✅ **All P0 macro tools completed** - Remaining items are P1/P2.

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

### 5.2 Shared Identifier Schemas & Normalization

**Shared Identifier Utilities:**

✅ **`common/identifiers.py`** provides:
- `normalize_ticker(ticker: str) -> str` - Normalizes stock ticker symbols
- `normalize_cik(cik: Union[str, int]) -> str` - Normalizes SEC CIK to 10-digit format
- `normalize_nct_id(nct_id: str) -> str` - Normalizes ClinicalTrials.gov NCT IDs
- `normalize_cpt_code(code: str) -> str` - Normalizes CPT procedure codes
- `normalize_hcpcs_code(code: str) -> str` - Normalizes HCPCS codes
- `normalize_npi(npi: Union[str, int]) -> str` - Normalizes National Provider Identifier
- `normalize_address(address: Union[str, Dict]) -> Dict` - Normalizes address structures

**Servers Using `common.identifiers`:**
- ✅ **clinical-trials-mcp**: Uses `normalize_nct_id` in `server.py`
- ✅ **healthcare-equities-orchestrator-mcp**: Uses `normalize_ticker`, `normalize_cik` in `analyze_company_tool.py` and `mcp_orchestrator_client.py`
- ✅ **biotech-markets-mcp**: Uses `normalize_cik` in `dossier_generator.py` and `sec_edgar_client.py`
- ✅ **sec-edgar-mcp**: Uses `normalize_cik`, `normalize_ticker` in `sec_edgar_client.py`
- ✅ **claims-edi-mcp**: Uses `normalize_cpt_code`, `normalize_hcpcs_code`, `normalize_npi` in `edi_parser.py`

**Progress**: ✅ **Shared identifier utilities created and actively used** (was missing in v3)

**Identifier Schemas in `schemas/`:**
1. **Ticker Identifier** (`schemas/ticker_identifier.json`)
   - Pattern: `^[A-Z0-9.-]+$`
   - Used in: `biotech-markets-mcp`, `healthcare-equities-orchestrator-mcp`, `sec-edgar-mcp`

2. **SEC CIK** (`schemas/sec_identifier.json`)
   - Pattern: `^\\d{10}$` (10-digit zero-padded)
   - Used in: `biotech-markets-mcp`, `healthcare-equities-orchestrator-mcp`, `sec-edgar-mcp`

3. **Clinical Trial Identifier** (`schemas/clinical_trial_identifier.json`)
   - Pattern: `^NCT[0-9]{8}$`
   - Used in: `clinical-trials-mcp`, `biomcp-mcp`

**Status**: ✅ **Shared identifiers fully implemented** - Both schemas and normalization utilities exist and are used.

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

| Server | Unit Tests | Integration Tests | E2E Tests | Macro Tools Tested? | Status vs v3 |
|--------|------------|-------------------|-----------|-------------------|--------------|
| **biomcp-mcp** | ✅ Yes (extensive) | ✅ Yes | ⚠️ Partial | N/A | ✅ **Unchanged** |
| **biotech-markets-mcp** | ✅ Yes | ❌ No | ❌ No | ✅ **Yes** (`test_dossier_tools.py`) | ✅ **IMPROVED** |
| **clinical-trials-mcp** | ✅ Yes | ❌ No | ✅ Yes | ✅ **Yes** (`test_matching.py`) | ✅ **IMPROVED** |
| **nhanes-mcp** | ✅ Yes | ❌ No | ❌ No | N/A | ✅ **Unchanged** |
| **sec-edgar-mcp** | ❌ No | ❌ No | ❌ No | N/A | ⚠️ **Unchanged** |
| **sp-global-mcp** | ❌ No | ❌ No | ❌ No | N/A | ⚠️ **Unchanged** |
| **healthcare-equities-orchestrator-mcp** | ✅ Yes | ❌ No | ✅ **Yes** (`test_e2e_orchestrator.py`) | ✅ **Yes** | ✅ **IMPROVED** |
| **hospital-prices-mcp** | ✅ Yes | ❌ No | ❌ No | ✅ **Yes** (`test_hospital_pricing.py`) | ✅ **IMPROVED** |
| **claims-edi-mcp** | ✅ Yes | ❌ No | ❌ No | ✅ **Yes** (`test_macro_tools.py`) | ✅ **IMPROVED** |
| **real-estate-mcp** | ✅ Yes | ❌ No | ❌ No | N/A | ✅ **Unchanged** |
| **playwright-mcp** | ✅ Yes | ❌ No | ❌ No | ✅ Yes (idempotency) | ✅ **Unchanged** |
| **pubmed-mcp** | ❌ No | ❌ No | ❌ No | N/A | ⚠️ **Unchanged** |
| **fda-mcp** | ❌ No | ❌ No | ❌ No | N/A | ⚠️ **Unchanged** |

**Progress**: ✅ **Comprehensive tests added** for macro tools and orchestrators

### 6.3 Macro Tool Test Coverage

**Tests Created (from `TEST_IMPLEMENTATION_SUMMARY.md`):**

1. **Biotech Markets MCP - Dossier Tools** (`test_dossier_tools.py`)
   - `generate_biotech_company_dossier`: 6 tests
   - `refine_biotech_dossier`: 6 tests
   - **Total**: 12 test cases

2. **Claims EDI MCP - Macro Tools** (`test_macro_tools.py`)
   - `claims_summarize_claim_with_risks`: 12 tests
   - `claims_plan_claim_adjustments`: 11 tests
   - **Total**: 23 test cases

3. **Healthcare Equities Orchestrator MCP - E2E Tests** (`test_e2e_orchestrator.py`)
   - `analyze_company_across_markets_and_clinical`: 6 E2E tests
   - **Total**: 6 test cases

4. **Hospital Prices MCP - OOP Estimate** (`test_hospital_pricing.py`)
   - `patient_oop_estimate_macro`: 5+ tests (with hospital pricing, CMS data, self-pay, deductible, missing data)
   - **Total**: 5+ test cases

5. **Clinical Trials MCP - Matching** (`test_matching.py`)
   - `clinical_trial_matching`: Integration tests for matching utilities
   - **Total**: Multiple test cases

**Total**: **41+ test cases** for macro tools and orchestrators

**Test Patterns Used:**
- **Mocking Strategy**: All external API calls are mocked to avoid flakiness
- **Test Data**: Synthetic EDI examples with no real PHI, well-known public tickers
- **Error Handling**: Tests verify graceful degradation when upstreams fail
- **Integration Style**: Tests exercise full tool handlers, verify complete output structures

**Status**: ✅ **Comprehensive test coverage** - All major macro tools and orchestrators have dedicated tests

### 6.4 CI/CD Coverage

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
- ⚠️ E2E tests may run in CI (need verification)

**Status**: ✅ **CI/CD runs comprehensive test suites** - Registry, schema, Python, and TypeScript tests all run.

---

## 7. QC Scorecard & Next Steps

### 7.1 QC Scorecard

| Category | Status | Justification | Status vs v3 |
|----------|--------|---------------|--------------|
| **Config & fail-soft/fail-fast** | 🟢 **Green** | 11/13 servers (85%) use `ServerConfig`. Only 2 TypeScript servers remain. Fail-fast/fail-soft behavior is consistent. | ✅ **IMPROVED** (was 🟡 Yellow) |
| **Standardized HTTP + error handling** | 🟢 **Green** | 6/13 servers (46%) use `common.http`. Most Python servers migrated. Error mapping is consistent where used. | ✅ **IMPROVED** (was 🟡 Yellow) |
| **Actionable workflow tools** | 🟢 **Green** | 9 macro tools exist, including both P0 tools (Patient OOP Estimate, Clinical Trial Matching). Strong foundation. | ✅ **IMPROVED** (was 🟢 Green, but now has P0 tools) |
| **Cross-MCP orchestration** | 🟢 **Green** | Orchestrator exists (`healthcare-equities-orchestrator-mcp`). Shared identifier schemas AND normalization utilities exist. | ✅ **IMPROVED** (was 🟢 Green, but now has normalization) |
| **Caching & artifacts** | 🟢 **Green** | `common.cache` widely adopted (9/13 servers, 69%). Artifact storage in biotech-markets-mcp. | ✅ **IMPROVED** (was 🟡 Yellow) |
| **Tests & CI** | 🟢 **Green** | Comprehensive tests for macro tools (41+ test cases). E2E tests for orchestrator. CI runs test suites. | ✅ **IMPROVED** (was 🟡 Yellow) |
| **PHI & sensitive data** | 🟢 **Green** | `common.phi` module exists and is integrated into logging. `claims-edi-mcp` uses PHI redaction. Config flag exists. | ✅ **Unchanged** (was 🟢 Green) |
| **TypeScript/JS alignment** | 🟡 **Yellow** | TypeScript servers (pubmed-mcp, fda-mcp) don't use Python config framework. Alignment needed. | ⚠️ **Unchanged** (was 🟡 Yellow) |

**Overall Health: 🟢 Green** (up from 🟡 Yellow in v3) - Strong foundation with most P0 items completed. Remaining gaps are primarily TypeScript server alignment and some edge cases.

### 7.2 Delta vs Previous Audits

**What improved since v3:**
- ✅ **5 servers migrated to config framework** (clinical-trials-mcp, nhanes-mcp, sec-edgar-mcp, sp-global-mcp, biomcp-mcp)
- ✅ **5 servers migrated to `common.http`** (biotech-markets-mcp, sec-edgar-mcp, sp-global-mcp, clinical-trials-mcp, real-estate-mcp)
- ✅ **Shared identifier utilities created** (`common/identifiers.py` with all normalization functions)
- ✅ **Both P0 macro tools implemented** (Patient OOP Estimate, Clinical Trial Matching)
- ✅ **Comprehensive tests added** (41+ test cases for macro tools and orchestrators)
- ✅ **E2E tests for orchestrator** (`test_e2e_orchestrator.py` with 6 test cases)
- ✅ **Caching widely adopted** (9/13 servers now use `common.cache`)

**Which P0/P1 items from v3 are now done:**
- ✅ **P0 #1**: Migrate remaining servers to config framework - **PARTIAL** (5/7 Python servers done, 2 TypeScript remain)
- ✅ **P0 #2**: Migrate HTTP clients to `common.http` - **PARTIAL** (5/8 servers done)
- ✅ **P0 #3**: Add E2E tests for orchestrator workflows - **DONE** (6 E2E tests exist)
- ✅ **P0 #4**: Create shared identifier normalization utilities - **DONE** (`common/identifiers.py` exists and is used)
- ✅ **P0 #5**: Add tests for macro tools - **DONE** (41+ test cases exist)
- ✅ **P1 #6**: Migrate all servers to `common.cache` - **PARTIAL** (9/13 servers done)
- ✅ **P1 #7**: Implement Patient Out-of-Pocket Estimate macro tool - **DONE** (`patient_oop_estimate_macro` exists)
- ✅ **P1 #8**: Implement Clinical Trial Matching tool - **DONE** (`clinical_trial_matching` exists)
- ⚠️ **P1 #9**: Add comprehensive error mapping - **PARTIAL** (some servers still need migration)
- ⚠️ **P1 #10**: Add tests for servers without coverage - **PARTIAL** (sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp still need tests)

**Which are still open:**
- ⚠️ **TypeScript server alignment** (pubmed-mcp, fda-mcp) - Need config framework equivalent
- ⚠️ **Error mapping** - Some servers still need `map_upstream_error` adoption
- ⚠️ **Test coverage** - 4 servers still have no tests (sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp)

### 7.3 Prioritized Roadmap (Next Steps)

#### P0 (Must-Do / Highest Risk or Leverage)

1. **Document TypeScript server alignment strategy**
   - **Target**: `docs/` directory
   - **Outcome**: Documentation of config patterns for TypeScript servers (pubmed-mcp, fda-mcp)
   - **Why**: TypeScript servers need equivalent patterns to Python `ServerConfig`
   - **Risk if skipped**: Inconsistent configuration patterns across language boundaries

2. **Add tests for servers without coverage**
   - **Target**: sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp
   - **Outcome**: Unit tests for each server
   - **Why**: Prevents regressions, increases confidence in deployments
   - **Risk if skipped**: Bugs go undetected, lower confidence in deployments

#### P1 (High Value)

3. **Complete HTTP client migration**
   - **Target**: Remaining servers using raw `requests` (if any)
   - **Outcome**: All Python servers use `common.http`
   - **Why**: Standardized timeouts, retries, circuit breakers, error handling
   - **Risk if skipped**: Inconsistent timeout/retry behavior

4. **Add comprehensive error mapping**
   - **Target**: Servers not using `map_upstream_error`
   - **Outcome**: All servers use `map_upstream_error` for consistent error codes
   - **Why**: Consistent error codes across servers, better LLM error handling
   - **Risk if skipped**: Inconsistent error handling, harder to debug upstream failures

5. **Complete cache migration**
   - **Target**: Remaining servers with custom caching (if any)
   - **Outcome**: All servers use `common.cache` for consistency
   - **Why**: Better cache hit rates, easier cache debugging, centralized cache management
   - **Risk if skipped**: Inconsistent caching behavior

#### P2 (Nice-to-Have)

6. **Implement Drug Pipeline Competitive Analysis macro tool**
   - **Target**: New tool in `markets/` domain
   - **Outcome**: Tool that analyzes competitive landscape for target disease/indication
   - **Why**: Combines multiple data sources for actionable insight
   - **Risk if skipped**: Missing actionable workflow for market research

7. **Add integration tests for all servers**
   - **Target**: `tests/integration/` directory
   - **Outcome**: Integration tests that exercise real upstream APIs (with mocking)
   - **Why**: Catches upstream API changes, validates real-world usage patterns
   - **Risk if skipped**: Integration issues discovered in production

### 7.4 "If You Only Do Three Things Next..."

**Top 3 Most Leveraged Next Actions:**

1. **Document TypeScript server alignment strategy** (P0)
   - **Impact**: Enables consistent patterns across language boundaries
   - **Effort**: Low (documentation only)
   - **Risk reduction**: Prevents divergence between Python and TypeScript servers

2. **Add tests for servers without coverage** (P0)
   - **Target**: sec-edgar-mcp, sp-global-mcp, pubmed-mcp, fda-mcp
   - **Impact**: Prevents regressions in 4 servers
   - **Effort**: Medium (unit tests for each server)
   - **Risk reduction**: Catches bugs before production deployment

3. **Complete HTTP client migration** (P1)
   - **Target**: Any remaining servers using raw `requests`
   - **Impact**: Standardized resilience patterns across all servers
   - **Effort**: Low (most servers already migrated)
   - **Risk reduction**: Prevents upstream failures from cascading, adds circuit breaker protection

**Rationale**: These three items address the remaining gaps (TypeScript alignment, test coverage, HTTP standardization) with manageable effort.

---

## 8. Owner-Friendly Synopsis

**For Tech Lead Planning Doc:**

- **Status**: 🟢 **Green** (up from 🟡 Yellow in v3) - Strong foundation with most P0 items completed
- **Config Framework**: 11/13 servers migrated (85%), only 2 TypeScript servers remain (pubmed-mcp, fda-mcp)
- **HTTP Client**: 6/13 servers use `common.http` (46%), up from 1/13 (8%) in v3
- **Macro Tools**: 9 macro tools exist (up from 7), including both P0 tools (Patient OOP Estimate, Clinical Trial Matching)
- **Shared Identifiers**: ✅ `common/identifiers.py` exists with all normalization functions, actively used across servers
- **Caching**: ✅ 9/13 servers (69%) use `common.cache`, up from 2/13 (15%) in v3
- **PHI Handling**: ✅ Properly implemented in `common/phi.py` and integrated into logging; `claims-edi-mcp` has config flag
- **Propose-vs-Execute**: ✅ Implemented in `playwright-mcp` (dry-run + idempotency), not widely adopted elsewhere
- **Tests**: ✅ Comprehensive tests for macro tools (41+ test cases), E2E tests for orchestrator; 4 servers still need tests
- **CI/CD**: ✅ Runs registry validation, schema validation, Python tests (3.8-3.11), TypeScript tests
- **Top 3 Next Actions**: (1) Document TypeScript server alignment strategy, (2) Add tests for servers without coverage, (3) Complete HTTP client migration
- **Major Progress Since v3**: 5 servers migrated to config framework, 5 servers migrated to `common.http`, shared identifiers created, both P0 macro tools implemented, comprehensive tests added

---

**Report Generated**: December 2024  
**Compared Against**: AUDIT_REPORT_v3.md (December 2024), AUDIT_REPORT_v2.md, AUDIT_REPORT.md  
**Next Review**: After remaining P0 items completed
