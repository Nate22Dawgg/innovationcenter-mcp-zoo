# Playwright MCP Server

Official Microsoft Playwright MCP server for browser automation.

## Overview

The Playwright MCP server provides enterprise-grade browser automation capabilities using [Playwright](https://playwright.dev). This server enables LLMs to interact with web pages through structured accessibility snapshots, bypassing the need for screenshots or visually-tuned models.

## Key Features

- **Fast and lightweight**: Uses Playwright's accessibility tree, not pixel-based input
- **LLM-friendly**: No vision models needed, operates purely on structured data
- **Deterministic tool application**: Avoids ambiguity common with screenshot-based approaches
- **Enterprise-grade**: Official Microsoft support, production-ready

## Installation

The server is installed via npm/npx:

```bash
npx @playwright/mcp@latest
```

For MCP client configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest"
      ]
    }
  }
}
```

## Requirements

- Node.js 18 or newer
- VS Code, Cursor, Windsurf, Claude Desktop, Goose or any other MCP client

## Biotech Use Cases

This MCP server is particularly valuable for biotech applications:

### FDA Website Monitoring
- Automate checking FDA drug approval pages
- Monitor adverse event reports
- Track device clearances
- Scrape drug labeling updates

### Clinical Trial Site Automation
- Navigate clinical trial registries
- Extract trial data from websites
- Monitor trial status changes
- Collect enrollment information

### Competitor Analysis
- Scrape competitor websites
- Monitor pricing pages
- Track product launches
- Collect market intelligence

### Regulatory Document Collection
- Download FDA documents
- Archive regulatory filings
- Extract structured data from PDFs
- Monitor regulatory updates

## Available Tools

### Core Automation
- `browser_navigate` - Navigate to URLs
- `browser_snapshot` - Capture accessibility tree (LLM-friendly)
- `browser_click` - Click elements
- `browser_type` - Type text into fields
- `browser_fill_form` - Fill multiple form fields
- `browser_take_screenshot` - Capture screenshots
- `browser_evaluate` - Execute JavaScript
- `browser_wait_for` - Wait for conditions
- And many more...

### Tab Management
- `browser_tabs` - Manage browser tabs

### PDF Generation (opt-in)
- `browser_pdf_save` - Save page as PDF (requires `--caps=pdf`)

### Vision/Coordinate-based (opt-in)
- `browser_mouse_click_xy` - Click at coordinates (requires `--caps=vision`)

### Testing (opt-in)
- `browser_generate_locator` - Generate test locators (requires `--caps=testing`)

See the [official Playwright MCP documentation](https://github.com/microsoft/playwright-mcp) for the complete list of tools and capabilities.

## Configuration

The server supports extensive configuration via CLI arguments or a configuration file. Key options include:

- `--headless` - Run browser in headless mode
- `--browser <browser>` - Choose browser (chrome, firefox, webkit, msedge)
- `--caps <caps>` - Enable capabilities (vision, pdf, testing, tracing)
- `--timeout-action <ms>` - Set action timeout
- `--timeout-navigation <ms>` - Set navigation timeout
- `--config <path>` - Path to configuration file

See the main [Playwright MCP README](../README.md) for full configuration options.

## Docker Support

The server can run in Docker for headless environments:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--init", "--pull=always", "mcr.microsoft.com/playwright/mcp"]
    }
  }
}
```

## Resources

- **GitHub**: https://github.com/microsoft/playwright-mcp
- **Official Documentation**: See main README.md in repository root
- **Playwright Docs**: https://playwright.dev
- **License**: Apache 2.0

## Notes

- Browser binaries are downloaded automatically on first use
- The server uses accessibility trees for LLM-friendly page representation
- Some tools require opt-in capabilities (pdf, vision, testing, tracing)
- Safety level is set to "medium" due to browser automation capabilities
