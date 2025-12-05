# PROMPT 03: Build Hospital Pricing MCP Server

## 🎯 Objective

Build an MCP server for hospital price transparency data. This server will wrap the Turquoise Health API (commercial API for hospital pricing data) or implement a local aggregator that scrapes hospital MRF (Machine-Readable File) data.

**RECOMMENDATION**: Start with **Option B (Turquoise Health API wrapper)** for faster MVP, then migrate to Option A if usage justifies cost savings.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Discovery Findings**:
- CMS provides schemas and validators BUT no query API
- Hospital MRF files are publicly available BUT scattered
- Turquoise Health has commercial API ($$$) BUT clean and fast
- Perfect use case for MCP aggregation layer

**Target Location**: `servers/pricing/hospital-pricing-mcp/`

**Existing Registry Entry**: `hospital_prices.get_rates` (status: "stub")

---

## ✅ Tasks

### Task 1: Choose Implementation Strategy

**Option A: Local Aggregator (Free, More Work)**
- Crawl hospital MRF files (Python scraper)
- Parse JSON/CSV into DuckDB/SQLite
- Build MCP query layer
- Update weekly via cron
- **Effort**: 20-32 hours

**Option B: Turquoise Health Wrapper (Paid, Faster)** ⭐ RECOMMENDED
- Subscribe to Turquoise API (~$500-1000/month)
- Build MCP wrapper
- Cache responses locally
- Much cleaner data
- **Effort**: 8-12 hours

**For this prompt, implement Option B**. Option A can be a future enhancement.

### Task 2: Get Turquoise Health API Access

1. Sign up for Turquoise Health API trial: https://turquoise.health/
2. Get API key
3. Review API documentation: https://docs.turquoise.health/
4. Understand endpoints:
   - Search procedures by CPT/HCPCS
   - Get hospital rates
   - Compare prices
   - Estimate cash prices

### Task 3: Set Up Server Structure

Create in `servers/pricing/hospital-pricing-mcp/`:
```
hospital-pricing-mcp/
├── server.py              (NEW - MCP server)
├── turquoise_client.py    (NEW - API client)
├── requirements.txt       (NEW)
├── README.md              (update existing)
└── .env.example           (NEW - API key template)
```

### Task 4: Build Turquoise API Client

Create `turquoise_client.py` with functions:
- `search_procedure_price(cpt_code, location, radius)`
- `get_hospital_rates(hospital_id, cpt_codes)`
- `compare_prices(cpt_code, location, limit)`
- `estimate_cash_price(cpt_code, location)`

Handle:
- API authentication (API key in headers)
- Rate limiting
- Error handling
- Response normalization

### Task 5: Build MCP Server

Create `server.py` with 4-5 tools:

**Tool 1: `hospital_prices_search_procedure`**
- Input: `cpt_code` (string), `location` (string, optional), `radius` (int, optional)
- Calls: `turquoise_client.search_procedure_price()`
- Output: List of hospitals with prices

**Tool 2: `hospital_prices_get_rates`**
- Input: `hospital_id` (string), `cpt_codes` (array, optional)
- Calls: `turquoise_client.get_hospital_rates()`
- Output: Hospital rate sheet

**Tool 3: `hospital_prices_compare`**
- Input: `cpt_code` (string), `location` (string), `limit` (int, default: 10)
- Calls: `turquoise_client.compare_prices()`
- Output: Ranked list of facilities by price

**Tool 4: `hospital_prices_estimate_cash`**
- Input: `cpt_code` (string), `location` (string)
- Calls: `turquoise_client.estimate_cash_price()`
- Output: Estimated cash price range

### Task 6: Create Schemas

Create/update schema files in `schemas/`:
- `hospital_prices_search.json` (input)
- `hospital_prices_output.json` (output)
- `hospital_prices_compare.json` (input)
- `hospital_prices_compare_output.json` (output)

### Task 7: Add Caching Layer (Optional but Recommended)

Implement local caching:
- Cache API responses for 24 hours
- Use SQLite or JSON files
- Reduce API calls and costs
- Faster responses for repeated queries

### Task 8: Test the Server

1. Start server with API key
2. Test each tool:
   - Search: CPT code "99213" (office visit)
   - Get rates: Hospital ID + CPT codes
   - Compare: CPT code + location
   - Estimate: CPT code + location

### Task 9: Update README

Document:
- What the server does
- Setup instructions (API key required)
- How to get Turquoise Health API key
- Tool descriptions
- Example queries
- Cost considerations
- Future: Option A (local aggregator) roadmap

### Task 10: Update Registry

Update `registry/tools_registry.json`:
- Update existing `hospital_prices.get_rates` entry
- Add new tool entries for all 4 tools
- Set status to "production"
- Mark auth_required: true
- Add auth_type: "api_key"
- Document external_source: Turquoise Health API

---

## 🔍 Reference

**Turquoise Health API**: https://docs.turquoise.health/  
**CMS Hospital Price Transparency**: https://www.cms.gov/hospital-price-transparency  
**Existing Schema**: `schemas/hospital_prices_search.json`, `schemas/hospital_prices_output.json`

**Example CPT Codes for Testing**:
- 99213: Office visit (established patient)
- 27447: Total knee arthroplasty
- 45378: Colonoscopy
- 70450: CT head without contrast

---

## 📝 Expected Output

1. **Complete MCP server** with 4 tools
2. **Turquoise API client** with proper error handling
3. **Schema files** for all tools
4. **README** with full documentation
5. **Requirements file** with dependencies
6. **Registry updated** with all tools
7. **Working server** tested with real API calls

---

## 🚨 Important Notes

- **API Key Security**: Never commit API keys. Use `.env` file and `.gitignore`
- **Rate Limiting**: Turquoise Health has rate limits - implement retry logic
- **Cost Awareness**: Document API costs in README
- **Error Handling**: Handle API errors gracefully (invalid CPT codes, no results, etc.)
- **Data Freshness**: Hospital pricing data changes - document update frequency

---

## ✅ Completion Criteria

- [ ] MCP server created with 4 tools
- [ ] Turquoise API client implemented
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Tool 1 (search) works with test CPT code
- [ ] Tool 2 (get_rates) works with test hospital
- [ ] Tool 3 (compare) works with test query
- [ ] Tool 4 (estimate) works with test query
- [ ] Schemas created/updated
- [ ] README updated with documentation
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Future Enhancements (Not in This Prompt)

- **Option A Implementation**: Local MRF scraper and aggregator
- **Additional Data Sources**: Integrate other pricing APIs
- **Historical Pricing**: Track price changes over time
- **Insurance-Specific Pricing**: Add payer-specific rate lookups

---

## 🎯 Next Steps

After completion, move to `PROMPT_04_CLAIMS_EDI_MCP.md` or work on other prompts in parallel.

