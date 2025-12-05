# Tools Registry Summary

**Last Updated**: December 5, 2025  
**Registry Version**: 0.2.2  
**Total Tools**: 79

---

## Overview

This document provides a comprehensive summary of all MCP tools registered in the `innovationcenter-mcp-zoo` registry. All tools are organized by domain and include status, authentication requirements, and external source information.

---

## Statistics

### By Domain

| Domain | Count | Description |
|--------|-------|-------------|
| **clinical** | 42 | Clinical trials, medical research, patient data, healthcare research, and precision oncology tools |
| **markets** | 7 | Financial markets data, biotech markets, and market analytics |
| **pricing** | 4 | Healthcare pricing, cost transparency, and hospital rates |
| **claims** | 5 | Insurance claims processing, EDI parsing, and CMS fee schedules |
| **real_estate** | 6 | Real estate data, property lookup, tax records, and market trends |
| **misc** | 15 | External MCP servers (PubMed, FDA) and uncategorized tools |
| **Total** | **79** | |

### By Status

| Status | Count | Percentage |
|--------|-------|------------|
| **active** | 78 | 98.7% |
| **stub** | 1 | 1.3% |
| **Total** | **79** | 100% |

### Authentication Requirements

| Auth Required | Count | Percentage |
|---------------|-------|------------|
| **No Auth** | 62 | 78.5% |
| **API Key Required** | 17 | 21.5% |
| **Total** | **79** | 100% |

### Safety Levels

| Safety Level | Count | Description |
|--------------|-------|-------------|
| **low** | 73 | Public data, read-only operations |
| **medium** | 6 | Semi-sensitive data, may require authentication |

---

## Tools by Server

### 1. Clinical Trials MCP (`servers/clinical/clinical-trials-mcp/`)

**Domain**: clinical  
**Tools**: 2

1. `clinical_trials.search` - Search for clinical trials by condition, intervention, location
2. `clinical_trials.get_detail` - Retrieve detailed information about a specific clinical trial

**External Source**: https://clinicaltrials.gov/api/v2  
**Auth Required**: No

---

### 2. NHANES MCP (`servers/clinical/nhanes-mcp/`)

**Domain**: clinical  
**Tools**: 5

1. `nhanes.list_datasets` - List available NHANES datasets for a cycle
2. `nhanes.get_data` - Query NHANES data with optional filters and variable selection
3. `nhanes.get_variable_info` - Get information about a specific variable in a dataset
4. `nhanes.calculate_percentile` - Calculate percentile rank of a value for a variable
5. `nhanes.get_demographics_summary` - Get summary statistics for demographics data

**External Source**: https://www.cdc.gov/nchs/nhanes/  
**Auth Required**: No

---

### 3. BioMCP - Precision Oncology (`servers/clinical/biomcp-mcp/`)

**Domain**: clinical  
**Tools**: 35

**Core Tools (3)**:
1. `biomcp.think` - Sequential thinking tool for structured problem-solving (ALWAYS USE FIRST)
2. `biomcp.search` - Universal search across all biomedical domains with unified query language
3. `biomcp.fetch` - Retrieve detailed information for any biomedical record (auto-detects domain)

**Article Tools (2)**:
4. `biomcp.article_searcher` - Search PubMed/PubTator3 with entity recognition and cBioPortal integration
5. `biomcp.article_getter` - Fetch detailed article information (supports PMID, DOI, PMC ID)

**Trial Tools (6)**:
6. `biomcp.trial_searcher` - Search ClinicalTrials.gov with comprehensive filters
7. `biomcp.trial_getter` - Get complete trial details
8. `biomcp.trial_protocol_getter` - Get protocol information only
9. `biomcp.trial_locations_getter` - Get site locations and contacts
10. `biomcp.trial_outcomes_getter` - Get outcome measures and results
11. `biomcp.trial_references_getter` - Get trial publications

**Variant Tools (3)**:
12. `biomcp.variant_searcher` - Search MyVariant.info with clinical significance filters
13. `biomcp.variant_getter` - Get comprehensive variant details with TCGA/cBioPortal data
14. `biomcp.alphagenome_predictor` - Predict variant effects using Google DeepMind's AlphaGenome

**BioThings Tools (3)**:
15. `biomcp.gene_getter` - Get gene information from MyGene.info
16. `biomcp.disease_getter` - Get disease information from MyDisease.info
17. `biomcp.drug_getter` - Get drug/chemical information from MyChem.info

**NCI Tools (6)**:
18. `biomcp.nci_organization_searcher` - Search NCI's organization database
19. `biomcp.nci_organization_getter` - Get organization details
20. `biomcp.nci_intervention_searcher` - Search NCI's intervention database
21. `biomcp.nci_intervention_getter` - Get intervention details
22. `biomcp.nci_biomarker_searcher` - Search biomarkers used in trial eligibility
23. `biomcp.nci_disease_searcher` - Search NCI's controlled vocabulary of cancer conditions

**OpenFDA Tools (12)**:
24. `biomcp.openfda_adverse_searcher` - Search FDA adverse event reports (FAERS)
25. `biomcp.openfda_adverse_getter` - Get adverse event report details
26. `biomcp.openfda_label_searcher` - Search FDA drug product labels
27. `biomcp.openfda_label_getter` - Get drug label details
28. `biomcp.openfda_device_searcher` - Search FDA device adverse events (MAUDE)
29. `biomcp.openfda_device_getter` - Get device event details
30. `biomcp.openfda_approval_searcher` - Search FDA drug approval records
31. `biomcp.openfda_approval_getter` - Get drug approval details
32. `biomcp.openfda_recall_searcher` - Search FDA drug recall records
33. `biomcp.openfda_recall_getter` - Get drug recall details
34. `biomcp.openfda_shortage_searcher` - Search FDA drug shortage database
35. `biomcp.openfda_shortage_getter` - Get drug shortage details

**External Sources**:
- PubMed/PubTator3 (30M+ articles with entity recognition)
- ClinicalTrials.gov (500K+ trials)
- MyVariant.info (genetic variant annotations)
- cBioPortal (cancer genomics)
- OncoKB (precision oncology knowledge base)
- OpenFDA (adverse events, labels, devices, approvals)
- NCI Clinical Trials API (advanced cancer trial search)
- BioThings Suite (MyGene, MyDisease, MyChem)
- AlphaGenome API (variant effect prediction)

**Auth Required**: Mostly no auth (optional API keys for enhanced features). NCI tools and AlphaGenome require API keys.

**Key Features**:
- Precision oncology focus with genetic variant analysis
- PubTator3 entity recognition in literature
- Automatic cBioPortal integration showing mutation frequencies
- OncoKB clinical variant interpretation
- Unified query language for cross-domain searches
- Built by GenomOncology (precision oncology company)

---

### 4. Hospital Pricing MCP (`servers/pricing/hospital-prices-mcp/`)

**Domain**: pricing  
**Tools**: 4

1. `hospital_prices.search_procedure` - Search for hospital procedure prices by CPT code and location
2. `hospital_prices.get_rates` - Get hospital rate sheet for a specific hospital
3. `hospital_prices.compare` - Compare prices for a procedure across multiple facilities
4. `hospital_prices.estimate_cash` - Estimate cash price range for a procedure in a location

**External Source**: https://api.turquoise.health  
**Auth Required**: Yes (API Key)

---

### 5. Claims/EDI MCP (`servers/claims/claims-edi-mcp/`)

**Domain**: claims  
**Tools**: 5

1. `claims.parse_edi_837` - Parse EDI 837 Professional Claim file into normalized JSON
2. `claims.parse_edi_835` - Parse EDI 835 Remittance Advice file into normalized JSON
3. `claims.normalize_line_item` - Normalize a claim line item to consistent format
4. `claims.lookup_cpt_price` - Lookup CPT code price from CMS Physician Fee Schedule
5. `claims.lookup_hcpcs_price` - Lookup HCPCS code price from CMS fee schedules

**External Source**: CMS fee schedules (local cache)  
**Auth Required**: No  
**Note**: Handles PHI - ensure HIPAA compliance

---

### 6. Biotech Markets MCP (`servers/markets/biotech-markets-mcp/`)

**Domain**: markets  
**Tools**: 6

1. `biotech.search_companies` - Search for biotech companies by therapeutic area, stage, and location
2. `biotech.get_company_profile` - Get unified company profile aggregating multiple data sources
3. `biotech.get_funding_rounds` - Get funding rounds history for a company
4. `biotech.get_pipeline_drugs` - Get pipeline drugs for a company from clinical trials
5. `biotech.get_investors` - Get investors/backers for a company
6. `biotech.analyze_target_exposure` - Analyze target exposure - companies working on a specific target

**External Sources**: 
- https://clinicaltrials.gov/api/v2
- https://data.sec.gov
- https://eutils.ncbi.nlm.nih.gov

**Auth Required**: No

---

### 7. Real Estate MCP (`servers/real-estate/real-estate-mcp/`)

**Domain**: real_estate  
**Tools**: 6

1. `real_estate.property_lookup` - Lookup comprehensive property data by address
2. `real_estate.address_enrichment` - Enrich and verify a partial address
3. `real_estate.get_tax_records` - Get property tax records for an address
4. `real_estate.get_parcel_info` - Get parcel information for an address
5. `real_estate.search_recent_sales` - Search for recent property sales in a ZIP code
6. `real_estate.get_market_trends` - Get market trends for a location

**External Sources**:
- https://api.batchdata.com (requires API key)
- County Assessor APIs (free, varies by county)
- County GIS APIs (free, varies by county)
- https://www.redfin.com/news/data-center (free)

**Auth Required**: Optional (BatchData.io API key recommended)

---

### 8. PubMed MCP (`servers/misc/pubmed-mcp/`)

**Domain**: misc  
**Tools**: 5

1. `pubmed.search_articles` - Search PubMed for articles using query terms, filters, and date ranges
2. `pubmed.fetch_contents` - Retrieve detailed article information using PMIDs or search history
3. `pubmed.article_connections` - Find related articles, citations, and references for a given PMID
4. `pubmed.research_agent` - Generate structured research plans with literature search strategies
5. `pubmed.generate_chart` - Create customizable PNG charts from structured publication data

**External Source**: https://github.com/cyanheads/pubmed-mcp-server  
**API Source**: https://eutils.ncbi.nlm.nih.gov  
**Auth Required**: No (NCBI API key optional but recommended)

---

### 9. FDA MCP (`servers/misc/fda-mcp/`)

**Domain**: misc  
**Tools**: 10

#### Drug Tools (6)
1. `fda.search_drug_adverse_events` - Search FDA Adverse Event Reporting System (FAERS) data
2. `fda.search_drug_labels` - Search drug product labeling information
3. `fda.search_drug_ndc` - Query the National Drug Code (NDC) directory
4. `fda.search_drug_recalls` - Find drug recall enforcement reports
5. `fda.search_drugs_fda` - Search the Drugs@FDA database for approved products
6. `fda.search_drug_shortages` - Query current drug shortages

#### Device Tools (4)
7. `fda.search_device_510k` - Search FDA 510(k) device clearances
8. `fda.search_device_classifications` - Search FDA device classifications
9. `fda.search_device_adverse_events` - Search FDA device adverse events (MDR)
10. `fda.search_device_recalls` - Search FDA device recall enforcement reports

**External Source**: https://github.com/Augmented-Nature/OpenFDA-MCP-Server  
**API Source**: https://open.fda.gov/  
**Auth Required**: No (FDA API key optional but recommended)

---

### 10. Markets Timeseries (Stub)

**Domain**: markets  
**Tools**: 1 (stub)

1. `markets.get_timeseries` - Retrieve historical price data for financial instruments (not yet implemented)

**Status**: stub  
**Auth Required**: Yes (API key - when implemented)

---

## External Data Sources

### Public APIs (No Auth Required)
- ClinicalTrials.gov API v2
- CDC/NCHS NHANES
- NCBI E-utilities (PubMed)
- PubTator3 (entity recognition)
- MyVariant.info (genetic variants)
- cBioPortal (cancer genomics)
- OncoKB (precision oncology)
- BioThings Suite (MyGene, MyDisease, MyChem)
- NCI Clinical Trials API
- openFDA API
- AlphaGenome API (variant predictions)
- SEC EDGAR
- County Assessor APIs (various)
- County GIS APIs (various)
- Redfin Data Center

### Commercial APIs (Auth Required)
- Turquoise Health API (hospital pricing)
- BatchData.io API (real estate)

### Local/Cached Data
- CMS Physician Fee Schedule (manually downloaded)
- CMS HCPCS fee schedules (manually downloaded)
- NHANES data (downloaded on-demand and cached)

---

## Implementation Notes

### Status Definitions

- **active**: Production-ready and available for use
- **stub**: Placeholder with no real implementation yet

### Safety Levels

- **low**: Read-only operations, public data, no sensitive information
- **medium**: May access semi-sensitive data, requires authentication or handles PHI

### Authentication Types

- **api_key**: Requires API key for external service
- **oauth**: OAuth authentication (currently none)
- **null**: No authentication required

---

## Validation

The registry is validated using `scripts/validate_registry.py` which checks:

- All required fields are present
- Status values are from allowed list
- Safety level values are from allowed list
- Domain references exist in `domains_taxonomy.json`
- Schema file paths reference valid files
- Input/output schema files are valid JSON Schemas

**Last Validation**: ✅ Passed (December 5, 2025)

---

## Future Enhancements

- Complete implementation of `markets.get_timeseries` (currently stub)
- Add more real estate data sources
- Expand biotech markets with additional funding data sources
- Add more clinical research tools
- Enhance claims processing with additional EDI formats

---

## Related Documentation

- [Registry Format Documentation](./REGISTRY_FORMAT.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Domain Taxonomy](../registry/domains_taxonomy.json)
- [Tools Registry](../registry/tools_registry.json)

