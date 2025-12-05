# Clinical Trials MCP Server

MCP server for searching and retrieving clinical trials data from ClinicalTrials.gov.

## Status

✅ **Production**

This MCP server provides full access to the ClinicalTrials.gov API v2 through the Model Context Protocol (MCP).

## Overview

The Clinical Trials MCP Server wraps the ClinicalTrials.gov API v2, providing two main tools:
1. **Search** for clinical trials by various criteria
2. **Get detailed information** about specific trials by NCT ID

## Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Navigate to the server directory:
   ```bash
   cd servers/clinical/clinical-trials-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install mcp requests
   ```

## Running the Server

### As an MCP Server

The server runs on stdio (standard input/output) and communicates via the MCP protocol:

```bash
python server.py
```

The server will listen for MCP protocol messages on stdin and respond on stdout.

### CLI Mode (Testing)

If the MCP SDK is not installed, the server falls back to CLI mode for testing:

**Search for trials:**
```bash
python server.py --tool search --condition "diabetes" --limit 5
```

**Get trial details:**
```bash
python server.py --tool get_detail --nct_id "NCT00002540"
```

## Tools

### `clinical_trials_search`

Search for clinical trials by condition, intervention, location, and other criteria.

**Input Parameters:**
- `condition` (string, optional): Medical condition or disease (e.g., "diabetes", "cancer")
- `intervention` (string, optional): Intervention type (drug, device, procedure, etc.)
- `location` (string, optional): Geographic location (country, state, or city)
- `status` (string, optional): Recruitment status. Valid values:
  - `"recruiting"`
  - `"not yet recruiting"`
  - `"active"`
  - `"completed"`
  - `"suspended"`
  - `"terminated"`
  - `"withdrawn"`
- `phase` (string, optional): Trial phase. Valid values:
  - `"Phase 1"`
  - `"Phase 2"`
  - `"Phase 3"`
  - `"Phase 4"`
  - `"N/A"`
- `study_type` (string, optional): Type of study. Valid values:
  - `"Interventional"`
  - `"Observational"`
  - `"Expanded Access"`
- `limit` (integer, optional): Maximum number of results (1-100, default: 20)
- `offset` (integer, optional): Number of results to skip for pagination (default: 0)

**Output:**
Returns a dictionary with:
- `total` (integer): Total number of matching trials found
- `count` (integer): Number of trials in this response
- `offset` (integer): Offset used for this query
- `trials` (array): List of trial objects, each containing:
  - `nct_id` (string): ClinicalTrials.gov identifier
  - `title` (string): Trial title
  - `status` (string): Current recruitment status
  - `phase` (string): Trial phase
  - `conditions` (array): List of conditions being studied
  - `interventions` (array): List of interventions
  - `locations` (array): List of trial locations
  - `lead_sponsor` (string): Lead sponsor name
  - `start_date` (string or null): Trial start date (ISO 8601)
  - `completion_date` (string or null): Trial completion date (ISO 8601)
  - `url` (string): Link to trial details page

**Example Query:**
```json
{
  "condition": "pancreatic cancer",
  "status": "recruiting",
  "phase": "Phase 2",
  "limit": 10
}
```

### `clinical_trials_get_detail`

Retrieve detailed information about a specific clinical trial by NCT ID.

**Input Parameters:**
- `nct_id` (string, required): ClinicalTrials.gov identifier (format: `NCT01234567`)

**Output:**
Returns a dictionary with detailed trial information including:
- `nct_id` (string): ClinicalTrials.gov identifier
- `brief_title` (string): Brief title of the trial
- `official_title` (string): Official title of the trial
- `summary` (string): Brief summary
- `detailed_description` (string): Detailed description
- `status` (string): Current overall status
- `phase` (string): Trial phase(s)
- `study_type` (string): Type of study
- `conditions` (array): List of conditions being studied
- `interventions` (array): List of interventions with details (name, type, description)
- `outcomes` (array): List of primary and secondary outcomes
- `enrollment` (object): Enrollment information (target, actual, eligibility_criteria)
- `locations` (array): List of trial locations with details
- `contacts` (array): List of central contacts
- `sponsor` (object): Sponsor information (lead, collaborators)
- `dates` (object): Trial dates (start_date, completion_date, primary_completion_date)
- `references` (object): Reference citations
- `url` (string): Link to trial details page

**Example Query:**
```json
{
  "nct_id": "NCT00002540"
}
```

## Example Usage

### Search for Recruiting Diabetes Trials

```python
# Via MCP protocol
{
  "tool": "clinical_trials_search",
  "arguments": {
    "condition": "diabetes",
    "status": "recruiting",
    "limit": 5
  }
}
```

### Get Trial Details

```python
# Via MCP protocol
{
  "tool": "clinical_trials_get_detail",
  "arguments": {
    "nct_id": "NCT00002540"
  }
}
```

## Testing

### Test the API Functions

Run the test script to verify the API functions work correctly:

```bash
python test_clinical_trials_api.py
```

### Test the MCP Server

1. Start the server:
   ```bash
   python server.py
   ```

2. Use an MCP client or inspector to test the tools.

3. Or use CLI mode for quick testing:
   ```bash
   # Search test
   python server.py --tool search --condition "diabetes" --limit 3
   
   # Detail test
   python server.py --tool get_detail --nct_id "NCT00002540"
   ```

## Implementation Details

- **Language**: Python 3.8+
- **MCP SDK**: `mcp` Python package
- **API**: ClinicalTrials.gov API v2 (official REST API)
- **Dependencies**: 
  - `mcp>=0.1.0` - MCP Python SDK
  - `requests>=2.31.0` - HTTP client

## Architecture

```
server.py
├── MCP Server (stdio transport)
├── Tool Handlers
│   ├── clinical_trials_search()
│   └── clinical_trials_get_detail()
└── API Client
    └── clinical_trials_api.py
        ├── search_trials()
        └── get_trial_detail()
```

## Error Handling

The server handles errors gracefully:
- Invalid NCT ID format returns an error message
- API failures return error information in the response
- Network errors are caught and reported
- Invalid parameters are validated against schemas

## Schemas

Input and output schemas are defined in:
- `schemas/clinical_trials_search.json` - Search input schema
- `schemas/clinical_trials_search_output.json` - Search output schema
- `schemas/clinical_trials_get_detail.json` - Detail input schema
- `schemas/clinical_trials_get_detail_output.json` - Detail output schema

## Reference

- **API Documentation**: https://clinicaltrials.gov/api/v2/docs
- **MCP Protocol**: https://modelcontextprotocol.io
- **Registry Entry**: See `registry/tools_registry.json`
- **Schemas**: See `schemas/clinical_trials_*.json`

## License

This server wraps the public ClinicalTrials.gov API, which provides open access to clinical trial data.
