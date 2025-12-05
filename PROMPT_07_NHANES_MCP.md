# PROMPT 07: Build NHANES Data MCP Server

## 🎯 Objective

Build an MCP server for NHANES (National Health and Nutrition Examination Survey) public health survey data. NHANES provides comprehensive health and nutrition data from the US population, perfect for public health analytics and research.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**NHANES Overview**:
- National Health and Nutrition Examination Survey
- Conducted by CDC/NCHS
- Public health data (demographics, examinations, laboratory, questionnaire)
- Data available in cycles (2-year periods)
- Free, public data
- Perfect for population health analytics

**Data Access**:
- NHANES website: https://www.cdc.gov/nchs/nhanes/
- Data files: XPT (SAS transport) format
- Can convert to CSV/JSON
- API: No official API, but data files are downloadable

**Target Location**: `servers/clinical/nhanes-mcp/`

---

## ✅ Tasks

### Task 1: Research NHANES Data Structure

1. Visit NHANES website: https://www.cdc.gov/nchs/nhanes/
2. Understand data organization:
   - Data cycles (2017-2018, 2019-2020, etc.)
   - Data types (Demographics, Examination, Laboratory, Questionnaire)
   - File formats (XPT files)
3. Identify key datasets:
   - Demographics (DEMO)
   - Body Measures (BMX)
   - Blood Pressure (BPX)
   - Laboratory data (various)
   - Questionnaire data (various)
4. Document data download process

### Task 2: Set Up Server Structure

Create in `servers/clinical/nhanes-mcp/`:
```
nhanes-mcp/
├── server.py              (NEW - MCP server)
├── nhanes_data_loader.py  (NEW - download and load data)
├── nhanes_query_engine.py (NEW - query interface)
├── requirements.txt       (NEW)
├── README.md              (NEW)
├── data/                  (NEW - cached data)
│   ├── .gitkeep
│   └── .gitignore         (ignore large data files)
└── config/
    └── datasets.json      (NEW - dataset catalog)
```

### Task 3: Choose Data Storage Strategy

**Option A: SQLite Database** (Recommended)
- Download NHANES XPT files
- Convert to SQLite tables
- Fast queries
- Easy to query with SQL

**Option B: DuckDB**
- Similar to SQLite but optimized for analytics
- Better for large datasets
- Supports Parquet format

**Option C: Parquet Files**
- Convert XPT to Parquet
- Query with pandas/polars
- Good for analytics workloads

**RECOMMENDATION**: Use **SQLite** for simplicity and portability.

### Task 4: Build NHANES Data Loader

Create `nhanes_data_loader.py` with functions:
- `download_nhanes_data(cycle: str, data_type: str) -> str` (downloads XPT file)
- `convert_xpt_to_sqlite(xpt_file: str, db_path: str, table_name: str) -> None`
- `load_demographics(cycle: str, db_path: str) -> None`
- `load_laboratory_data(cycle: str, data_type: str, db_path: str) -> None`
- `get_available_cycles() -> list`
- `get_available_datasets(cycle: str) -> list`

**Implementation Notes**:
- Use `pyreadstat` or `pandas` to read XPT files
- Download data on-demand or pre-download common datasets
- Cache converted data in SQLite
- Handle large files (some datasets are 100MB+)

### Task 5: Build NHANES Query Engine

Create `nhanes_query_engine.py` with functions:
- `list_datasets(cycle: str) -> list`
- `get_dataset_info(dataset_name: str, cycle: str) -> dict`
- `query_data(dataset: str, cycle: str, filters: dict, limit: int) -> list`
- `get_variable_info(dataset: str, variable: str, cycle: str) -> dict`
- `calculate_percentile(variable: str, value: float, dataset: str, cycle: str) -> dict`
- `get_demographics_summary(cycle: str) -> dict`

**Query Interface**:
- Support filtering by demographics (age, gender, race, etc.)
- Support variable selection
- Support aggregations (mean, median, percentile)
- Return JSON results

### Task 6: Create Dataset Catalog

Create `config/datasets.json` with catalog of key datasets:
```json
{
  "demographics": {
    "name": "Demographics",
    "cycles": ["2017-2018", "2019-2020", "2021-2022"],
    "description": "Demographic data",
    "key_variables": ["RIDAGEYR", "RIAGENDR", "RIDRETH3"]
  },
  "body_measures": {
    "name": "Body Measures",
    "cycles": ["2017-2018", "2019-2020"],
    "description": "Height, weight, BMI",
    "key_variables": ["BMXHT", "BMXWT", "BMXBMI"]
  }
  // ... more datasets
}
```

### Task 7: Build MCP Server

Create `server.py` with 4-5 tools:

**Tool 1: `nhanes_list_datasets`**
- Input: `cycle` (string, optional) - e.g., "2017-2018"
- Calls: `nhanes_query_engine.list_datasets()`
- Output: List of available datasets for cycle

**Tool 2: `nhanes_get_data`**
- Input: `dataset` (string), `cycle` (string), `filters` (dict, optional), `variables` (list, optional), `limit` (int, optional)
- Calls: `nhanes_query_engine.query_data()`
- Output: Query results as JSON

**Tool 3: `nhanes_get_variable_info`**
- Input: `dataset` (string), `variable` (string), `cycle` (string)
- Calls: `nhanes_query_engine.get_variable_info()`
- Output: Variable description, type, valid values

**Tool 4: `nhanes_calculate_percentile`**
- Input: `variable` (string), `value` (float), `dataset` (string), `cycle` (string), `filters` (dict, optional)
- Calls: `nhanes_query_engine.calculate_percentile()`
- Output: Percentile rank and statistics

**Tool 5: `nhanes_get_demographics_summary`** (Optional)
- Input: `cycle` (string)
- Calls: `nhanes_query_engine.get_demographics_summary()`
- Output: Summary statistics (age distribution, gender, race, etc.)

### Task 8: Create Schemas

Create schema files in `schemas/`:
- `nhanes_list_datasets.json` (input/output)
- `nhanes_get_data.json` (input/output)
- `nhanes_get_variable_info.json` (input/output)
- `nhanes_calculate_percentile.json` (input/output)

### Task 9: Add Data Download Script (Optional)

Create `scripts/download_nhanes_data.py`:
- Downloads common datasets
- Converts to SQLite
- Caches for faster access
- Can be run manually or via cron

### Task 10: Test the Server

1. Start server
2. Test each tool:
   - List datasets: cycle="2017-2018"
   - Get data: dataset="DEMO", cycle="2017-2018", limit=10
   - Get variable info: dataset="DEMO", variable="RIDAGEYR"
   - Calculate percentile: variable="BMXBMI", value=25.0, dataset="BMX"

### Task 11: Update README

Document:
- What the server does
- Setup instructions
- How to download NHANES data
- Available datasets
- Tool descriptions
- Example queries
- Data size considerations
- Update frequency (NHANES releases new cycles every 2 years)

### Task 12: Update Registry

Add entries to `registry/tools_registry.json`:
- `nhanes.list_datasets`
- `nhanes.get_data`
- `nhanes.get_variable_info`
- `nhanes.calculate_percentile`

Set:
- Domain: "clinical"
- Status: "production"
- Auth required: false
- Safety level: "low" (public data)
- Notes: Document data cycles and update frequency

---

## 🔍 Reference

**NHANES Website**: https://www.cdc.gov/nchs/nhanes/  
**NHANES Data Files**: https://wwwn.cdc.gov/nchs/nhanes/Default.aspx  
**XPT Format**: SAS Transport format (use pyreadstat or pandas to read)

**Key Datasets**:
- **DEMO**: Demographics
- **BMX**: Body Measures (height, weight, BMI)
- **BPX**: Blood Pressure
- **LAB**: Laboratory data (various)
- **DIQ**: Diabetes questionnaire
- **BPQ**: Blood Pressure questionnaire

**Example Variables**:
- `RIDAGEYR`: Age in years
- `RIAGENDR`: Gender (1=Male, 2=Female)
- `RIDRETH3`: Race/Hispanic origin
- `BMXBMI`: Body Mass Index
- `BPXSY1`: Systolic blood pressure

---

## 📝 Expected Output

1. **Complete MCP server** with 4-5 tools
2. **NHANES data loader** that downloads and converts data
3. **Query engine** for querying NHANES data
4. **Dataset catalog** with key datasets
5. **Schema files** for all tools
6. **README** with full documentation
7. **Requirements file** with dependencies (pandas, pyreadstat, etc.)
8. **Registry updated** with all tools
9. **Working server** tested with real NHANES queries

---

## 🚨 Important Notes

- **Data Size**: NHANES datasets can be large (100MB+ per file) - cache efficiently
- **XPT Format**: Requires special libraries (pyreadstat) to read
- **Data Cycles**: NHANES releases data every 2 years - document cycle availability
- **Variable Names**: NHANES uses cryptic variable names - provide lookup/description
- **Privacy**: NHANES data is de-identified but still sensitive - handle appropriately
- **Update Frequency**: New cycles released every 2 years - document update process

---

## ✅ Completion Criteria

- [ ] MCP server created with 4-5 tools
- [ ] NHANES data loader implemented
- [ ] Query engine working
- [ ] Dataset catalog created
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Tool 1 (list_datasets) works
- [ ] Tool 2 (get_data) works with test query
- [ ] Tool 3 (get_variable_info) works
- [ ] Tool 4 (calculate_percentile) works
- [ ] Schemas created for all tools
- [ ] README updated with documentation
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Future Enhancements (Not in This Prompt)

- **Pre-download Common Datasets**: Download and cache popular datasets
- **Advanced Analytics**: Trend analysis across cycles, correlation analysis
- **Visualization**: Generate charts/graphs from data
- **Export**: Export query results to CSV/Excel
- **API Caching**: Cache query results for faster responses

---

## 🎯 Next Steps

After completion, move to `PROMPT_08_REGISTRY_UPDATE.md` to consolidate all registry entries.

