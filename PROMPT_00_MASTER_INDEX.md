# MCP ANALYST PLATFORM - MASTER PROMPT INDEX

## 📋 Overview

This directory contains **discrete, self-contained prompts** for deploying the complete MCP Analyst Platform. Each prompt can be used in a **separate chat context** to work on different parts of the system in parallel.

## 🎯 Project Context

**Repository**: `innovationcenter-mcp-zoo`  
**Goal**: Build a registry and collection of MCP (Model Context Protocol) servers for multi-domain healthcare/finance analytics

**Current State**:
- Registry structure exists (`registry/tools_registry.json`)
- Clinical Trials API exists (Python, needs MCP wrapper)
- Schemas defined for several tools
- Architecture documented

**Target State**: 7+ production-ready MCP servers covering:
- Clinical trials, PubMed, FDA data
- Hospital pricing transparency
- Claims/EDI processing
- Biotech private markets
- Real estate deal flow
- NHANES public health data

---

## 📚 Prompt Files (Use in Separate Chats)

### **Phase 1: Clone Existing Servers** (2 hours)
**File**: `PROMPT_01_CLONE_PUBMED_FDA.md`  
**Goal**: Clone and integrate PubMed MCP and OpenFDA MCP servers from GitHub  
**Dependencies**: None  
**Output**: 2 working MCP servers in `servers/misc/`

---

### **Phase 2: Clinical Trials MCP** (6-8 hours)
**File**: `PROMPT_02_CLINICAL_TRIALS_MCP.md`  
**Goal**: Build complete MCP server wrapper around existing Python API  
**Dependencies**: None (Python API already exists)  
**Output**: Full MCP server in `servers/clinical/clinical-trials-mcp/`

---

### **Phase 3A: Hospital Pricing MCP** (8-12 hours)
**File**: `PROMPT_03_HOSPITAL_PRICING_MCP.md`  
**Goal**: Build MCP server for hospital price transparency (Turquoise Health API wrapper)  
**Dependencies**: Turquoise Health API key (trial available)  
**Output**: MCP server in `servers/pricing/hospital-pricing-mcp/`

---

### **Phase 3B: Claims/EDI MCP** (16-24 hours)
**File**: `PROMPT_04_CLAIMS_EDI_MCP.md`  
**Goal**: Build MCP server for EDI 837/835 parsing and claims processing  
**Dependencies**: None (uses open-source parsers)  
**Output**: MCP server in `servers/claims/claims-edi-mcp/`

---

### **Phase 3C: Biotech Markets MCP** (20-28 hours)
**File**: `PROMPT_05_BIOTECH_MARKETS_MCP.md`  
**Goal**: Build MCP server for biotech private markets and drug pipeline tracking  
**Dependencies**: None (uses free APIs: ClinicalTrials.gov, SEC EDGAR)  
**Output**: MCP server in `servers/markets/biotech-markets-mcp/`

---

### **Phase 3D: Real Estate Extension** (40-48 hours)
**File**: `PROMPT_06_REAL_ESTATE_EXTEND.md`  
**Goal**: Fork and extend batchdata-mcp-real-estate with free data sources  
**Dependencies**: Optional BatchData.io API key  
**Output**: Extended MCP server in `servers/real-estate/real-estate-mcp/`

---

### **Phase 3E: NHANES Data MCP** (12-16 hours)
**File**: `PROMPT_07_NHANES_MCP.md`  
**Goal**: Build MCP server for NHANES public health survey data  
**Dependencies**: None (public data)  
**Output**: MCP server in `servers/clinical/nhanes-mcp/`

---

### **Phase 4: Registry Updates** (2-4 hours)
**File**: `PROMPT_08_REGISTRY_UPDATE.md`  
**Goal**: Update `registry/tools_registry.json` with all new servers  
**Dependencies**: All previous phases (or run after each server)  
**Output**: Updated registry with all tools documented

---

## 🚀 Usage Instructions

1. **Start with Phase 1** (cloning) - fastest, validates setup
2. **Run Phases 2-3 in parallel** - each prompt is self-contained
3. **Run Phase 4** after each server or at the end

### Example Workflow:

```
Chat 1: PROMPT_01_CLONE_PUBMED_FDA.md
Chat 2: PROMPT_02_CLINICAL_TRIALS_MCP.md
Chat 3: PROMPT_03_HOSPITAL_PRICING_MCP.md
Chat 4: PROMPT_04_CLAIMS_EDI_MCP.md
Chat 5: PROMPT_05_BIOTECH_MARKETS_MCP.md
Chat 6: PROMPT_06_REAL_ESTATE_EXTEND.md (optional, longest)
Chat 7: PROMPT_07_NHANES_MCP.md
Chat 8: PROMPT_08_REGISTRY_UPDATE.md (final consolidation)
```

---

## ✅ Completion Checklist

After each prompt completes, verify:
- [ ] Server starts without errors
- [ ] All tools are registered and callable
- [ ] Test queries return expected data
- [ ] README.md exists with setup instructions
- [ ] Server added to registry (or note for Phase 4)

---

## 📊 Total Estimated Effort

- Phase 1: **2 hours**
- Phase 2: **6-8 hours**
- Phase 3A: **8-12 hours**
- Phase 3B: **16-24 hours**
- Phase 3C: **20-28 hours**
- Phase 3D: **40-48 hours** (optional)
- Phase 3E: **12-16 hours**
- Phase 4: **2-4 hours**

**Total: 106-142 hours** (2.5-3.5 weeks full-time, or 2-3 weeks with parallel execution)

---

## 🎯 Next Steps

1. Open `PROMPT_01_CLONE_PUBMED_FDA.md` in a new chat
2. Copy the entire contents
3. Paste into Cursor and execute
4. Move to next prompt when complete

Each prompt is **completely self-contained** - no need to reference other prompts during execution.

