# Real Estate MCP Server

Extended MCP server for real estate data with multiple data sources. This server extends the functionality of `batchdata-mcp-real-estate` by adding free data sources including county assessor APIs, GIS data, and Redfin market trends.

## 🎯 Overview

This server provides comprehensive real estate data access through:

- **BatchData.io** (paid, comprehensive property data)
- **County Assessor APIs** (free, property tax records)
- **GIS APIs** (free, parcel information and boundaries)
- **Redfin Data Center** (free, market trends and statistics)

The server intelligently routes queries to the best available data source, prioritizing free sources over paid sources.

## 📋 Status

✅ **Production Ready** (with stub implementations for free sources)

The server is fully implemented with:
- ✅ BatchData.io integration (requires API key)
- ✅ County assessor client framework (stub implementations, ready for county-specific APIs)
- ✅ GIS client framework (stub implementations, ready for county-specific APIs)
- ✅ Redfin client framework (stub implementation, ready for data integration)
- ✅ Data source router with intelligent fallback
- ✅ Caching layer with data-type-specific TTLs
- ✅ All MCP tools registered and callable

**Note**: County-specific implementations need to be added for production use. The framework is ready and documented.

## 🚀 Setup

### Prerequisites

- Python 3.8 or higher
- BatchData.io API key (optional, for comprehensive property lookup)

### Installation

1. **Navigate to the server directory:**
   ```bash
   cd servers/real-estate/real-estate-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key (optional):**
   
   Create a `.env` file in the server directory:
   ```bash
   BATCHDATA_API_KEY=your_api_key_here
   ```
   
   Or set the environment variable:
   ```bash
   export BATCHDATA_API_KEY=your_api_key_here
   ```
   
   **Note**: The server will work without BatchData.io API key, but property lookup and address enrichment will be limited.

### Getting a BatchData.io API Key

1. Visit [BatchData.io](https://batchdata.io/)
2. Sign up for an account
3. Navigate to API settings to get your API key
4. **Note**: BatchData.io offers trial access. Pricing varies based on usage.

## 🛠️ Usage

### Running the Server

**With MCP SDK:**
```bash
python server.py
```

**CLI Mode (for testing without MCP SDK):**
```bash
python server.py --tool property_lookup --address "123 Main St, New York, NY 10001"
python server.py --tool get_tax_records --address "123 Main St" --county "New York" --state "NY"
python server.py --tool get_parcel_info --address "123 Main St" --county "New York" --state "NY"
python server.py --tool search_recent_sales --zip_code "10001" --days 90 --limit 10
python server.py --tool get_market_trends --zip_code "10001"
```

## 📊 Tools

### 1. `real_estate_property_lookup`

Lookup comprehensive property data by address using BatchData.io API.

**Input:**
- `address` (required): Full property address (e.g., "123 Main St, New York, NY 10001")
- `county` (optional): County name (helps with routing)
- `state` (optional): State abbreviation (helps with routing)

**Example:**
```json
{
  "address": "123 Main St, New York, NY 10001"
}
```

**Output:**
Returns comprehensive property data including APN, property type, estimated value, square footage, bedrooms, bathrooms, year built, and more.

### 2. `real_estate_address_enrichment`

Enrich and verify a partial address using BatchData.io API.

**Input:**
- `partial_address` (required): Partial or incomplete address

**Example:**
```json
{
  "partial_address": "123 Main St, NY"
}
```

**Output:**
Returns verified and enriched address data with standardized format.

### 3. `real_estate_get_tax_records`

Get property tax records for an address. Tries county assessor APIs first (free), falls back to BatchData.io.

**Input:**
- `address` (required): Property address
- `county` (optional): County name (required for county assessor lookup)
- `state` (optional): State abbreviation (required for county assessor lookup)

**Example:**
```json
{
  "address": "123 Main St, New York, NY 10001",
  "county": "New York",
  "state": "NY"
}
```

**Output:**
Returns tax records including assessed value, tax amount, tax year, and assessment data.

**Supported Counties:**
- New York City (5 boroughs)
- Los Angeles County, CA
- San Francisco County, CA
- Miami-Dade County, FL
- Dallas County, TX
- Cook County, IL (Chicago)
- Harris County, TX (Houston)
- Maricopa County, AZ (Phoenix)
- King County, WA (Seattle)
- Orange County, CA

**Note**: County-specific implementations are stubs. See "Adding New Counties" section below.

### 4. `real_estate_get_parcel_info`

Get parcel information for an address. Tries GIS APIs first (free), falls back to BatchData.io.

**Input:**
- `address` (required): Property address
- `county` (optional): County name (required for GIS lookup)
- `state` (optional): State abbreviation (required for GIS lookup)

**Example:**
```json
{
  "address": "123 Main St, Los Angeles, CA 90001",
  "county": "Los Angeles",
  "state": "CA"
}
```

**Output:**
Returns parcel information including parcel ID, boundary geometry (GeoJSON), and parcel attributes.

### 5. `real_estate_search_recent_sales`

Search for recent property sales in a ZIP code. Uses Redfin Data Center (free) or BatchData.io as fallback.

**Input:**
- `zip_code` (required): ZIP code to search
- `days` (optional): Number of days to look back (default: 90)
- `limit` (optional): Maximum number of results (default: 10)

**Example:**
```json
{
  "zip_code": "10001",
  "days": 90,
  "limit": 10
}
```

**Output:**
Returns list of recent sales with address, sale price, sale date, and property details.

### 6. `real_estate_get_market_trends`

Get market trends for a location. Uses Redfin Data Center (free).

**Input:**
- `zip_code` (optional): ZIP code (preferred)
- `city` (optional): City name (if no ZIP code)
- `state` (optional): State abbreviation (required if using city)

**Example:**
```json
{
  "zip_code": "10001"
}
```

or

```json
{
  "city": "New York",
  "state": "NY"
}
```

**Output:**
Returns market trends including median sale price, price per square foot, homes sold, days on market, inventory, months of supply, and year-over-year changes.

## 💾 Caching

The server includes an intelligent caching layer with data-type-specific TTLs:

- **County Assessor Data**: 365 days (changes annually)
- **GIS Data**: 30 days (changes infrequently)
- **Market Trends**: 7 days (update weekly)
- **Recent Sales**: 1 day (update daily)
- **Property Lookup**: 7 days (update weekly)

Cache is stored in `cache.db` in the server directory. To clear the cache:

```python
from cache import Cache
cache = Cache()
cache.clear_all()  # Clear all entries
cache.clear_expired()  # Clear only expired entries
cache.clear_by_type("assessor")  # Clear specific data type
```

## 🗺️ County Coverage

The server is configured for high-value markets:

1. **New York City** (5 boroughs) - NY
2. **Los Angeles County** - CA
3. **San Francisco County** - CA
4. **Miami-Dade County** - FL
5. **Dallas County** - TX
6. **Cook County** (Chicago) - IL
7. **Harris County** (Houston) - TX
8. **Maricopa County** (Phoenix) - AZ
9. **King County** (Seattle) - WA
10. **Orange County** - CA

### Adding New Counties

To add support for a new county:

1. **Add county configuration** to `config/counties.json`:
   ```json
   {
     "county_key": {
       "name": "County Name",
       "counties": ["County Name"],
       "state": "ST",
       "assessor_api": {
         "base_url": "https://...",
         "type": "web_scrape",
         "notes": "..."
       },
       "gis_api": {
         "base_url": "https://...",
         "type": "arcgis",
         "parcel_layer": "Parcels",
         "notes": "..."
       },
       "priority": 11
     }
   }
   ```

2. **Implement county-specific API calls** in:
   - `county_assessor_client.py` - Add county-specific tax record retrieval
   - `gis_client.py` - Add county-specific GIS queries

3. **Test** with addresses in the new county

## 🔄 Data Source Routing

The server intelligently routes queries:

1. **Free sources first**: County assessor → GIS → Redfin
2. **Fallback to paid**: BatchData.io if free sources fail or aren't available
3. **Caching**: All responses are cached with appropriate TTLs
4. **Error handling**: Graceful fallback if a source is unavailable

## 🔒 Security

- **API Key**: Never commit your API key to version control
- **Environment Variables**: Use `.env` file or environment variables
- **Rate Limiting**: Clients implement rate limiting and retry logic
- **Error Handling**: All API errors are handled gracefully

## 📈 Cost Considerations

- **BatchData.io API**: Requires subscription (pricing varies)
- **County Assessor APIs**: Free (public data)
- **GIS APIs**: Free (public data)
- **Redfin Data Center**: Free (public data)
- **Caching**: Reduces API calls and costs significantly

## 🐛 Error Handling

The server handles various error scenarios:

- Invalid addresses
- Unsupported counties
- API rate limiting
- Network timeouts
- Authentication failures
- Missing API keys

All errors are returned in a structured format with error messages.

## 📝 Data Freshness

- **Property Data**: Updated regularly by BatchData.io
- **Tax Records**: Updated annually by county assessors
- **GIS Data**: Updated infrequently (monthly/quarterly)
- **Market Trends**: Updated weekly by Redfin
- **Recent Sales**: Updated daily

Cache TTLs are configured to match data update frequencies.

## 🔮 Future Enhancements

### County-Specific Implementations

Each county needs specific API integration:

- **NYC**: NYC Department of Finance API
- **LA County**: LA County Assessor Portal API
- **SF**: SF Assessor-Recorder Office API
- **Miami-Dade**: Miami-Dade Property Appraiser API
- **Dallas**: Dallas Central Appraisal District API
- And more...

### Additional Features

- Historical price tracking
- Investment analysis (ROI, cap rates)
- Agent statistics integration
- Distressed property search (foreclosures)
- Zillow integration (rate-limited, unofficial)
- ATTOM Data API integration (paid, comprehensive)

## 📚 Reference

- **BatchData.io API**: https://developer.batchdata.com/
- **BatchData MCP**: https://github.com/zellerhaus/batchdata-mcp-real-estate
- **Redfin Data Center**: https://www.redfin.com/news/data-center/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **County Assessor APIs**: Varies by county (see `config/counties.json`)

## 📄 License

See parent repository for license information.

## 🤝 Contributing

See parent repository for contribution guidelines.

## 🎯 Example Queries

### Get Tax Records for NYC Property
```
Get tax records for 123 Main St, New York, NY 10001 in New York County, NY
```

### Get Parcel Info for LA Property
```
Get parcel information for 456 Sunset Blvd, Los Angeles, CA 90028 in Los Angeles County, CA
```

### Search Recent Sales
```
Find recent sales in ZIP code 10001 in the last 90 days
```

### Get Market Trends
```
Get market trends for ZIP code 90210
```

### Property Lookup
```
Lookup property at 789 Market St, San Francisco, CA 94102
```
