# PROMPT 04: Build Claims/EDI MCP Server

## 🎯 Objective

Build an MCP server for health insurance claims processing, EDI 837/835 parsing, CPT/HCPCS pricing, and claims normalization. This server will wrap existing open-source EDI parsers and integrate CMS fee schedules.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Discovery Findings**:
- EDI parsers exist BUT none wrapped in MCP protocol
- Claims processing is niche, no community MCP servers
- Data is highly structured (perfect for MCP tooling)

**Open-Source Parsers to Use**:
- `edi-837-parser` (Python) - Professional claims
- `edi-835-parser` (Python) - Remittance advice
- CMS CPT/HCPCS fee schedules (public, free)

**Target Location**: `servers/claims/claims-edi-mcp/`

---

## ✅ Tasks

### Task 1: Research and Identify EDI Parsers

Find and evaluate Python EDI parsers:
1. Search for: `edi-837-parser`, `edi-835-parser`, `x12-parser`
2. Check GitHub repos for:
   - `mehru-un-nisa/edi-837-parser`
   - `keironstoddart/edi-835-parser`
   - `hiplab/parser` (X12 837/835 → JSON)
3. Choose the most maintained, well-documented parser
4. Document installation method (pip? git clone?)

### Task 2: Set Up Server Structure

Create in `servers/claims/claims-edi-mcp/`:
```
claims-edi-mcp/
├── server.py              (NEW - MCP server)
├── edi_parser.py          (NEW - wrapper around parsers)
├── cms_fee_schedules.py   (NEW - CMS data integration)
├── requirements.txt       (NEW)
├── README.md              (NEW)
├── data/                  (NEW - for CMS fee schedules)
│   └── .gitkeep
└── .env.example           (NEW)
```

### Task 3: Install and Test EDI Parsers

1. Install chosen EDI parser(s)
2. Test with sample EDI files:
   - Sample 837 file (professional claim)
   - Sample 835 file (remittance advice)
3. Understand parser output format
4. Document parser limitations

### Task 4: Build EDI Parser Wrapper

Create `edi_parser.py` with functions:
- `parse_edi_837(edi_content: str) -> dict`
- `parse_edi_835(edi_content: str) -> dict`
- `normalize_claim_line_item(line_item: dict) -> dict`
- `extract_cpt_codes(claim: dict) -> list`
- `extract_hcpcs_codes(claim: dict) -> list`

Handle:
- File input (string or file path)
- Error handling (malformed EDI)
- Output normalization to consistent JSON format

### Task 5: Integrate CMS Fee Schedules

Create `cms_fee_schedules.py` with functions:
- `lookup_cpt_price(cpt_code: str, year: int, locality: str) -> dict`
- `lookup_hcpcs_price(hcpcs_code: str, year: int) -> dict`
- `download_fee_schedule(year: int)` (downloads from CMS if not cached)

**CMS Data Sources**:
- Physician Fee Schedule: https://www.cms.gov/medicare/physician-fee-schedule
- HCPCS codes: https://www.cms.gov/medicare/coding-billing/medicare-coding
- Download and cache locally (update annually)

### Task 6: Build MCP Server

Create `server.py` with 5 tools:

**Tool 1: `claims_parse_edi_837`**
- Input: `edi_content` (string) or `edi_file_path` (string)
- Calls: `edi_parser.parse_edi_837()`
- Output: Normalized claim JSON

**Tool 2: `claims_parse_edi_835`**
- Input: `edi_content` (string) or `edi_file_path` (string)
- Calls: `edi_parser.parse_edi_835()`
- Output: Normalized remittance advice JSON

**Tool 3: `claims_normalize_line_item`**
- Input: `line_item` (dict)
- Calls: `edi_parser.normalize_claim_line_item()`
- Output: Normalized line item

**Tool 4: `claims_lookup_cpt_price`**
- Input: `cpt_code` (string), `year` (int, optional), `locality` (string, optional)
- Calls: `cms_fee_schedules.lookup_cpt_price()`
- Output: CMS fee schedule price

**Tool 5: `claims_lookup_hcpcs_price`**
- Input: `hcpcs_code` (string), `year` (int, optional)
- Calls: `cms_fee_schedules.lookup_hcpcs_price()`
- Output: CMS fee schedule price

### Task 7: Create Schemas

Create schema files in `schemas/`:
- `claims_parse_edi_837.json` (input)
- `claims_parse_edi_837_output.json` (output)
- `claims_parse_edi_835.json` (input)
- `claims_parse_edi_835_output.json` (output)
- `claims_lookup_cpt_price.json` (input)
- `claims_lookup_cpt_price_output.json` (output)
- `claims_lookup_hcpcs_price.json` (input)
- `claims_lookup_hcpcs_price_output.json` (output)

### Task 8: Add Sample EDI Files (Optional)

Include sample EDI files in `data/samples/` for testing:
- `sample_837.txt` (professional claim)
- `sample_835.txt` (remittance advice)
- Document format and structure

### Task 9: Test the Server

1. Start server
2. Test each tool:
   - Parse 837: Use sample EDI file
   - Parse 835: Use sample EDI file
   - Normalize: Use parsed line item
   - Lookup CPT: Test with "99213" (office visit)
   - Lookup HCPCS: Test with common HCPCS code

### Task 10: Update README

Document:
- What the server does
- Setup instructions
- EDI parser dependencies
- How to get CMS fee schedules
- Tool descriptions
- Example EDI file formats
- Limitations and known issues

### Task 11: Update Registry

Add entries to `registry/tools_registry.json`:
- `claims.parse_edi_837`
- `claims.parse_edi_835`
- `claims.normalize_line_item`
- `claims.lookup_cpt_price`
- `claims.lookup_hcpcs_price`

Set:
- Domain: "claims"
- Status: "production"
- Auth required: false
- Safety level: "medium" (handles sensitive healthcare data)

---

## 🔍 Reference

**EDI Format**: X12 EDI 837 (Professional Claims), 835 (Remittance Advice)  
**CMS Fee Schedules**: https://www.cms.gov/medicare/physician-fee-schedule  
**CPT Codes**: https://www.ama-assn.org/amaone/cpt-current-procedural-terminology  
**HCPCS Codes**: https://www.cms.gov/medicare/coding-billing/medicare-coding

**Potential Parser Repos**:
- https://github.com/mehru-un-nisa/edi-837-parser
- https://github.com/keironstoddart/edi-835-parser
- https://github.com/hiplab/parser

---

## 📝 Expected Output

1. **Complete MCP server** with 5 tools
2. **EDI parser wrapper** that normalizes output
3. **CMS fee schedule integration** with lookup functions
4. **Schema files** for all tools
5. **README** with full documentation
6. **Requirements file** with all dependencies
7. **Registry updated** with all tools
8. **Working server** tested with sample EDI files

---

## 🚨 Important Notes

- **EDI Format Complexity**: EDI files are complex - handle parsing errors gracefully
- **CMS Data Updates**: Fee schedules update annually - document update process
- **Data Privacy**: EDI files contain PHI - document security considerations
- **Parser Maintenance**: EDI parsers may be unmaintained - choose carefully
- **File Size**: EDI files can be large - handle memory efficiently

---

## ✅ Completion Criteria

- [ ] MCP server created with 5 tools
- [ ] EDI parser wrapper implemented
- [ ] CMS fee schedule integration working
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Tool 1 (parse 837) works with sample file
- [ ] Tool 2 (parse 835) works with sample file
- [ ] Tool 3 (normalize) works
- [ ] Tool 4 (lookup CPT) works with test code
- [ ] Tool 5 (lookup HCPCS) works with test code
- [ ] Schemas created for all tools
- [ ] README updated with documentation
- [ ] Registry updated (status: "production")
- [ ] Validation passes: `python scripts/validate_registry.py`

---

## 🎯 Future Enhancements (Not in This Prompt)

- **Batch Processing**: Process multiple EDI files at once
- **Validation**: Validate claims against business rules
- **Analytics**: Claim volume, denial rates, etc.
- **Integration**: Connect to claims clearinghouses

---

## 🎯 Next Steps

After completion, move to `PROMPT_05_BIOTECH_MARKETS_MCP.md` or work on other prompts in parallel.

