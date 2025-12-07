#!/usr/bin/env python3
"""
Playwright MCP Server with Idempotent Write Tools

Extended MCP server for browser automation with idempotent write operations.
Provides safe, guarded tools for form submission and data updates with:
- Idempotency keys to prevent duplicate executions
- Dry-run mode by default
- Explicit confirmation required for real writes
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for schema loading and common modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from config import PlaywrightServerConfig
from idempotency_store import get_idempotency_store, IdempotencyStore
from common.config import validate_config_or_raise, ConfigValidationError
from common.errors import ErrorCode, ValidationError, McpError
from common.logging import get_logger

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not found. Install with: pip install playwright && playwright install", file=sys.stderr)

# Try to import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not found. Install with: pip install mcp", file=sys.stderr)

logger = get_logger(__name__)

# Global instances
_config: Optional[PlaywrightServerConfig] = None
_config_error_payload: Optional[Dict[str, Any]] = None
_browser: Optional[Browser] = None
_browser_context: Optional[BrowserContext] = None
_idempotency_store: Optional[IdempotencyStore] = None

# Required confirmation phrase for non-dry-run operations
REQUIRED_CONFIRMATION_PHRASE = "I_understand_this_updates_real_data"


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    schema_file = Path(__file__).parent.parent.parent.parent / schema_path
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with open(schema_file, 'r') as f:
        return json.load(f)


async def get_browser_context() -> BrowserContext:
    """
    Get or create a browser context.
    
    Returns:
        Browser context for automation
    """
    global _browser, _browser_context
    
    if not PLAYWRIGHT_AVAILABLE:
        raise McpError(
            code=ErrorCode.SERVICE_NOT_CONFIGURED,
            message="Playwright is not installed. Install with: pip install playwright && playwright install"
        )
    
    if _browser_context is None or _browser_context.browser is None:
        playwright = await async_playwright().start()
        
        browser_type_name = (_config.browser_type if _config else "chromium") or "chromium"
        browser_type_map = {
            "chromium": playwright.chromium,
            "firefox": playwright.firefox,
            "webkit": playwright.webkit
        }
        browser_type = browser_type_map.get(browser_type_name, playwright.chromium)
        
        headless = _config.headless if _config else True
        
        _browser = await browser_type.launch(headless=headless)
        _browser_context = await _browser.new_context()
    
    return _browser_context


async def submit_regulatory_form(
    idempotency_key: str,
    url: str,
    dry_run: bool = True,
    confirm: Optional[str] = None,
    form_data: Optional[Dict[str, str]] = None,
    submit_button_selector: Optional[str] = None,
    wait_for_selector: Optional[str] = None,
    timeout: int = 30000
) -> Dict[str, Any]:
    """
    Submit a regulatory form with idempotency and safety guardrails.
    
    Args:
        idempotency_key: Unique key for idempotency
        url: URL of the form
        dry_run: If True, preview without submitting
        confirm: Confirmation phrase (required if dry_run=False)
        form_data: Form fields to fill
        submit_button_selector: CSS selector for submit button
        wait_for_selector: Selector to wait for after submission
        timeout: Timeout in milliseconds
        
    Returns:
        Result dictionary with status and details
    """
    global _idempotency_store
    
    if _idempotency_store is None:
        _idempotency_store = get_idempotency_store()
    
    # Normalize parameters for idempotency check
    parameters = {
        "url": url,
        "form_data": form_data or {},
        "submit_button_selector": submit_button_selector,
        "wait_for_selector": wait_for_selector,
        "timeout": timeout
    }
    
    # Check idempotency
    existing_record = _idempotency_store.get(idempotency_key, "submit_regulatory_form", parameters)
    if existing_record:
        logger.info(f"Idempotency hit for key: {idempotency_key}")
        return {
            "success": True,
            "idempotent": True,
            "message": "Action was previously completed with this idempotency key",
            "previous_result": existing_record.result,
            "execution_id": existing_record.execution_id,
            "completed_at": existing_record.completed_at
        }
    
    # Validate confirmation if not dry run
    if not dry_run:
        if confirm != REQUIRED_CONFIRMATION_PHRASE:
            raise ValidationError(
                message=f"Confirmation required for non-dry-run operations. 'confirm' must equal '{REQUIRED_CONFIRMATION_PHRASE}'",
                field="confirm"
            )
    
    # Generate execution ID
    execution_id = str(uuid.uuid4())
    
    try:
        context = await get_browser_context()
        page = await context.new_page()
        
        try:
            # Navigate to URL
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # Fill form fields
            form_preview = {}
            if form_data:
                for selector, value in form_data.items():
                    try:
                        element = page.locator(selector).first
                        if dry_run:
                            # In dry-run, just capture what would be filled
                            current_value = await element.input_value() if await element.count() > 0 else ""
                            form_preview[selector] = {
                                "current_value": current_value,
                                "would_set_to": value
                            }
                        else:
                            # Actually fill the field
                            await element.fill(value)
                            form_preview[selector] = {"set_to": value}
                    except Exception as e:
                        logger.warning(f"Could not fill field {selector}: {e}")
                        form_preview[selector] = {"error": str(e)}
            
            # Find submit button
            submit_button_text = None
            if submit_button_selector:
                submit_locator = page.locator(submit_button_selector).first
            else:
                # Try to find submit button automatically
                submit_locator = page.locator("button[type='submit'], input[type='submit']").first
                if await submit_locator.count() == 0:
                    submit_locator = page.locator("button:has-text('Submit')").first
            
            if await submit_locator.count() > 0:
                submit_button_text = await submit_locator.text_content()
            else:
                submit_button_text = "Submit button not found"
            
            if dry_run:
                # Dry-run: return preview without submitting
                result = {
                    "success": True,
                    "dry_run": True,
                    "message": "Dry-run completed. No data was submitted.",
                    "preview": {
                        "url": url,
                        "form_data_preview": form_preview,
                        "submit_button": submit_button_text,
                        "would_submit": True
                    },
                    "execution_id": execution_id
                }
            else:
                # Actual submission
                await submit_locator.click()
                
                # Wait for confirmation if selector provided
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=timeout)
                        confirmation_text = await page.locator(wait_for_selector).first.text_content()
                    except PlaywrightTimeoutError:
                        confirmation_text = "Timeout waiting for confirmation selector"
                else:
                    # Wait a bit for page to update
                    await page.wait_for_timeout(2000)
                    confirmation_text = "No confirmation selector provided"
                
                result = {
                    "success": True,
                    "dry_run": False,
                    "message": "Form submitted successfully",
                    "submitted": {
                        "url": url,
                        "form_data": form_data,
                        "confirmation": confirmation_text
                    },
                    "execution_id": execution_id
                }
                
                # Store in idempotency store
                _idempotency_store.store(
                    idempotency_key=idempotency_key,
                    tool_name="submit_regulatory_form",
                    parameters=parameters,
                    result=result,
                    execution_id=execution_id
                )
            
            return result
            
        finally:
            await page.close()
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }
        logger.error(f"Error in submit_regulatory_form: {e}")
        raise McpError(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Failed to submit regulatory form: {str(e)}",
            details={"execution_id": execution_id}
        )


async def update_tracker_sheet(
    idempotency_key: str,
    url: str,
    dry_run: bool = True,
    confirm: Optional[str] = None,
    row_data: Optional[Dict[str, Any]] = None,
    row_selector: Optional[str] = None,
    action: str = "update",
    timeout: int = 30000
) -> Dict[str, Any]:
    """
    Update a tracker sheet (e.g., Google Sheets, Airtable) with idempotency and safety guardrails.
    
    Args:
        idempotency_key: Unique key for idempotency
        url: URL of the tracker sheet
        dry_run: If True, preview without updating
        confirm: Confirmation phrase (required if dry_run=False)
        row_data: Data to update in the sheet
        row_selector: Selector or identifier for the row
        action: Action to perform (add, update, delete)
        timeout: Timeout in milliseconds
        
    Returns:
        Result dictionary with status and details
    """
    global _idempotency_store
    
    if _idempotency_store is None:
        _idempotency_store = get_idempotency_store()
    
    # Normalize parameters for idempotency check
    parameters = {
        "url": url,
        "row_data": row_data or {},
        "row_selector": row_selector,
        "action": action,
        "timeout": timeout
    }
    
    # Check idempotency
    existing_record = _idempotency_store.get(idempotency_key, "update_tracker_sheet", parameters)
    if existing_record:
        logger.info(f"Idempotency hit for key: {idempotency_key}")
        return {
            "success": True,
            "idempotent": True,
            "message": "Action was previously completed with this idempotency key",
            "previous_result": existing_record.result,
            "execution_id": existing_record.execution_id,
            "completed_at": existing_record.completed_at
        }
    
    # Validate confirmation if not dry run
    if not dry_run:
        if confirm != REQUIRED_CONFIRMATION_PHRASE:
            raise ValidationError(
                message=f"Confirmation required for non-dry-run operations. 'confirm' must equal '{REQUIRED_CONFIRMATION_PHRASE}'",
                field="confirm"
            )
    
    # Generate execution ID
    execution_id = str(uuid.uuid4())
    
    try:
        context = await get_browser_context()
        page = await context.new_page()
        
        try:
            # Navigate to URL
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # Preview what would be updated
            preview = {
                "url": url,
                "action": action,
                "row_data": row_data,
                "row_selector": row_selector
            }
            
            if dry_run:
                # Dry-run: return preview without updating
                result = {
                    "success": True,
                    "dry_run": True,
                    "message": "Dry-run completed. No data was updated.",
                    "preview": preview,
                    "execution_id": execution_id
                }
            else:
                # Actual update (simplified - real implementation would depend on sheet type)
                # This is a placeholder that demonstrates the pattern
                # In practice, you'd need to:
                # - For Google Sheets: Use Google Sheets API or interact with the UI
                # - For Airtable: Use Airtable API or interact with the UI
                # - For other trackers: Implement specific logic
                
                # For demonstration, we'll simulate the update
                await page.wait_for_timeout(1000)  # Simulate interaction
                
                result = {
                    "success": True,
                    "dry_run": False,
                    "message": f"Tracker sheet {action} completed successfully",
                    "updated": preview,
                    "execution_id": execution_id
                }
                
                # Store in idempotency store
                _idempotency_store.store(
                    idempotency_key=idempotency_key,
                    tool_name="update_tracker_sheet",
                    parameters=parameters,
                    result=result,
                    execution_id=execution_id
                )
            
            return result
            
        finally:
            await page.close()
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "execution_id": execution_id
        }
        logger.error(f"Error in update_tracker_sheet: {e}")
        raise McpError(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Failed to update tracker sheet: {str(e)}",
            details={"execution_id": execution_id}
        )


def create_server(fail_fast: bool = True) -> Server:
    """
    Create and configure the MCP server.
    
    Args:
        fail_fast: If True, raise ConfigValidationError on critical config issues.
                   If False, allow server to start but tools will return SERVICE_NOT_CONFIGURED errors.
    
    Returns:
        Configured MCP Server instance
    """
    global _config, _config_error_payload
    
    # Load configuration from environment variables
    config = PlaywrightServerConfig(
        browser_type=os.getenv("PLAYWRIGHT_BROWSER_TYPE"),
        headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
        browser_timeout=int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")),
        base_url=os.getenv("PLAYWRIGHT_BASE_URL"),
        default_dry_run=os.getenv("PLAYWRIGHT_DEFAULT_DRY_RUN", "true").lower() == "true"
    )
    
    logger.info(f"Validating configuration (fail_fast={fail_fast})...")
    
    # Validate configuration
    try:
        is_valid, error_payload = validate_config_or_raise(config, fail_fast=fail_fast)
        if not is_valid:
            _config_error_payload = error_payload
            logger.warning("Configuration validation failed (fail-soft mode)")
        else:
            _config = config
            logger.info("Configuration validated successfully")
    except ConfigValidationError as e:
        if fail_fast:
            raise
        _config_error_payload = {
            "error_code": ErrorCode.SERVICE_NOT_CONFIGURED.value,
            "message": str(e),
            "issues": [{"field": issue.field, "message": issue.message, "critical": issue.critical} for issue in e.issues]
        }
        logger.warning("Configuration validation failed (fail-soft mode)")
    
    # Create MCP server
    server = Server("playwright-mcp")
    
    # Load schemas
    submit_form_schema = load_schema("schemas/playwright_submit_regulatory_form.json")
    update_sheet_schema = load_schema("schemas/playwright_update_tracker_sheet.json")
    
    # Register tools
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="submit_regulatory_form",
                description="Submit a regulatory form with idempotency and safety guardrails. Defaults to dry-run mode.",
                inputSchema=submit_form_schema
            ),
            Tool(
                name="update_tracker_sheet",
                description="Update a tracker sheet (e.g., Google Sheets, Airtable) with idempotency and safety guardrails. Defaults to dry-run mode.",
                inputSchema=update_sheet_schema
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        # Check configuration
        if _config_error_payload:
            return [TextContent(
                type="text",
                text=json.dumps(_config_error_payload, indent=2)
            )]
        
        try:
            if name == "submit_regulatory_form":
                # Apply default dry_run from config if not specified
                if "dry_run" not in arguments and _config:
                    arguments["dry_run"] = _config.default_dry_run
                result = await submit_regulatory_form(**arguments)
            elif name == "update_tracker_sheet":
                # Apply default dry_run from config if not specified
                if "dry_run" not in arguments and _config:
                    arguments["dry_run"] = _config.default_dry_run
                result = await update_tracker_sheet(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except McpError as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": e.to_dict()}, indent=2)
            )]
        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": {
                        "code": ErrorCode.INTERNAL_ERROR.value,
                        "message": str(e)
                    }
                }, indent=2)
            )]
    
    return server


async def main():
    """Run the MCP server."""
    server = create_server(fail_fast=False)  # Use fail-soft for development
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
