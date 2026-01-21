# STRYDA COMPLIANCE PROTOCOL V2.0
## Master Ingestion & Agent Protocol for NZ Building Code RAG System

---

## 📋 TABLE OF CONTENTS
1. [Overview](#overview)
2. [Naming Standards](#naming-standards)
3. [4-Sector Anchor Hierarchy](#4-sector-anchor-hierarchy)
4. [Handshake Logic](#handshake-logic)
5. [Guardrail Extraction Rules](#guardrail-extraction-rules)
6. [Audit Framework](#audit-framework)

---

## 🎯 OVERVIEW

The STRYDA Compliance Protocol V2.0 establishes a standardized framework for ingesting, organizing, and cross-referencing NZ Building Code compliance documents with manufacturer product data. This protocol enables AI agents (Inspector, Engineer, Product Rep) to provide accurate, citation-backed responses during compliance audits.

### Core Principles
- **Traceability**: Every chunk links back to source PDF with page number
- **Deduplication**: SHA-256 page hashing prevents duplicate ingestion
- **Weaponized Guardrails**: Critical compliance values extracted into structured `unit_range` field
- **Agent Assignment**: Documents tagged with appropriate agent owners

---

## 📝 NAMING STANDARDS

### Rule S1: Context-Aware Naming
All files must follow the pattern:
```
[Category] - [Standard/Brand] - [Document Type] ([Edition/Version]).pdf
```

### Examples by Category:

#### NZBC Acceptable Solutions
```
NZBC - E2_AS1 - External Moisture (4th Ed 2025).pdf
NZBC - H1_AS1 - Energy Efficiency (6th Ed 2026).pdf
NZBC - F4_AS1 - Safety from Falling (Amd 6 2021).pdf
```

#### Standards
```
Standards - NZS 3604_2011 - Timber-framed Buildings.pdf
Standards - NZS 3602_2003 - Timber and Wood-based Products for Building.pdf
Standards - AS_NZS 3000_2018 - Electrical Wiring Rules (Changes Guide).pdf
```

#### MBIE Guidance
```
MBIE - Materials and Workmanship Tolerances Guide.pdf
WorkSafe - Designing and Installing Safe Electrical Installations.pdf
```

#### Industry Codes
```
Industry - NZ Metal Roofing Code of Practice.pdf
Industry - BRANZ House Insulation Guide (6th Ed V2.4).pdf
GIB - Fire Rated Systems Manual.pdf
```

#### Manufacturer Products
```
[Brand] - [Product Line] - [Document Type] ([Year]).pdf

Marshall - Tekton - BPIR (Dec 2023).pdf
Masons - 40 Below Platinum - Technical Data Sheet.pdf
Kingspan - Kooltherm K12 - Installation Guide (v10).pdf
```

### Rule S2: Sanitization
- Remove special characters: `:` → `_`, `/` → `_`
- No double spaces
- Preserve version numbers and dates
- Use Title Case for main terms

---

## 🏗️ 4-SECTOR ANCHOR HIERARCHY

The STRYDA library is organized into 4 primary sectors with hierarchical numbering:

### Hierarchy Levels

| Level | Type | Priority | Description |
|-------|------|----------|-------------|
| **1** | Building Code | 95-100 | NZBC, AS/NZS Standards |
| **2** | Industry Guidance | 85-90 | BRANZ, MBIE, Industry COPs |
| **3** | Manufacturer | 75-85 | TDS, Install Guides, BPIRs |
| **3.5** | Source Truth | 90 | Manufacturer "Gold Standard" docs |

### Folder Structure

```
product-library/
│
├── 01_Compliance/                    [Hierarchy 1-2]
│   ├── NZBC_Acceptable_Solutions/    [Level 1]
│   ├── Standards/                    [Level 1]
│   ├── MBIE_Guidance/                [Level 2]
│   ├── Industry_Codes/               [Level 2]
│   └── _Archive_Expired/             [Inactive]
│
├── A_Structure/                      [Hierarchy 3]
│   └── [Structural manufacturers]
│
├── B_Enclosure/                      [Hierarchy 3]
│   ├── Cladding/
│   ├── Roofing/
│   └── Underlays_and_Wraps/
│       ├── Marshall/
│       ├── Masons/
│       └── Kingspan_Thermakraft/
│
├── C_Interiors/                      [Hierarchy 3]
│   ├── Kingspan_Insulation/
│   ├── Knauf_Insulation/
│   └── [Other interior products]
│
└── F_Manufacturers/                  [Hierarchy 3]
    └── [Brand-wide documents]
```

---

## 🤝 HANDSHAKE LOGIC

The Handshake Logic cross-references manufacturer product claims against governing code requirements.

### Anchor Key System

Each compliance concept is assigned an **Anchor Key** that links:
- **Code Source**: The governing standard/clause
- **Product Data**: Manufacturer specifications
- **Validation Rule**: Pass/fail criteria

### Master Anchor Keys

| Anchor Key | Unit | Code Source | Validation Rule |
|------------|------|-------------|-----------------|
| `UV_LIMIT` | days | E2-AS1 | `product_uv ≤ 180 days` |
| `R_VALUE_CEILING` | m²K/W | H1-AS1 | `product_R ≥ 6.6` (2026) |
| `R_VALUE_WALL` | m²K/W | H1-AS1 | `product_R ≥ 2.0` |
| `R_VALUE_FLOOR` | m²K/W | H1-AS1 | `product_R ≥ 1.3` |
| `TIMBER_HAZARD_CLASS` | H-class | NZS 3602 | `product_H ≥ required_H` |
| `WIND_ZONE` | zone | E2-AS1 | Zone-appropriate fixing |
| `FIRE_RATING` | FRR mins | C-AS1 | `product_FRR ≥ required` |
| `SILL_REQUIREMENT` | layers | E2-AS1 | `layers ≥ 2` |
| `AIR_GAP` | mm | E2-AS1/H1 | `gap ≥ 25mm` |
| `CODEMARK` | boolean | MBIE | Valid certificate |
| `BRANZ_APPRAISAL` | number | BRANZ | Valid appraisal |
| `BPIR_CLASS` | class | Regs 2022 | Class 1 or 2 declared |
| `RCD_REQUIRED` | mA | AS/NZS 3000 | `≤ 30mA` |
| `BALUSTRADE_HEIGHT` | mm | F4-AS1 | `≥ 1000mm` |

### Handshake Process

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CODE SOURCE    │    │   HANDSHAKE     │    │    PRODUCT      │
│  (Level 1-2)    │───▶│   VALIDATOR     │◀───│   (Level 3)     │
│                 │    │                 │    │                 │
│ • H1-AS1 R6.6   │    │ Compare values  │    │ • Knauf R7.0    │
│ • E2 UV 180d    │    │ Apply rules     │    │ • Masons UV180  │
│ • F4 1000mm     │    │ Generate status │    │ • Marshall BPIR │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  AUDIT RESULT   │
                       │ ✅ PASS         │
                       │ ❌ FAIL         │
                       │ ⚠️ UNVERIFIED   │
                       └─────────────────┘
```

---

## 🛡️ GUARDRAIL EXTRACTION RULES

### Rule 6: Intelligence-First Extraction

During ingestion, scan for and extract critical compliance data points:

#### Mandatory Extractions

| Data Type | Pattern | Storage Field |
|-----------|---------|---------------|
| UV Exposure | `\d+ days UV` | `unit_range.uv_exposure_limit_days` |
| R-Values | `R\d\.\d` | `unit_range.r_value` |
| Hazard Class | `H\d\.\d` | `unit_range.hazard_class` |
| Wind Zone | `(Very High\|High\|Medium\|Low)` | `unit_range.wind_zone` |
| Fire Rating | `FRR \d+/\d+/\d+` | `unit_range.fire_rating` |

#### Rule S4: The Trinity
For key products, ensure all three core documents are present:
1. **Installation Guide** - How to install
2. **Technical Data Sheet (TDS)** - Specifications
3. **BPIR/CodeMark/BRANZ** - Compliance certification

#### Rule S8: Version Control
- Always prefer latest edition
- Mark expired documents with `_EXPIRED` suffix
- Move superseded docs to `_Archive_Expired/`

---

## 📊 AUDIT FRAMEWORK

### 2026 Code Requirements

| Requirement | Value | Source |
|-------------|-------|--------|
| Ceiling R-Value | ≥ R6.6 | H1-AS1 6th Ed |
| Wall R-Value | ≥ R2.0 | H1-AS1 6th Ed |
| Floor R-Value | ≥ R1.3 | H1-AS1 6th Ed |
| Max UV Exposure | ≤ 180 days | E2-AS1 4th Ed |
| Air Gap | ≥ 25mm | E2-AS1 / H1 |
| Sill Flashing | 2 layers | E2-AS1 |
| Balustrade Height | ≥ 1000mm | F4-AS1 |
| RCD Sensitivity | ≤ 30mA | AS/NZS 3000 |

### Audit Status Definitions

| Status | Meaning |
|--------|---------|
| ✅ **PASS** | All guardrail checks meet 2026 requirements |
| ❌ **FAIL** | One or more guardrails exceed limits |
| ⚠️ **UNVERIFIED** | Insufficient data for validation |

### Agent Assignment

| Agent | Responsibility | Document Types |
|-------|---------------|----------------|
| **Inspector** | Installation compliance | Install Guides, COPs |
| **Engineer** | Technical specifications | TDS, Standards, Calcs |
| **Product_Rep** | Certification & claims | BPIR, CodeMark, EPDs |

---

## 📁 DATABASE SCHEMA

### Key Fields (Protocol V2.0)

| Field | Type | Purpose |
|-------|------|---------|
| `page_hash` | SHA-256 | Deduplication |
| `hierarchy_level` | int | 1-3.5 priority |
| `agent_owner` | array | Assigned agents |
| `unit_range` | JSONB | Extracted guardrails |
| `geo_context` | string | NZ_Specific |
| `doc_type` | string | Document classification |
| `brand_name` | string | Manufacturer |
| `trade` | string | Product category |
| `is_active` | boolean | Current/expired |

---

## 🔄 REVISION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-01-21 | Full protocol rewrite, H1 2026 integration |
| 1.0 | 2025-12-01 | Initial protocol |

---

**Document Owner:** STRYDA AI System  
**Last Updated:** 2026-01-21  
**Classification:** Internal Protocol
