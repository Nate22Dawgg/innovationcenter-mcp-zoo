# PROMPT 09: Add Microsoft Playwright MCP Server

## 🎯 Objective

Add the official Microsoft Playwright MCP server to the MCP zoo. This server provides enterprise-grade browser automation capabilities that are essential for biotech use cases including web scraping, FDA website monitoring, and clinical trial site automation.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**MCP Details**:
- **Name**: Microsoft Playwright MCP ⭐ Official
- **Built by**: Microsoft (official)
- **GitHub**: https://github.com/microsoft/playwright-mcp
- **License**: Apache 2.0 (open source)
- **NPM Package**: `@playwright/mcp@latest`

**Why for Biotech**:
- Web scraping for clinical trial sites
- Automated FDA website monitoring
- Competitor analysis automation
- Enterprise-grade browser automation

**Target Location**: `servers/misc/playwright-mcp/`

---

## ✅ Tasks

### Task 1: Clone Playwright MCP Server

1. Navigate to `servers/misc/`
2. Clone: `https://github.com/microsoft/playwright-mcp.git` → `playwright-mcp/`
3. Verify repository structure
4. Check package.json for dependencies

### Task 2: Understand Tool Capabilities

The Playwright MCP server provides extensive browser automation tools:

**Core Automation Tools**:
- `browser_navigate` - Navigate to URLs
- `browser_snapshot` - Capture accessibility tree (LLM-friendly)
- `browser_click` - Click elements
- `browser_type` - Type text into fields
- `browser_fill_form` - Fill multiple form fields
- `browser_take_screenshot` - Capture screenshots
- `browser_evaluate` - Execute JavaScript
- `browser_wait_for` - Wait for conditions
- `browser_hover` - Hover over elements
- `browser_drag` - Drag and drop
- `browser_select_option` - Select dropdown options
- `browser_press_key` - Press keyboard keys
- `browser_resize` - Resize browser window
- `browser_close` - Close browser/page
- `browser_navigate_back` - Go back in history
- `browser_run_code` - Run Playwright code snippets
- `browser_handle_dialog` - Handle dialogs
- `browser_file_upload` - Upload files
- `browser_console_messages` - Get console messages
- `browser_network_requests` - List network requests

**Tab Management**:
- `browser_tabs` - Manage browser tabs

**PDF Generation** (opt-in via `--caps=pdf`):
- `browser_pdf_save` - Save page as PDF

**Vision/Coordinate-based** (opt-in via `--caps=vision`):
- `browser_mouse_click_xy` - Click at coordinates
- `browser_mouse_drag_xy` - Drag at coordinates
- `browser_mouse_move_xy` - Move mouse to coordinates

**Testing** (opt-in via `--caps=testing`):
- `browser_generate_locator` - Generate test locators
- `browser_verify_element_visible` - Verify element visibility
- `browser_verify_list_visible` - Verify list visibility
- `browser_verify_text_visible` - Verify text visibility
- `browser_verify_value` - Verify element value

**Tracing** (opt-in via `--caps=tracing`):
- `browser_start_tracing` - Start trace recording
- `browser_stop_tracing` - Stop trace recording

**Installation**:
- `browser_install` - Install browser binaries

### Task 3: Create README

Create `servers/misc/playwright-mcp/README.md` with:
- What the server does
- Setup instructions
- Installation via npm/npx
- Configuration options
- Key features for biotech use cases
- Example usage
- Link to official documentation

### Task 4: Update Registry

Add entries to `registry/tools_registry.json` for core tools:
- Focus on most commonly used tools for biotech automation
- Include tools for navigation, interaction, data extraction
- Set domain: "misc"
- Set status: "active"
- Set safety_level: "medium" (browser automation can be risky)
- Add tags: ["playwright", "browser-automation", "web-scraping", "biotech", "fda-monitoring"]
- Note: Official Microsoft MCP server

### Task 5: Update Documentation

Update main README.md if needed to mention Playwright MCP.

---

## 🔍 Key Features

**Fast and Lightweight**:
- Uses Playwright's accessibility tree, not pixel-based input
- No vision models needed
- Operates purely on structured data

**LLM-Friendly**:
- Accessibility snapshots are better than screenshots for LLM processing
- Deterministic tool application
- Avoids ambiguity common with screenshot-based approaches

**Enterprise-Grade**:
- Official Microsoft support
- Production-ready
- Extensive configuration options
- Supports headless and headed modes
- Docker support available

---

## 📝 Expected Output

1. **Cloned Playwright MCP server** in `servers/misc/playwright-mcp/`
2. **README file** with setup and usage instructions
3. **Registry entries** for core automation tools (10+ tools)
4. **Documentation** of biotech use cases
5. **Verification** that the server structure is correct

---

## 🚨 Important Notes

- **Installation**: Server is installed via `npx @playwright/mcp@latest` - no local build required
- **Browser Binaries**: Playwright will download browser binaries on first use
- **Safety**: Browser automation can be risky - set safety_level to "medium"
- **Configuration**: Supports extensive configuration via CLI args or config file
- **Capabilities**: Some tools require opt-in capabilities (pdf, vision, testing, tracing)
- **Use Cases**: Perfect for FDA website monitoring, clinical trial site scraping, competitor analysis

---

## ✅ Completion Criteria

- [ ] Playwright MCP server cloned successfully
- [ ] README created with setup instructions
- [ ] Registry updated with core automation tools (10+ tools)
- [ ] Tools properly categorized (domain: "misc")
- [ ] Tags include biotech-relevant keywords
- [ ] Safety levels set appropriately
- [ ] Validation script passes: `python scripts/validate_registry.py`
- [ ] Documentation mentions biotech use cases

---

## 🎯 Biotech Use Cases

**FDA Website Monitoring**:
- Automate checking FDA drug approval pages
- Monitor adverse event reports
- Track device clearances
- Scrape drug labeling updates

**Clinical Trial Site Automation**:
- Navigate clinical trial registries
- Extract trial data from websites
- Monitor trial status changes
- Collect enrollment information

**Competitor Analysis**:
- Scrape competitor websites
- Monitor pricing pages
- Track product launches
- Collect market intelligence

**Regulatory Document Collection**:
- Download FDA documents
- Archive regulatory filings
- Extract structured data from PDFs
- Monitor regulatory updates

---

## 🎯 Next Steps

After completion, the Playwright MCP server will be available for use in biotech automation workflows. Consider integrating with other MCP servers for comprehensive data collection and analysis pipelines.

