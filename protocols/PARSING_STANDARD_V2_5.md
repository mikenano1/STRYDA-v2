# STRYDA PROTOCOL V2.5: INTELLIGENT HYBRID PARSING
**Status:** 🔴 MANDATORY FOR ALL TECHNICAL DATA

## 1. The "Smart Switch" Rule
* **IF TABLE DETECTED:**
  * Action: Must use OCR (Tesseract) to extract text.
  * Logic: **Context Injection**. Every cell value must be stored with its Row/Column headers attached (e.g., "Size: 1/2 | Load: 24,000").
  
* **IF DIAGRAM DETECTED:**
  * Action: Crop and save as Image.
  * Logic: **Triangulation Labeling**. Filename must be derived from:
    1. Parent Product Name
    2. Surrounding "Anchor Text" (e.g., "Figure 2")
    3. Vision AI Caption

## 2. Image-Only Handling
* If `get_text()` returns < 50 chars, the file is treated as a Scan.
* OCR is mandatory. Skipping files is prohibited.

## 3. Implementation Stack
```python
# Required Tools
import pytesseract          # OCR Engine
from pdf2image import convert_from_bytes  # PDF to Image
from PIL import Image       # Image processing
import fitz                 # PyMuPDF for text-layer PDFs
```

## 4. Processing Flow
```
PDF Input
    │
    ▼
┌─────────────────┐
│ Try get_text()  │
└────────┬────────┘
         │
    < 50 chars?
    /         \
   NO          YES
   │            │
   ▼            ▼
[Text Layer]  [Image Scan]
   │            │
   ▼            ▼
PyMuPDF      OCR Pipeline
Extract      ├─► pdf2image
   │         ├─► Tesseract
   │         └─► Text Output
   │            │
   └────────────┘
         │
         ▼
┌─────────────────┐
│ Context Inject  │
│ Table Parser    │
└────────┬────────┘
         │
         ▼
   Vector Database
```

## 5. Quality Standards
* **Minimum OCR Confidence:** 70%
* **Table Detection:** Grid pattern or aligned columns
* **Context Format:** `Context: {Product: X | Size: Y | Property: Z} -> Value: V`

---
*Protocol Version: 2.5 (Hybrid OCR + Vision) | Created: January 2026*
