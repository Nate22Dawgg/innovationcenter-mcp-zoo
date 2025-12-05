# S&P Global MCP Server ⭐ HIGHEST PRIORITY

MCP server for accessing S&P Global Market Intelligence data including S&P Capital IQ company data, fundamentals, and earnings transcripts.

## 🎯 Overview

This MCP server provides institutional-grade financial data through S&P Global Market Intelligence:

- **S&P Capital IQ**: Company search, profiles, and comprehensive corporate intelligence
- **Company Fundamentals**: Financial statements, ratios, and key metrics
- **Earnings Transcripts**: Earnings call transcripts with full-text search

**Built by**: Kensho (S&P Global's AI Innovation Hub)  
**Official Partnership**: Anthropic + S&P Global (July 2025)  
**License**: Enterprise (requires S&P subscription)

## ⚠️ Enterprise License Required

This server requires an **active S&P Global Market Intelligence subscription**. Access is provided through the S&P Global Market Intelligence API.

**Why for MS PWM:**
- Institutional-grade financial data
- Capital IQ integration (same system MS uses)
- Built-in MCP support for Claude
- Official partnership with Anthropic

## 📋 Features

### 4 MCP Tools

1. **`sp_global_search_companies`** - Search for companies using S&P Capital IQ by name, ticker, or CIQ ID
2. **`sp_global_get_fundamentals`** - Get company fundamentals (financial statements, ratios, metrics)
3. **`sp_global_get_earnings_transcripts`** - Get earnings call transcripts for analysis
4. **`sp_global_get_company_profile`** - Get comprehensive company profile from Capital IQ

## 🚀 Setup

### Prerequisites

- Python 3.8+
- pip
- **S&P Global Market Intelligence subscription** with API access

### Installation

```bash
# Navigate to server directory
cd servers/markets/sp-global-mcp

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required: S&P Global API Key
SP_GLOBAL_API_KEY=your_api_key_here

# Optional: Custom API base URL (if different from default)
SP_GLOBAL_API_URL=https://api.spglobal.com/marketintelligence/v1
```

**Get your API key**: Contact S&P Global Market Intelligence support or visit your subscription portal.

## 📖 Usage

### MCP Server Mode

```bash
python server.py
```

The server will run in stdio mode, ready to accept MCP protocol messages.

### CLI Mode (Testing)

```bash
# Search for companies
python server.py --tool search_companies --query "Apple Inc." --country US --limit 10

# Get company fundamentals
python server.py --tool get_fundamentals --company_id CIQ123456789 --period_type Annual

# Get earnings transcripts
python server.py --tool get_transcripts --company_id CIQ123456789 --start_date 2023-01-01 --limit 5

# Get company profile
python server.py --tool get_profile --company_id CIQ123456789
```

## 🔍 Data Sources

### S&P Global Market Intelligence API

- **Official Documentation**: Available through S&P Global Market Intelligence portal
- **GitHub**: Available through S&P Global Market Intelligence (contact for access)
- **Authentication**: API key (Bearer token)
- **Rate Limits**: As per your subscription tier

### API Endpoints

The server integrates with S&P Global Market Intelligence API endpoints:
- Company search and lookup
- Fundamentals data (financial statements, ratios)
- Earnings transcripts
- Company profiles and corporate intelligence

**Note**: Actual endpoint structure depends on your S&P Global subscription. This implementation provides the framework - replace API client methods with actual endpoints based on your API documentation.

## 🏗️ Architecture

```
sp-global-mcp/
├── server.py                  # Main MCP server with 4 tools
├── sp_global_client.py        # S&P Global API client
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .env.example              # Environment variable template
```

## 📊 Example Queries

### Search Companies

```python
{
  "query": "Apple Inc.",
  "country": "US",
  "sector": "Technology",
  "limit": 10
}
```

### Get Fundamentals

```python
{
  "company_id": "CIQ123456789",
  "period_type": "Annual",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "metrics": ["Revenue", "NetIncome", "EBITDA"]
}
```

### Get Earnings Transcripts

```python
{
  "company_id": "CIQ123456789",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "limit": 10
}
```

### Get Company Profile

```python
{
  "company_id": "CIQ123456789"
}
```

## 🔧 Implementation Notes

### Current Status

This is a **framework implementation** that provides:
- ✅ Complete MCP server structure
- ✅ Tool definitions and schemas
- ✅ API client framework
- ✅ Error handling
- ✅ CLI mode for testing

### Integration Required

The `sp_global_client.py` contains stub implementations. To complete the integration:

1. **Obtain API Documentation**: Contact S&P Global Market Intelligence for official API documentation
2. **Replace API Client Methods**: Update `sp_global_client.py` with actual API endpoints and request/response formats
3. **Test Authentication**: Verify API key authentication works with your subscription
4. **Map Response Formats**: Align API responses with the defined JSON schemas

### API Client Structure

The `SPGlobalClient` class provides these methods:
- `search_companies()` - Company search
- `get_fundamentals()` - Financial fundamentals
- `get_earnings_transcripts()` - Earnings call transcripts
- `get_company_profile()` - Comprehensive company profile

Each method includes TODO comments indicating where to add actual API integration.

## 🧪 Testing

After implementing the actual API integration, test with:

**Test Companies**:
- Apple Inc. (AAPL)
- Microsoft Corporation (MSFT)
- JPMorgan Chase & Co. (JPM)
- Amazon.com Inc. (AMZN)

**Test Scenarios**:
1. Search by company name
2. Search by ticker symbol
3. Retrieve annual and quarterly fundamentals
4. Get recent earnings transcripts
5. Fetch comprehensive company profiles

## 📝 Future Enhancements

### Additional Data Sources

- [ ] Market data (real-time and historical prices)
- [ ] Credit ratings and analysis
- [ ] Industry benchmarking
- [ ] M&A transactions
- [ ] ESG (Environmental, Social, Governance) data
- [ ] Supply chain intelligence

### Advanced Features

- [ ] Bulk data export
- [ ] Custom metric calculations
- [ ] Comparative analysis across companies
- [ ] Historical data tracking
- [ ] Automated report generation

## 🔗 References

- **S&P Global Market Intelligence**: https://www.spglobal.com/marketintelligence/en/solutions/capital-iq
- **Official Partnership Announcement**: Anthropic + S&P Global (July 2025)
- **MCP Protocol**: https://modelcontextprotocol.io
- **Kensho (S&P Global's AI Innovation Hub)**: Contact S&P Global for more information

## ⚡ Performance Notes

- API responses should be cached where appropriate to reduce API calls
- Rate limiting is enforced by S&P Global based on subscription tier
- Bulk operations may require pagination handling
- Consider implementing request batching for efficiency

## 🔐 Security & Compliance

- **API Keys**: Store securely, never commit to version control
- **Data Handling**: Ensure compliance with data usage agreements
- **Rate Limiting**: Respect API rate limits to avoid service disruption
- **Enterprise License**: Ensure proper licensing for production use

## 🐛 Known Issues

1. **Stub Implementation**: API client methods are stubs - requires actual API integration
2. **Documentation**: Actual API endpoints depend on subscription - verify with S&P Global
3. **Authentication**: API authentication method may vary by subscription type

## 📞 Support

For issues or questions:
- **S&P Global Support**: Contact your S&P Global Market Intelligence account representative
- **API Documentation**: Available through S&P Global Market Intelligence portal
- **GitHub**: Available through S&P Global Market Intelligence (contact for access)

## 📄 License

Enterprise license required. See your S&P Global Market Intelligence subscription agreement for terms and conditions.

## 🌟 Priority Status

⭐ **HIGHEST PRIORITY** - This is a critical enterprise integration for institutional-grade financial data access.

