# PROMPT 02: Build Clinical Trials MCP Server

## 🎯 Objective

Build a complete MCP server wrapper around the existing ClinicalTrials.gov Python API. The Python API already exists in `servers/clinical/clinical-trials-mcp/clinical_trials_api.py` - we need to wrap it in an MCP server.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Existing Code**:
- `servers/clinical/clinical-trials-mcp/clinical_trials_api.py` - Python API client (complete)
- `servers/clinical/clinical-trials-mcp/__init__.py` - Package init
- `schemas/clinical_trials_search.json` - Input schema
- `schemas/clinical_trials_search_output.json` - Output schema
- `schemas/clinical_trials_get_detail.json` - Detail input schema
- `schemas/clinical_trials_get_detail_output.json` - Detail output schema

**Registry Entry**: Already exists in `registry/tools_registry.json` (status: "experimental")

---

## ✅ Tasks

### Task 1: Choose Implementation Language

**Option A: Python MCP Server** (Recommended)
- Use `mcp` Python SDK
- Directly import `clinical_trials_api.py`
- Simpler, no language barrier

**Option B: TypeScript/Node.js MCP Server**
- Use `@modelcontextprotocol/sdk`
- Call Python via subprocess or HTTP
- More complex but consistent with other servers

**RECOMMENDATION**: Use **Option A (Python)** since the API is already in Python.

### Task 2: Set Up Python MCP Server Structure

Create in `servers/clinical/clinical-trials-mcp/`:
```
clinical-trials-mcp/
├── __init__.py
├── clinical_trials_api.py  (exists)
├── server.py               (NEW - MCP server)
├── requirements.txt        (NEW)
├── README.md               (update)
└── test_server.py          (NEW - optional)
```

### Task 3: Install MCP Python SDK

```bash
cd servers/clinical/clinical-trials-mcp
pip install mcp requests
```

Or add to `requirements.txt`:
```
mcp>=0.1.0
requests>=2.31.0
```

### Task 4: Build MCP Server (`server.py`)

Create an MCP server that exposes two tools:

**Tool 1: `clinical_trials_search`**
- Input: Uses `schemas/clinical_trials_search.json`
- Calls: `clinical_trials_api.search_trials(params)`
- Output: Uses `schemas/clinical_trials_search_output.json`

**Tool 2: `clinical_trials_get_detail`**
- Input: Uses `schemas/clinical_trials_get_detail.json`
- Calls: `clinical_trials_api.get_trial_detail(nct_id)`
- Output: Uses `schemas/clinical_trials_get_detail_output.json`

**MCP Server Structure**:
```python
from mcp import Server
from mcp.types import Tool
import json
from clinical_trials_api import search_trials, get_trial_detail

# Load schemas
def load_schema(path):
    with open(path, 'r') as f:
        return json.load(f)

# Create server
server = Server("clinical-trials-mcp")

# Register tools
@server.tool()
async def clinical_trials_search(params: dict):
    """Search for clinical trials"""
    # Validate against schema
    # Call API
    # Return results
    pass

@server.tool()
async def clinical_trials_get_detail(nct_id: str):
    """Get detailed trial information"""
    # Validate NCT ID
    # Call API
    # Return results
    pass

# Run server
if __name__ == "__main__":
    server.run()
```

### Task 5: Test the Server

1. Start the server: `python server.py`
2. Test with MCP inspector or direct calls
3. Verify both tools work with sample queries:
   - Search: condition="diabetes", limit=5
   - Detail: nct_id="NCT01234567" (use real NCT ID)

### Task 6: Update README

Create/update `README.md` with:
- What the server does
- Setup instructions
- How to run
- Tool descriptions
- Example queries
- API documentation link

### Task 7: Update Registry

Update `registry/tools_registry.json`:
- Change status from "experimental" to "production"
- Verify all metadata is correct
- Ensure schema paths are correct

---

## 🔍 Reference

**MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk  
**ClinicalTrials.gov API**: https://clinicaltrials.gov/api/v2  
**Existing API Code**: `servers/clinical/clinical-trials-mcp/clinical_trials_api.py`

**Schema Files** (already exist):
- `schemas/clinical_trials_search.json`
- `schemas/clinical_trials_search_output.json`
- `schemas/clinical_trials_get_detail.json`
- `schemas/clinical_trials_get_detail_output.json`

---

## 📝 Expected Output

1. **Complete MCP server** (`server.py`) that:
   - Exposes 2 tools
   - Uses existing Python API
   - Validates inputs against schemas
   - Returns properly formatted outputs

2. **Requirements file** (`requirements.txt`) with dependencies

3. **Updated README** with full documentation

4. **Registry updated** (status: "production")

5. **Working server** that can be started and tested

---

## 🚨 Important Notes

- **MCP SDK Version**: Check latest MCP Python SDK version and usage patterns
- **Async/Await**: MCP servers are async - use `async def` for tool handlers
- **Error Handling**: Wrap API calls in try/except, return proper MCP errors
- **Schema Validation**: Validate inputs against JSON schemas before calling API
- **Testing**: Test with real ClinicalTrials.gov queries

---

## ✅ Completion Criteria

- [ ] MCP server file created (`server.py`)
- [ ] Server starts without errors
- [ ] Both tools are registered and callable
- [ ] Tool 1 (search) works with test query
- [ ] Tool 2 (get_detail) works with test NCT ID
- [ ] README updated with documentation
- [ ] Requirements file created
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Next Steps

After completion, move to `PROMPT_03_HOSPITAL_PRICING_MCP.md` or work on other prompts in parallel.

