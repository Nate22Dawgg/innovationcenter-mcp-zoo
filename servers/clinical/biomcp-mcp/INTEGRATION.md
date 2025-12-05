# BioMCP Integration

**Source**: Cloned from [genomoncology/biomcp](https://github.com/genomoncology/biomcp)  
**License**: MIT  
**Status**: Production-ready

## Overview

BioMCP is an open-source Model Context Protocol (MCP) server designed specifically for precision oncology and biomedical research. It provides comprehensive access to specialized biomedical databases with 35 specialized tools.

## Key Features

### Data Sources

- **PubMed/PubTator3** - 30M+ articles with entity recognition for genes, diseases, drugs, and variants
- **ClinicalTrials.gov** - 500K+ trials searchable by condition, location, phase, and eligibility
- **MyVariant.info** - Comprehensive genetic variant annotations with clinical significance
- **cBioPortal** - Cancer genomics data automatically integrated with searches
- **OncoKB** - Precision oncology knowledge base for clinical variant interpretation
- **OpenFDA** - Adverse events, drug labels, device events, approvals, recalls, shortages
- **NCI Clinical Trials API** - Advanced cancer trial search with biomarkers and prior therapies
- **BioThings Suite** - MyGene.info, MyDisease.info, MyChem.info

### Unique Capabilities

Unlike other MCPs in this zoo:

1. **Precision Oncology Focus** - Specialized for cancer genomics and precision medicine
2. **Entity Recognition** - PubTator3 provides automatic annotation of genes, diseases, drugs, variants in literature
3. **Variant Analysis** - Comprehensive genetic variant annotations from MyVariant.info
4. **Cancer Genomics** - Automatic cBioPortal integration showing mutation frequencies across cancer studies
5. **Clinical Interpretation** - OncoKB provides therapeutic implications and FDA-approved treatments
6. **Unified Query Language** - Cross-domain searches with field syntax (e.g., `gene:BRAF AND disease:melanoma`)

## Tools Provided

BioMCP provides **35 specialized tools** organized into:

- **Core Tools (3)**: `search`, `fetch`, `think`
- **Article Tools (2)**: `article_searcher`, `article_getter`
- **Trial Tools (6)**: Search and detail retrieval for ClinicalTrials.gov and NCI
- **Variant Tools (3)**: Variant search, retrieval, and AlphaGenome predictions
- **BioThings Tools (3)**: Gene, disease, and drug information
- **NCI Tools (6)**: Organization, intervention, biomarker, and disease searches
- **OpenFDA Tools (12)**: Adverse events, labels, devices, approvals, recalls, shortages

## Comparison with Existing MCPs

### PubMed MCP (`servers/misc/pubmed-mcp/`)
- **Overlap**: Both access PubMed
- **Difference**: BioMCP adds PubTator3 entity recognition, cBioPortal integration, and unified cross-domain search

### ClinicalTrials MCP (`servers/clinical/clinical-trials-mcp/`)
- **Overlap**: Both access ClinicalTrials.gov
- **Difference**: BioMCP adds NCI API support, advanced biomarker searches, and disease synonym expansion

### FDA MCP (`servers/misc/fda-mcp/`)
- **Overlap**: Both access OpenFDA
- **Difference**: BioMCP provides more granular tools (12 vs 10) with additional filtering options

### Biotech Markets MCP (`servers/markets/biotech-markets-mcp/`)
- **Overlap**: Uses PubMed and ClinicalTrials.gov for company intelligence
- **Difference**: BioMCP focuses on precision oncology workflows (variants, genomics, clinical interpretation) rather than market intelligence

## Setup

### Installation

```bash
cd servers/clinical/biomcp-mcp
pip install biomcp-python
# Or using uv (recommended)
uv pip install biomcp-python
```

### Configuration

Optional environment variables:

```bash
# cBioPortal API authentication (optional)
export CBIO_TOKEN="your-api-token"

# OncoKB token (optional - demo server works without)
export ONCOKB_TOKEN="your-oncokb-token"

# OpenFDA API key (optional - for higher rate limits)
export OPENFDA_API_KEY="your-openfda-key"

# NCI API key (required for NCI tools)
export NCI_API_KEY="your-nci-api-key"
```

### Running the Server

```bash
# STDIO mode (for Claude Desktop)
biomcp run

# HTTP mode
biomcp run --mode streamable_http
```

## Usage Examples

### Precision Oncology Workflow

```python
# 1. Always start with thinking
think(
    thought="Analyzing BRAF V600E mutation in melanoma...",
    thoughtNumber=1,
    totalThoughts=4
)

# 2. Get gene context
gene_getter("BRAF")

# 3. Search for pathogenic variants with OncoKB clinical interpretation
variant_searcher(
    gene="BRAF",
    hgvsp="V600E",
    significance="pathogenic",
    include_oncokb=True
)

# 4. Find relevant clinical trials
trial_searcher(
    conditions=["melanoma"],
    interventions=["BRAF inhibitor"],
    phase="PHASE3"
)

# 5. Search literature with automatic cBioPortal integration
article_searcher(
    genes=["BRAF"],
    diseases=["melanoma"],
    keywords=["resistance|resistant"],
    include_cbioportal=True
)
```

### Unified Query Language

```python
# Cross-domain search
search(query="gene:BRAF AND disease:melanoma AND trials.phase:PHASE3")

# Complex variant queries
search(query="variants.significance:pathogenic AND variants.frequency:<0.001")
```

## Documentation

For comprehensive documentation, visit:
- **Official Docs**: https://biomcp.org
- **GitHub Repository**: https://github.com/genomoncology/biomcp
- **Tool Reference**: See `docs/user-guides/02-mcp-tools-reference.md` in this directory

## License

MIT License - fully open source and forkable.

