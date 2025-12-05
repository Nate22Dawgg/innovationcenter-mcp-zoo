# PROMPT 05: Build Biotech Markets MCP Server

## 🎯 Objective

Build an MCP server for biotech private markets, venture funding rounds, drug pipeline tracking, and preclinical/clinical analytics. This server will integrate free public APIs (ClinicalTrials.gov, SEC EDGAR) and optionally paid sources (Crunchbase).

**RECOMMENDATION**: Start with **Phase 1 (free sources only)**. Add paid sources later if ROI justifies.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Discovery Findings**:
- Highly specialized domain (no community interest yet)
- Data is proprietary/paid (Pitchbook, CB Insights, Crunchbase)
- BUT: Some free sources exist (SEC EDGAR, ClinicalTrials.gov)
- HIGH-VALUE niche for PWM/endowment clients

**Target Location**: `servers/markets/biotech-markets-mcp/`

**Data Sources (Phase 1 - Free)**:
- ClinicalTrials.gov API (drug pipeline, phase)
- SEC EDGAR API (IPO filings, S-1s, 10-Qs)
- PubMed Central (research publications → company mentions)
- Google Patents API (patent filings)

**Data Sources (Phase 2 - Paid, Optional)**:
- Crunchbase API ($29-499/month) - funding rounds
- Pitchbook API (enterprise only, $$$$)
- CB Insights API (enterprise only, $$$$)

---

## ✅ Tasks

### Task 1: Set Up Server Structure

Create in `servers/markets/biotech-markets-mcp/`:
```
biotech-markets-mcp/
├── server.py              (NEW - MCP server)
├── clinical_trials_client.py  (NEW - reuse existing or call API)
├── sec_edgar_client.py    (NEW - SEC EDGAR API)
├── pubmed_client.py       (NEW - PubMed API for company mentions)
├── patents_client.py      (NEW - Google Patents API, optional)
├── company_aggregator.py  (NEW - aggregates data from all sources)
├── requirements.txt       (NEW)
├── README.md              (NEW)
└── .env.example           (NEW - for optional API keys)
```

### Task 2: Integrate ClinicalTrials.gov API

**Option A**: Reuse existing `clinical_trials_api.py` from `servers/clinical/clinical-trials-mcp/`

**Option B**: Call ClinicalTrials.gov API directly

Create `clinical_trials_client.py` with functions:
- `get_company_trials(company_name: str) -> list`
- `get_pipeline_drugs(company_name: str) -> list`
- `get_target_exposure(target: str) -> list` (companies working on target)

**Note**: ClinicalTrials.gov API doesn't directly support company search - need to:
1. Search by sponsor name
2. Filter results
3. Extract company names from sponsor fields

### Task 3: Integrate SEC EDGAR API

Create `sec_edgar_client.py` with functions:
- `search_company_filings(company_name: str, form_type: str) -> list`
- `get_filing_content(cik: str, accession_number: str) -> dict`
- `extract_financials(filing: dict) -> dict`
- `get_ipo_filings(company_name: str) -> list` (S-1 forms)

**SEC EDGAR API**:
- Base URL: https://data.sec.gov/
- No API key required (rate-limited)
- Use `requests` with proper User-Agent header
- CIK lookup: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=

### Task 4: Integrate PubMed API (Optional but Valuable)

Create `pubmed_client.py` with functions:
- `search_company_publications(company_name: str) -> list`
- `get_publication_mentions(company_name: str, limit: int) -> list`

**PubMed API**:
- Use existing PubMed MCP server (if available) OR
- Call PubMed E-utilities API directly
- Search for company name in author affiliations

### Task 5: Build Company Aggregator

Create `company_aggregator.py` that:
- Takes company name
- Queries all data sources
- Aggregates results into unified company profile
- Handles company name variations (e.g., "Pfizer" vs "Pfizer Inc.")

### Task 6: Build MCP Server

Create `server.py` with 6 tools:

**Tool 1: `biotech_search_companies`**
- Input: `therapeutic_area` (string, optional), `stage` (string, optional), `location` (string, optional)
- Calls: Aggregate search across ClinicalTrials.gov, SEC EDGAR
- Output: List of biotech companies matching criteria

**Tool 2: `biotech_get_company_profile`**
- Input: `company_name` (string)
- Calls: `company_aggregator.get_profile()`
- Output: Unified company profile (pipeline, financials, trials)

**Tool 3: `biotech_get_funding_rounds`**
- Input: `company_name` (string)
- Calls: SEC EDGAR (S-1, 10-Q) OR Crunchbase (if available)
- Output: Funding rounds history
- **Note**: Free sources limited - document limitations

**Tool 4: `biotech_get_pipeline_drugs`**
- Input: `company_name` (string)
- Calls: ClinicalTrials.gov API
- Output: List of drugs in pipeline with phases

**Tool 5: `biotech_get_investors`**
- Input: `company_name` (string)
- Calls: SEC EDGAR (S-1, proxy statements) OR Crunchbase (if available)
- Output: List of investors/backers
- **Note**: Free sources limited - document limitations

**Tool 6: `biotech_analyze_target_exposure`**
- Input: `target` (string) - e.g., "PD-1", "HER2"
- Calls: ClinicalTrials.gov API
- Output: Companies working on target, trial phases, competitive landscape

### Task 7: Create Schemas

Create schema files in `schemas/`:
- `biotech_search_companies.json` (input)
- `biotech_search_companies_output.json` (output)
- `biotech_get_company_profile.json` (input)
- `biotech_get_company_profile_output.json` (output)
- `biotech_get_pipeline_drugs.json` (input)
- `biotech_get_pipeline_drugs_output.json` (output)
- `biotech_analyze_target_exposure.json` (input)
- `biotech_analyze_target_exposure_output.json` (output)

### Task 8: Add Caching Layer

Implement caching:
- Cache API responses for 24 hours (SEC EDGAR, ClinicalTrials.gov)
- Reduce API calls
- Faster responses
- Use SQLite or JSON files

### Task 9: Test the Server

1. Start server
2. Test each tool:
   - Search companies: therapeutic_area="oncology"
   - Get profile: company_name="Moderna"
   - Get pipeline: company_name="BioNTech"
   - Get funding: company_name="Pfizer" (may be limited)
   - Get investors: company_name="Gilead" (may be limited)
   - Analyze target: target="PD-1"

### Task 10: Update README

Document:
- What the server does
- Setup instructions
- Data sources (free vs paid)
- Tool descriptions
- Limitations of free sources
- How to add paid sources (Crunchbase, etc.)
- Example queries
- Company name matching challenges

### Task 11: Update Registry

Add entries to `registry/tools_registry.json`:
- `biotech.search_companies`
- `biotech.get_company_profile`
- `biotech.get_funding_rounds`
- `biotech.get_pipeline_drugs`
- `biotech.get_investors`
- `biotech.analyze_target_exposure`

Set:
- Domain: "markets" or new "biotech" domain
- Status: "production"
- Auth required: false (for Phase 1)
- Notes: Document data source limitations

---

## 🔍 Reference

**ClinicalTrials.gov API**: https://clinicaltrials.gov/api/v2  
**SEC EDGAR API**: https://www.sec.gov/edgar/sec-api-documentation  
**PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25497/  
**Google Patents API**: https://patents.google.com/ (unofficial, scraping)

**Example Companies for Testing**:
- Moderna (mRNA vaccines)
- BioNTech (mRNA vaccines)
- Gilead (antivirals)
- Regeneron (antibodies)
- Vertex (rare diseases)

**Example Targets for Testing**:
- PD-1 (checkpoint inhibitor)
- HER2 (breast cancer)
- EGFR (lung cancer)
- CD19 (CAR-T)

---

## 📝 Expected Output

1. **Complete MCP server** with 6 tools
2. **Multiple API clients** (ClinicalTrials.gov, SEC EDGAR, PubMed)
3. **Company aggregator** that unifies data
4. **Schema files** for all tools
5. **README** with full documentation
6. **Requirements file** with dependencies
7. **Registry updated** with all tools
8. **Working server** tested with real company names

---

## 🚨 Important Notes

- **Data Limitations**: Free sources have limitations - document clearly
- **Company Name Matching**: Company names vary - implement fuzzy matching
- **Rate Limiting**: SEC EDGAR has strict rate limits (10 requests/second)
- **Data Freshness**: Clinical trials update frequently, SEC filings less so
- **Future Paid Sources**: Design architecture to easily add Crunchbase/Pitchbook later

---

## ✅ Completion Criteria

- [ ] MCP server created with 6 tools
- [ ] ClinicalTrials.gov integration working
- [ ] SEC EDGAR integration working
- [ ] Company aggregator implemented
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Tool 1 (search) works with test query
- [ ] Tool 2 (get_profile) works with test company
- [ ] Tool 3 (get_funding) works (may return limited data)
- [ ] Tool 4 (get_pipeline) works with test company
- [ ] Tool 5 (get_investors) works (may return limited data)
- [ ] Tool 6 (analyze_target) works with test target
- [ ] Schemas created for all tools
- [ ] README updated with documentation
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Future Enhancements (Not in This Prompt)

- **Phase 2**: Add Crunchbase API integration
- **Phase 3**: Add Pitchbook/CB Insights (if budget allows)
- **Company Matching**: Improve fuzzy matching algorithm
- **Historical Data**: Track company evolution over time
- **Competitive Analysis**: Compare companies in same therapeutic area

---

## 🎯 Next Steps

After completion, move to `PROMPT_06_REAL_ESTATE_EXTEND.md` or `PROMPT_07_NHANES_MCP.md`, or work on other prompts in parallel.

