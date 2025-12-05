# PROMPT 08: Update Registry with All Servers

## 🎯 Objective

Consolidate and update the `registry/tools_registry.json` file with all MCP servers and tools built in previous prompts. Ensure consistency, completeness, and proper categorization.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Registry File**: `registry/tools_registry.json`

**Expected Servers** (from previous prompts):
1. **PubMed MCP** (PROMPT_01) - `servers/misc/pubmed-mcp/`
2. **FDA MCP** (PROMPT_01) - `servers/misc/fda-mcp/`
3. **Clinical Trials MCP** (PROMPT_02) - `servers/clinical/clinical-trials-mcp/`
4. **Hospital Pricing MCP** (PROMPT_03) - `servers/pricing/hospital-pricing-mcp/`
5. **Claims/EDI MCP** (PROMPT_04) - `servers/claims/claims-edi-mcp/`
6. **Biotech Markets MCP** (PROMPT_05) - `servers/markets/biotech-markets-mcp/`
7. **Real Estate MCP** (PROMPT_06) - `servers/real-estate/real-estate-mcp/`
8. **NHANES MCP** (PROMPT_07) - `servers/clinical/nhanes-mcp/`

**Existing Registry**: Already has some entries (clinical_trials, markets, hospital_prices)

---

## ✅ Tasks

### Task 1: Audit Existing Registry

1. Read current `registry/tools_registry.json`
2. Identify existing entries
3. Check which servers are already documented
4. Identify gaps and inconsistencies
5. Note any entries that need status updates (e.g., "stub" → "production")

### Task 2: Inspect Each Server Directory

For each server, verify:
1. Server exists and is built
2. What tools it exposes (check server.py or README)
3. What schemas exist (check schemas/ directory)
4. What domain it belongs to
5. Auth requirements
6. Status (production, experimental, stub)

**Servers to Check**:
- `servers/misc/pubmed-mcp/`
- `servers/misc/fda-mcp/`
- `servers/clinical/clinical-trials-mcp/`
- `servers/pricing/hospital-pricing-mcp/`
- `servers/claims/claims-edi-mcp/`
- `servers/markets/biotech-markets-mcp/`
- `servers/real-estate/real-estate-mcp/`
- `servers/clinical/nhanes-mcp/`

### Task 3: Update Domain Taxonomy (If Needed)

Check `registry/domains_taxonomy.json`:
- Ensure all domains are defined
- Add new domains if needed (e.g., "claims", "real_estate", "biotech")
- Verify domain hierarchy is correct

### Task 4: Create/Update Registry Entries

For each server, create registry entries following this format:

```json
{
  "id": "domain.tool_name",
  "name": "Human-Readable Tool Name",
  "description": "What the tool does",
  "domain": "domain_name",
  "status": "production" | "experimental" | "stub",
  "safety_level": "low" | "medium" | "high",
  "auth_required": true | false,
  "auth_type": "api_key" | "oauth" | null,
  "mcp_server_path": "servers/domain/server-name",
  "input_schema": "schemas/tool_input.json",
  "output_schema": "schemas/tool_output.json",
  "capabilities": ["search", "filter", "pagination"],
  "tags": ["tag1", "tag2"],
  "external_source": "https://api.example.com",
  "notes": "Additional notes or limitations"
}
```

### Task 5: Organize by Domain

Group tools by domain in the registry:
- **clinical**: clinical_trials, nhanes, pubmed (if medical)
- **markets**: markets_timeseries, biotech_markets
- **pricing**: hospital_prices
- **claims**: claims_edi
- **real_estate**: real_estate
- **misc**: pubmed (if general), fda

### Task 6: Verify Schema Files Exist

For each tool entry:
1. Check that `input_schema` file exists in `schemas/`
2. Check that `output_schema` file exists in `schemas/`
3. If missing, note in registry or create placeholder schemas

### Task 7: Update Metadata

Update registry-level metadata:
- `version`: Increment if major changes
- `last_updated`: Set to current date
- Add any new fields if needed

### Task 8: Validate Registry

Run validation script:
```bash
python scripts/validate_registry.py
```

Fix any validation errors:
- Missing required fields
- Invalid domain references
- Missing schema files
- Invalid status values
- etc.

### Task 9: Create Registry Summary

Create a summary document or update README with:
- Total number of tools
- Tools by domain
- Tools by status
- Tools requiring auth
- External data sources

### Task 10: Document Any Gaps

If any servers are missing or incomplete:
- Document which servers are missing
- Note what needs to be built
- Create TODO list for future work

---

## 📝 Expected Registry Structure

```json
{
  "version": "0.2.0",
  "last_updated": "2024-01-15T00:00:00Z",
  "tools": [
    // Clinical domain
    { "id": "clinical_trials.search", ... },
    { "id": "clinical_trials.get_detail", ... },
    { "id": "nhanes.list_datasets", ... },
    { "id": "nhanes.get_data", ... },
    { "id": "pubmed.search", ... },
    
    // Markets domain
    { "id": "markets.get_timeseries", ... },
    { "id": "biotech.search_companies", ... },
    { "id": "biotech.get_company_profile", ... },
    
    // Pricing domain
    { "id": "hospital_prices.search_procedure", ... },
    { "id": "hospital_prices.get_rates", ... },
    
    // Claims domain
    { "id": "claims.parse_edi_837", ... },
    { "id": "claims.parse_edi_835", ... },
    
    // Real Estate domain
    { "id": "real_estate.property_lookup", ... },
    { "id": "real_estate.get_tax_records", ... },
    
    // FDA/Misc
    { "id": "fda.search_drugs", ... },
    { "id": "fda.get_recall", ... }
  ]
}
```

---

## 🔍 Reference

**Existing Registry**: `registry/tools_registry.json`  
**Domain Taxonomy**: `registry/domains_taxonomy.json`  
**Validation Script**: `scripts/validate_registry.py`  
**Registry Format Docs**: `docs/REGISTRY_FORMAT.md`

**Registry Field Definitions**:
- `id`: Unique identifier (domain.tool_name)
- `status`: "production" (ready), "experimental" (testing), "stub" (not implemented)
- `safety_level`: "low" (public data), "medium" (sensitive), "high" (restricted)
- `auth_required`: Whether tool requires authentication
- `mcp_server_path`: Relative path to server directory
- `input_schema`/`output_schema`: Relative paths to JSON schema files

---

## ✅ Completion Criteria

- [ ] All 8 servers documented in registry
- [ ] All tools from each server have registry entries
- [ ] Domain taxonomy updated (if needed)
- [ ] All schema file paths are correct
- [ ] All status fields are accurate ("production" for completed servers)
- [ ] Auth requirements documented correctly
- [ ] External sources documented
- [ ] Validation script passes: `python scripts/validate_registry.py`
- [ ] Registry is well-organized and consistent
- [ ] README or summary document updated

---

## 🚨 Important Notes

- **Consistency**: Use consistent naming conventions (snake_case for IDs)
- **Completeness**: Every tool should have a registry entry
- **Accuracy**: Verify all paths, schemas, and metadata are correct
- **Status Updates**: Update status from "stub"/"experimental" to "production" for completed servers
- **Schema Files**: Ensure all referenced schema files exist

---

## 🎯 Next Steps

After completion:
1. **Test Integration**: Verify all servers can be loaded from registry
2. **Documentation**: Update main README with complete tool list
3. **CI/CD**: Consider adding registry validation to CI pipeline
4. **Future**: Continue adding new servers and updating registry

---

## 📊 Expected Final Count

**Total Tools**: ~30-40 tools across 8 servers

**By Domain**:
- Clinical: ~10-12 tools
- Markets: ~8-10 tools
- Pricing: ~4-5 tools
- Claims: ~5 tools
- Real Estate: ~6-8 tools
- Misc: ~3-5 tools

