# STRYDA DATA INGESTION MASTER PROTOCOL (v2.0)

> **SYSTEM DIRECTIVE:** These rules are MANDATORY for all scraping and ingestion tasks.
> 
> **Last Updated:** January 2025
> **Maintained By:** STRYDA Data Pipeline Team

---

## 0. The "Structure First" Law (Reconnaissance)

**MANDATORY PRE-REQ:** Never start an ingestion without a Structural Recon.

| Step | Action | Output |
|------|--------|--------|
| 1 | Extract Product List | List of all products/profiles on manufacturer site |
| 2 | Analyze URL Pattern | Identify deep-link structure (e.g., `/product/{slug}/downloads`) |
| 3 | Target Deep-Link Pages | Go directly to technical resources, not landing pages |

* **Directive:** Do not blind scrape. Provide exact Product Shelf URLs.
* **Process:** 
  1. Extract Product List from main navigation
  2. Analyze URL Pattern for technical downloads
  3. Target deep-link pages containing actual PDFs

---

## 1. The "Context-Aware" Naming Law

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

## 2. The "Sanitization" Law

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

### Examples:
```
✅ Viking Roofspec - Speed Deck Ultra - Span Tables.pdf
✅ Roofing Industries - Corrugate - BPIS Sheet.pdf
✅ Metalcraft - MSS Purlins - Section Geometry.pdf
```

---

## 3. The "Universal vs. Specific" Law

**Do not clutter specific product folders with generic docs.**

### Universal Keywords (Trigger Words):
- "Warranty"
- "Terms of Trade"
- "Maintenance"
- "Color Chart" / "Colour Chart"
- "Environmental"
- "Sustainability"
- "Care Guide"
- "Company Profile"

### Action:
1. Detect universal keywords in filename or document title
2. Move to `00_General_Resources/` folder
3. Rename using format: `[Brand] - Universal - [Title].pdf`

### Example:
```
❌ /Corrugate/Warranty Guide.pdf
✅ /00_General_Resources/Dimond - Universal - Warranty Guide.pdf
```

---

## 4. The "Extension" Law

### Allowed:
- `.pdf` ONLY

### Forbidden:
- `.zip` (archive files)
- `.exe` (executables)
- `.dwg` / `.dxf` (CAD files - unless CAD run explicitly requested)
- `.jpg` / `.png` (images - unless visual library requested)

---

## 5. The "Verification" Law

**Verify output before completion.**

### Pre-Completion Checklist:
- [ ] Output 5 sample filenames from the batch
- [ ] Check for "Download.pdf" failures
- [ ] Verify folder structure matches specification
- [ ] Confirm no duplicate files exist
- [ ] Run file count against expected total

### Failure Indicators:
```
❌ Download.pdf
❌ View.pdf  
❌ document(1).pdf
❌ 66e3...abc.pdf
```

---

## 6. The "Hidden Technical Data" Law

**Never judge a file solely by its "Accessories" label.**

### Problem:
Some manufacturers hide span tables and technical data inside generic "Accessories" or "Brochure" PDFs.

### Solution:
1. **Scan** files labeled "Accessories", "Brochure", "Product Guide"
2. **Search** for keywords: "Span Tables", "Fixing Patterns", "Load Capacity", "Installation"
3. **If Found:** Rename to include technical scope

### Rename Format:
```
[Brand] - [Product] - Product Brochure & Installation.pdf
```

### Example:
```
❌ Accessories.pdf (contains span tables inside)
✅ Viking - Speed Deck - Product Brochure & Installation.pdf
```

---

## 7. The "Supply Chain Hierarchy" Law

**Never duplicate upstream supplier data.**

### Trigger Keywords:
- ColorSteel / ColourSteel
- ColorCote / ColourCote  
- Galvsteel
- Zincalume
- ZinaCore
- Alumigard
- MagnaFlow
- NZ Steel

### Decision Tree:
```
IF filename contains [Trigger Keyword]:
    CHECK: Does file exist in /00_Material_Suppliers/[Supplier]/ ?
    
    IF YES → SKIP (do not download)
    IF NO  → Ingest to /00_Material_Suppliers/[Supplier]/
             NOT to the manufacturer's folder
```

### Supplier Folder Structure:
```
/B_Enclosure/00_Material_Suppliers/
├── ColorSteel/          (31 docs)
├── ColorCote/           (33 docs)
├── NZ_Steel_Galv/       (durability statements)
└── [Future Suppliers]/
```

---

## 8. The "Monolith" Law

**Prevent duplication of "Bible" documents.**

### Trigger Conditions:
- PDF covers >2 distinct product categories
- File size > 20MB
- Page count > 50 pages
- Examples: "Master Technical Manual", "Complete Design Guide", "Full Product Catalog"

### Action:
1. Save to `00_General_Resources/` (not in product-specific folder)
2. Rename using scope notation:

```
[Brand] - Master Technical Manual ([Scope]).pdf
```

### Examples:
```
✅ Metalcraft - Master Structural Design Guide (MSS, MZ, MC, Top Hats).pdf
✅ Firth - Complete Product Handbook (Foundations, Paving, Masonry).pdf
✅ Simpson Strong-Tie - Connector Catalog (Framing, Bracing, Anchoring).pdf
```

---

## Storage Architecture Reference

```
/product-library/
├── A_Structure/
│   └── Metalcraft_Structural/
│       ├── 00_General_Resources/
│       ├── MSS_Purlins/
│       ├── MC_Purlins/
│       └── ComFlor_*/
│
├── B_Enclosure/
│   ├── 00_Material_Suppliers/
│   │   ├── ColorSteel/
│   │   ├── ColorCote/
│   │   └── NZ_Steel_Galv/
│   ├── Dimond_Roofing/
│   ├── Metalcraft_Roofing/
│   ├── Viking_Roofspec/
│   ├── Roofing_Industries/
│   └── Steel_and_Tube/
│
└── [Future Categories]/
```

---

## Version History

| Version | Date | Changes |
|---------|------|--------|
| 1.0 | Dec 2024 | Initial protocol |
| 2.0 | Jan 2025 | Added Rules 6-8, Supply Chain Hierarchy, Monolith Law |

---

**END OF PROTOCOL**
