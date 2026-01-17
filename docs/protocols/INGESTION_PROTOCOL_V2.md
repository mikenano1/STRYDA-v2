# 🚀 STRYDA MASTER INGESTION & AGENT PROTOCOL V2.0 (FINAL)

**Version:** 2.0  
**Status:** ACTIVE  
**Last Updated:** January 2026  
**Author:** STRYDA Architect  

---

## Purpose

This is the **definitive technical directive** for the STRYDA "Brain Build." This protocol ensures the **4-Agent Architecture** (Foreman, Inspector, Rep, Engineer) can operate with surgical precision and legal safety.

> ⚠️ **CRITICAL**: Do not execute any new ingestions until these code barriers are integrated.

---

## 1. DETERMINISTIC IDENTITY & VERSIONING

### 1.1 Hashing
- Assign a **unique SHA-256 hash** to every individual page
- Hash serves as the canonical identifier for deduplication

### 1.2 Deduplication
- **Check the hash before upserting** to Supabase
- If the hash exists → Update metadata only; **do not create duplicate vectors**
- Prevents vector bloat and ensures single source of truth

### 1.3 Version Logic
Maintain two key fields:
- `version_id` (INT) - Incremental version number
- `is_latest` (BOOL) - Flag for current version

**Foreman Routing Rule:**  
If two documents cover the same topic, the Foreman must **only route to the chunk where `is_latest: true`**.

```sql
-- Example query pattern
SELECT * FROM document_chunks 
WHERE topic = $1 
AND is_latest = true 
ORDER BY hierarchy_level ASC;
```

---

## 2. HIERARCHY OF TRUTH (CONFLICT RESOLUTION)

Assign a `hierarchy_level` to every chunk during ingestion to enable the **"Safety Override"**:

| Level | Weight | Source Type | Tag |
|-------|--------|-------------|-----|
| **1** | 1.0 | NZ Building Code (NZBC), Standards, Acts | `role: authority` |
| **2** | 0.8 | BRANZ Appraisals, CodeMark, BPIR/PTS | `role: compliance` |
| **3** | 0.6 | Manufacturer Manuals & Datasheets | `role: product` |

### Conflict Override Logic
```
IF Inspector_Logic == "Prohibited" AND Product_Rep_Logic == "Allowed":
    THEN Foreman MUST:
        1. Lead with the Code (hierarchy_level: 1)
        2. Flag manufacturer data as "Conditional Supplement"
        3. Surface warning to user
```

---

## 3. SEMANTIC CHUNKING & MAPPING

### 3.1 Boundary Rule
> **NEVER split a "thought"** (e.g., a multi-step install process) across vectors.  
> Split **only at Section Headers**.

This preserves:
- Installation sequences
- Specification tables
- Conditional logic blocks
- Safety warnings with their context

### 3.2 Metadata Schema

Update the `document_chunks` table with these additional columns:

```sql
ALTER TABLE document_chunks 
ADD COLUMN page_title TEXT,            -- Extracted from Title Block
ADD COLUMN dwg_id TEXT,                -- e.g., "VS11", "PXR-4-05"
ADD COLUMN agent_owner TEXT[],         -- ["Product_Rep", "Engineer"]
ADD COLUMN hierarchy_level INT,        -- 1, 2, or 3
ADD COLUMN bounding_boxes JSONB,       -- [x1, y1, x2, y2] for visual crops
ADD COLUMN unit_range JSONB,           -- Min/Max measurement values
ADD COLUMN geo_context TEXT;           -- e.g., "NZ_Specific"
```

### 3.3 Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `page_title` | TEXT | Extracted from PDF title block | "Typical Base Channel Over Waterproof Deck" |
| `dwg_id` | TEXT | Drawing/detail identifier | "NW-HOC-00702", "PXR-4-05-SM" |
| `agent_owner` | TEXT[] | Which agents can access this chunk | `["Product_Rep", "Engineer"]` |
| `hierarchy_level` | INT | 1=Authority, 2=Compliance, 3=Product | `2` |
| `bounding_boxes` | JSONB | Coordinates for visual extraction | `[[50, 100, 400, 300]]` |
| `unit_range` | JSONB | Measurement min/max values | `{"min": 50, "max": 150, "unit": "mm"}` |
| `geo_context` | TEXT | Geographic applicability | "NZ_Specific", "AU_Specific", "Universal" |

---

## 4. THE ENGINEER'S VISUAL EXTRACTION

The **Engineer Agent** fetches visuals, not text.

### 4.1 OCR Vision Pass
During ingestion, identify and tag:
- Tables (span tables, specification tables)
- Diagrams (CAD details, installation sequences)
- Technical drawings (cross-sections, elevations)

### 4.2 Coordinate Mapping
Save the **exact bounding box** `[x1, y1, x2, y2]` of every table/diagram:

```json
{
  "bounding_boxes": [
    {"type": "table", "coords": [50, 100, 500, 400], "label": "Span Table"},
    {"type": "diagram", "coords": [50, 450, 500, 700], "label": "Detail Section"}
  ]
}
```

### 4.3 Tool Contract: `get_technical_diagram`

When called, return:
1. **Cropped high-res image** of the specified coordinates
2. **Sheet Title** from the title block
3. **Direct deep-link** to the parent PDF in Supabase Storage

```typescript
interface TechnicalDiagramResponse {
  image_url: string;           // Cropped image URL
  sheet_title: string;         // "Typical Window Head Detail"
  dwg_id: string;              // "NW-HOC-01702"
  source_pdf: string;          // Deep link to Supabase
  page_number: number;         // 1
  bounding_box: number[];      // [x1, y1, x2, y2]
}
```

---

## 5. THE SAFETY SHIELDS

### 5.1 Unit/Range Guardrail
Tag all measurements to prevent AI from confusing minimums with maximums:

```json
{
  "unit_range": {
    "value": 150,
    "unit": "mm",
    "type": "minimum",      // "minimum", "maximum", "nominal", "range"
    "context": "cavity_depth"
  }
}
```

**Example protections:**
- "Minimum 50mm cavity" → `type: minimum`
- "Maximum 600mm centres" → `type: maximum`
- "90-150mm range" → `type: range, min: 90, max: 150`

### 5.2 Regionality Filter
Tag NZ-specific environmental data to **block international data hallucinations**:

| Tag Value | Applies To |
|-----------|-----------|
| `NZ_Specific` | Wind Zones (Very High, High, Medium, Low), Seismic Zones, NZS Standards |
| `AU_Specific` | BCA references, AS Standards |
| `Universal` | General physics, material properties |

```sql
-- Example: Filter for NZ context only
SELECT * FROM document_chunks 
WHERE geo_context IN ('NZ_Specific', 'Universal')
AND topic ILIKE '%wind zone%';
```

### 5.3 Conflict Override Logic

```python
def resolve_conflict(inspector_result, product_rep_result):
    """
    When Inspector (Code) conflicts with Product Rep (Manufacturer)
    """
    if inspector_result.status == "Prohibited":
        if product_rep_result.status == "Allowed":
            return {
                "primary_answer": inspector_result,
                "supplement": product_rep_result,
                "warning": "⚠️ Manufacturer guidance conflicts with Building Code. Code takes precedence.",
                "flag": "CONDITIONAL_SUPPLEMENT"
            }
    return {"primary_answer": product_rep_result}
```

---

## 6. TRACEABILITY (THE SOURCE PILL)

Every response **MUST** return a **Grounding Object** for legal defensibility:

### 6.1 Grounding Object Schema

```typescript
interface GroundingObject {
  content_snippet: string;     // The specific text/quote used
  image_url?: string;          // If visual was referenced
  page_number: number;         // Exact page in source document
  deep_link: string;           // Direct URL to page in Supabase Storage
  document_title: string;      // "Nu-Wall - NW-HOC-00702 - Typical Base Channel..."
  manufacturer: string;        // "Nu-Wall"
  hierarchy_level: number;     // 1, 2, or 3
  role: string;                // "authority", "compliance", "product"
  confidence: number;          // 0.0 - 1.0
  retrieval_timestamp: string; // ISO timestamp
}
```

### 6.2 Response Format

Every agent response must include:

```json
{
  "answer": "The minimum cavity depth for this installation is 50mm...",
  "sources": [
    {
      "content_snippet": "Minimum 50mm drained and ventilated cavity required",
      "page_number": 12,
      "deep_link": "https://supabase.co/.../Nu-Wall-NW-HOC-00702.pdf#page=12",
      "document_title": "Nu-Wall - NW-HOC-00702 - Typical Base Channel Over Waterproof Deck",
      "manufacturer": "Nu-Wall",
      "hierarchy_level": 3,
      "role": "product",
      "confidence": 0.95
    }
  ],
  "conflict_flags": [],
  "warnings": []
}
```

---

## 7. AGENT OWNERSHIP MATRIX

| Agent | Owns | hierarchy_level Access | Primary Tools |
|-------|------|----------------------|---------------|
| **Foreman** | Routing, orchestration | All | `route_query`, `delegate_to_agent` |
| **Inspector** | Code compliance, regulations | 1, 2 | `check_compliance`, `get_code_reference` |
| **Product Rep** | Manufacturer data, specs | 3 | `get_product_spec`, `compare_products` |
| **Engineer** | Technical drawings, visuals | 2, 3 | `get_technical_diagram`, `extract_table` |

---

## 8. INGESTION CHECKLIST

Before ingesting any new document:

- [ ] Generate SHA-256 hash for each page
- [ ] Check for existing hash in database
- [ ] Assign `hierarchy_level` (1, 2, or 3)
- [ ] Extract and tag `dwg_id` from title block
- [ ] Run OCR vision pass for tables/diagrams
- [ ] Save `bounding_boxes` for all visuals
- [ ] Tag all measurements with `unit_range`
- [ ] Assign `geo_context` (NZ_Specific/AU_Specific/Universal)
- [ ] Set `agent_owner` array
- [ ] Chunk at section headers only (no thought splitting)
- [ ] Verify `is_latest` flag for version control
- [ ] Generate deep-link URLs for traceability

---

## 9. CHANGE LOG

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Jan 2026 | Initial release of 4-Agent Architecture protocol |

---

**END OF PROTOCOL**
