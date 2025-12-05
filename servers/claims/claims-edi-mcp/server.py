#!/usr/bin/env python3
"""
Claims/EDI MCP Server

MCP server for health insurance claims processing, EDI 837/835 parsing, 
CPT/HCPCS pricing, and claims normalization.

Provides tools for:
- Parsing EDI 837 (Professional Claims) files
- Parsing EDI 835 (Remittance Advice) files
- Normalizing claim line items
- Looking up CPT codes in CMS fee schedules
- Looking up HCPCS codes in CMS fee schedules
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading
sys.path.insert(0, str(Path(__file__).parent))

from edi_parser import (
    parse_edi_837,
    parse_edi_835,
    normalize_claim_line_item,
    extract_cpt_codes,
    extract_hcpcs_codes
)
from cms_fee_schedules import (
    lookup_cpt_price,
    lookup_hcpcs_price
)

# Try to import MCP SDK - fallback to basic implementation if not available
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    # Fallback: create minimal MCP-like interface
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not found. Install with: pip install mcp", file=sys.stderr)


# Load schemas
def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


# Tool implementations
async def claims_parse_edi_837(
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse EDI 837 Professional Claim file.
    
    Args:
        edi_content: EDI file content as string
        edi_file_path: Path to EDI file (alternative to edi_content)
    
    Returns:
        Dictionary with normalized claim data
    """
    try:
        if edi_file_path:
            result = parse_edi_837(edi_file_path)
        elif edi_content:
            result = parse_edi_837(edi_content)
        else:
            return {
                "error": "Either edi_content or edi_file_path must be provided",
                "status": "error"
            }
        
        return result
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


async def claims_parse_edi_835(
    edi_content: Optional[str] = None,
    edi_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse EDI 835 Remittance Advice file.
    
    Args:
        edi_content: EDI file content as string
        edi_file_path: Path to EDI file (alternative to edi_content)
    
    Returns:
        Dictionary with normalized remittance data
    """
    try:
        if edi_file_path:
            result = parse_edi_835(edi_file_path)
        elif edi_content:
            result = parse_edi_835(edi_content)
        else:
            return {
                "error": "Either edi_content or edi_file_path must be provided",
                "status": "error"
            }
        
        return result
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


async def claims_normalize_line_item(
    line_item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize a claim line item to consistent format.
    
    Args:
        line_item: Raw line item dictionary from parser
    
    Returns:
        Normalized line item with standard fields
    """
    try:
        result = normalize_claim_line_item(line_item)
        return {
            "status": "success",
            "normalized_item": result
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }


async def claims_lookup_cpt_price(
    cpt_code: str,
    year: Optional[int] = None,
    locality: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lookup CPT code price from CMS Physician Fee Schedule.
    
    Args:
        cpt_code: CPT procedure code (5-digit, e.g., "99213")
        year: Year for fee schedule (default: current year)
        locality: Locality code (default: "00" for national average)
    
    Returns:
        Dictionary with price information
    """
    try:
        result = lookup_cpt_price(
            cpt_code=cpt_code,
            year=year,
            locality=locality
        )
        return result
    except Exception as e:
        return {
            "cpt_code": cpt_code,
            "error": str(e),
            "status": "error"
        }


async def claims_lookup_hcpcs_price(
    hcpcs_code: str,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lookup HCPCS code price from CMS fee schedules.
    
    Args:
        hcpcs_code: HCPCS procedure code (5-character alphanumeric, e.g., "A0425")
        year: Year for fee schedule (default: current year)
    
    Returns:
        Dictionary with price information
    """
    try:
        result = lookup_hcpcs_price(
            hcpcs_code=hcpcs_code,
            year=year
        )
        return result
    except Exception as e:
        return {
            "hcpcs_code": hcpcs_code,
            "error": str(e),
            "status": "error"
        }


# MCP Server setup
if MCP_AVAILABLE:
    # Create MCP server
    server = Server("claims-edi-mcp")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="claims_parse_edi_837",
                description="Parse EDI 837 Professional Claim file into normalized JSON format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to edi_content)"
                        }
                    },
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_parse_edi_835",
                description="Parse EDI 835 Remittance Advice file into normalized JSON format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "edi_content": {
                            "type": "string",
                            "description": "EDI file content as string"
                        },
                        "edi_file_path": {
                            "type": "string",
                            "description": "Path to EDI file (alternative to edi_content)"
                        }
                    },
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_normalize_line_item",
                description="Normalize a claim line item to consistent format with standard fields",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "line_item": {
                            "type": "object",
                            "description": "Raw line item dictionary from parser"
                        }
                    },
                    "required": ["line_item"],
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_lookup_cpt_price",
                description="Lookup CPT code price from CMS Physician Fee Schedule",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpt_code": {
                            "type": "string",
                            "description": "CPT procedure code (5-digit, e.g., '99213')",
                            "pattern": "^[0-9]{5}$"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for fee schedule (default: current year)",
                            "minimum": 2000,
                            "maximum": 2100
                        },
                        "locality": {
                            "type": "string",
                            "description": "Locality code (default: '00' for national average)",
                            "default": "00"
                        }
                    },
                    "required": ["cpt_code"],
                    "additionalProperties": false
                }
            ),
            Tool(
                name="claims_lookup_hcpcs_price",
                description="Lookup HCPCS code price from CMS fee schedules",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hcpcs_code": {
                            "type": "string",
                            "description": "HCPCS procedure code (5-character alphanumeric, e.g., 'A0425')",
                            "pattern": "^[A-Z][0-9A-Z]{4}$"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for fee schedule (default: current year)",
                            "minimum": 2000,
                            "maximum": 2100
                        }
                    },
                    "required": ["hcpcs_code"],
                    "additionalProperties": false
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "claims_parse_edi_837":
                result = await claims_parse_edi_837(**arguments)
            elif name == "claims_parse_edi_835":
                result = await claims_parse_edi_835(**arguments)
            elif name == "claims_normalize_line_item":
                result = await claims_normalize_line_item(**arguments)
            elif name == "claims_lookup_cpt_price":
                result = await claims_lookup_cpt_price(**arguments)
            elif name == "claims_lookup_hcpcs_price":
                result = await claims_lookup_hcpcs_price(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, indent=2)
            )]
    
    async def main():
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    if __name__ == "__main__":
        asyncio.run(main())

else:
    # Fallback: Simple CLI interface for testing
    async def main():
        """Simple CLI interface for testing."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Claims/EDI MCP Server (CLI Mode)")
        parser.add_argument("--tool", required=True, choices=[
            "parse_837", "parse_835", "normalize", "lookup_cpt", "lookup_hcpcs"
        ])
        parser.add_argument("--edi_file", help="Path to EDI file")
        parser.add_argument("--cpt_code", help="CPT code")
        parser.add_argument("--hcpcs_code", help="HCPCS code")
        parser.add_argument("--year", type=int, help="Year for fee schedule")
        parser.add_argument("--locality", help="Locality code")
        parser.add_argument("--line_item", help="Line item JSON (for normalize)")
        
        args = parser.parse_args()
        
        try:
            if args.tool == "parse_837":
                result = await claims_parse_edi_837(edi_file_path=args.edi_file)
            elif args.tool == "parse_835":
                result = await claims_parse_edi_835(edi_file_path=args.edi_file)
            elif args.tool == "normalize":
                if args.line_item:
                    line_item = json.loads(args.line_item)
                else:
                    line_item = {}
                result = await claims_normalize_line_item(line_item=line_item)
            elif args.tool == "lookup_cpt":
                result = await claims_lookup_cpt_price(
                    cpt_code=args.cpt_code,
                    year=args.year,
                    locality=args.locality
                )
            elif args.tool == "lookup_hcpcs":
                result = await claims_lookup_hcpcs_price(
                    hcpcs_code=args.hcpcs_code,
                    year=args.year
                )
            
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
    
    if __name__ == "__main__":
        asyncio.run(main())

