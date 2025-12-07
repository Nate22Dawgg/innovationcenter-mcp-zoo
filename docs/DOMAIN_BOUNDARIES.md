# Domain Boundaries

This document defines the domain taxonomy for MCP servers in the innovationcenter-mcp-zoo repository and provides guidelines for scoping servers correctly.

## Domain Taxonomy

MCP servers are organized into the following domains:

### Clinical & Biomedical
**Purpose**: Clinical trials, biomedical research, healthcare data, medical literature

**Examples**:
- `biomcp-mcp`: Comprehensive biomedical research (clinical trials, variants, genes, drugs, OpenFDA)
- `clinical-trials-mcp`: ClinicalTrials.gov search and retrieval
- `nhanes-mcp`: CDC NHANES health survey data
- `pubmed-mcp`: PubMed literature search
- `fda-mcp`: OpenFDA drug and device data

**Scope**: Any server that provides tools for:
- Clinical trial data
- Biomedical research
- Medical literature
- Healthcare datasets
- Drug/device information
- Patient health data

### Markets & Financial
**Purpose**: Financial markets, company data, SEC filings, market intelligence

**Examples**:
- `biotech-markets-mcp`: Biotech company analysis with SEC, trials, publications
- `sec-edgar-mcp`: SEC EDGAR filings and company data
- `sp-global-mcp`: S&P Global market intelligence

**Scope**: Any server that provides tools for:
- Financial markets data
- Company financials
- SEC filings
- Market intelligence
- Stock prices and trading data
- Investment research

### Pricing
**Purpose**: Price transparency, fee schedules, pricing data

**Examples**:
- `hospital-prices-mcp`: Hospital price transparency via Turquoise Health

**Scope**: Any server that provides tools for:
- Healthcare pricing transparency
- Fee schedules
- Cost data
- Price comparisons

### Claims & Billing
**Purpose**: Insurance claims, EDI processing, billing codes

**Examples**:
- `claims-edi-mcp`: EDI 837/835 parsing and CMS fee schedules

**Scope**: Any server that provides tools for:
- Insurance claims processing
- EDI parsing
- Billing codes
- Payment processing
- Revenue cycle management

### Real Estate
**Purpose**: Property data, real estate markets, property values

**Examples**:
- `real-estate-mcp`: Property data via BatchData API

**Scope**: Any server that provides tools for:
- Property data
- Real estate markets
- Property values
- Assessor data
- GIS data

### Misc
**Purpose**: General-purpose tools, utilities, cross-domain functionality

**Examples**:
- `playwright-mcp`: Browser automation

**Scope**: Any server that provides:
- General-purpose tools
- Cross-domain functionality
- Utilities that don't fit into other domains
- Infrastructure tools (browsers, file systems, etc.)

## Scoping Guidelines

### Good Scoping Examples

#### ✅ Focused and Single-Purpose
```
hospital-prices-mcp
- Scope: Hospital price transparency ONLY
- Tools: Search prices, get price comparisons, fetch fee schedules
- Rationale: Single data source (Turquoise Health), single purpose
```

```
clinical-trials-mcp
- Scope: ClinicalTrials.gov data ONLY
- Tools: Search trials, get trial details, filter by criteria
- Rationale: Single data source, focused domain
```

```
sec-edgar-mcp
- Scope: SEC EDGAR filings ONLY
- Tools: Search filings, get filing content, extract company data
- Rationale: Single data source, clear boundaries
```

#### ✅ Well-Defined Domain Boundaries
```
biotech-markets-mcp
- Scope: Biotech company analysis combining multiple sources
- Tools: Company profiles (aggregates SEC, trials, publications)
- Rationale: Aggregates data but stays within biotech/markets domain
- Note: This is an aggregation server, not mixing unrelated domains
```

### Bad Scoping Examples

#### ❌ Monster Servers Mixing Domains
```
all-healthcare-mcp
- Scope: Clinical trials + hospital prices + claims + real estate
- Problem: Mixes clinical, pricing, claims, and real estate domains
- Solution: Split into separate servers per domain
```

```
everything-markets-mcp
- Scope: Stocks + real estate + clinical trials + pricing
- Problem: Combines unrelated domains (markets, real estate, clinical, pricing)
- Solution: Separate servers: markets-mcp, real-estate-mcp, clinical-trials-mcp
```

#### ❌ Unclear Boundaries
```
data-server-mcp
- Scope: "All data APIs"
- Problem: Too vague, no clear domain
- Solution: Identify the specific domain and scope accordingly
```

## When to Create a New Server vs. Add to Existing

### Create a New Server When:

1. **Different Data Source**: The new functionality uses a completely different upstream API or data source
   - Example: Adding S&P Global → new `sp-global-mcp` server

2. **Different Domain**: The new functionality belongs to a different domain category
   - Example: Adding real estate data to a clinical server → new `real-estate-mcp` server

3. **Different Auth/Config**: The new functionality requires different authentication or configuration
   - Example: Adding a paid API with different keys → consider separate server

4. **Independent Lifecycle**: The new functionality has different deployment, versioning, or maintenance needs
   - Example: Adding experimental features → separate server for isolation

5. **Different Rate Limits/Constraints**: The new functionality has significantly different rate limits or usage patterns
   - Example: High-volume API vs. low-volume API → separate servers

### Add to Existing Server When:

1. **Same Data Source**: The new functionality uses the same upstream API
   - Example: Adding new search filters to `clinical-trials-mcp` using ClinicalTrials.gov

2. **Same Domain**: The new functionality fits within the existing server's domain
   - Example: Adding drug interaction tools to `biomcp-mcp`

3. **Natural Extension**: The new functionality is a logical extension of existing tools
   - Example: Adding "get company financials" to `biotech-markets-mcp`

4. **Shared Configuration**: The new functionality uses the same authentication and configuration
   - Example: Adding endpoints from the same API provider

## Orchestration MCPs

**Orchestration MCPs** are servers that coordinate multiple domain servers rather than providing direct data access.

### Characteristics:
- **Composite Tools**: Tools that call multiple other MCP servers
- **Aggregation**: Combines results from multiple sources
- **Coordination**: Orchestrates workflows across domains
- **No Direct API Calls**: Doesn't directly call upstream APIs (or only for auth/coordination)

### Examples:

```
biotech-markets-mcp (partial orchestration)
- Aggregates data from: clinical-trials-mcp, sec-edgar-mcp, pubmed-mcp
- Provides unified company profiles
- Note: This also makes direct API calls, so it's hybrid
```

```
workflow-orchestrator-mcp (pure orchestration)
- Tool: "analyze biotech company"
  - Calls: biotech-markets-mcp for company data
  - Calls: clinical-trials-mcp for trial data
  - Calls: hospital-prices-mcp for pricing context
  - Aggregates results into unified report
```

### Guidelines for Orchestration MCPs:

1. **Clear Purpose**: The orchestration should have a clear, valuable purpose
2. **Document Dependencies**: Clearly document which servers the orchestration depends on
3. **Error Handling**: Handle partial failures gracefully (if one server fails, others can still succeed)
4. **Naming**: Consider naming with `-orchestrator` or `-aggregator` suffix to make purpose clear
5. **Domain Placement**: Place in the domain of the primary use case, or `misc` if truly cross-domain

## Domain Assignment Decision Tree

```
Start
  │
  ├─ Does it fit an existing domain?
  │   ├─ Yes → Does it use the same data source/API?
  │   │   ├─ Yes → Add to existing server
  │   │   └─ No → Create new server in same domain
  │   │
  │   └─ No → Create new server in appropriate domain
  │
  └─ Is it orchestration/composite?
      ├─ Yes → Create orchestration server
      └─ No → Follow domain assignment above
```

## Examples by Scenario

### Scenario 1: Adding New Clinical Data Source
**Question**: "I want to add clinical trial data from a new source (not ClinicalTrials.gov)"

**Answer**: 
- If it's a different API → Create new server: `{provider}-clinical-trials-mcp`
- If it complements existing → Consider adding to `clinical-trials-mcp` if same domain
- Domain: `clinical`

### Scenario 2: Adding Real Estate to Markets Server
**Question**: "Should I add real estate property data to the markets server?"

**Answer**: 
- **No** → Real estate is a different domain
- Create new server: `real-estate-mcp` in `real-estate` domain
- Real estate markets ≠ financial markets

### Scenario 3: Adding Price Comparison Across Domains
**Question**: "I want to compare hospital prices with drug prices and real estate prices"

**Answer**: 
- Create orchestration server: `price-comparison-orchestrator-mcp`
- Calls: `hospital-prices-mcp`, `{drug-pricing-mcp}`, `real-estate-mcp`
- Domain: `misc` (cross-domain orchestration)

### Scenario 4: Adding More SEC EDGAR Endpoints
**Question**: "I want to add more SEC EDGAR endpoints to the existing server"

**Answer**: 
- **Yes** → Add to existing `sec-edgar-mcp` server
- Same data source, same domain, same configuration

## Summary

- **Stay focused**: One server = one clear purpose
- **Respect domains**: Don't mix unrelated domains
- **Consider orchestration**: For cross-domain workflows, use orchestration servers
- **When in doubt**: Ask for review or create a new server (easier to merge later than split)
- **Document decisions**: Clear scope documentation helps future developers
