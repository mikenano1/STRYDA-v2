# STRYDA v2 - MASTER INGESTION TRACKER
================================================================================

**Last Updated:** 2026-01-25 21:15:00
**V4 Nightly Auditor:** ⚡ ACTIVE

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
```

---

# 📊 GRAND SUMMARY

| Metric | Count |
|--------|-------|
| **Total PDFs in Storage** | 4,184+ |
| Compliance PDFs (`pdfs` bucket) | 36 |
| Product PDFs (`product-library` bucket) | 4,148+ |
| **Text Chunks Ingested** | 105,954 |
| **Visual Assets Ingested** | 1 |

## ⚡ V4 SHADOW AUDIT STATUS

| Segment | Chunks | Audit Status | Pass Rate | Certification |
|---------|--------|--------------|-----------|---------------|
| Bremick Fasteners | 8,361 | ✅ PASSED | 90.0% | ⚡ PLATINUM |
| Pryda | 0 | ⏳ PENDING | - | - |
| Simpson Strong-Tie | 0 | ⏳ PENDING | - | - |
| Ecko | 0 | ⏳ PENDING | - | - |

**Nightly Auditor Service:** `/app/services/nightly_auditor.py`
**Schedule:** Daily at 02:00 AM
**Log:** `/app/logs/nightly_mastery.log`

---

# 🔍 AGENT ZONE 1: THE INSPECTOR (Compliance)

**Role:** Compliance Expert - Retrieves regulatory/legal documents
**Priority:** HIGHEST - Cannot be overruled by other agents

**Doc Types Served:**
- Building_Code, Compliance_Document, standard
- acceptable_solution, verification_method
- legislation, Building_Act, MBIE_Guidance
- NZS_Standard, NZS_3604, NZS_4229

## 📜 Compliance Documents (`pdfs` bucket)

| Document | Size | Text Chunks | Visuals | Status |
|----------|------|-------------|---------|--------|
| Ardex-Waterproofing-Manual.pdf | 42.6 MB | ✅ 911 | ⬜ 0 | ✅ READY |
| B1-Structure-Amendment13.pdf | 1.6 MB | ✅ 173 | ⬜ 0 | ✅ READY |
| C-AS1_2nd-Edition_2023.pdf | 2.6 MB | ✅ 133 | ⬜ 0 | ✅ READY |
| C-AS2_2nd-Edition_2025.pdf | 5.8 MB | ✅ 345 | ⬜ 0 | ✅ READY |
| C-AS3_Amendment-4_2019-EXPIRED.pdf | 3.6 MB | ✅ 242 | ⬜ 0 | ✅ READY |
| C-AS4_Amendment-4_2019-EXPIRED.pdf | 4.1 MB | ✅ 268 | ⬜ 0 | ✅ READY |
| C-AS5_Amendment-4_2019-EXPIRED.pdf | 3.9 MB | ✅ 241 | ⬜ 0 | ✅ READY |
| C-AS6_Amendment-4_2019-EXPIRED.pdf | 3.7 MB | ✅ 211 | ⬜ 0 | ✅ READY |
| C-AS7_Amendment-4_2019-EXPIRED.pdf | 1.5 MB | ✅ 33 | ⬜ 0 | ✅ READY |
| C-VM2_Amendment-6_2020.pdf | 2.0 MB | ✅ 225 | ⬜ 0 | ✅ READY |
| CAS3-Amendment4-2019-EXPIRED.pdf | 3.6 MB | ✅ 242 | ⬜ 0 | ✅ READY |
| E1-AS1_1st-Edition-Amd12-2024.pdf | 2.7 MB | ✅ 128 | ⬜ 0 | ✅ READY |
| E2-AS1_4th-Edition-2025.pdf | 12.2 MB | ✅ 491 | ⬜ 0 | ✅ READY |
| E3-AS1_2nd-Edition-Amd7-2020.pdf | 0.9 MB | ✅ 42 | ⬜ 0 | ✅ READY |
| F4-AS1_Amendment-6-2021.pdf | 0.6 MB | ✅ 28 | ⬜ 0 | ✅ READY |
| F6-AS1_Amendment-3-2021.pdf | 0.5 MB | ✅ 34 | ⬜ 0 | ✅ READY |
| F7-AS1_5th-Edition-2023.pdf | 0.5 MB | ✅ 21 | ⬜ 0 | ✅ READY |
| G12-AS1_3rd-Edition-Amd14-2024.pdf | 5.9 MB | ✅ 192 | ⬜ 0 | ✅ READY |
| G13-AS1_3rd-Edition-Amd14-2024.pdf | 3.3 MB | ✅ 96 | ⬜ 0 | ✅ READY |
| GIB-Bracing-Supplement-2016.pdf | 1.8 MB | ✅ 48 | ⬜ 0 | ✅ READY |
| GIB-EzyBrace-Systems-2016.pdf | 3.7 MB | ✅ 91 | ⬜ 0 | ✅ READY |
| GIB-Fire-Systems-Manual.pdf | 9.6 MB | ✅ 409 | ⬜ 0 | ✅ READY |
| H1-AS1_6th-Edition.pdf | 1.5 MB | ✅ 177 | ⬜ 0 | ✅ READY |
| H1-VM1_6th-Edition-2025.pdf | 0.9 MB | ✅ 125 | ⬜ 0 | ✅ READY |
| Internal-WetArea-Membrane-CodeOfPractice_4th-Edition-20 | 2.2 MB | ✅ 521 | ⬜ 0 | ✅ READY |
| MBIE-Minor-Variation-Guidance.pdf.pdf | 2.4 MB | ✅ 41 | ⬜ 0 | ✅ READY |
| MBIE-Schedule-1-Exemptions-Guidance.pdf.pdf | 9.2 MB | ✅ 332 | ⬜ 0 | ✅ READY |
| MBIE-Tolerances-Guide.pdf.pdf | 0.7 MB | ✅ 225 | ⬜ 0 | ✅ READY |
| NZS-36042011.pdf | 10.1 MB | ✅ 1044 | ⬜ 0 | ✅ READY |
| NZS-42292013.pdf | 5.0 MB | ✅ 361 | ⬜ 0 | ✅ READY |
| SNZ-HB-3604-2011-Selected-Extracts.pdf | 10.1 MB | ✅ 1044 | ⬜ 0 | ✅ READY |
| WGANZ-Guide-to-E2-AS1-Amd-10-V1.7-November-2022.pdf | 3.7 MB | ✅ 74 | ⬜ 0 | ✅ READY |
| b1-structure-as1-second-edition.pdf | 0.6 MB | ✅ 71 | ⬜ 0 | ✅ READY |
| building-code.pdf | 1.6 MB | ✅ 494 | ⬜ 0 | ✅ READY |
| e2-external-moisture-as1-fourth-edition.pdf | 22.4 MB | ✅ 64 | ⬜ 0 | ✅ READY |
| nz_metal_roofing.pdf | 17.9 MB | ✅ 1092 | ⬜ 0 | ✅ READY |

**Inspector Total:** 10,269 text chunks

---

# 📦 AGENT ZONE 2: THE PRODUCT REP (Supplier Data)

**Role:** Supplier Data Expert - Retrieves manufacturer/product documents
**Priority:** MEDIUM - Can be overruled by Inspector

**Doc Types Served:**
- Technical_Data_Sheet, Installation_Guide, Technical_Manual
- Product_Manual, BRANZ_Appraisal, Certification
- Product_Catalog, warranty

## 🏠 A_Structure (Structural Products)

### Abodo_Wood (81 PDFs, 79.8 MB)
**Text:** 1,074 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| ABODO-New-TMT-Painting-and-Staining-Spec-Nov-2014.pdf | ✅ 29 | ⬜ 0 |
| AW62-180x20mm-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| AW62P-187x18-Profile-Drawing-Abodo-Wood-Jan-18.pdf | ✅ 2 | ⬜ 0 |
| Abodo-Brochure-New-Growth-Feature-Timbers.pdf | ✅ 41 | ⬜ 0 |
| Abodo-CodeMark-Weatherboard-Cladding-System-Manual.pdf | ✅ 311 | ⬜ 0 |
| Abodo-Codemark-Certification-2020.pdf | ✅ 15 | ⬜ 0 |
| Abodo-Guidelines-for-Vulcan-Cladding-Standard-Series-Clear-2 | ✅ 3 | ⬜ 0 |
| Abodo-Mixed-Length-Specification-Export.pdf | ✅ 1 | ⬜ 0 |
| Abodo-Profile-Drawing-WB18-180x18.pdf | ✅ 1 | ⬜ 0 |
| Abodo-Safety-Data-Sheet-End-Seal-MAY-23-V3.pdf | ✅ 15 | ⬜ 0 |
| Abodo-Safety-Data-Sheet-NZ-Protector-Jan-24.pdf | ✅ 87 | ⬜ 0 |
| Abodo-Safety-Data-Sheet-Vulcan.pdf | ✅ 10 | ⬜ 0 |
| Abodo-Safety-Data-Sheet_Rejuvenator-Wood-Cleaner-May-22.pdf | ✅ 30 | ⬜ 0 |
| Abodo-Semi-Vertical-Grain-SVG-Grain-Orientation-Guidelines.p | ✅ 4 | ⬜ 0 |
| Abodo-Sioox-Wood-Protection-Manual-Apr-23.pdf | ✅ 21 | ⬜ 0 |
| Abodo-Thermal-Conductivity-Memo.pdf | ✅ 1 | ⬜ 0 |
| Abodo-Vulcan-Cladding-Comparison-Guide.pdf | ✅ 1 | ⬜ 0 |
| Abodo-Vulcan-Shingles-Oculus-Compliance-Letter.pdf | ✅ 6 | ⬜ 0 |
| Abodo-Vulcan-Timber-LRV-and-SRI-Guide-May-23.pdf | ✅ 37 | ⬜ 0 |
| Abodo-Wood-Declare-Certification.pdf | ❌ 0 | ⬜ 0 |
| Abodo-Wood-Environmental-Product-Declaration.pdf | ✅ 80 | ⬜ 0 |
| Appearance-Grades-Timber-Grading-Rules-Abodo-Wood.pdf | ✅ 9 | ⬜ 0 |
| BAND4S-138x18-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| BAND4S-180x18-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| BAND4S-42x42-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| BAND4S-65x18-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| BAND4S-88x18-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| Built-to-Last-Warranty-30yrs-ACQ-Abodo-Wood.pdf | ✅ 4 | ⬜ 0 |
| Comparative-Biomass-Growth-and-Carbon-Sequestration-Report-A | ✅ 11 | ⬜ 0 |
| DK14S-90x21-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| DK16V-142x27mm-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| DK4R-140x27-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| FSC-Certificate-SGS-COC-004944.pdf | ✅ 2 | ⬜ 0 |
| Group-Number-Classification-Certificate-Fire-Rating-Abodo-Wo | ✅ 4 | ⬜ 0 |
| How-Vulcan-Timber-Weathers-Abodo-Wood.pdf | ✅ 2 | ⬜ 0 |
| Look-Book-Vulcan-Feature-Timber-Projects.pdf | ✅ 7 | ⬜ 0 |
| M116317-Abodo-Profile-Drawing-Download-Vulcan-Shingles-450x1 | ✅ 1 | ⬜ 0 |
| M116317-Abodo-Profile-Drawing-Download-Vulcan-Shingles-450x9 | ✅ 1 | ⬜ 0 |
| Maintenance-Guidelines-Timber-Cladding-Screening-NZ-Abodo-Wo | ✅ 6 | ⬜ 0 |
| Maintenance-Guidelines-Vulcan-Sand-Decking-Abodo-Wood.pdf | ✅ 6 | ⬜ 0 |
| OPX-Treatment-Guide-Abodo-Wood-Feb-2023.pdf | ✅ 8 | ⬜ 0 |
| Performance-Testing-Guide-for-Vulcan-Timber-Abodo-Wood.pdf | ✅ 36 | ⬜ 0 |
| Resene-Paint-Complementary-Colour-Suggestions.pdf | ✅ 9 | ⬜ 0 |
| Rhombus-Batten-Clip-RHBC2-with-clip-90x26-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| Rhombus-Clip-RHBC2-with-clip-68x26-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| TDS-69-Vulcan-Shingles-Roof-Dec-23.pdf | ✅ 21 | ⬜ 0 |
| TDS-70-Vulcan-Shingles-Wall-Dec-23.pdf | ✅ 20 | ⬜ 0 |
| TG17-84x17-Profile-Drawing-Abodo-Wood.pdf | ✅ 1 | ⬜ 0 |
| TG9-135x10-Profile-Drawing-Abodo-Wood-Jan-18.pdf | ✅ 1 | ⬜ 0 |
| TG9-175x10-Profile-Drawing-Abodo-Wood-Jan-18.pdf | ✅ 1 | ⬜ 0 |
| *... and 31 more PDFs* | | |

### CHH_Woodproducts (16 PDFs, 5.6 MB)
**Text:** 407 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| 2017_CHH-_Pinex_SpecificationInstallationGuide_v3-Web.pdf | ✅ 17 | ⬜ 0 |
| 20191126CHHWP-TIM-Moulds-on-Timber-Technical-Note-September- | ✅ 3 | ⬜ 0 |
| 20191126CHHWP-Trouble-with-Substitutes-Timber-September-2018 | ✅ 5 | ⬜ 0 |
| Antisapstain-Hylite-NCF-Treated-Pine-Solid-Wood-November-201 | ✅ 62 | ⬜ 0 |
| Antisapstain-Treated-Pine-Solid-Wood-July-2017-v3.pdf | ✅ 48 | ⬜ 0 |
| CCA-Treated-Pine-Solid-Wood-May-2018-v2.pdf | ✅ 46 | ⬜ 0 |
| CCA-Treated-Pine-Solid-Wood-May-2018.pdf | ✅ 46 | ⬜ 0 |
| CHH-H1.2-Boron-Treated-Pine-Solid-Wood-V-15.1.1.1-Sept-2019. | ✅ 50 | ⬜ 0 |
| CHHTimberLaserframe68x34CeilingBattenPTSAndBPISCurrent.pdf | ✅ 10 | ⬜ 0 |
| CHHTimberLaserframeResidentialApplicationsPTSAndBPISCurrent. | ✅ 12 | ⬜ 0 |
| CHHTimberPinexAnchorPilesPTSAndBPISCurrent.pdf | ✅ 9 | ⬜ 0 |
| CHHTimberPinexHousePilesPTSAndBPISCurrent-.pdf | ✅ 9 | ⬜ 0 |
| CHHTimberPinexPostsRailsandPalingsPTSAndBPISCurrent.pdf | ✅ 9 | ⬜ 0 |
| CHHTimberPinexVerifiedPTSAndBPISCurrent.pdf | ✅ 14 | ⬜ 0 |
| LaserframeProductGuideCurrent.pdf | ✅ 17 | ⬜ 0 |
| Timber-CHH-LOSP-Azole-Treated-Solid-Wood-Timber-September-20 | ✅ 50 | ⬜ 0 |

### Firth (11 PDFs, 29.6 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| EcoPave_Installation_Guide_Aug_2024.pdf | ❌ 0 | ⬜ 0 |
| Firth_Paving_Category_Flyer_2025.pdf | ❌ 0 | ⬜ 0 |
| Firth_Paving_Concepts_Brochure.pdf | ❌ 0 | ⬜ 0 |
| Firth_Paving_Installation_Guide_2025.pdf | ❌ 0 | ⬜ 0 |
| Hollow_Masonry_Brochure_2023.pdf | ❌ 0 | ⬜ 0 |
| RibRaft_Technical_Manual_CodeMark_2024.pdf | ❌ 0 | ⬜ 0 |
| Structural_Masonry_Product_Technical_Statement.pdf | ❌ 0 | ⬜ 0 |
| Two_Storey_Masonry_Veneer_Solutions.pdf | ❌ 0 | ⬜ 0 |
| X-Pod_Installation_Guide_July_2025.pdf | ❌ 0 | ⬜ 0 |
| X-Pod_Installers_Guide_Dec_2018.pdf | ❌ 0 | ⬜ 0 |
| X-Pod_Structural_Designers_Guide_July_2025.pdf | ❌ 0 | ⬜ 0 |

### JL_Duke (17 PDFs, 31.5 MB)
**Text:** 207 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| 593_2022.pdf | ✅ 20 | ⬜ 0 |
| Inter-Tenancy-Wall-Technical-Literature-1.pdf | ✅ 20 | ⬜ 0 |
| J-Frame-Care-Maintenance-Guide-CodeMark-1-1-2.pdf | ✅ 2 | ⬜ 0 |
| J-Frame-Design-Installation-Guide-2025-1.pdf | ✅ 10 | ⬜ 0 |
| J-Frame-and-Exposure-to-the-Elements-1.pdf | ✅ 4 | ⬜ 0 |
| J-Frame-beam-span-tables-V1.0.pdf | ✅ 42 | ⬜ 0 |
| J-Frame-stud-span-tables-V1.0.pdf | ✅ 14 | ⬜ 0 |
| J-frame-BRANZ.pdf | ✅ 15 | ⬜ 0 |
| Procedure-for-testing-moisture-content-of-J-Frame-2.pdf | ✅ 2 | ⬜ 0 |
| Triboard-Bracing-Details-1.pdf | ✅ 2 | ⬜ 0 |
| Triboard-Brochure-2022-1.pdf | ✅ 10 | ⬜ 0 |
| Triboard-Constuction-System-Appraisal-481.pdf | ✅ 27 | ⬜ 0 |
| Triboard-General-MSDS-2020-1.pdf | ✅ 14 | ⬜ 0 |
| Triboard-Lining-TGV-Panels-Brochure-1.pdf | ✅ 4 | ⬜ 0 |
| Triboard-Lining-TGV-Panels-Brochure-1.pdf | ✅ 4 | ⬜ 0 |
| Triboard-TGV-Lining-Panel-FAQ-1-1.pdf | ✅ 6 | ⬜ 0 |
| Triboard-Wall-Lining-Installation-Sheet-2022.pdf | ✅ 11 | ⬜ 0 |

### Red_Stag (11 PDFs, 5.1 MB)
**Text:** 65 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Boron_Treated_Wood_SDS_2020.pdf | ✅ 10 | ⬜ 0 |
| CCA_Treated_Wood_MSDS_2015.pdf | ✅ 10 | ⬜ 0 |
| CCA_Treated_Wood_SDS_2020.pdf | ✅ 9 | ⬜ 0 |
| LOSP_Treated_Wood_SDS_-_26_Jun_2020.pdf | ✅ 9 | ⬜ 0 |
| Landscaping_Timber_20240229.pdf | ✅ 2 | ⬜ 0 |
| Non_Structural_Timber_20230922.pdf | ✅ 2 | ⬜ 0 |
| Packets_and_Lengths.pdf | ❌ 0 | ⬜ 0 |
| Producers_Statement_2025.pdf | ✅ 3 | ⬜ 0 |
| SDS-FramePro-Treated-Wood_002.pdf | ✅ 12 | ⬜ 0 |
| Structurally_Graded_Timber_20230922.pdf | ✅ 7 | ⬜ 0 |
| Timberwrap_Recycling_options.pdf | ✅ 1 | ⬜ 0 |

## 🧱 B_Enclosure (Cladding, Panels, Roofing)

### Kingspan (46 PDFs, 93.5 MB)
**Text:** 2,045 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Kingspan KS1000 RW CodeMark Roof Details Ver. Q4 2023 -Techn | ✅ 122 | ⬜ 0 |
| Kingspan KS1000 RW CodeMark Roof Details Ver. Q4 2023 -Techn | ✅ 122 | ⬜ 0 |
| Kingspan KS1000 RW CodeMark Roof High Humidity Details Ver.  | ✅ 23 | ⬜ 0 |
| Kingspan KS1000 RW CodeMark Roof High Humidity Details Ver.  | ✅ 23 | ⬜ 0 |
| kingspan-architectural-wall-panel-data-sheet-en-nz.pdf | ✅ 43 | ⬜ 0 |
| kingspan-architectural-wall-panel-environmental-product-decl | ✅ 84 | ⬜ 0 |
| kingspan-architectural-wall-panel-installation-guide-horizon | ✅ 20 | ⬜ 0 |
| kingspan-architectural-wall-panel-installation-guide-vertica | ✅ 18 | ⬜ 0 |
| kingspan-architectural-wall-panel-technical-drawing-horizont | ✅ 130 | ⬜ 0 |
| kingspan-architectural-wall-panel-technical-drawing-vertical | ✅ 122 | ⬜ 0 |
| kingspan-awp-evolution-codemark-certificate-en-nz.pdf | ✅ 23 | ⬜ 0 |
| kingspan-awp-evolution-codemark-certificate-en-nz.pdf | ✅ 23 | ⬜ 0 |
| kingspan-controlled-environment-greentag-certificate-en-nz-a | ❌ 0 | ⬜ 0 |
| kingspan-evolution-panelised-facade-environmental-product-de | ✅ 58 | ⬜ 0 |
| kingspan-k-roc-firemaster-wall-panel-data-sheet-en-nz.pdf | ✅ 17 | ⬜ 0 |
| kingspan-k-roc-firemaster-wall-vertical-technical-drawing-st | ✅ 25 | ⬜ 0 |
| kingspan-k-roc-rockspan-wall-horizontal-technical-drawing-st | ✅ 37 | ⬜ 0 |
| kingspan-k-roc-rockspan-wall-panel-data-sheet-en-nz.pdf | ✅ 26 | ⬜ 0 |
| kingspan-k-roc-rockspan-wall-vertical-technical-drawing-stan | ✅ 37 | ⬜ 0 |
| kingspan-ks1000rw-codemark-certificate-en-nz.pdf | ✅ 18 | ⬜ 0 |
| kingspan-ks1000rw-codemark-certificate-en-nz.pdf | ✅ 18 | ⬜ 0 |
| kingspan-ks1000rw-roof-panel-environmental-product-declarati | ✅ 52 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-roof-panel-installation-guide- | ✅ 28 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-roof-panel-technical-drawing-s | ✅ 33 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-roof-wall-data-sheet-en-nz.pdf | ✅ 67 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-roof-wall-data-sheet-en-nz.pdf | ✅ 67 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-wall-panel-installation-guide- | ✅ 22 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-wall-panel-installation-guide- | ✅ 21 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-wall-panel-technical-drawing-h | ✅ 86 | ⬜ 0 |
| kingspan-ks1000rw-trapezoidal-wall-panel-technical-drawing-v | ✅ 103 | ⬜ 0 |
| *... and 16 more PDFs* | | |

### Wall_Cladding (11 PDFs, 53.9 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Hardie_Oblique_and_Stria_Cladding_Vertical_Installation_Guid | ❌ 0 | ⬜ 0 |
| HomeRAB_Pre-Cladding_and_RAB_Board_Installation_Manual.pdf | ❌ 0 | ⬜ 0 |
| James_Hardie_Facades_Installation_Manual.pdf | ❌ 0 | ⬜ 0 |
| James_Hardie_Fire_and_Acoustic_Design_Manual.pdf | ❌ 0 | ⬜ 0 |
| Linea_Weatherboard_Direct_Fix_Technical_Specification.pdf | ❌ 0 | ⬜ 0 |
| Linea_Weatherboard_Installation_Checklist.pdf | ❌ 0 | ⬜ 0 |
| Linea_Weatherboard_Installation_Guide.pdf | ❌ 0 | ⬜ 0 |
| Linea_Weatherboard_Installation_Guide_Apr23.pdf | ❌ 0 | ⬜ 0 |
| RAB_Board_Installation_Guide_Legacy.pdf | ❌ 0 | ⬜ 0 |
| Stria_Cladding_Vertical_40mm_Structural_Cavity_Batten.pdf | ❌ 0 | ⬜ 0 |
| Stria_Cladding_Vertical_Installation_Technical_Specification | ❌ 0 | ⬜ 0 |

## 🏢 C_Interiors (Insulation, Linings, Acoustics)

### Asona_Acoustics (193 PDFs, 375.4 MB)
**Text:** 567 chunks | **Visuals:** 0

*193 PDFs - see detailed inventory for full list*

### Autex (191 PDFs, 286.0 MB)
**Text:** 8,327 chunks | **Visuals:** 0

*191 PDFs - see detailed inventory for full list*

### Bradford (113 PDFs, 81.0 MB)
**Text:** 1,448 chunks | **Visuals:** 0

*113 PDFs - see detailed inventory for full list*

### Earthwool (16 PDFs, 15.0 MB)
**Text:** 277 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| BRANZ Certificate.pdf | ✅ 21 | ⬜ 0 |
| CodeMark Certificate.pdf | ✅ 53 | ⬜ 0 |
| Earthwool Glasswool Product Guide.pdf | ✅ 67 | ⬜ 0 |
| Earthwool glasswool Building Product Information Sheet.pdf | ✅ 23 | ⬜ 0 |
| Earthwool glasswool Ceiling - Skillion Roof Datasheet.pdf | ✅ 12 | ⬜ 0 |
| Earthwool glasswool Ceiling Installation Instructions.pdf | ✅ 10 | ⬜ 0 |
| Earthwool glasswool Floorshield Underfloor Datasheet.pdf | ✅ 9 | ⬜ 0 |
| Earthwool glasswool Floorshield Underfloor Installation Inst | ✅ 10 | ⬜ 0 |
| Earthwool glasswool Product Finder.pdf | ✅ 10 | ⬜ 0 |
| Earthwool glasswool Product Flyer.pdf | ✅ 7 | ⬜ 0 |
| Earthwool glasswool R1.3 Wall and Ceiling Installation Instr | ✅ 12 | ⬜ 0 |
| Earthwool glasswool Underfloor Roll Datasheet.pdf | ✅ 11 | ⬜ 0 |
| Earthwool glasswool Underfloor Roll Installation Instruction | ✅ 10 | ⬜ 0 |
| Earthwool glasswool Wall Datasheet.pdf | ❌ 0 | ⬜ 0 |
| Earthwool glasswool Wall Installation Instructions.pdf | ✅ 11 | ⬜ 0 |
| Knauf Insulation Internal Partition Datasheet.pdf | ✅ 11 | ⬜ 0 |

### Expol (28 PDFs, 48.7 MB)
**Text:** 411 chunks | **Visuals:** 0

*28 PDFs - see detailed inventory for full list*

### GreenStuf (39 PDFs, 18.2 MB)
**Text:** 411 chunks | **Visuals:** 0

*39 PDFs - see detailed inventory for full list*

### Kingspan_Insulation (109 PDFs, 53.8 MB)
**Text:** 2,408 chunks | **Visuals:** 0

*109 PDFs - see detailed inventory for full list*

### Mammoth (43 PDFs, 13.4 MB)
**Text:** 297 chunks | **Visuals:** 0

*43 PDFs - see detailed inventory for full list*

### Pink_Batts (33 PDFs, 33.0 MB)
**Text:** 0 chunks | **Visuals:** 0

*33 PDFs - see detailed inventory for full list*

### Plasterboard_Linings (5 PDFs, 22.4 MB)
**Text:** 424 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| GIB_Aqualine_Wet_Wall_System_Installation.pdf | ❌ 0 | ⬜ 0 |
| GIB_Fire_and_Noise_Rated_System_Tables.pdf | ❌ 0 | ⬜ 0 |
| GIB_Performance_Systems.pdf | ❌ 0 | ⬜ 0 |
| GIB_Site_Guide_2024.pdf | ✅ 424 | ⬜ 0 |
| GIB_Weatherline_Design_and_Construction_Manual.pdf | ❌ 0 | ⬜ 0 |

## 🔩 F_Manufacturers/Fasteners

### Bremick (291 PDFs, ~50 MB) ⚡ PLATINUM CERTIFIED
**Text:** 8,361 chunks | **Visuals:** 0 | **Audit:** 90.0% Pass Rate

| Document | Text | Visual |
|----------|------|--------|
| Bremick_Industrial_Fasteners_Catalogue.pdf | ✅ 2,100+ | ⬜ 0 |
| Bremick_Masonry_Anchor_Catalogue.pdf | ✅ 1,500+ | ⬜ 0 |
| Bremick_Socket_Screws_Catalogue.pdf | ✅ 1,200+ | ⬜ 0 |
| Bremick_Stainless_Steel_Catalogue.pdf | ✅ 1,100+ | ⬜ 0 |
| + 287 TDS PDFs (Hex Nuts, Bolts, Anchors) | ✅ 2,461 | ⬜ 0 |

**V4 Shadow Audit Results (2026-01-25):**
- Total Questions: 30
- Passed: 27 (90.0%)
- Critical Fails: 3 (cross-domain traps)
- Status: ⚡ PLATINUM CERTIFIED

### Buildex (3 PDFs, 5.8 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Buildex_Low_Profile_Roof_Clip_Fastener_Guide.pdf | ❌ 0 | ⬜ 0 |
| ITW_Buildex_2020_Catalog.pdf | ❌ 0 | ⬜ 0 |
| ITW_Buildex_Catalog_2024-25.pdf | ❌ 0 | ⬜ 0 |

### Delfast (3 PDFs, 5.8 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Delfast_Nails_BRANZ_Appraisal_1154.pdf | ❌ 0 | ⬜ 0 |
| Delfast_PlaceMakers_Nail_Guide_2023.pdf | ❌ 0 | ⬜ 0 |
| Delfast_PlaceMakers_Rural_Range_2021.pdf | ❌ 0 | ⬜ 0 |

### Ecko (44 PDFs, 133.1 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| 0-ECKO-AG16-BRADS.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-BC-BRADS.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-Blue-Head-Screw-Bolt-Installation-Guide.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-Bottom-Plate-Fixing-Installation-Guide-2.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-Bottom-Plate-Fixing-Installation-Guide.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-DA-BRADS.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-EC-BRADS.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-Orange-Head-Screw-Bolt-Installation-Guide.pdf | ❌ 0 | ⬜ 0 |
| 0-ECKO-Through-Bolt-Installation-Guide.pdf | ❌ 0 | ⬜ 0 |
| 1-Bracing-Bracket-SPEC-Sheet-1.pdf | ❌ 0 | ⬜ 0 |
| 1-FrameFit-Packer-SPEC-Sheet_OCT25.pdf | ❌ 0 | ⬜ 0 |
| 1-TurboSpitze-Cladding-Screws-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 12kN-Pile-Fixing-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 2-I-Joist-Hangers-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 2-Joist-Hangers-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 3-CPC-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 3-ECKO-Loose-Nails-Staples.pdf | ❌ 0 | ⬜ 0 |
| 4-ECKO-Collated-Fasteners.pdf | ❌ 0 | ⬜ 0 |
| 4-ECKO-Collated-fasteners-gas-pack.pdf | ❌ 0 | ⬜ 0 |
| 4-Steel-Strap-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 5-ECKO-H-Packer.pdf | ❌ 0 | ⬜ 0 |
| 6-ECKO-Masonry-Fixings.pdf | ❌ 0 | ⬜ 0 |
| 6-MultiGrip-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 6kN-Pile-Fixing-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 7-Split-Hanger-SPEC-Sheet.pdf | ❌ 0 | ⬜ 0 |
| 8-Stud-Strap-SPEC-Sheet-1.pdf | ❌ 0 | ⬜ 0 |
| A1-1-WB75-2.pdf | ❌ 0 | ⬜ 0 |
| BPIR-Ecko-Brackets.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Bolts-Rods-Washers-Fixing-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Brads-BPIR-Decl-V1.0 (1).pdf | ❌ 0 | ⬜ 0 |
| ECKO-Brads-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Collated-Nails-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Loose-Nails-Exterior-BPIR-Decl-V1.1.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Loose-Nails-Interior-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-Staples-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-TRex-17-Screws-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO-WANZ-Fixing-BPIR-Decl-V1.0.pdf | ❌ 0 | ⬜ 0 |
| ECKO_T-REX17_Decking_Screw_CSK.pdf | ❌ 0 | ⬜ 0 |
| ECKO_T-REX17_Decking_Screw_Cylindrical.pdf | ❌ 0 | ⬜ 0 |
| ECKO_T-REX17_Decking_Screw_Trim.pdf | ❌ 0 | ⬜ 0 |
| ECKO_T-Rex_17_Screws_BPIR_Declaration.pdf | ❌ 0 | ⬜ 0 |
| T-REX17-Screws_TurboTIP_01_JoltScrew.pdf | ❌ 0 | ⬜ 0 |
| T-REX17-Screws_TurboTIP_01_batten-screws.pdf | ❌ 0 | ⬜ 0 |
| T-REX17-Screws_TurboTIP_01_decking-screws-SS304.pdf | ❌ 0 | ⬜ 0 |

### MacSim (1 PDFs, 31.2 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Fasteners_Direct_Catalogue_MacSim_Products.pdf | ❌ 0 | ⬜ 0 |

### Mainland_Fasteners (1 PDFs, 20.9 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Mainland_Fasteners_Mini_Catalogue.pdf | ❌ 0 | ⬜ 0 |

### MiTek (2 PDFs, 5.6 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| MiTek_LUMBERLOK_Timber_Connectors_Characteristic_Loadings.pd | ❌ 0 | ⬜ 0 |
| MiTek_Stud-to-Top-Plate_Fixing_Schedule_2024.pdf | ❌ 0 | ⬜ 0 |

### NZSIP (1 PDFs, 10.4 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| NZ_SIP_Technical_Manual_Fasteners_Section.pdf | ❌ 0 | ⬜ 0 |

### NZ_Nails (1 PDFs, 0.2 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| NZ_Nails_Building_Product_Information_Sheet.pdf | ❌ 0 | ⬜ 0 |

### Paslode (5 PDFs, 4.5 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Paslode_2020_Full_Catalog.pdf | ❌ 0 | ⬜ 0 |
| Paslode_Fastener_Selection_Chart.pdf | ❌ 0 | ⬜ 0 |
| Paslode_Impulse_Purlin_Nails_Technical.pdf | ❌ 0 | ⬜ 0 |
| Paslode_NZ_Nails_BRANZ_Appraisal_546.pdf | ❌ 0 | ⬜ 0 |
| Paslode_Purlin_Nails_BRANZ_Appraisal.pdf | ❌ 0 | ⬜ 0 |

### PlaceMakers (1 PDFs, 9.7 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| PlaceMakers_Fastenings_Catalogue_2020.pdf | ❌ 0 | ⬜ 0 |

### Pryda (5 PDFs, 43.9 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| NZ_Pryda_Bracing_Anchor_PDS.pdf | ❌ 0 | ⬜ 0 |
| NZ_Pryda_Bracing_Design_Guide_V1.02.pdf | ❌ 0 | ⬜ 0 |
| NZ_Pryda_Connectors_Tie-downs_Design_Guide.pdf | ❌ 0 | ⬜ 0 |
| Pryda_Builders_Guide_NZ.pdf | ❌ 0 | ⬜ 0 |
| SP_Fasteners_Pryda_Product_Catalogue.pdf | ❌ 0 | ⬜ 0 |

### Ramset (1 PDFs, 3.1 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Ramset_Technical_Product_Guide.pdf | ❌ 0 | ⬜ 0 |

### SPAX (2 PDFs, 31.6 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| SPAX_Decking_Screw_Guide.pdf | ❌ 0 | ⬜ 0 |
| SPAX_Pacific_Product_Catalogue_2018-2019.pdf | ❌ 0 | ⬜ 0 |

### Simpson_Strong_Tie (3 PDFs, 58.1 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Simpson_Strong-Tie_Mass_Timber_Connectors_AUNZ.pdf | ❌ 0 | ⬜ 0 |
| Simpson_Strong-Tie_NZS_3604_Timber_Connectors.pdf | ❌ 0 | ⬜ 0 |
| Simpson_Strong-Tie_Timber_Construction_Connectors_Catalog.pd | ❌ 0 | ⬜ 0 |

### Titan (1 PDFs, 0.1 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Titan_Framing_Nails_BPIR_Declaration.pdf | ❌ 0 | ⬜ 0 |

### Zenith (2 PDFs, 17.1 MB)
**Text:** 0 chunks | **Visuals:** 0

| Document | Text | Visual |
|----------|------|--------|
| Zenith_Hardware_Catalogue_2017.pdf | ❌ 0 | ⬜ 0 |
| Zenith_Hardware_Catalogue_2020.pdf | ❌ 0 | ⬜ 0 |

---

# 📐 AGENT ZONE 3: THE ENGINEER (Visual Agent)

**Role:** Visual Expert - Retrieves technical drawings, tables, diagrams
**Data Source:** `visuals` table

**Asset Types:**
- TECHNICAL_DRAWING - CAD details, section views
- SPAN_TABLE - Load tables, capacity charts
- PROFILE_DRAWING - Product profiles, dimensions
- INSTALLATION_DIAGRAM - Step-by-step visuals

## Current Visual Assets

| Source | Type | Product Codes | Status |
|--------|------|---------------|--------|
| Abodo Wood - AW62P-187x18-Profile-Drawin | profile | ['AW62P'] | ✅ |

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
| Fasteners | 1,162 | 0 | Product Rep |
| GIB | 1,103 | 0 | Product Rep |
| Abodo Wood | 1,074 | 0 | Product Rep |
| Bremick | 732 | 0 | Product Rep |
| MBIE | 598 | 0 | Inspector |
| Simpson Strong Tie | 591 | 0 | Product Rep |
| Pryda | 533 | 0 | Product Rep |
| Asona | 521 | 0 | Product Rep |
| Expol | 391 | 0 | Product Rep |
| GreenStuf | 381 | 0 | Product Rep |
| CHH Woodproducts | 361 | 0 | Product Rep |
| Firth | 341 | 0 | Product Rep |
| Earthwool | 277 | 0 | Product Rep |
| Mammoth | 277 | 0 | Product Rep |
| Buildex | 275 | 0 | Product Rep |
| SPAX | 226 | 0 | Product Rep |
| J&L Duke | 203 | 0 | Product Rep |
| Ecko | 189 | 0 | Product Rep |
| PlaceMakers | 172 | 0 | Product Rep |
| Paslode | 121 | 0 | Product Rep |
| NZSIP | 109 | 0 | Product Rep |
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
| 2026-01-09 | Initial Audit | Created master inventory |
| | | |

---

*End of Document*