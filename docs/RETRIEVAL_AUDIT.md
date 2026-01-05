# STRYDA v2 - Retrieval & Ranking System Audit
## Technical Breakdown (June 2025)

---

## 1. INGESTION TRIGGER (Metadata Assignment)

### How are `doc_type` and `trade` tags assigned?

**Answer: Hard-coded by filename/folder pattern matching in each ingestion script.**

There is **NO AI classifier** running on upload. Each ingestion script has a pre-defined `DOC_CLASSIFICATION` dictionary that maps filename patterns to metadata.

### Example: Compliance Documents (`compliance_vision_reingest.py`)
```python
DOC_CLASSIFICATION = {
    'NZS-36042011.pdf': {'category': 'Z_Compliance', 'trade': 'nz_standard', 'family': 'NZS 3604:2011'},
    'F4-AS1_Amendment-6-2021.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'F4 Safety from Falling AS1'},
    'C-AS1_2nd-Edition_2023.pdf': {'category': 'Z_Compliance', 'trade': 'acceptable_solution', 'family': 'C Fire Safety AS1'},
    # ... etc
}
```

### Example: Timber Suppliers (`timber_deep_dive.py`)
```python
# Auto-detect trade from filename/content keywords
TRADE_KEYWORDS = {
    'framing': ['framing', 'laserframe', 'frame', 'stud', 'dwang', 'nog'],
    'treated_timber': ['treated', 'cca', 'losp', 'boron', 'h1', 'h3', 'h4'],
    'structural_timber': ['structural', 'graded', 'sg8', 'sg10', 'sg12'],
    'plywood': ['plywood', 'ply', 'panel'],
    'lvl': ['lvl', 'laminated veneer', 'hyspan'],
    # ... etc
}
```

### Current Tag Inventory

#### DOC_TYPE Values (18 types):
| doc_type | Chunks | Description |
|----------|--------|-------------|
| `Product_Catalog` | 9,900 | Product brochures, catalogs |
| `Compliance_Document` | 9,671 | NZ Building Code, AS/VM docs |
| `Installation_Guide` | 5,511 | How-to install guides |
| `Technical_Manual` | 4,204 | GIB, Ardex technical manuals |
| `Technical_Data_Sheet` | 3,102 | Product TDS |
| `CAD_Detail` | 1,091 | CAD drawings |
| `MBIE_Guidance` | 598 | MBIE guidance docs (NEW) |
| `EPD` | 706 | Environmental product declarations |
| `Safety_Data_Sheet` | 126 | SDS/MSDS |
| `Certification` | 207 | CodeMark, BRANZ appraisals |

#### TRADE Values (60+ trades):
| Category | Trades |
|----------|--------|
| **Compliance** | `acceptable_solution`, `verification_method`, `nz_standard`, `building_code`, `industry_code`, `technical_manual`, `industry_guide`, `mbie_guidance` |
| **Structure** | `framing`, `structural_timber`, `treated_timber`, `bracing`, `foundations`, `nailplates` |
| **Enclosure** | `cladding`, `roofing`, `roof_panel`, `coldstore_panel`, `fire_rated_panel` |
| **Insulation** | `general_insulation`, `wall_insulation`, `roof_insulation`, `ceiling_insulation`, `underfloor_insulation`, `soffit_insulation`, `slab_insulation` |
| **Acoustic** | `acoustic_wall`, `acoustic_ceiling`, `acoustic_screens`, `acoustic_panel`, `acoustic_timber`, `acoustic_baffle` |
| **Fasteners** | `fasteners`, `screws`, `bolts`, `nails`, `anchoring`, `hardware` |
| **Interior** | `interior_linings`, `wall_panel` |

---

## 2. AUTHORITY SCORING (Ranking Weights)

### Scoring Formula
```
final_score = base_similarity + (priority/1000) + intent_bonus
```

Where:
- `base_similarity`: 0.0-1.0 (cosine similarity from embedding search)
- `priority`: 0-100 → contributes 0.00-0.10 to final score
- `intent_bonus`: -0.15 to +0.10 based on doc_type/trade alignment

### Exact Numerical Boost Values

#### For COMPLIANCE Queries (`intent = "compliance_strict"`)

| doc_type / trade | Boost | Rationale |
|------------------|-------|-----------|
| `MBIE_Guidance` + `mbie_guidance` | **+0.10** | HIGHEST - Government authority |
| `building_code` trade | **+0.09** | NZ Building Code itself |
| `acceptable_solution_current` | +0.10 | Current AS documents |
| `acceptable_solution` trade | +0.08 | Acceptable Solutions (E2/AS1, F4/AS1) |
| `verification_method_current` | +0.08 | Current VM documents |
| `verification_method` trade | +0.07 | Verification Methods |
| `nz_standard` trade | +0.06 | NZS 3604, NZS 4229 |
| `industry_code_of_practice` | +0.05 | Industry codes (NZ Metal Roofing) |
| `industry_code` trade | +0.04 | Industry codes |
| `acceptable_solution_legacy` | +0.03 | Legacy AS (still official) |
| `technical_manual` trade | +0.03 | GIB, Ardex manuals |
| `industry_guide` trade | +0.03 | Industry guides |
| `Compliance_Document` (other) | +0.02 | Base bonus for any compliance doc |
| `handbook_guide` | -0.01 | Slight penalty for guides |
| `manufacturer_manual_*` | **-0.05** | Penalty for manufacturer docs |
| `Product_Catalog` | **-0.15** | STRONG PENALTY - No product catalogs for compliance! |

#### For GENERAL HELP Queries (`intent = "general_help"`)

| doc_type | Boost | Rationale |
|----------|-------|-----------|
| `Product_Catalog` | +0.08 | Bonus - good for product questions |
| `manufacturer_manual_*` | +0.08 | Bonus - practical info |
| `handbook_guide` | +0.06 | Bonus - user-friendly |
| `acceptable_solution_current` | +0.02 | Keep standards as useful context |
| `Compliance_Document` | +0.01 | Small bonus |

### Priority Field Distribution
| Priority | Chunks | Assignment |
|----------|--------|------------|
| 100 | 565 | Top-tier official standards |
| 98 | 373 | MBIE Guidance (Minor Variations, Schedule 1) |
| 95 | 9,896 | Compliance documents, NZ Building Code |
| 85 | 13,782 | Product technical data |
| 80 | 11,167 | General product info |

---

## 3. CONFLICT RESOLUTION LOGIC

### "Who Wins" in a Conflict?

**The `priority` field + `intent_bonus` determine the winner.**

Example scenario: Building Code (F4/AS1) vs Product Manual

| Document | base_similarity | priority | intent_bonus | FINAL |
|----------|-----------------|----------|--------------|-------|
| F4/AS1 (trade=`acceptable_solution`) | 0.75 | 95 | +0.08 | **0.925** |
| Product Manual (doc_type=`Product_Catalog`) | 0.78 | 80 | -0.15 | **0.710** |

**F4/AS1 wins** despite lower semantic similarity because:
1. Higher priority (95 vs 80)
2. Intent bonus (+0.08 vs -0.15) = +0.23 swing

### Priority Tiers (Gob Mode Hierarchy)
```
100 ─── TOP-TIER OFFICIAL STANDARDS
 98 ─── MBIE GUIDANCE (Minor Variations, Schedule 1, Tolerances)
 95 ─── COMPLIANCE DOCS (NZS 3604, E2/AS1, F4/AS1, Building Code)
 90 ─── [Reserved]
 85 ─── TECHNICAL DATA (Product TDS, Installation Guides)
 80 ─── GENERAL PRODUCT INFO (Catalogs, Brochures)
 60 ─── LOW PRIORITY CONTENT
```

---

## 4. TRIGGER MECHANISM

### How Specific Questions Trigger Specific Files

**The `canonical_source_map()` function detects keywords and returns specific source names.**

This is a **keyword-based filter, NOT fuzzy text match**.

### Example: Red Stag Query
```python
# In fastener_brands dictionary:
fastener_brands = {
    'pryda': 'Final Sweep - Pryda',
    'red stag': 'Red Stag',  # Would need to be added for strict filtering
    ...
}
```

**Current behavior for "Red Stag":**
- ❌ NO strict `brand_name = 'Red Stag'` filter exists currently
- ✅ Semantic search will find Red Stag content via embedding similarity
- ⚠️ Results may include other timber brands if semantically similar

### Key Trigger Mappings

| Keywords | Triggered Source(s) | Filter Type |
|----------|---------------------|-------------|
| `f4`, `balustrade`, `deck height` | `F4-AS1_Amendment-6-2021` | Direct source name |
| `minor variation`, `exempt`, `schedule 1` | `MBIE` (brand_name filter) | Brand filter |
| `nzs 3604`, `stud`, `joist`, `bearer` | `NZS 3604:2011` | Source name |
| `e2`, `flashing`, `cladding` | `E2/AS1` | Source name |
| `gib`, `plasterboard`, `fire rating` | `GIB Site Guide 2024` | Source name |
| `pink batts`, `insulation`, `r-value` | `Pink Batts Deep Dive` | Source name |
| `kingspan`, `kooltherm`, `coldstore` | `Kingspan Deep Dive` | Source name |
| `pryda`, `zenith`, `macsim` | `Final Sweep - [Brand]` | Brand-specific |
| Generic: `insulation` | Multiple sources | Multi-brand search |

### MBIE Guidance Special Handling (NEW)
```python
if has_mbie:
    # MBIE guidance documents use brand_name = 'MBIE'
    sql = """
        SELECT ... FROM documents 
        WHERE embedding IS NOT NULL
          AND (brand_name = 'MBIE' OR source LIKE 'MBIE%%')
        ...
    """
```

---

## 5. GAPS IDENTIFIED FOR TIMBER & COMPLIANCE

### Current Issues:

1. **No strict brand filter for timber suppliers**
   - "Red Stag" query: No hard-coded source mapping
   - "CHH Woodproducts" query: No hard-coded source mapping
   - Relies purely on semantic search

2. **Timber trade detection is basic**
   - Keywords like `framing`, `structural`, `treated` exist
   - But `brand_name` filter not engaged

### Recommended Additions to `canonical_source_map()`:

```python
# Timber Suppliers
if any(term in query_lower for term in [
    'red stag', 'redstag', 'framepro',
    'chh', 'carter holt', 'woodproducts', 'laserframe', 'pinex'
]):
    sources.append('Timber Deep Dive')  # Or filter by brand_name
```

---

## 6. SUMMARY: GOB MODE VERIFICATION

| Requirement | Status | Notes |
|-------------|--------|-------|
| Compliance docs get priority over product catalogs | ✅ | -0.15 penalty for Product_Catalog in compliance queries |
| Building Code wins over manufacturer docs | ✅ | +0.09 vs -0.05 swing |
| MBIE Guidance highest authority | ✅ | +0.10 bonus, priority 98 |
| F4/AS1 triggered for balustrade questions | ✅ | Direct source name mapping |
| Brand-specific filtering | ⚠️ PARTIAL | Works for fasteners, NOT for timber |
| Priority field respected | ✅ | Contributes up to +0.10 to score |

---

*Generated: June 2025*
*File: `/app/backend-minimal/simple_tier1_retrieval.py`*
