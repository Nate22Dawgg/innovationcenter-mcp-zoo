# Innovation Center MCP Zoo - QC Audit & Strategic Roadmap

**Date**: December 2025  
**Auditor**: Senior Architect & Codebase Auditor  
**Scope**: Comprehensive QC pass on robustness patterns, actionable tools, orchestration, and testing

---

## 1. Global Repo View

### 1.1 Repository Structure

**Top-level directories:**
- `common/` - Shared utilities (config, errors, HTTP, cache, validation, observability)
- `servers/` - MCP server implementations organized by domain
- `scripts/` - Helper scripts including `create_mcp_server.py` scaffolding
- `docs/` - Documentation (ARCHITECTURE.md, CONFIGURATION_PATTERNS.md, DOMAIN_BOUNDARIES.md)
- `schemas/` - JSON schemas for tool inputs/outputs (100+ files)
- `registry/` - Centralized tool registry (`tools_registry.json`, `domains_taxonomy.json`)
- `tests/` - Test suite (unit, integration, e2e, contract tests)

### 1.2 MCP Servers Inventory

**Total: 13 MCP servers across 5 domains**

#### Clinical & Biomedical (5 servers)
1. **biomcp-mcp** (`servers/clinical/biomcp-mcp/`)
   - **Tools**: ~35-40 tools
   - **Domain**: Comprehensive biomedical research (trials, variants, genes, drugs, OpenFDA)
   - **Config pattern**: ❌ **NOT using new template** (no config.py found, likely uses different pattern)
   - **Notes**: Largest server, sophisticated domain routing, unified query language

2. **clinical-trials-mcp** (`servers/clinical/clinical-trials-mcp/`)
   - **Tools**: 2 tools
   - **Domain**: ClinicalTrials.gov search and retrieval
   - **Config pattern**: ❌ **NOT using new template** (no config.py found)

3. **nhanes-mcp** (`servers/clinical/nhanes-mcp/`)
   - **Tools**: 5 tools
   - **Domain**: CDC NHANES health survey data
   - **Config pattern**: ❌ **NOT using new template** (no config.py found)

4. **pubmed-mcp** (`servers/misc/pubmed-mcp/`)
   - **Tools**: 5 tools
   - **Domain**: PubMed literature search
   - **Config pattern**: ❌ **NOT using new template** (TypeScript server)

5. **fda-mcp** (`servers/misc/fda-mcp/`)
   - **Tools**: 10 tools
   - **Domain**: OpenFDA drug and device data
   - **Config pattern**: ❌ **NOT using new template** (TypeScript server)

#### Markets & Financial (4 servers)
6. **biotech-markets-mcp** (`servers/markets/biotech-markets-mcp/`)
   - **Tools**: 6+ tools (includes dossier generation)
   - **Domain**: Biotech company analysis with SEC, trials, publications
   - **Config pattern**: ✅ **Using new template** (`BiotechMarketsConfig` extends `ServerConfig`, uses `validate_config_or_raise`)

7. **sec-edgar-mcp** (`servers/markets/sec-edgar-mcp/`)
   - **Tools**: 6 tools
   - **Domain**: SEC EDGAR filings and company data
   - **Config pattern**: ❌ **NOT using new template** (no config.py found)

8. **sp-global-mcp** (`servers/markets/sp-global-mcp/`)
   - **Tools**: 4 tools
   - **Domain**: S&P Global market intelligence
   - **Config pattern**: ❌ **NOT using new template** (no config.py found)

9. **healthcare-equities-orchestrator-mcp** (`servers/markets/healthcare-equities-orchestrator-mcp/`)
   - **Tools**: 1+ tools (cross-domain orchestration)
   - **Domain**: Cross-domain orchestration (markets + clinical)
   - **Config pattern**: ✅ **Using new template** (`HealthcareEquitiesOrchestratorConfig`)

#### Healthcare Operations (2 servers)
10. **hospital-prices-mcp** (`servers/pricing/hospital-prices-mcp/`)
    - **Tools**: 4 tools
    - **Domain**: Hospital price transparency via Turquoise Health
    - **Config pattern**: ✅ **Using new template** (`HospitalPricesConfig`, uses `validate_config_or_raise`)

11. **claims-edi-mcp** (`servers/claims/claims-edi-mcp/`)
    - **Tools**: 5 tools
    - **Domain**: EDI 837/835 parsing and CMS fee schedules
    - **Config pattern**: ✅ **Using new template** (`ClaimsEdiConfig`, uses `validate_config_or_raise`)

#### Real Estate (1 server)
12. **real-estate-mcp** (`servers/real-estate/real-estate-mcp/`)
    - **Tools**: 5+ tools
    - **Domain**: Property data via BatchData API + free sources
    - **Config pattern**: ✅ **Using new template** (`RealEstateConfig`, uses `validate_config_or_raise`)

#### Misc (1 server)
13. **playwright-mcp** (`servers/misc/playwright-mcp/`)
    - **Tools**: Multiple tools
    - **Domain**: Browser automation
    - **Config pattern**: ✅ **Using new template** (`PlaywrightServerConfig`, uses `validate_config_or_raise`)

### 1.3 Key Infrastructure Verification

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| `SERVICE_NOT_CONFIGURED` error code | ✅ **OK** | `common/errors.py:62` | Properly defined with documentation |
| `ServerConfig` base class | ✅ **OK** | `common/config.py:36` | Well-documented, supports fail-fast/fail-soft |
| `validate_config_or_raise()` function | ✅ **OK** | `common/config.py:117` | Returns `(bool, error_payload)` tuple |
| `common/__init__.py` exports | ✅ **OK** | `common/__init__.py:93-98` | Exports `ConfigIssue`, `ServerConfig`, `ConfigValidationError`, `validate_config_or_raise` |
| Template directory | ✅ **OK** | `scripts/templates/mcp-server-template/` | Complete structure with minimal stubs |
| Scaffolding script | ✅ **OK** | `scripts/create_mcp_server.py` | Prompts for server details, copies template, replaces placeholders |
| `DOMAIN_BOUNDARIES.md` | ✅ **OK** | `docs/DOMAIN_BOUNDARIES.md` | Defines domain taxonomy, scoping guidelines |
| `CONFIGURATION_PATTERNS.md` | ✅ **OK** | `docs/CONFIGURATION_PATTERNS.md` | Comprehensive guide with examples |

**Summary**: Core infrastructure is **solid and well-documented**. Template exists and is usable. However, **only 6 of 13 servers** (46%) are using the new config framework.

---

## 2. Robustness & Configuration Patterns

### 2.1 Server-by-Server Analysis

#### ✅ **biotech-markets-mcp** (Markets)
- **Config**: ✅ Uses `BiotechMarketsConfig(ServerConfig)`, validates with `validate_config_or_raise`
- **Fail-fast/fail-soft**: ✅ Supports both (env var `BIOTECH_MARKETS_FAIL_FAST`)
- **SERVICE_NOT_CONFIGURED**: ✅ Uses error payload pattern
- **HTTP client**: ⚠️ **Partial** - Uses direct `requests` calls, not `common.http` wrapper
- **Error handling**: ✅ Uses `map_upstream_error` from `common.errors`
- **Observability**: ⚠️ **Unknown** - No explicit observability decorators found

#### ✅ **hospital-prices-mcp** (Pricing)
- **Config**: ✅ Uses `HospitalPricesConfig(ServerConfig)`, validates with `validate_config_or_raise`
- **Fail-fast/fail-soft**: ✅ Supports fail-fast (default)
- **SERVICE_NOT_CONFIGURED**: ✅ Returns error payload when API key missing
- **HTTP client**: ✅ **Good** - Uses `common.http.call_upstream` wrapper
- **Error handling**: ✅ Uses `map_upstream_error`
- **Observability**: ⚠️ **Unknown** - No explicit observability decorators found

#### ✅ **claims-edi-mcp** (Claims)
- **Config**: ✅ Uses `ClaimsEdiConfig(ServerConfig)`, validates with `validate_config_or_raise`
- **Fail-fast/fail-soft**: ✅ Supports fail-fast (default)
- **SERVICE_NOT_CONFIGURED**: ✅ Uses error payload pattern
- **HTTP client**: ⚠️ **Partial** - Uses direct HTTP calls, not `common.http` wrapper
- **Error handling**: ✅ Uses `map_upstream_error`
- **Observability**: ⚠️ **Unknown** - No explicit observability decorators found

#### ✅ **real-estate-mcp** (Real Estate)
- **Config**: ✅ Uses `RealEstateConfig(ServerConfig)`, validates with `validate_config_or_raise`
- **Fail-fast/fail-soft**: ✅ Supports fail-soft (optional API key)
- **SERVICE_NOT_CONFIGURED**: ✅ Uses error payload for missing API key (non-critical)
- **HTTP client**: ⚠️ **Partial** - Uses direct HTTP calls, not `common.http` wrapper
- **Error handling**: ⚠️ **Unknown** - Need to verify error mapping
- **Observability**: ⚠️ **Unknown**

#### ✅ **healthcare-equities-orchestrator-mcp** (Orchestration)
- **Config**: ✅ Uses `HealthcareEquitiesOrchestratorConfig(ServerConfig)`, validates with `validate_config_or_raise`
- **Fail-fast/fail-soft**: ✅ Supports both
- **SERVICE_NOT_CONFIGURED**: ✅ Uses error payload pattern
- **HTTP client**: ⚠️ **Partial** - Orchestrates MCP calls, not direct HTTP
- **Error handling**: ✅ Uses `map_upstream_error`
- **Observability**: ⚠️ **Unknown**

#### ❌ **biomcp-mcp** (Clinical - Largest Server)
- **Config**: ❌ **NOT using new template** - No `config.py` found, likely uses different pattern
- **Fail-fast/fail-soft**: ❌ **Unknown** - Cannot verify without config file
- **SERVICE_NOT_CONFIGURED**: ❌ **Unknown**
- **HTTP client**: ⚠️ **Unknown** - Need to inspect implementation
- **Error handling**: ⚠️ **Unknown**
- **Observability**: ⚠️ **Unknown**

#### ❌ **clinical-trials-mcp**, **nhanes-mcp**, **sec-edgar-mcp**, **sp-global-mcp**
- **Config**: ❌ **NOT using new template** - No `config.py` files found
- **Status**: These appear to be simpler servers without config validation

### 2.2 Highest Impact Missing Robustness Patterns

1. **Inconsistent HTTP client usage** (P0)
   - Only `hospital-prices-mcp` uses `common.http.call_upstream`
   - Others use direct `requests` calls, missing retries, circuit breakers, timeouts
   - **Impact**: Brittle upstream error handling, no circuit breaker protection

2. **Missing config framework adoption** (P0)
   - 7 of 13 servers (54%) not using `ServerConfig` pattern
   - No standardized fail-fast/fail-soft behavior
   - **Impact**: Inconsistent error handling, harder to maintain

3. **Limited observability integration** (P1)
   - No evidence of `@observe_tool_call_sync` decorators in sampled servers
   - Missing metrics collection hooks
   - **Impact**: Limited visibility into tool performance and errors

4. **Inconsistent error mapping** (P1)
   - Some servers use `map_upstream_error`, others may have custom error handling
   - **Impact**: Inconsistent error codes across servers

5. **No schema validation enforcement** (P2)
   - Schemas exist in `schemas/` but validation may not be enforced at runtime
   - **Impact**: Type safety issues, runtime errors from invalid inputs

---

## 3. Actionable "Macro" Tools and Workflows

### 3.1 Existing Macro Tools

| Tool Name | Server | Description | Workflow Steps | IO Typing |
|-----------|--------|-------------|----------------|-----------|
| `generate_biotech_company_dossier` | `biotech-markets-mcp` | Comprehensive biotech company dossier | 1. Company profile lookup<br>2. Pipeline drugs from ClinicalTrials.gov<br>3. SEC filings and investors<br>4. PubMed publications<br>5. Financial timeseries<br>6. Risk flag calculation | ✅ Strong (uses schemas, structured output) |
| `refine_biotech_dossier` | `biotech-markets-mcp` | Refine existing dossier with new questions | 1. Load existing dossier<br>2. Extract insights by category<br>3. Answer new questions<br>4. Update dossier | ✅ Strong (structured input/output) |
| `generate_property_investment_brief` | `real-estate-mcp` | Property investment analysis | 1. Property lookup<br>2. Tax records<br>3. Recent sales<br>4. Market trends<br>5. Red flag calculation | ⚠️ Moderate (needs schema verification) |
| `analyze_company_across_markets_and_clinical` | `healthcare-equities-orchestrator-mcp` | Cross-domain company analysis | 1. Company identifier resolution<br>2. Financial data (biotech-markets-mcp)<br>3. SEC filings (sec-edgar-mcp)<br>4. Clinical trials (clinical-trials-mcp)<br>5. Risk assessment | ✅ Strong (uses shared identifier schemas) |
| `biomcp.think` + research workflow | `biomcp-mcp` | Sequential thinking for biomedical research | 10-step process: scoping → search → collection → quality assessment → extraction → synthesis → analysis → knowledge synthesis → reporting | ✅ Strong (structured thought process) |

### 3.2 Missing Macro Tools (Prioritized)

1. **Patient Out-of-Pocket Estimate Tool** (P0)
   - **Domain**: Pricing + Claims
   - **Workflow**: 1) Patient demographics, 2) Insurance plan lookup, 3) Procedure CPT code, 4) Hospital price lookup, 5) CMS fee schedule, 6) Deductible/coinsurance calculation, 7) Final estimate
   - **Why**: High-value use case combining pricing and claims data

2. **Clinical Trial Matching Tool** (P0)
   - **Domain**: Clinical
   - **Workflow**: 1) Patient condition/demographics, 2) Search trials, 3) Filter by eligibility, 4) Location matching, 5) Generate match report
   - **Why**: Actionable workflow vs. just "search trials"

3. **Claim Risk Flagging Tool** (P1)
   - **Domain**: Claims
   - **Workflow**: 1) Parse EDI 837, 2) Extract procedure codes, 3) Compare to CMS fee schedules, 4) Flag anomalies, 5) Generate risk report
   - **Why**: Adds value beyond just parsing

4. **Drug Pipeline Competitive Analysis** (P1)
   - **Domain**: Markets + Clinical
   - **Workflow**: 1) Target disease/indication, 2) Find all companies in space, 3) Aggregate pipeline stages, 4) Compare timelines, 5) Generate competitive landscape
   - **Why**: Combines multiple data sources for actionable insight

5. **Property Investment Portfolio Analysis** (P2)
   - **Domain**: Real Estate
   - **Workflow**: 1) List of addresses, 2) Generate briefs for each, 3) Aggregate metrics, 4) Risk assessment, 5) Portfolio summary
   - **Why**: Batch processing of existing investment brief tool

6. **Biomedical Literature Review Generator** (P2)
   - **Domain**: Clinical
   - **Workflow**: 1) Research question, 2) PubMed search, 3) Article retrieval, 4) Key finding extraction, 5) Synthesis report
   - **Why**: Automates common research workflow

7. **Hospital Price Comparison Report** (P2)
   - **Domain**: Pricing
   - **Workflow**: 1) Procedure code, 2) Geographic area, 3) Price lookup across hospitals, 4) Statistical analysis, 5) Recommendation report
   - **Why**: Adds analysis to existing comparison tool

8. **SEC Filing Trend Analysis** (P2)
   - **Domain**: Markets
   - **Workflow**: 1) Company identifier, 2) Historical filings, 3) Extract key metrics, 4) Trend analysis, 5) Anomaly detection
   - **Why**: Adds intelligence to raw filing data

9. **Cross-Domain Drug Safety Analysis** (P2)
   - **Domain**: Clinical + Markets
   - **Workflow**: 1) Drug name, 2) FDA adverse events, 3) Clinical trial safety data, 4) Market impact analysis, 5) Risk assessment
   - **Why**: Combines FDA, trials, and market data

10. **Real Estate Market Trend Analysis** (P2)
    - **Domain**: Real Estate
    - **Workflow**: 1) Geographic area, 2) Recent sales aggregation, 3) Price trend calculation, 4) Market forecast, 5) Investment recommendation
    - **Why**: Adds predictive analytics to existing data

---

## 4. Cross-MCP Orchestration & Shared Identifiers

### 4.1 Existing Orchestration

**✅ `healthcare-equities-orchestrator-mcp`**
- **Purpose**: Orchestrates biotech-markets-mcp, sec-edgar-mcp, and clinical-trials-mcp
- **Tool**: `analyze_company_across_markets_and_clinical`
- **Implementation**: Uses `MCPOrchestratorClient` to coordinate calls
- **Status**: ✅ **Well-implemented** - Uses shared identifier schemas

### 4.2 Shared Identifier Schemas

**✅ Found in `schemas/` directory:**
- `ticker_identifier.json` - Stock ticker with exchange, ISIN, CUSIP
- `sec_identifier.json` - SEC CIK and accession numbers
- `clinical_trial_identifier.json` - NCT ID format
- `address.json` - Normalized address representation
- `healthcare_equities_analyze_company.json` - Company identifier (ticker/name/CIK)

**✅ Consistency Check:**
- Ticker format: Consistent pattern `^[A-Z0-9]{1,5}$` across schemas
- CIK format: Consistent `^\\d{10}$` pattern (10-digit zero-padded)
- NCT ID: Standard format in clinical trial schemas
- Address: Normalized structure with street, city, state, zip

**⚠️ Potential Issues:**
1. **Company name normalization** - No shared schema for name normalization/matching
2. **Drug identifier** - No shared schema for drug names/NDC codes across clinical and markets
3. **CPT/HCPCS codes** - Used in claims and pricing but no shared schema found
4. **NPI (National Provider Identifier)** - Used in claims but no shared schema found

### 4.3 Identifier Inconsistencies

**⚠️ Gaps that could make cross-MCP workflows brittle:**

1. **Company Name Matching**
   - `biotech-markets-mcp` has `_normalize_company_name()` function
   - No shared utility or schema for this
   - **Risk**: Different servers may normalize differently

2. **Drug Name Variations**
   - Clinical trials use drug names, markets may use different formats
   - No shared drug identifier schema
   - **Risk**: Matching failures across domains

3. **Geographic Identifiers**
   - Real estate uses addresses, clinical trials use location strings
   - No shared geographic normalization
   - **Risk**: Location-based matching failures

4. **Provider Identifiers**
   - Claims use NPI, hospital pricing may use different IDs
   - No shared provider identifier schema
   - **Risk**: Cannot link claims to pricing data

---

## 5. Caching, Artifacts, and Tests

### 5.1 Caching Infrastructure

**✅ Shared Cache Utility**
- **Location**: `common/cache.py`
- **Implementation**: In-memory cache with TTL support
- **Features**: `get_cache()`, `build_cache_key()`, `build_cache_key_simple()`
- **Status**: ✅ **Available and documented**

**Usage Across Servers:**
- ✅ `biotech-markets-mcp` - Uses `get_cache()` for dossier generation
- ✅ `hospital-prices-mcp` - Uses caching (TTL configurable)
- ✅ `real-estate-mcp` - Uses `get_cache()` for property lookups
- ⚠️ Other servers - Unknown usage (need verification)

**Derived Artifacts:**
- ✅ `biotech-markets-mcp` - Has `artifact_store.py` for storing dossiers
- ⚠️ Other servers - No evidence of artifact storage

### 5.2 Testing Coverage

**Test Structure:**
- `tests/unit/` - Unit tests for individual servers
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests
- `tests/contract/` - API contract tests
- `tests/schema/` - Schema validation tests

**Server-by-Server Test Status:**

| Server | Unit Tests | Integration Tests | E2E Tests | Notes |
|--------|-----------|-------------------|-----------|-------|
| `biotech-markets-mcp` | ✅ `test_biotech_markets.py` | ❌ | ❌ | Basic unit tests |
| `hospital-prices-mcp` | ✅ `test_hospital_pricing.py` | ❌ | ❌ | Basic unit tests |
| `claims-edi-mcp` | ✅ `test_claims_edi.py` | ❌ | ❌ | Basic unit tests |
| `real-estate-mcp` | ✅ `test_real_estate.py` | ❌ | ❌ | Basic unit tests |
| `clinical-trials-mcp` | ✅ `test_clinical_trials.py` | ❌ | ✅ `test_e2e_clinical_trials.py` | Has E2E tests |
| `nhanes-mcp` | ✅ `test_nhanes.py` | ❌ | ❌ | Basic unit tests |
| `biomcp-mcp` | ✅ Extensive (`tests/tdd/`) | ✅ | ✅ | **Best test coverage** |
| `healthcare-equities-orchestrator-mcp` | ✅ `test_orchestrator.py` | ❌ | ❌ | Tests orchestration logic |
| `fda-mcp` | ✅ `test_fda.py` | ❌ | ❌ | Basic unit tests |
| `pubmed-mcp` | ✅ `test_pubmed.py` | ❌ | ❌ | Basic unit tests |

**Test Gaps:**
1. **Integration tests** - Most servers lack integration tests that exercise real upstream APIs
2. **E2E tests** - Only `clinical-trials-mcp` and `biomcp-mcp` have E2E tests
3. **Macro tool tests** - Dossier generation and investment brief tools may not have comprehensive tests
4. **Orchestration tests** - Limited tests for cross-MCP workflows
5. **Error scenario tests** - Need more tests for SERVICE_NOT_CONFIGURED, upstream failures

---

## 6. QC Summary & "What Next" Roadmap

### 6.1 QC Scorecard

| Category | Status | Key Notes |
|----------|--------|-----------|
| **Config & fail-soft/fail-fast** | 🟡 **Yellow** | 6/13 servers (46%) using new framework. Template exists but adoption incomplete. |
| **Standardized HTTP + error handling** | 🟡 **Yellow** | Only `hospital-prices-mcp` uses `common.http`. Others use direct `requests`. Error mapping inconsistent. |
| **Actionable workflow tools** | 🟢 **Green** | 5 macro tools exist (dossiers, investment briefs, orchestration). Good foundation. |
| **Cross-MCP orchestration** | 🟢 **Green** | `healthcare-equities-orchestrator-mcp` demonstrates pattern. Shared identifier schemas exist. |
| **Caching / artifacts** | 🟢 **Green** | Shared cache utility available. Some servers use it. Artifact storage in biotech-markets. |
| **Tests & CI around MCPs** | 🟡 **Yellow** | Unit tests exist for most servers. Integration/E2E tests sparse. `biomcp-mcp` has best coverage. |

### 6.2 Prioritized Roadmap (Next 8-12 Steps)

#### P0 - Critical (Must Do)

1. **Migrate remaining servers to config framework** (6-8 hours)
   - **Touches**: `biomcp-mcp`, `clinical-trials-mcp`, `nhanes-mcp`, `sec-edgar-mcp`, `sp-global-mcp`
   - **Why**: Standardizes error handling, enables fail-fast/fail-soft patterns, improves maintainability
   - **Priority**: P0

2. **Standardize HTTP client usage across all servers** (8-10 hours)
   - **Touches**: `biotech-markets-mcp`, `claims-edi-mcp`, `real-estate-mcp`, others using direct `requests`
   - **Why**: Enables retries, circuit breakers, consistent error mapping, better observability
   - **Priority**: P0

3. **Implement Patient Out-of-Pocket Estimate macro tool** (12-16 hours)
   - **Touches**: New tool in `pricing/` or `claims/` domain, orchestrates hospital-prices + claims-edi
   - **Why**: High-value actionable workflow combining pricing and claims data
   - **Priority**: P0

4. **Add integration tests for all servers** (10-12 hours)
   - **Touches**: `tests/integration/` directory, all server directories
   - **Why**: Catches upstream API changes, validates real-world usage patterns
   - **Priority**: P0

#### P1 - High Value (Should Do)

5. **Implement Clinical Trial Matching macro tool** (10-12 hours)
   - **Touches**: New tool in `clinical/` domain, extends clinical-trials-mcp
   - **Why**: Actionable workflow vs. primitive search, high user value
   - **Priority**: P1

6. **Create shared identifier normalization utilities** (6-8 hours)
   - **Touches**: `common/identifiers.py`, update schemas, update servers
   - **Why**: Prevents brittle cross-MCP workflows, enables better orchestration
   - **Priority**: P1

7. **Add observability decorators to all tools** (8-10 hours)
   - **Touches**: All server `server.py` files, tool implementations
   - **Why**: Enables metrics collection, better error tracking, performance monitoring
   - **Priority**: P1

8. **Implement Claim Risk Flagging macro tool** (8-10 hours)
   - **Touches**: New tool in `claims/` domain, extends claims-edi-mcp
   - **Why**: Adds intelligence to claims processing, actionable insights
   - **Priority**: P1

9. **Add E2E tests for macro tools** (6-8 hours)
   - **Touches**: `tests/e2e/` directory, test dossier generation, investment briefs
   - **Why**: Validates end-to-end workflows, catches integration issues
   - **Priority**: P1

#### P2 - Nice to Have (Consider)

10. **Implement Drug Pipeline Competitive Analysis macro tool** (12-16 hours)
    - **Touches**: New tool in `markets/` domain, orchestrates multiple sources
    - **Why**: Combines markets and clinical data for actionable insights
    - **Priority**: P2

11. **Create shared artifact storage layer** (8-10 hours)
    - **Touches**: `common/artifacts.py`, update servers using artifacts
    - **Why**: Standardizes artifact storage, enables cross-server artifact sharing
    - **Priority**: P2

12. **Add schema validation enforcement at runtime** (6-8 hours)
    - **Touches**: All server `server.py` files, use `validate_tool_input`/`validate_tool_output`
    - **Why**: Type safety, catches errors early, better error messages
    - **Priority**: P2

### 6.3 Risks & Gotchas

#### High Priority Risks

1. **PHI Handling** (Claims domain)
   - **Risk**: EDI 837/835 files contain PHI (patient health information)
   - **Current**: `claims-edi-mcp` has `enable_phi_redaction` config option
   - **Action**: Verify PHI redaction is working correctly, audit logging

2. **Brittle Upstream Dependencies**
   - **Risk**: Many servers depend on free public APIs (ClinicalTrials.gov, SEC EDGAR, PubMed)
   - **Current**: No circuit breakers in most servers, limited retry logic
   - **Action**: Migrate to `common.http` for automatic retries and circuit breakers

3. **Inconsistent Identifier Schemas**
   - **Risk**: Company names, drug names, addresses normalized differently across servers
   - **Current**: Some shared schemas exist but no normalization utilities
   - **Action**: Create `common/identifiers.py` with shared normalization functions

4. **TypeScript/JavaScript Servers**
   - **Risk**: `pubmed-mcp` and `fda-mcp` are TypeScript, may not follow Python patterns
   - **Current**: Cannot use Python `common/` utilities
   - **Action**: Document patterns for non-Python servers, consider porting or creating JS equivalents

5. **Large Server Complexity** (`biomcp-mcp`)
   - **Risk**: 35+ tools, complex domain routing, may be harder to migrate
   - **Current**: Not using new config framework
   - **Action**: Prioritize migration, may need phased approach

#### Medium Priority Risks

6. **Cache Invalidation**
   - **Risk**: In-memory cache doesn't persist across restarts, no distributed cache
   - **Current**: `common/cache.py` is in-memory only
   - **Action**: Document cache TTL best practices, consider Redis for production

7. **Rate Limiting**
   - **Risk**: Free APIs have rate limits, no consistent rate limiting across servers
   - **Current**: Some servers may hit rate limits
   - **Action**: Use `common/rate_limit.py` utilities, add rate limiting to all servers

8. **Schema Drift**
   - **Risk**: Upstream APIs may change, breaking tool schemas
   - **Current**: Schemas in `schemas/` directory but may not be validated at runtime
   - **Action**: Add schema validation, version schemas, add contract tests

---

## Summary

**Overall Assessment**: The repository has **solid foundations** with good infrastructure (config framework, error handling, caching, schemas) and **excellent examples** of macro tools and orchestration. However, **adoption is incomplete** - only 46% of servers use the new config framework, and HTTP client standardization is limited.

**Key Strengths:**
- ✅ Robust config framework with fail-fast/fail-soft support
- ✅ Good macro tool examples (dossiers, investment briefs)
- ✅ Cross-MCP orchestration pattern demonstrated
- ✅ Shared identifier schemas
- ✅ Comprehensive test infrastructure (though coverage varies)

**Key Weaknesses:**
- ❌ Incomplete adoption of config framework (54% of servers)
- ❌ Inconsistent HTTP client usage (only 1 server uses `common.http`)
- ⚠️ Limited integration/E2E test coverage
- ⚠️ Missing shared identifier normalization utilities
- ⚠️ Limited observability integration

**Recommended Focus**: Prioritize P0 items (config migration, HTTP standardization, integration tests) to establish consistent robustness patterns across all servers before adding new macro tools.

