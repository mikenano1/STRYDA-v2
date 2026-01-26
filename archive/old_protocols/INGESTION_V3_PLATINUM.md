# STRYDA PROTOCOL V3.0: CLOUD VISION INGESTION
**Status:** 🔴 MANDATORY FOR ALL PRODUCTION DATA (Bremick, Pryda, LVL, etc.)

## 1. The Engine
* **Source:** Gemini 1.5 Flash Vision API.
* **Logic:** "Visual Parsing" (Not OCR). The AI reads the page image like a human engineer.

## 2. The Output Rules
* **Tables:** Output as Markdown. **CRITICAL:** Every cell value must contain its Row/Column Header context.
* **Diagrams:** Detect technical drawings. Generate a descriptive caption (e.g., "Detail of rafter fixing").
* **Text:** Transcribe verbatim.

## 3. Implementation Flow
```
PDF Input
    │
    ▼
┌─────────────────┐
│  pdf2image      │ Convert to high-res images (300 DPI)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini Flash   │ Visual AI parsing
│  Vision API     │ "Read this technical data sheet"
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         STRUCTURED OUTPUT           │
├─────────────────────────────────────┤
│ • Tables → Markdown + Context       │
│ • Diagrams → Descriptive captions   │
│ • Text → Verbatim transcription     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Context Inject  │ Attach product/size/property to values
└────────┬────────┘
         │
         ▼
   Vector Database
```

## 4. Prompt Engineering
```
SYSTEM: You are a technical document parser for construction product data sheets.

TASK: Analyze this page image and extract ALL content:

1. TABLES: Convert to Markdown format. For each cell with a numeric value,
   include the row header (e.g., size "1/2 inch") and column header 
   (e.g., "Proof Load") in the output.
   
2. DIAGRAMS: Describe any technical drawings or figures.

3. TEXT: Transcribe all text content verbatim.

OUTPUT FORMAT:
## TABLES
[Markdown tables with context]

## DIAGRAMS  
[Descriptions of any figures/drawings]

## TEXT
[Transcribed text content]
```

## 5. Quality Standards
* **Accuracy Target:** >98% for table values
* **Context Requirement:** Every numeric value must have headers attached
* **Diagram Captions:** Must describe the technical purpose

---
*Protocol Version: 3.0 (Platinum - Cloud Vision) | Created: January 2026*
