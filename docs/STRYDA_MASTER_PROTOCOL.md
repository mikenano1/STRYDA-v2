# STRYDA DATA INGESTION MASTER PROTOCOL (v3.1)

> **SYSTEM DIRECTIVE:** These rules are MANDATORY for all scraping, ingestion, and retrieval tasks.
> 
> **Last Updated:** January 2026
> **Version:** 3.1 PLATINUM
> **Maintained By:** STRYDA Data Pipeline Team

---

# PART I: THE 8 INGESTION LAWS

---

## LAW 0: The "Structure First" Law (Reconnaissance)

**MANDATORY PRE-REQ:** Never start an ingestion without a Structural Recon.

| Step | Action | Output |
|------|--------|--------|
| 1 | Extract Product List | List of all products/profiles on manufacturer site |
| 2 | Analyze URL Pattern | Identify deep-link structure (e.g., `/product/{slug}/downloads`) |
| 3 | Target Deep-Link Pages | Go directly to technical resources, not landing pages |

* **Directive:** Do not blind scrape. Provide exact Product Shelf URLs.

---

## LAW 1: The "Context-Aware" Naming Law

**Never trust the filename on the server.**

### Problem
```
❌ 66e3a8f2download.pdf
❌ View.pdf
❌ Brochure.pdf
```

### Solution
```
✅ Dimond - Corrugate - Residential Roof Installation Details.pdf
✅ Metalcraft - Espan 340 - Loadspan Tables Steel.pdf
```

* **Fix:** Scrape Text Context (H1-H6, Labels, Link Text) surrounding the download link
* **Prohibition:** No `Download.pdf`, `View.pdf`, or `Brochure.pdf`
* **Requirement:** Files must include `[Brand]` + `[Product]` + `[Document Type]`

---

## LAW 2: The "Sanitization" Law

**Filenames must be clean, professional, and human-readable.**

### Strip These:
- Hash codes (`66e3a8f2...`, `abc123def456...`)
- URL garbage (`%20`, `_`, `+`, `-`)
- Trademark symbols (`™`, `®`, `©`)
- Leading/trailing whitespace

### Format Standard:
```
[Manufacturer] - [Product Name] - [Clean Document Title].pdf
```

---

## LAW 3: The "Universal vs. Specific" Law

**Do not clutter specific product folders with generic docs.**

### Universal Keywords (Trigger Words):
- "Warranty", "Terms of Trade", "Maintenance"
- "Color Chart" / "Colour Chart"
- "Environmental", "Sustainability"
- "Care Guide", "Company Profile"

### Action:
1. Detect universal keywords in filename or document title
2. Move to `00_General_Resources/` folder
3. Rename using format: `[Brand] - Universal - [Title].pdf`

---

## LAW 4: The "Extension" Law

### Allowed:
- `.pdf` ONLY

### Forbidden:
- `.zip`, `.exe`, `.dwg`, `.dxf`, `.jpg`, `.png`

---

## LAW 5: The "Verification" Law

**Verify output before completion.**

### Pre-Completion Checklist:
- [ ] Output 5 sample filenames from the batch
- [ ] Check for "Download.pdf" failures
- [ ] Verify folder structure matches specification
- [ ] Confirm no duplicate files exist
- [ ] Run file count against expected total

---

## LAW 6: The "Hidden Technical Data" Law

**Never judge a file solely by its "Accessories" label.**

### Solution:
1. **Scan** files labeled "Accessories", "Brochure", "Product Guide"
2. **Search** for keywords: "Span Tables", "Fixing Patterns", "Load Capacity"
3. **If Found:** Rename to include technical scope

---

## LAW 7: The "Supply Chain Hierarchy" Law

**Never duplicate upstream supplier data.**

### Trigger Keywords:
- ColorSteel, ColorCote, Galvsteel, Zincalume, ZinaCore, Alumigard, NZ Steel

### Decision Tree:
```
IF filename contains [Trigger Keyword]:
    CHECK: Does file exist in /00_Material_Suppliers/[Supplier]/?
    IF YES → SKIP
    IF NO  → Ingest to /00_Material_Suppliers/[Supplier]/
```

---

## LAW 8: The "Monolith" Law

**Prevent duplication of "Bible" documents.**

### Trigger Conditions:
- PDF covers >2 distinct product categories
- File size > 20MB
- Page count > 50 pages

### Action:
Save to `00_General_Resources/` with scope notation.

---

# PART II: THE 8 RETRIEVAL BOUNDARIES

---

## BOUNDARY 1: The DNA Test (Segment Verification)

**Every query must match its knowledge segment.**

```python
SEGMENTS = {
    'bremick': ['fastener', 'bolt', 'nut', 'screw', 'anchor'],
    'pryda': ['connector', 'hanger', 'strap', 'bracket', 'tie-down'],
    'roofing': ['span', 'purlin', 'batten', 'flashing', 'ridge']
}
```

If query DNA doesn't match segment → Return clarification request.

---

## BOUNDARY 2: Coordinate Mapping (GOD TIER Laws)

**Expand technical nomenclature automatically.**

| Input | Expansion |
|-------|-----------|
| `M12` | `M12, 12mm, 12 mm, metric 12, size 12` |
| `1/2"` | `1/2", 1/2 inch, 0.5 inch, half inch, 1/2-13` |
| `SG8` | `SG8, stress grade 8, timber grade SG8` |
| `JD4` | `JD4, joint group JD4, hardwood joint` |

---

## BOUNDARY 3: Domain Isolation (Anti-Hallucination Lock)

**Prevent cross-domain contamination.**

### STRICT EXCLUSION LIST
```python
PRYDA_EXCLUSIONS = [
    'nzs 3604', 'timber span', 'rafter span',
    'joist span', 'bearer span', 'wind zone calculation'
]
```

### Response When Triggered:
```
"Data not in Pryda Spec. Referring to Manufacturer Loadings only."
```

---

## BOUNDARY 4: Unit Anchoring (Pryda Unit Law)

**Primary force unit per segment.**

| Segment | Primary Unit | Secondary |
|---------|--------------|-----------|
| Pryda | kN | - |
| Bremick | lbf | N |
| Roofing | mm spans | kPa loads |

---

## BOUNDARY 5: Context Injection (Table Extraction)

**Every table cell must have row+column context.**

### Format:
```
"Product: JHH100 | Timber: SG8 | Fixing: 4×TCS12-35 | Capacity: 30.0 kN"
```

NOT:
```
"30.0"
```

---

## BOUNDARY 6: Source Citation (Mandatory Attribution)

**Every answer must include source reference.**

### Format:
```
Value: [X] kN (Source: [Filename], Page [Y])
```

---

## BOUNDARY 7: Granular Chunking (High-Zoom Extraction)

**For HIGH COMPLEXITY files, create unique chunk per:**
- Product code
- Nailing option
- Timber grade combination

### Example:
```
File: Pryda Hangers Design Guide
→ Chunk 1: JHH100 | SG8 | 4×TCS12-35 | 30.0 kN
→ Chunk 2: JHH100 | SG10 | 6×TCS12-35 | 35.2 kN
```

---

## BOUNDARY 8: The Shadow Audit (Quality Gate)

**Every segment must pass automated stress testing.**

| Requirement | Threshold |
|-------------|-----------|
| Minimum Test Questions | 50 randomized queries |
| Pass Rate Required | ≥90% for PLATINUM |
| Hallucination Tolerance | 0% |
| Retrieval Accuracy | ≥75% |

### Certification Levels

| Level | Success Rate | Badge |
|-------|--------------|-------|
| PLATINUM | ≥90% | ⚡ Production Ready |
| GOLD | ≥75% | ✅ Stable |
| SILVER | ≥50% | 🟡 Needs Improvement |
| NEEDS REPAIR | <50% | 🔴 Do Not Deploy |

### Automated Nightly Audit
```
Service: /app/services/nightly_auditor.py
Schedule: Daily at 02:00 AM
Log: /app/logs/nightly_mastery.log
Reports: /app/logs/audit_reports/
```

---

# PART III: SYSTEM ARCHITECTURE

---

## Vision Engine Configuration

```python
# /app/core/config.py
VISION_MODEL_PROVIDER = 'gemini'
VISION_MODEL_NAME = 'gemini-2.5-flash'
PDF_DPI_STANDARD = 200
PDF_DPI_HIGH_COMPLEXITY = 300
```

### Dependencies (requirements_platinum.txt)
```
emergentintegrations==0.1.0
pdf2image==1.17.0
poppler-utils (system)
```

---

## Storage Architecture

```
/product-library/
├── A_Structure/
├── B_Enclosure/
├── F_Manufacturers/
│   └── Fasteners/
│       ├── Bremick/     (291 files, 8,361 chunks) ⚡ PLATINUM
│       └── Pryda/       (17 files, 357 chunks) ⚡ PLATINUM
└── 00_General_Resources/
```

---

## Segment Certification Status

| Segment | Files | Chunks | Audit Pass | Status |
|---------|-------|--------|------------|--------|
| Bremick | 291 | 8,361 | 90.0% | ⚡ PLATINUM |
| Pryda | 17 | 357 | 100.0% | ⚡ PLATINUM |
| **TOTAL** | **4,200+** | **106,311** | - | - |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial protocol (Laws 0-5) |
| 2.0 | Jan 2025 | Added Laws 6-8 |
| 3.0 | Jan 2026 | Added Shadow Audit (Law 9), Vision Engine |
| **3.1** | **Jan 2026** | **Merged 8 Laws + 8 Boundaries, Pryda PLATINUM certified** |

---

**END OF PROTOCOL v3.1**
