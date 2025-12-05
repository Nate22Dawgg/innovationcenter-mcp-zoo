# NHANES MCP Server

MCP server for accessing NHANES (National Health and Nutrition Examination Survey) public health survey data from CDC/NCHS.

## Status

✅ **Production Ready**

This MCP server provides access to NHANES data through the Model Context Protocol (MCP). Data is downloaded on-demand from the CDC/NCHS website and cached in SQLite for efficient querying.

## Overview

The NHANES MCP Server provides tools for querying comprehensive health and nutrition data from the US population. NHANES is conducted by the CDC/NCHS and provides data on demographics, examinations, laboratory tests, and questionnaires.

**Key Features:**
- Download and cache NHANES data automatically
- Query datasets with flexible filtering
- Calculate percentiles for health metrics
- Get variable information and statistics
- Support for multiple data cycles (2017-2018, 2019-2020, 2021-2022)

## Setup

### Prerequisites

- Python 3.8 or higher
- pip
- Internet connection (for downloading NHANES data)

### Installation

1. Navigate to the server directory:
   ```bash
   cd servers/clinical/nhanes-mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install mcp pandas pyreadstat numpy
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

**List datasets:**
```bash
python server.py --tool list_datasets --cycle "2017-2018"
```

**Get data:**
```bash
python server.py --tool get_data --dataset demographics --cycle "2017-2018" --limit 10
```

**Get variable info:**
```bash
python server.py --tool get_variable_info --dataset demographics --variable RIDAGEYR --cycle "2017-2018"
```

**Calculate percentile:**
```bash
python server.py --tool calculate_percentile --variable BMXBMI --value 25.0 --dataset body_measures --cycle "2017-2018"
```

## Data Download

NHANES data is downloaded automatically on first use. Data files are cached in the `data/` directory as SQLite databases for fast subsequent queries.

**Manual Data Download:**

You can pre-download datasets using the data loader:

```bash
python nhanes_data_loader.py 2017-2018 DEMO demographics
```

This downloads and converts the demographics dataset for the 2017-2018 cycle.

## Tools

### `nhanes_list_datasets`

List available NHANES datasets for a cycle.

**Input Parameters:**
- `cycle` (string, optional): Data cycle (e.g., "2017-2018"). If not provided, lists datasets for all cycles.

**Output:**
Returns a dictionary with:
- `cycle` (string): Data cycle (if specified)
- `datasets` (array): List of available datasets, each containing:
  - `id` (string): Dataset ID
  - `name` (string): Dataset name
  - `file_prefix` (string): NHANES file prefix
  - `data_type` (string): Data type (demographics, examination, laboratory, questionnaire)
  - `description` (string): Dataset description
  - `key_variables` (array): List of key variable names
- `count` (integer): Number of datasets

**Example Query:**
```json
{
  "cycle": "2017-2018"
}
```

### `nhanes_get_data`

Query NHANES data with optional filters and variable selection.

**Input Parameters:**
- `dataset` (string, required): Dataset ID (e.g., "demographics", "body_measures", "blood_pressure")
- `cycle` (string, required): Data cycle (e.g., "2017-2018")
- `filters` (object, optional): Filter dictionary. Supports:
  - `{"variable": {"min": value, "max": value}}` - Range filter
  - `{"variable": value}` - Equality filter
  - `{"variable": {"in": [value1, value2]}}` - In-list filter
- `variables` (array, optional): List of variables to select. If not provided, all variables are returned.
- `limit` (integer, optional): Maximum number of rows to return (default: 100, max: 10000)

**Output:**
Returns a dictionary with:
- `dataset` (string): Dataset ID
- `cycle` (string): Data cycle
- `count` (integer): Number of rows returned
- `limit` (integer): Limit applied
- `filters` (object): Filters applied
- `variables` (string or array): Variables selected
- `data` (array): Query results as array of objects

**Example Query:**
```json
{
  "dataset": "body_measures",
  "cycle": "2017-2018",
  "filters": {
    "RIDAGEYR": {"min": 18, "max": 65}
  },
  "variables": ["RIDAGEYR", "RIAGENDR", "BMXBMI"],
  "limit": 100
}
```

### `nhanes_get_variable_info`

Get information about a specific variable in a dataset.

**Input Parameters:**
- `dataset` (string, required): Dataset ID
- `variable` (string, required): Variable name (e.g., "RIDAGEYR", "BMXBMI", "BPXSY1")
- `cycle` (string, required): Data cycle

**Output:**
Returns a dictionary with:
- `variable` (string): Variable name
- `dataset` (string): Dataset ID
- `cycle` (string): Data cycle
- `count` (integer): Total number of records
- `non_null_count` (integer): Number of non-null values
- `min_value`: Minimum value
- `max_value`: Maximum value
- `mean_value`: Mean value
- `distinct_count` (integer): Number of distinct values
- `sample_values` (array): Sample values from the dataset

**Example Query:**
```json
{
  "dataset": "demographics",
  "variable": "RIDAGEYR",
  "cycle": "2017-2018"
}
```

### `nhanes_calculate_percentile`

Calculate percentile rank of a value for a variable.

**Input Parameters:**
- `variable` (string, required): Variable name (e.g., "BMXBMI", "BPXSY1")
- `value` (number, required): Value to calculate percentile for
- `dataset` (string, required): Dataset ID
- `cycle` (string, required): Data cycle
- `filters` (object, optional): Optional filters to apply (e.g., filter by gender, age range)

**Output:**
Returns a dictionary with:
- `variable` (string): Variable name
- `value` (number): Value for which percentile was calculated
- `dataset` (string): Dataset ID
- `cycle` (string): Data cycle
- `percentile` (number): Percentile rank (0-100)
- `sample_size` (integer): Number of samples used
- `statistics` (object): Statistical summary including:
  - `mean`, `median`, `std`, `min`, `max`
  - `p25`, `p50`, `p75`, `p90`, `p95`, `p99`

**Example Query:**
```json
{
  "variable": "BMXBMI",
  "value": 25.0,
  "dataset": "body_measures",
  "cycle": "2017-2018",
  "filters": {
    "RIAGENDR": 1
  }
}
```

### `nhanes_get_demographics_summary`

Get summary statistics for demographics data.

**Input Parameters:**
- `cycle` (string, required): Data cycle

**Output:**
Returns a dictionary with:
- `cycle` (string): Data cycle
- `total_records` (integer): Total number of records
- `age_distribution` (object): Age statistics (mean, median, min, max, std)
- `gender_distribution` (object): Gender counts (1=Male, 2=Female)
- `race_ethnicity_distribution` (object): Race/ethnicity counts

**Example Query:**
```json
{
  "cycle": "2017-2018"
}
```

## Available Datasets

The server supports the following datasets (configured in `config/datasets.json`):

- **demographics**: Demographics data (age, gender, race/ethnicity, education, income)
- **body_measures**: Body measurements (height, weight, BMI, waist circumference)
- **blood_pressure**: Blood pressure measurements
- **diabetes**: Diabetes questionnaire data
- **blood_pressure_questionnaire**: Blood pressure questionnaire data
- **cholesterol**: Total cholesterol laboratory data
- **glucose**: Fasting glucose and insulin laboratory data
- **complete_blood_count**: Complete blood count laboratory data

## Key Variables

Common NHANES variables:

- `RIDAGEYR`: Age in years
- `RIAGENDR`: Gender (1=Male, 2=Female)
- `RIDRETH3`: Race/Hispanic origin
- `BMXBMI`: Body Mass Index
- `BMXHT`: Height (cm)
- `BMXWT`: Weight (kg)
- `BPXSY1`: Systolic blood pressure (first reading)
- `BPXDI1`: Diastolic blood pressure (first reading)

## Example Usage

### Query BMI Data for Adults

```python
# Via MCP protocol
{
  "tool": "nhanes_get_data",
  "arguments": {
    "dataset": "body_measures",
    "cycle": "2017-2018",
    "filters": {
      "RIDAGEYR": {"min": 18, "max": 65}
    },
    "variables": ["RIDAGEYR", "RIAGENDR", "BMXBMI"],
    "limit": 100
  }
}
```

### Calculate BMI Percentile

```python
# Via MCP protocol
{
  "tool": "nhanes_calculate_percentile",
  "arguments": {
    "variable": "BMXBMI",
    "value": 25.0,
    "dataset": "body_measures",
    "cycle": "2017-2018",
    "filters": {
      "RIAGENDR": 1,
      "RIDAGEYR": {"min": 30, "max": 40}
    }
  }
}
```

### Get Demographics Summary

```python
# Via MCP protocol
{
  "tool": "nhanes_get_demographics_summary",
  "arguments": {
    "cycle": "2017-2018"
  }
}
```

## Data Cycles

NHANES releases data in 2-year cycles. The server currently supports:

- **2017-2018** (Cycle P)
- **2019-2020** (Cycle Q)
- **2021-2022** (Cycle R)

New cycles are released approximately every 2 years. To add support for new cycles, update the cycle mapping in `nhanes_data_loader.py`.

## Data Storage

NHANES data is stored in SQLite format for efficient querying:

- **Location**: `data/nhanes.db`
- **Format**: SQLite database with one table per dataset/cycle
- **Table naming**: `{file_prefix}_{cycle_code}` (e.g., `DEMO_P`, `BMX_P`)

Data files are downloaded on-demand and cached locally. Large datasets (100MB+) may take several minutes to download on first use.

## Implementation Details

- **Language**: Python 3.8+
- **MCP SDK**: `mcp` Python package
- **Data Format**: XPT (SAS Transport) files converted to SQLite
- **Dependencies**: 
  - `mcp>=0.1.0` - MCP Python SDK
  - `pandas>=2.0.0` - Data manipulation
  - `pyreadstat>=1.2.0` - XPT file reading (preferred)
  - `numpy>=1.24.0` - Numerical operations

## Architecture

```
server.py
├── MCP Server (stdio transport)
├── Tool Handlers
│   ├── nhanes_list_datasets()
│   ├── nhanes_get_data()
│   ├── nhanes_get_variable_info()
│   ├── nhanes_calculate_percentile()
│   └── nhanes_get_demographics_summary()
└── Query Engine
    └── nhanes_query_engine.py
        ├── query_data()
        ├── get_variable_info()
        ├── calculate_percentile()
        └── get_demographics_summary()
└── Data Loader
    └── nhanes_data_loader.py
        ├── download_nhanes_data()
        ├── convert_xpt_to_sqlite()
        └── load_dataset()
```

## Error Handling

The server handles errors gracefully:
- Missing datasets are downloaded automatically
- Invalid variable names return error messages
- Network errors during download are caught and reported
- Invalid parameters are validated against schemas
- Large queries are limited to prevent memory issues

## Data Size Considerations

- **Download Size**: Individual XPT files range from 1MB to 100MB+
- **Database Size**: SQLite databases are typically 2-3x the XPT file size
- **Memory Usage**: Queries are limited to 10,000 rows by default
- **Cache**: Downloaded files are cached in `data/` directory

## Update Frequency

NHANES releases new data cycles approximately every 2 years. To update:

1. Add new cycle to `get_available_cycles()` in `nhanes_data_loader.py`
2. Add cycle code mapping in `get_cycle_code()`
3. Update dataset cycles in `config/datasets.json`
4. Data will be downloaded automatically on first use

## Schemas

Input and output schemas are defined in:
- `schemas/nhanes_list_datasets.json` / `nhanes_list_datasets_output.json`
- `schemas/nhanes_get_data.json` / `nhanes_get_data_output.json`
- `schemas/nhanes_get_variable_info.json` / `nhanes_get_variable_info_output.json`
- `schemas/nhanes_calculate_percentile.json` / `nhanes_calculate_percentile_output.json`
- `schemas/nhanes_get_demographics_summary.json` / `nhanes_get_demographics_summary_output.json`

## Reference

- **NHANES Website**: https://www.cdc.gov/nchs/nhanes/
- **NHANES Data Files**: https://wwwn.cdc.gov/nchs/nhanes/Default.aspx
- **MCP Protocol**: https://modelcontextprotocol.io
- **Registry Entry**: See `registry/tools_registry.json`
- **Schemas**: See `schemas/nhanes_*.json`

## Privacy and Data Handling

- NHANES data is de-identified public health data
- Data is downloaded from official CDC/NCHS sources
- No personal identifying information is included
- Data is cached locally for performance but can be deleted at any time

## License

This server accesses public NHANES data from CDC/NCHS, which is freely available for research and public health purposes.

