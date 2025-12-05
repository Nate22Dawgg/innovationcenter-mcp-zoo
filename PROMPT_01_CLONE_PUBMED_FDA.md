# PROMPT 01: Clone PubMed & FDA MCP Servers

## 🎯 Objective

Clone and integrate two existing MCP servers from GitHub:
1. **PubMed MCP Server** (cyanheads/pubmed-mcp-server)
2. **OpenFDA MCP Server** (Augmented-Nature/OpenFDA-MCP-Server)

These are production-ready servers that just need to be cloned, tested, and added to the registry.

---

## 📋 Context

**Repository**: `innovationcenter-mcp-zoo`  
**Location**: `/Users/nathanyoussef/Dropbox/Git_Codes/innovationcenter-mcp-zoo`

**Current Structure**:
```
servers/
├── clinical/
│   └── clinical-trials-mcp/  (existing)
├── markets/
├── pricing/
└── misc/  (where external servers go)
```

**Target Structure**:
```
servers/
└── misc/
    ├── pubmed-mcp/  (NEW - cloned)
    └── fda-mcp/     (NEW - cloned)
```

---

## ✅ Tasks

### Task 1: Clone PubMed MCP Server

1. Navigate to `servers/misc/`
2. Clone: `https://github.com/cyanheads/pubmed-mcp-server.git` → `pubmed-mcp/`
3. Install dependencies (`npm install`)
4. Build the server (`npm run build`)
5. Test that it starts (then Ctrl+C)
6. Document API key requirements (NCBI API key - optional but recommended)

### Task 2: Clone OpenFDA MCP Server

1. In `servers/misc/`
2. Clone: `https://github.com/Augmented-Nature/OpenFDA-MCP-Server.git` → `fda-mcp/`
3. Install dependencies (`npm install`)
4. Build the server (`npm run build`)
5. Test that it starts (then Ctrl+C)
6. Document API key requirements (FDA API key - optional)

### Task 3: Create README Files

For each server, create a `README.md` in the server directory with:
- What the server does
- Setup instructions
- API key requirements (if any)
- How to test
- Tool list

### Task 4: Update Registry

Add entries to `registry/tools_registry.json` for:
- PubMed search tools (check what tools the server exposes)
- FDA tools (check what tools the server exposes)

Use the existing registry format as a template.

---

## 🔍 Discovery

**Before cloning, inspect the repos to understand:**
- What tools each server exposes
- What dependencies they need
- What environment variables/API keys are required
- How they're structured (TypeScript? Node.js?)

**PubMed MCP Server**:
- Repo: https://github.com/cyanheads/pubmed-mcp-server
- Likely tools: search_pubmed, get_article, etc.

**OpenFDA MCP Server**:
- Repo: https://github.com/Augmented-Nature/OpenFDA-MCP-Server
- Likely tools: search_drugs, get_recall, search_device, etc.

---

## 📝 Expected Output

1. **Two working MCP servers** in `servers/misc/`:
   - `pubmed-mcp/` - fully built and tested
   - `fda-mcp/` - fully built and tested

2. **README files** for each server with setup instructions

3. **Registry entries** in `registry/tools_registry.json` documenting:
   - Tool IDs, names, descriptions
   - Domain classifications
   - Input/output schema paths (create schemas if needed)
   - Auth requirements
   - Status: "production" (since these are cloned, not built)

4. **Verification**: Both servers should start without errors

---

## 🚨 Important Notes

- **API Keys**: Both servers may work without API keys (rate-limited), but document how to get keys if needed
- **Node.js Version**: Ensure Node.js 18+ is available
- **TypeScript**: These are likely TypeScript servers - ensure `tsc` works
- **Testing**: Don't just clone - actually test that the servers start and expose tools correctly

---

## ✅ Completion Criteria

- [ ] Both servers cloned successfully
- [ ] Both servers build without errors
- [ ] Both servers start without errors
- [ ] README files created for both
- [ ] Registry updated with all tools from both servers
- [ ] Tool schemas created (if not already in schemas/)
- [ ] Validation script passes: `python scripts/validate_registry.py`

---

## 🎯 Next Steps

After completion, move to `PROMPT_02_CLINICAL_TRIALS_MCP.md` or work on other prompts in parallel.

