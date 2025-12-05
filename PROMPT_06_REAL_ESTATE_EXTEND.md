# PROMPT 06: Extend Real Estate MCP Server

## 🎯 Objective

Fork and extend the existing `batchdata-mcp-real-estate` MCP server with free/cheap data sources. The base server wraps BatchData.io API (paid), and we'll add free sources like county assessor APIs, GIS data, and public real estate data.

**STRATEGY**: Start with batchdata-mcp, extend with free sources, prioritize high-value markets (NYC, LA, SF, Miami, Dallas).

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Discovery Findings**:
- **zellerhaus/batchdata-mcp-real-estate** exists and works
- Wraps BatchData.io API (property lookup, address enrichment)
- **LIMITATION**: Requires BatchData.io API key ($$$)
- Good foundation BUT limited to BatchData.io ecosystem

**Target Location**: `servers/real-estate/real-estate-mcp/`

**Data Sources to Add**:
- County Assessor APIs (property tax, FREE, per-county)
- County GIS APIs (parcel maps, FREE)
- Zillow GraphQL (unofficial, rate-limited, FREE)
- Realtor.com scraping (use brightdata-mcp, $$)
- Redfin Data Center (FREE, public data)
- ATTOM Data API ($49-499/month, comprehensive)

---

## ✅ Tasks

### Task 1: Fork and Study batchdata-mcp-real-estate

1. Clone: `https://github.com/zellerhaus/batchdata-mcp-real-estate.git`
2. Place in `servers/real-estate/real-estate-mcp/`
3. Study the codebase:
   - What tools does it expose?
   - How is it structured?
   - What's the MCP server implementation?
4. Install dependencies and test with BatchData.io trial (if available)
5. Document existing functionality

### Task 2: Set Up Extended Server Structure

Restructure to support multiple data sources:
```
real-estate-mcp/
├── server.py              (NEW - unified MCP server)
├── batchdata_client.py    (EXISTING - from fork)
├── county_assessor_client.py  (NEW)
├── gis_client.py          (NEW)
├── zillow_client.py       (NEW)
├── redfin_client.py       (NEW)
├── data_source_router.py  (NEW - routes to best data source)
├── requirements.txt       (UPDATE)
├── README.md              (UPDATE)
└── config/
    └── counties.json      (NEW - high-value counties config)
```

### Task 3: Identify High-Value Counties

Create `config/counties.json` with top 10-20 high-value markets:
```json
{
  "nyc": {
    "name": "New York City",
    "counties": ["New York", "Kings", "Queens", "Bronx", "Richmond"],
    "assessor_api": "https://...",
    "gis_api": "https://...",
    "priority": 1
  },
  "la": {
    "name": "Los Angeles",
    "counties": ["Los Angeles"],
    "assessor_api": "https://...",
    "gis_api": "https://...",
    "priority": 2
  }
  // ... SF, Miami, Dallas, etc.
}
```

Research and document:
- County assessor API endpoints
- GIS API endpoints
- Data availability
- API documentation

### Task 4: Build County Assessor Client

Create `county_assessor_client.py` with functions:
- `get_tax_records(address: str, county: str) -> dict`
- `get_property_assessment(parcel_id: str, county: str) -> dict`
- `get_tax_history(parcel_id: str, county: str) -> dict`

**Implementation Notes**:
- Each county has different API format
- Some require API keys, some don't
- Some have rate limits
- Handle county-specific variations

**Priority Counties** (start with these):
1. NYC (5 boroughs)
2. Los Angeles County
3. San Francisco County
4. Miami-Dade County
5. Dallas County

### Task 5: Build GIS Client

Create `gis_client.py` with functions:
- `get_parcel_info(address: str, county: str) -> dict`
- `get_parcel_map(parcel_id: str, county: str) -> dict`
- `search_parcels_by_criteria(criteria: dict, county: str) -> list`

**Implementation Notes**:
- Most counties use ArcGIS REST APIs
- Standard format but county-specific endpoints
- Returns GeoJSON or similar

### Task 6: Build Zillow Client (Optional - Rate Limited)

Create `zillow_client.py` with functions:
- `search_recent_sales(address: str, radius: int) -> list`
- `get_zestimate(zillow_id: str) -> dict`
- `get_comparable_sales(zillow_id: str) -> list`

**Implementation Notes**:
- Unofficial API (scraping or GraphQL)
- Rate-limited
- May violate ToS - use carefully
- Consider using BrightData or similar proxy service

### Task 7: Build Redfin Client

Create `redfin_client.py` with functions:
- `get_market_trends(zip_code: str) -> dict`
- `get_neighborhood_stats(city: str, state: str) -> dict`
- `get_price_history(address: str) -> dict`

**Implementation Notes**:
- Redfin Data Center is public
- No API - need to scrape or use public data exports
- Free but may have usage restrictions

### Task 8: Build Data Source Router

Create `data_source_router.py` that:
- Takes a query (e.g., "get tax records for 123 Main St, NYC")
- Determines best data source (free > paid, local > remote)
- Routes to appropriate client
- Falls back to BatchData.io if free sources fail
- Caches results

### Task 9: Extend MCP Server

Add new tools to `server.py`:

**Existing (from batchdata-mcp)**:
- `property_lookup` (address → full property data)
- `address_enrichment` (partial → complete address)

**New Tools**:
- `real_estate_get_tax_records` (address → tax records)
- `real_estate_get_parcel_info` (address → parcel data)
- `real_estate_search_recent_sales` (address/zip → recent sales)
- `real_estate_get_market_trends` (zip/city → market trends)
- `real_estate_get_agent_stats` (agent name → stats, optional)
- `real_estate_search_distressed` (location → foreclosures, optional)

### Task 10: Create Schemas

Create schema files in `schemas/`:
- `real_estate_get_tax_records.json` (input/output)
- `real_estate_get_parcel_info.json` (input/output)
- `real_estate_search_recent_sales.json` (input/output)
- `real_estate_get_market_trends.json` (input/output)

### Task 11: Add Caching Layer

Implement aggressive caching:
- County assessor data (changes annually)
- GIS data (changes infrequently)
- Market trends (update weekly)
- Recent sales (update daily)

### Task 12: Test the Server

1. Start server
2. Test each tool:
   - Tax records: Test address in NYC
   - Parcel info: Test address in LA
   - Recent sales: Test zip code
   - Market trends: Test city/state
   - Property lookup: Test with BatchData (if available)

### Task 13: Update README

Document:
- What the server does
- Setup instructions
- Data sources (free vs paid)
- County coverage
- How to add new counties
- Tool descriptions
- Example queries
- Limitations

### Task 14: Update Registry

Add entries to `registry/tools_registry.json`:
- `real_estate.property_lookup` (existing, from batchdata)
- `real_estate.address_enrichment` (existing, from batchdata)
- `real_estate.get_tax_records` (new)
- `real_estate.get_parcel_info` (new)
- `real_estate.search_recent_sales` (new)
- `real_estate.get_market_trends` (new)

Set:
- Domain: "real_estate" (new domain)
- Status: "production"
- Auth required: true (for BatchData.io, optional for free sources)
- Notes: Document county coverage and data source priorities

---

## 🔍 Reference

**BatchData MCP**: https://github.com/zellerhaus/batchdata-mcp-real-estate  
**BatchData.io API**: https://batchdata.io/  
**Redfin Data Center**: https://www.redfin.com/news/data-center/  
**County Assessor APIs**: Varies by county (research per county)

**High-Value Counties to Prioritize**:
1. New York City (5 boroughs)
2. Los Angeles County, CA
3. San Francisco County, CA
4. Miami-Dade County, FL
5. Dallas County, TX
6. Cook County, IL (Chicago)
7. Harris County, TX (Houston)
8. Maricopa County, AZ (Phoenix)
9. King County, WA (Seattle)
10. Orange County, CA

---

## 📝 Expected Output

1. **Extended MCP server** with 6+ tools
2. **Multiple data source clients** (county assessor, GIS, Zillow, Redfin)
3. **Data source router** that intelligently routes queries
4. **County configuration** for high-value markets
5. **Schema files** for all tools
6. **README** with full documentation
7. **Requirements file** with dependencies
8. **Registry updated** with all tools
9. **Working server** tested with addresses in multiple counties

---

## 🚨 Important Notes

- **County-Specific APIs**: Each county has different API format - document variations
- **Rate Limiting**: County APIs may have strict rate limits
- **Data Freshness**: Property data changes infrequently - cache aggressively
- **Legal Considerations**: Scraping may violate ToS - use official APIs when possible
- **Geographic Coverage**: Start with 5-10 high-value counties, expand iteratively
- **BatchData.io**: Keep as fallback for counties not yet supported

---

## ✅ Completion Criteria

- [ ] Forked batchdata-mcp-real-estate
- [ ] Extended server with 6+ tools
- [ ] County assessor client for 5+ counties
- [ ] GIS client implemented
- [ ] Data source router working
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Tool 1 (tax records) works in NYC
- [ ] Tool 2 (parcel info) works in LA
- [ ] Tool 3 (recent sales) works
- [ ] Tool 4 (market trends) works
- [ ] Schemas created for all tools
- [ ] README updated with documentation
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Future Enhancements (Not in This Prompt)

- **Expand County Coverage**: Add more counties iteratively
- **Agent Stats**: Integrate Realtor.com agent data
- **Distressed Properties**: Add foreclosure.com integration
- **Historical Data**: Track price changes over time
- **Investment Analysis**: ROI calculations, cap rates, etc.

---

## 🎯 Next Steps

After completion, move to `PROMPT_07_NHANES_MCP.md` or `PROMPT_08_REGISTRY_UPDATE.md`.

