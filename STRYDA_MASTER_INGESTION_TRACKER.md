# STRYDA v2 - MASTER INGESTION TRACKER
================================================================================

**Last Updated:** 2025-01-09
**Version:** 1.0

This document tracks all PDFs in the STRYDA knowledge base and their ingestion
status across both the **Text Agents** (Foreman, Inspector, Product Rep) and
the **Visual Agent** (Engineer).

---

# 🏗️ 4-AGENT ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                        THE FOREMAN                              │
│                    (Router & Orchestrator)                      │
│                   Has access to ALL agents                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          ▼               ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  THE INSPECTOR  │ │ PRODUCT REP │ │ THE ENGINEER│ │   (Future)  │
│  (Compliance)   │ │  (Supplier) │ │  (Visuals)  │ │             │
│                 │ │             │ │             │ │             │
│ • Building Code │ │ • TDS       │ │ • Drawings  │ │             │
│ • NZS Standards │ │ • Manuals   │ │ • Tables    │ │             │
│ • AS/VM Docs    │ │ • Guides    │ │ • Diagrams  │ │             │
│ • MBIE Guidance │ │ • Appraisals│ │ • Profiles  │ │             │
└─────────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
     TEXT AGENT         TEXT AGENT    VISUAL AGENT
```

---

# 📊 GRAND SUMMARY

| Metric | Count | Status |
|--------|-------|--------|
| **Total PDFs in Storage** | 1,251 | |
| Compliance PDFs (`pdfs` bucket) | 36 | ✅ 100% Ingested |
| Product PDFs (`product-library` bucket) | 1,215 | ✅ Partially Ingested |
| **Text Chunks Ingested** | 37,485 | ✅ |
| **Visual Assets Ingested** | 1 | ⚠️ Pending |

---

# 🔍 AGENT ZONE 1: THE INSPECTOR (Compliance)

**Role:** Compliance Expert - Retrieves regulatory/legal documents  
**Priority:** HIGHEST - Cannot be overruled by other agents  
**Database:** `documents` table (doc_type filter)

**Doc Types Served:**
- Building_Code, Compliance_Document, standard
- acceptable_solution, verification_method
- legislation, Building_Act, MBIE_Guidance
- NZS_Standard, NZS_3604, NZS_4229

## 📜 Compliance Documents (`pdfs` bucket) - 36 PDFs

### Building Code & Structure
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| building-code.pdf | ✅ 494 | ⬜ | READY |
| B1-Structure-Amendment13.pdf | ✅ 173 | ⬜ | READY |
| b1-structure-as1-second-edition.pdf | ✅ 71 | ⬜ | READY |

### C - Fire Safety (Protection from Fire)
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| C-AS1_2nd-Edition_2023.pdf | ✅ 133 | ⬜ | READY |
| C-AS2_2nd-Edition_2025.pdf | ✅ 345 | ⬜ | READY |
| C-AS3_Amendment-4_2019-EXPIRED.pdf | ✅ 242 | ⬜ | LEGACY |
| C-AS4_Amendment-4_2019-EXPIRED.pdf | ✅ 268 | ⬜ | LEGACY |
| C-AS5_Amendment-4_2019-EXPIRED.pdf | ✅ 241 | ⬜ | LEGACY |
| C-AS6_Amendment-4_2019-EXPIRED.pdf | ✅ 211 | ⬜ | LEGACY |
| C-AS7_Amendment-4_2019-EXPIRED.pdf | ✅ 33 | ⬜ | LEGACY |
| C-VM2_Amendment-6_2020.pdf | ✅ 225 | ⬜ | READY |

### E - Moisture (External & Internal)
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| E1-AS1_1st-Edition-Amd12-2024.pdf | ✅ 128 | ⬜ | READY |
| E2-AS1_4th-Edition-2025.pdf | ✅ 491 | ⬜ | READY |
| e2-external-moisture-as1-fourth-edition.pdf | ✅ 64 | ⬜ | READY |
| E3-AS1_2nd-Edition-Amd7-2020.pdf | ✅ 42 | ⬜ | READY |

### F - Safety of Users
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| F4-AS1_Amendment-6-2021.pdf | ✅ 28 | ⬜ | READY |
| F6-AS1_Amendment-3-2021.pdf | ✅ 34 | ⬜ | READY |
| F7-AS1_5th-Edition-2023.pdf | ✅ 21 | ⬜ | READY |

### G - Services & Facilities
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| G12-AS1_3rd-Edition-Amd14-2024.pdf | ✅ 192 | ⬜ | READY |
| G13-AS1_3rd-Edition-Amd14-2024.pdf | ✅ 96 | ⬜ | READY |

### H - Energy Efficiency
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| H1-AS1_6th-Edition.pdf | ✅ 177 | ⬜ | READY |
| H1-VM1_6th-Edition-2025.pdf | ✅ 125 | ⬜ | READY |

### NZ Standards
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| NZS-36042011.pdf | ✅ 1,044 | ⬜ | READY |
| NZS-42292013.pdf | ✅ 361 | ⬜ | READY |
| SNZ-HB-3604-2011-Selected-Extracts.pdf | ✅ 1,044 | ⬜ | READY |

### MBIE Guidance
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| MBIE-Minor-Variation-Guidance.pdf | ✅ 41 | ⬜ | READY |
| MBIE-Schedule-1-Exemptions-Guidance.pdf | ✅ 332 | ⬜ | READY |
| MBIE-Tolerances-Guide.pdf | ✅ 225 | ⬜ | READY |

### Industry Codes of Practice
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| nz_metal_roofing.pdf | ✅ 1,092 | ⬜ | READY |
| Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-2020.pdf | ✅ 521 | ⬜ | READY |
| WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf | ✅ 74 | ⬜ | READY |
| Ardex-Waterproofing-Manual.pdf | ✅ 911 | ⬜ | READY |

### GIB Specific (Compliance)
| Document | Text | Visual | Status |
|----------|------|--------|--------|
| GIB-Bracing-Supplement-2016.pdf | ✅ 48 | ⬜ | READY |
| GIB-EzyBrace-Systems-2016.pdf | ✅ 91 | ⬜ | READY |
| GIB-Fire-Systems-Manual.pdf | ✅ 409 | ⬜ | READY |

**Inspector Zone Total:** ~7,000 text chunks

---

# 📦 AGENT ZONE 2: THE PRODUCT REP (Supplier Data)

**Role:** Supplier Data Expert - Retrieves manufacturer/product documents  
**Priority:** MEDIUM - Can be overruled by Inspector  
**Database:** `documents` table (doc_type filter)

**Doc Types Served:**
- Technical_Data_Sheet, Installation_Guide, Technical_Manual
- Product_Manual, BRANZ_Appraisal, Certification
- Product_Catalog, warranty

## 🏠 A_Structure (Structural Products)

### Abodo Wood (78 PDFs)
**Text:** 1,074 chunks | **Visuals:** 0
- Brochures & Fact Sheets (4 PDFs)
- Certificates & Warranties (8 PDFs)
- Color Finishes & Textures (6 PDFs)
- Environmental Product Declaration (1 PDF)
- Guides & Manuals (13 PDFs)
- **Profile Drawings (29 PDFs)** ← ENGINEER PRIORITY
- Reports (2 PDFs)
- Safety Data Sheets (4 PDFs)
- Technical Data Sheets (20 PDFs)

### CHH Woodproducts (17 PDFs)
**Text:** 361 chunks | **Visuals:** 0
- Laserframe guides
- Pinex treatment specs
- Timber treatment data

### Firth (10 PDFs)
**Text:** 341 chunks | **Visuals:** 0
- RibRaft Technical Manual
- X-Pod Installation/Design Guides
- Masonry & Paving guides

### J&L Duke (18 PDFs)
**Text:** 203 chunks | **Visuals:** 0
- JFrame design guides
- TriBoard construction system
- TGV panel specs

### Red Stag (12 PDFs)
**Text:** 65 chunks | **Visuals:** 0
- Timber grade specs
- Treatment data sheets

## 🧱 B_Enclosure (Cladding, Panels, Roofing)

### Kingspan (66 PDFs)
**Text:** 2,884 chunks | **Visuals:** 0

| Product Range | PDFs | Trade |
|---------------|------|-------|
| Architectural Wall Panel | 9 | wall_panel |
| K-Roc Rockspan Wall | 3 | wall_panel |
| K-Roc Firemaster Wall | 2 | fire_rated_panel |
| Trapezoidal Wall Panel | 11 | wall_panel |
| Trapezoidal Roof Panel | 9 | roof_panel |
| Coldstore Panel | 5 | coldstore_panel |
| Evolution Panelised Facade | 4 | wall_panel |
| Fivecrown Roof/Wall | 3 | roof_panel |
| Kooltherm K12 Framing | 24 | wall_insulation |

**ENGINEER PRIORITY:** Technical drawings in Kingspan folder

### James Hardie (11 PDFs)
**Text:** 2,822 chunks | **Visuals:** 0
- Linea Weatherboard guides
- Stria Cladding specs
- RAB Board installation
- Fire & Acoustic design

### Bradford Ventilation
*Placeholder - no PDFs*

## 🏢 C_Interiors (Insulation, Linings, Acoustics)

### Asona Acoustics (303 PDFs)
**Text:** 521 chunks | **Visuals:** 0
- 52 product ranges
- Ceiling systems, wall panels, acoustic solutions

### Autex (229 PDFs)
**Text:** 2,853 chunks | **Visuals:** 0
- GreenStuf insulation
- Acoustic panels
- Composition range

### Bradford (77 PDFs)
**Text:** 1,274 chunks | **Visuals:** 0
- Gold Batts insulation
- Ceiling batts
- Wall insulation

### Earthwool (49 PDFs)
**Text:** 277 chunks | **Visuals:** 0
- Ceiling insulation
- Wall insulation
- Acoustic solutions

### Expol (36 PDFs)
**Text:** 391 chunks | **Visuals:** 0
- ThermaSlab
- TuffPods
- Platinum Board

### GreenStuf (33 PDFs)
**Text:** 381 chunks | **Visuals:** 0
- Ceiling insulation
- Wall insulation
- Underfloor

### GIB (145 PDFs)
**Text:** 1,103 chunks | **Visuals:** 0
- Plasterboard systems
- Noise control
- Fire systems

### Mammoth (18 PDFs)
**Text:** 277 chunks | **Visuals:** 0
- Polyester insulation

### Pink Batts (83 PDFs)
**Text:** 1,320 chunks | **Visuals:** 0
- Ceiling batts
- Wall insulation
- Underfloor

## 🔩 F_Manufacturers/Fasteners (17 Brands)

| Brand | PDFs | Text Chunks | Visuals |
|-------|------|-------------|---------|
| Bremick | 13 | 732 | 0 |
| Buildex | 4 | 275 | 0 |
| Delfast | 9 | 94 | 0 |
| Ecko | 12 | 189 | 0 |
| MacSim | 1 | 3,938 | 0 |
| Mainland Fasteners | 1 | 106 | 0 |
| MiTek | 2 | 41 | 0 |
| NZSIP | 1 | 109 | 0 |
| NZ Nails | 1 | 5 | 0 |
| Paslode | 5 | 121 | 0 |
| PlaceMakers | 1 | 172 | 0 |
| Pryda | 5 | 533 | 0 |
| Ramset | 1 | 26 | 0 |
| Simpson Strong-Tie | 3 | 591 | 0 |
| SPAX | 2 | 226 | 0 |
| Titan | 1 | 14 | 0 |
| Zenith | 2 | 2,735 | 0 |

---

# 📐 AGENT ZONE 3: THE ENGINEER (Visual Agent)

**Role:** Visual Expert - Retrieves technical drawings, tables, diagrams  
**Priority:** MEDIUM - Works alongside Product Rep  
**Database:** `visuals` table

**Asset Types:**
- TECHNICAL_DRAWING - CAD details, section views
- SPAN_TABLE - Load tables, capacity charts
- PROFILE_DRAWING - Product profiles, dimensions
- INSTALLATION_DIAGRAM - Step-by-step visuals

## Current Status

| Metric | Count |
|--------|-------|
| Total Visual Assets | 1 |
| Brands with Visuals | 1 (Abodo) |

⚠️ **VISUAL INGESTION PENDING**

## Priority PDFs for Visual Extraction

### HIGH PRIORITY
1. **Kingspan Technical Drawings** (66 PDFs)
   - Wall/roof panel details
   - Installation sections
   - Product profiles

2. **Abodo Profile Drawings** (29 PDFs)
   - Cladding profiles
   - Decking profiles
   - Dimension drawings

3. **Simpson Strong-Tie** (3 PDFs)
   - Connector details
   - Load tables
   - Installation diagrams

4. **NZS 3604 Span Tables**
   - Timber span tables
   - Bracing tables
   - Load tables

### MEDIUM PRIORITY
5. Pryda bracing details
6. Asona installation diagrams
7. James Hardie flashing details

---

# 📋 INGESTION STATUS BY BRAND

| Brand | Text Chunks | Visuals | Agent Zone |
|-------|-------------|---------|------------|
| NZ Building Code | 9,671 | 0 | Inspector |
| MacSim | 3,938 | 0 | Product Rep |
| Kingspan | 2,884 | 0 | Product Rep |
| Autex | 2,853 | 0 | Product Rep |
| James Hardie | 2,822 | 0 | Product Rep |
| Zenith | 2,735 | 0 | Product Rep |
| Pink Batts | 1,320 | 0 | Product Rep |
| Bradford | 1,274 | 0 | Product Rep |
| GIB | 1,103 | 0 | Product Rep |
| Abodo Wood | 1,074 | 1 | Product Rep |
| Bremick | 732 | 0 | Product Rep |
| MBIE | 598 | 0 | Inspector |
| Simpson Strong-Tie | 591 | 0 | Product Rep |
| Pryda | 533 | 0 | Product Rep |
| Asona | 521 | 0 | Product Rep |
| Expol | 391 | 0 | Product Rep |
| GreenStuf | 381 | 0 | Product Rep |
| CHH Woodproducts | 361 | 0 | Product Rep |
| Firth | 341 | 0 | Product Rep |
| Earthwool | 277 | 0 | Product Rep |
| Mammoth | 277 | 0 | Product Rep |
| SPAX | 226 | 0 | Product Rep |
| J&L Duke | 203 | 0 | Product Rep |
| Ecko | 189 | 0 | Product Rep |
| PlaceMakers | 172 | 0 | Product Rep |
| Paslode | 121 | 0 | Product Rep |
| Mainland Fasteners | 106 | 0 | Product Rep |
| Delfast | 94 | 0 | Product Rep |
| Red Stag | 65 | 0 | Product Rep |
| MiTek | 41 | 0 | Product Rep |
| Ramset | 26 | 0 | Product Rep |
| Titan | 14 | 0 | Product Rep |
| NZ Nails | 5 | 0 | Product Rep |

---

# 📝 CHANGE LOG

| Date | Action | Details |
|------|--------|---------|
| 2025-01-09 | Initial Audit | Created master inventory, identified 1,251 PDFs |
| 2025-01-09 | Bug Fix | Fixed Kingspan K10 triage bypass issue |
| | | |
| | | |

---

# 🎯 NEXT ACTIONS

1. **Run Visual Ingestion Pipeline** on Kingspan technical drawings
2. **Run Visual Ingestion Pipeline** on Abodo profile drawings
3. **Extract span tables** from NZS 3604
4. **Update this tracker** after each ingestion run

---

*End of Document*
