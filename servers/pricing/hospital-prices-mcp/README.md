# Hospital Pricing MCP Server

MCP server for accessing hospital price transparency data via the Turquoise Health API. Provides tools for searching, comparing, and estimating hospital procedure prices.

## 🎯 Overview

This server wraps the Turquoise Health API to provide access to hospital pricing transparency data. It enables users to:

- Search for procedure prices by CPT code and location
- Get hospital rate sheets for specific facilities
- Compare prices across multiple facilities
- Estimate cash price ranges for procedures
- **Estimate patient out-of-pocket costs using hospital pricing + CMS fee schedules** (macro tool)

## 📋 Status

✅ **Production Ready**

This server is fully implemented and ready for use. It requires a Turquoise Health API key.

## 🚀 Setup

### Prerequisites

- Python 3.8 or higher
- Turquoise Health API key (see below)

### Installation

1. **Navigate to the server directory:**
   ```bash
   cd servers/pricing/hospital-prices-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key:**
   
   Create a `.env` file in the server directory:
   ```bash
   TURQUOISE_API_KEY=your_api_key_here
   ```
   
   Or set the environment variable:
   ```bash
   export TURQUOISE_API_KEY=your_api_key_here
   ```

### Getting a Turquoise Health API Key

1. Visit [Turquoise Health](https://turquoise.health/)
2. Sign up for an account
3. Navigate to API settings to get your API key
4. **Note**: Turquoise Health offers trial access. Pricing typically ranges from $500-1000/month for production use.

## 🛠️ Usage

### Running the Server

**With MCP SDK:**
```bash
python server.py
```

**CLI Mode (for testing without MCP SDK):**
```bash
python server.py --tool search --cpt_code 99213 --location "New York, NY"
```

### Tools

#### 1. `hospital_prices_search_procedure`

Search for hospital procedure prices by CPT code and location.

**Input:**
- `cpt_code` (required): CPT or HCPCS procedure code (e.g., "99213")
- `location` (optional): Location string (city, state or zip code)
- `radius` (optional): Search radius in miles (default: 25)
- `zip_code` (optional): ZIP code for location-based search
- `state` (optional): US state code (2 letters)
- `limit` (optional): Maximum number of results (default: 50)

**Example:**
```json
{
  "cpt_code": "99213",
  "location": "New York, NY",
  "radius": 25,
  "limit": 10
}
```

**Output:**
Returns a list of hospitals with pricing information for the specified procedure.

#### 2. `hospital_prices_get_rates`

Get hospital rate sheet for a specific hospital and optional CPT codes.

**Input:**
- `hospital_id` (required): Turquoise Health hospital identifier
- `cpt_codes` (optional): List of CPT codes to filter rates

**Example:**
```json
{
  "hospital_id": "12345",
  "cpt_codes": ["99213", "27447"]
}
```

**Output:**
Returns hospital information and rate sheet for specified procedures.

#### 3. `hospital_prices_compare`

Compare prices for a procedure across multiple facilities.

**Input:**
- `cpt_code` (required): CPT or HCPCS procedure code
- `location` (required): Location string (city, state or zip code)
- `limit` (optional): Maximum number of results (default: 10)
- `zip_code` (optional): ZIP code for location-based search
- `state` (optional): US state code (2 letters)

**Example:**
```json
{
  "cpt_code": "27447",
  "location": "90210",
  "limit": 10
}
```

**Output:**
Returns a ranked list of facilities sorted by price (lowest first).

#### 4. `hospital_prices_estimate_cash`

Estimate cash price range for a procedure in a location.

**Input:**
- `cpt_code` (required): CPT or HCPCS procedure code
- `location` (required): Location string (city, state or zip code)
- `zip_code` (optional): ZIP code for location-based search
- `state` (optional): US state code (2 letters)

**Example:**
```json
{
  "cpt_code": "45378",
  "location": "San Francisco, CA"
}
```

**Output:**
Returns estimated cash price range with statistics (min, max, median, average).

#### 5. `hospital_prices_estimate_patient_out_of_pocket`

Estimate patient out-of-pocket costs for procedures at a specific hospital based on insurance benefits (hospital pricing only).

**Input:**
- `procedure_codes` (required): List of CPT/HCPCS procedure codes
- `hospital_id` (required): Turquoise Health hospital identifier
- `insurance_type` (optional): Insurance type (e.g., "PPO", "HMO", "self-pay")
- `deductible` (optional): Annual deductible amount remaining
- `coinsurance_percent` (optional): Coinsurance percentage (e.g., 20.0 for 20%)
- `copay` (optional): Fixed copay amount
- `out_of_pocket_max` (optional): Annual out-of-pocket maximum

**Output:**
Returns estimated OOP costs, assumptions, and risk flags based on hospital pricing data.

#### 6. `patient_oop_estimate_macro` ⭐ **NEW MACRO TOOL**

**High-value workflow tool** that estimates patient out-of-pocket costs using **both hospital pricing AND CMS fee schedule data**. This macro tool combines:

- **Hospital pricing data** from Turquoise Health API (negotiated rates, cash prices)
- **CMS fee schedule data** from claims-edi-mcp (allowed amounts, typical reimbursement)
- **Insurance benefit parameters** to calculate comprehensive OOP estimates

**Input:**
- `procedure_codes` (required): List of CPT/HCPCS procedure codes
- `patient_demographics` (optional): Patient demographics (age, zip_code, state)
- `facility` (optional): Facility identifier or location (hospital_id or address info)
- `insurance_plan` (optional): Insurance plan parameters (type, deductible, coinsurance, copay, OOP max, deductible_met)

**Example:**
```json
{
  "procedure_codes": ["99213", "27447"],
  "patient_demographics": {
    "zip_code": "10001",
    "state": "NY"
  },
  "facility": {
    "hospital_id": "12345"
  },
  "insurance_plan": {
    "insurance_type": "PPO",
    "deductible": 1000.0,
    "deductible_met": false,
    "coinsurance_percent": 20.0,
    "out_of_pocket_max": 5000.0
  }
}
```

**Output:**
Returns comprehensive OOP estimates with:
- `procedure_summary`: List of procedures with descriptions
- `price_components`: Breakdown of hospital pricing, CMS fee schedule, allowed amounts, plan pay, and patient pay ranges
- `assumptions`: Narrative text about deductible, coinsurance assumptions
- `risk_flags`: List of strings describing uncertainty or missing data
- `line_item_estimates`: Per-procedure OOP estimates with price sources
- `total_estimated_oop`: Total min/likely/max OOP estimates
- `data_sources`: List of data sources used

**Key Features:**
- ✅ Combines multiple data sources for more accurate estimates
- ✅ Handles missing data gracefully with risk flags
- ✅ Supports both CPT and HCPCS codes
- ✅ Calculates deductible, coinsurance, and OOP max scenarios
- ✅ Provides low/likely/high estimates for uncertainty
- ✅ Read-only: no real billing changes

**Note:** This tool requires access to both `hospital-prices-mcp` and `claims-edi-mcp` servers. CMS fee schedule data must be downloaded separately (see claims-edi-mcp documentation).

## 📊 Example CPT Codes for Testing

- **99213**: Office visit (established patient)
- **27447**: Total knee arthroplasty
- **45378**: Colonoscopy
- **70450**: CT head without contrast

## 💾 Caching

The server includes a built-in caching layer that:

- Caches API responses for 24 hours
- Uses SQLite for local storage
- Reduces API calls and costs
- Provides faster responses for repeated queries

Cache is stored in `cache.db` in the server directory. To clear the cache:

```python
from cache import Cache
cache = Cache()
cache.clear_all()  # Clear all entries
cache.clear_expired()  # Clear only expired entries
```

## 🔒 Security

- **API Key**: Never commit your API key to version control
- **Environment Variables**: Use `.env` file or environment variables
- **Rate Limiting**: The client implements rate limiting and retry logic
- **Error Handling**: All API errors are handled gracefully

## 📈 Cost Considerations

- **Turquoise Health API**: Requires subscription (~$500-1000/month)
- **Caching**: Reduces API calls and costs
- **Rate Limits**: The client respects API rate limits with exponential backoff

## 🐛 Error Handling

The server handles various error scenarios:

- Invalid CPT codes
- No results found
- API rate limiting
- Network timeouts
- Authentication failures

All errors are returned in a structured format with error messages.

## 📝 Data Freshness

- Hospital pricing data is updated regularly by Turquoise Health
- Cache TTL is set to 24 hours
- Data source is documented in all responses

## 🔮 Future Enhancements

### Option A: Local Aggregator (Future)

A future enhancement could implement a local aggregator that:

- Crawls hospital MRF (Machine-Readable File) files directly
- Parses JSON/CSV into DuckDB/SQLite
- Updates weekly via cron
- Eliminates API costs but requires more maintenance

**Effort**: 20-32 hours

### Additional Features

- Historical pricing tracking
- Insurance-specific rate lookups
- Integration with other pricing APIs
- Bulk price comparisons

## 📚 Reference

- **Turquoise Health API**: https://docs.turquoise.health/
- **CMS Hospital Price Transparency**: https://www.cms.gov/hospital-price-transparency
- **MCP Protocol**: https://modelcontextprotocol.io/

## 📄 License

See parent repository for license information.

## 🤝 Contributing

See parent repository for contribution guidelines.
