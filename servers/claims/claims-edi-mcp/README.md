# Claims/EDI MCP Server

MCP server for health insurance claims processing, EDI 837/835 parsing, CPT/HCPCS pricing, and claims normalization. This server wraps X12 EDI parsing functionality and integrates CMS fee schedules.

## 🎯 Overview

This server provides tools for processing healthcare claims data:

- **Parse EDI 837**: Professional claims submission files
- **Parse EDI 835**: Remittance advice (payment/denial) files
- **Normalize Claims**: Standardize claim line items to consistent format
- **CPT Pricing**: Lookup CPT codes in CMS Physician Fee Schedule
- **HCPCS Pricing**: Lookup HCPCS codes in CMS fee schedules

## 📋 Status

✅ **Production Ready**

This server is fully implemented and ready for use. CMS fee schedules must be downloaded manually from CMS website.

## 🚀 Setup

### Prerequisites

- Python 3.8 or higher
- Access to CMS fee schedule data (public, free download)

### Installation

1. **Navigate to the server directory:**
   ```bash
   cd servers/claims/claims-edi-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up CMS fee schedule data (optional):**
   
   See `data/README.md` for instructions on downloading CMS fee schedules.
   The server will work without fee schedule data, but price lookups will return "not_found" status.

## 🛠️ Usage

### Running the Server

**With MCP SDK:**
```bash
python server.py
```

**CLI Mode (for testing without MCP SDK):**
```bash
# Parse EDI 837 file
python server.py --tool parse_837 --edi_file data/samples/sample_837.txt

# Parse EDI 835 file
python server.py --tool parse_835 --edi_file data/samples/sample_835.txt

# Lookup CPT code
python server.py --tool lookup_cpt --cpt_code 99213 --year 2024

# Lookup HCPCS code
python server.py --tool lookup_hcpcs --hcpcs_code A0425 --year 2024
```

### Tools

#### 1. `claims_parse_edi_837`

Parse EDI 837 Professional Claim file into normalized JSON format.

**Input:**
- `edi_content` (optional): EDI file content as string
- `edi_file_path` (optional): Path to EDI file (alternative to edi_content)

**Example:**
```json
{
  "edi_file_path": "data/samples/sample_837.txt"
}
```

**Output:**
Returns normalized claim data including:
- Transaction ID and submission date
- Payer, provider, and patient information
- Claim details (claim number, charge amount, place of service)
- Line items with procedure codes
- Extracted CPT and HCPCS codes

#### 2. `claims_parse_edi_835`

Parse EDI 835 Remittance Advice file into normalized JSON format.

**Input:**
- `edi_content` (optional): EDI file content as string
- `edi_file_path` (optional): Path to EDI file (alternative to edi_content)

**Example:**
```json
{
  "edi_file_path": "data/samples/sample_835.txt"
}
```

**Output:**
Returns normalized remittance data including:
- Transaction ID and payment date
- Payer and payee information
- Claim payment details (charge, paid, patient responsibility)
- Summary information

#### 3. `claims_normalize_line_item`

Normalize a claim line item to consistent format with standard fields.

**Input:**
- `line_item` (required): Raw line item dictionary from parser

**Example:**
```json
{
  "line_item": {
    "line_number": "1",
    "procedure_code": "99213",
    "charge_amount": 100.00,
    "units": 1.0,
    "service_date": "2024-01-01"
  }
}
```

**Output:**
Returns normalized line item with standard fields:
- `line_number`: Line sequence number
- `procedure_code`: CPT or HCPCS code
- `procedure_modifier`: Procedure modifier codes
- `diagnosis_code`: Diagnosis code
- `units`: Number of units
- `charge_amount`: Charge amount
- `service_date`: Date of service
- `place_of_service`: Place of service code
- `description`: Procedure description

#### 4. `claims_lookup_cpt_price`

Lookup CPT code price from CMS Physician Fee Schedule.

**Input:**
- `cpt_code` (required): CPT procedure code (5-digit, e.g., "99213")
- `year` (optional): Year for fee schedule (default: current year)
- `locality` (optional): Locality code (default: "00" for national average)

**Example:**
```json
{
  "cpt_code": "99213",
  "year": 2024,
  "locality": "00"
}
```

**Output:**
Returns price information:
- `facility_price`: Price for facility setting
- `non_facility_price`: Price for non-facility setting
- `description`: Procedure description
- `status`: "found", "not_found", or "error"

#### 5. `claims_lookup_hcpcs_price`

Lookup HCPCS code price from CMS fee schedules.

**Input:**
- `hcpcs_code` (required): HCPCS procedure code (5-character alphanumeric, e.g., "A0425")
- `year` (optional): Year for fee schedule (default: current year)

**Example:**
```json
{
  "hcpcs_code": "A0425",
  "year": 2024
}
```

**Output:**
Returns price information:
- `price`: Price for the procedure
- `description`: Procedure description
- `status`: "found", "not_found", or "error"

## 📊 EDI File Format

### EDI 837 (Professional Claims)

X12 EDI format for submitting professional healthcare claims. Key segments:

- **ISA/GS/ST**: Interchange, functional group, and transaction headers
- **BHT**: Beginning of transaction
- **NM1**: Name segments (payer, provider, patient)
- **CLM**: Claim information
- **LX/SV1**: Line items with service details
- **HI**: Diagnosis codes

Sample file: `data/samples/sample_837.txt`

### EDI 835 (Remittance Advice)

X12 EDI format for remittance advice (payment information). Key segments:

- **ISA/GS/ST**: Interchange, functional group, and transaction headers
- **BPR**: Beginning of remittance
- **CLP**: Claim payment information
- **CAS**: Claim adjustment segments
- **NM1**: Name segments (payer, payee, patient)

Sample file: `data/samples/sample_835.txt`

## 💾 CMS Fee Schedule Data

### Download Instructions

CMS fee schedules must be downloaded manually from CMS website:

1. **Physician Fee Schedule**: https://www.cms.gov/medicare/physician-fee-schedule
2. **HCPCS Codes**: https://www.cms.gov/medicare/coding-billing/medicare-coding

### File Format

Fee schedule files should be saved as JSON in `data/` directory:

**Physician Fee Schedule** (`pfs_YYYY_LOCALITY.json`):
```json
{
  "99213": {
    "facility_price": 75.50,
    "non_facility_price": 100.25,
    "description": "Office or other outpatient visit"
  }
}
```

**HCPCS Schedule** (`hcpcs_YYYY.json`):
```json
{
  "A0425": {
    "price": 25.00,
    "description": "Ambulance service"
  }
}
```

### Update Frequency

CMS fee schedules are updated annually. Update files at the beginning of each year.

## 🔒 Security & Privacy

⚠️ **Important**: EDI files contain Protected Health Information (PHI)

- **Data Privacy**: EDI files may contain patient names, dates of birth, and medical information
- **HIPAA Compliance**: Ensure proper handling of PHI according to HIPAA regulations
- **Storage**: Do not store EDI files with PHI in unsecured locations
- **Transmission**: Use secure channels when transmitting EDI files

## 🐛 Error Handling

The server handles various error scenarios:

- Invalid EDI format
- Malformed X12 segments
- Missing required fields
- Invalid CPT/HCPCS codes
- Fee schedule not found

All errors are returned in a structured format with error messages.

## 📝 Parser Limitations

The current EDI parser implementation:

- **Basic Parsing**: Handles standard X12 segments but may not support all variations
- **Segment Order**: Assumes standard segment ordering (some EDI files may vary)
- **Complex Claims**: Very complex claims with many nested loops may not parse completely
- **Custom Segments**: Custom or proprietary segments may not be recognized

For production use with complex EDI files, consider:
- Using a commercial EDI parser library
- Extending the parser to handle specific segment variations
- Validating parsed output against business rules

## 🔮 Future Enhancements

### Enhanced EDI Parsing

- Support for institutional claims (837I)
- Support for dental claims (837D)
- Support for pharmacy claims (NCPDP)
- Better handling of complex segment loops

### Additional Features

- Batch processing of multiple EDI files
- Claim validation against business rules
- Denial analysis and reporting
- Integration with claims clearinghouses
- Real-time fee schedule updates

### CMS Data Integration

- Automated fee schedule downloads
- Support for all CMS localities
- Historical fee schedule tracking
- RVU (Relative Value Unit) calculations

## 📚 Reference

- **X12 EDI Standards**: https://x12.org/
- **CMS Physician Fee Schedule**: https://www.cms.gov/medicare/physician-fee-schedule
- **CMS HCPCS Codes**: https://www.cms.gov/medicare/coding-billing/medicare-coding
- **CPT Codes**: https://www.ama-assn.org/amaone/cpt-current-procedural-terminology
- **MCP Protocol**: https://modelcontextprotocol.io/

## 📄 License

See parent repository for license information.

## 🤝 Contributing

See parent repository for contribution guidelines.

