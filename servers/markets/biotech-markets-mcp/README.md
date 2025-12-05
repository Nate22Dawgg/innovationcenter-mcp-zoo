# Biotech Markets MCP Server

MCP server for biotech private markets, venture funding rounds, drug pipeline tracking, and preclinical/clinical analytics. Integrates free public APIs (ClinicalTrials.gov, SEC EDGAR, PubMed) and optionally paid sources (Crunchbase).

## 🎯 Overview

This server provides comprehensive biotech company intelligence by aggregating data from multiple sources:

- **ClinicalTrials.gov**: Drug pipeline, trial phases, therapeutic areas
- **SEC EDGAR**: Company filings, IPO information, financial data
- **PubMed**: Research publications, company mentions

**Current Status**: Phase 1 (free sources only)

## 📋 Features

### 6 MCP Tools

1. **`biotech_search_companies`** - Search for biotech companies by therapeutic area, stage, and location
2. **`biotech_get_company_profile`** - Get unified company profile aggregating all data sources
3. **`biotech_get_funding_rounds`** - Get funding rounds history (limited with free sources)
4. **`biotech_get_pipeline_drugs`** - Get pipeline drugs for a company
5. **`biotech_get_investors`** - Get investors/backers (limited with free sources)
6. **`biotech_analyze_target_exposure`** - Analyze competitive landscape for a target (e.g., PD-1, HER2)

## 🚀 Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Navigate to server directory
cd servers/markets/biotech-markets-mcp

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

No API keys required for Phase 1 (free sources). See `.env.example` for optional Phase 2 configuration.

## 📖 Usage

### MCP Server Mode

```bash
python server.py
```

The server will run in stdio mode, ready to accept MCP protocol messages.

### CLI Mode (Testing)

```bash
# Search companies
python server.py --tool search_companies --therapeutic_area oncology --limit 10

# Get company profile
python server.py --tool get_profile --company_name "Moderna"

# Get pipeline drugs
python server.py --tool get_pipeline --company_name "BioNTech"

# Analyze target exposure
python server.py --tool analyze_target --target "PD-1"
```

## 🔍 Data Sources

### Phase 1: Free Sources (Current)

#### ClinicalTrials.gov API
- **URL**: https://clinicaltrials.gov/api/v2
- **Auth**: None required
- **Rate Limit**: None specified (be respectful)
- **Data**: Clinical trials, drug pipelines, trial phases

#### SEC EDGAR API
- **URL**: https://data.sec.gov
- **Auth**: None required (User-Agent header required)
- **Rate Limit**: 10 requests/second
- **Data**: Company filings, IPO information, financial data

#### PubMed E-utilities API
- **URL**: https://eutils.ncbi.nlm.nih.gov/entrez/eutils
- **Auth**: None required
- **Rate Limit**: 3 requests/second recommended
- **Data**: Research publications, company mentions

### Phase 2: Paid Sources (Future)

#### Crunchbase API
- **Cost**: $29-499/month
- **Data**: Comprehensive funding rounds, investor data
- **Status**: Not yet integrated

#### Pitchbook API
- **Cost**: Enterprise only ($$$$)
- **Data**: Private market data, funding rounds
- **Status**: Not yet integrated

#### CB Insights API
- **Cost**: Enterprise only ($$$$)
- **Data**: Market intelligence, funding data
- **Status**: Not yet integrated

## ⚠️ Limitations

### Free Source Limitations

1. **Funding Rounds**: SEC EDGAR provides IPO filings (S-1) but limited historical funding data. Full funding extraction requires parsing complex documents.

2. **Investor Data**: Limited to what's available in SEC filings (proxy statements, S-1). Full investor extraction requires document parsing.

3. **Company Name Matching**: Company names vary across sources. The server uses fuzzy matching, but may miss some variations.

4. **Data Freshness**: 
   - Clinical trials update frequently
   - SEC filings update quarterly/annually
   - PubMed updates continuously

5. **Rate Limiting**: 
   - SEC EDGAR: 10 requests/second (enforced)
   - PubMed: 3 requests/second (recommended)
   - ClinicalTrials.gov: No official limit (be respectful)

## 🏗️ Architecture

```
biotech-markets-mcp/
├── server.py                  # Main MCP server with 6 tools
├── clinical_trials_client.py  # ClinicalTrials.gov API client
├── sec_edgar_client.py        # SEC EDGAR API client
├── pubmed_client.py           # PubMed API client
├── company_aggregator.py      # Aggregates data from all sources
├── cache.py                   # SQLite caching layer
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

## 📊 Example Queries

### Search Companies by Therapeutic Area

```python
# Search for oncology companies
{
  "therapeutic_area": "oncology",
  "stage": "Phase 3",
  "location": "United States",
  "limit": 20
}
```

### Get Company Profile

```python
# Get comprehensive profile for Moderna
{
  "company_name": "Moderna"
}
```

### Analyze Target Exposure

```python
# Find all companies working on PD-1
{
  "target": "PD-1"
}
```

## 🔧 Caching

The server includes a SQLite-based caching layer that:
- Caches API responses for 24 hours (configurable)
- Reduces API calls and improves performance
- Automatically expires old entries
- Cache file: `cache.db` in server directory

## 🧪 Testing

Test companies:
- Moderna (mRNA vaccines)
- BioNTech (mRNA vaccines)
- Gilead (antivirals)
- Regeneron (antibodies)
- Vertex (rare diseases)

Test targets:
- PD-1 (checkpoint inhibitor)
- HER2 (breast cancer)
- EGFR (lung cancer)
- CD19 (CAR-T)

## 📝 Future Enhancements

### Phase 2: Paid Sources
- [ ] Integrate Crunchbase API for comprehensive funding data
- [ ] Add Pitchbook integration (if budget allows)
- [ ] Add CB Insights integration (if budget allows)

### Phase 3: Advanced Features
- [ ] Improve company name fuzzy matching algorithm
- [ ] Historical data tracking (company evolution over time)
- [ ] Competitive analysis (compare companies in same therapeutic area)
- [ ] Patent tracking (Google Patents API integration)
- [ ] Financial analysis (extract and parse XBRL data from SEC filings)

## 🤝 Contributing

This is part of the `innovationcenter-mcp-zoo` project. See the main README for contribution guidelines.

## 📄 License

See main repository license.

## 🔗 References

- **ClinicalTrials.gov API**: https://clinicaltrials.gov/api/v2
- **SEC EDGAR API**: https://www.sec.gov/edgar/sec-api-documentation
- **PubMed E-utilities**: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- **MCP Protocol**: https://modelcontextprotocol.io

## ⚡ Performance Notes

- API responses are cached for 24 hours
- Rate limiting is enforced for SEC EDGAR (10 req/s) and PubMed (3 req/s)
- Company profile aggregation may take 5-10 seconds (multiple API calls)
- Use caching to improve performance for repeated queries

## 🐛 Known Issues

1. **Company Name Variations**: Some companies may not be found if name varies significantly across sources
2. **SEC Filing Parsing**: Full financial/investor extraction requires complex document parsing (simplified version implemented)
3. **PubMed XML Parsing**: Uses simplified regex parsing (full XML parsing recommended for production)

## 📞 Support

For issues or questions, please open an issue in the main repository.

