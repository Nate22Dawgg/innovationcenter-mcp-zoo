# SEC EDGAR MCP Server

MCP server for accessing SEC EDGAR filings, company data, and financial information. Uses the free SEC EDGAR API (data.sec.gov) - no authentication required.

## 🎯 Overview

This server provides comprehensive access to SEC EDGAR filings and company data:

- **Company Search**: Search companies by name or ticker symbol
- **Filing Access**: Get company filings with filtering by form type and date range
- **Filing Content**: Retrieve full filing documents
- **Financial Extraction**: Extract financial data from filings (10-K, 10-Q, etc.)
- **Company Information**: Get comprehensive company data including submissions index

**Status**: Production-ready using free SEC EDGAR API

## 📋 Features

### 6 MCP Tools

1. **`sec_search_company`** - Search for companies by name or ticker symbol
2. **`sec_get_company_filings`** - Get company filings with optional filters (form type, date range)
3. **`sec_get_filing_content`** - Get content of a specific filing
4. **`sec_search_filings`** - Search filings by keyword across all companies
5. **`sec_get_company_info`** - Get comprehensive company information
6. **`sec_extract_financials`** - Extract financial data from filings

## 🚀 Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Navigate to server directory
cd servers/markets/sec-edgar-mcp

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

No API keys required - uses free SEC EDGAR API.

## 📖 Usage

### MCP Server Mode

```bash
python server.py
```

The server will run in stdio mode, ready to accept MCP protocol messages.

### CLI Mode (Testing)

```bash
# Search for a company
python server.py --tool search_company --query "Apple"

# Get company filings
python server.py --tool get_filings --company_name "Apple" --form_type "10-K" --limit 5

# Get filing content
python server.py --tool get_content --cik "0000320193" --accession_number "0000320193-24-000001"

# Get company info
python server.py --tool get_company_info --ticker "AAPL"

# Extract financials
python server.py --tool extract_financials --cik "0000320193" --accession_number "0000320193-24-000001"
```

## 🔍 Data Sources

### SEC EDGAR API

- **URL**: https://data.sec.gov
- **Auth**: None required (User-Agent header required)
- **Rate Limit**: 10 requests/second (enforced)
- **Data**: All SEC EDGAR filings, company data, financial information

### API Endpoints Used

- `https://www.sec.gov/files/company_tickers.json` - Company ticker lookup
- `https://data.sec.gov/submissions/CIK{cik}.json` - Company submissions index
- `https://data.sec.gov/files/data/{cik}/{accession_number}/{accession_number}.txt` - Filing content

## 📊 Example Queries

### Search Company

```python
{
  "query": "Apple",
  "limit": 10
}
```

### Get Company Filings

```python
{
  "company_name": "Apple Inc.",
  "form_type": "10-K",
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "limit": 5
}
```

### Get Filing Content

```python
{
  "cik": "0000320193",
  "accession_number": "0000320193-24-000001",
  "extract_financials": true
}
```

### Extract Financials

```python
{
  "cik": "0000320193",
  "accession_number": "0000320193-24-000001"
}
```

## 🏗️ Architecture

```
sec-edgar-mcp/
├── server.py              # Main MCP server with 6 tools
├── sec_edgar_client.py     # SEC EDGAR API client
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## ⚠️ Limitations

### Free Source Limitations

1. **Rate Limiting**: SEC EDGAR enforces 10 requests/second. The client automatically enforces this limit.

2. **Financial Extraction**: Current financial extraction uses pattern matching. For comprehensive financial data, consider parsing XBRL files directly.

3. **Full-Text Search**: The `sec_search_filings` tool is simplified and searches company names/descriptions. Full-text search requires downloading and parsing filing content, which can be slow.

4. **Filing Content Size**: Large filings may be truncated in previews. Full content is available via the URL.

5. **XBRL Data**: For structured financial data, XBRL files are available but require specialized parsing (not included in this server).

## 🔧 Rate Limiting

The server automatically enforces SEC EDGAR's 10 requests/second rate limit. Each API call includes a 0.11 second delay to ensure compliance.

## 📝 Common Form Types

- **10-K**: Annual report
- **10-Q**: Quarterly report
- **8-K**: Current report (material events)
- **S-1**: Registration statement (IPO)
- **DEF 14A**: Proxy statement
- **13F**: Institutional investment manager holdings
- **4**: Statement of changes in beneficial ownership

## 🧪 Testing

Test companies:
- Apple Inc. (AAPL, CIK: 0000320193)
- Microsoft Corporation (MSFT, CIK: 0000789019)
- Amazon.com Inc. (AMZN, CIK: 0001018724)
- Tesla Inc. (TSLA, CIK: 0001318605)
- Meta Platforms Inc. (META, CIK: 0001326801)

## 📝 Future Enhancements

### Potential Improvements

- [ ] XBRL parsing for structured financial data
- [ ] Full-text search across filing content
- [ ] Caching layer for frequently accessed filings
- [ ] Batch operations for multiple companies
- [ ] Historical data tracking
- [ ] Financial statement parsing (balance sheet, income statement, cash flow)
- [ ] Insider trading data extraction (Form 4)
- [ ] Institutional holdings analysis (13F)

## 🤝 Contributing

This is part of the `innovationcenter-mcp-zoo` project. See the main README for contribution guidelines.

## 📄 License

See main repository license.

## 🔗 References

- **SEC EDGAR API**: https://www.sec.gov/edgar/sec-api-documentation
- **SEC EDGAR Data**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **MCP Protocol**: https://modelcontextprotocol.io

## ⚡ Performance Notes

- Rate limiting is enforced (10 req/s)
- Large filings may take time to download
- Financial extraction is pattern-based and may miss some data
- Use specific CIKs and accession numbers for fastest access

## 🐛 Known Issues

1. **Financial Extraction**: Pattern matching may miss financial data in non-standard formats
2. **Company Name Matching**: Fuzzy matching may not find all company name variations
3. **Filing Content**: Very large filings may timeout (30s timeout configured)
4. **XBRL Data**: XBRL files are not parsed - use XBRL parsing libraries for structured data

## 📞 Support

For issues or questions, please open an issue in the main repository.

