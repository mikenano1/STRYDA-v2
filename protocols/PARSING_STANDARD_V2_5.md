# STRYDA PROTOCOL V2.5: GOD-TIER PARSING
**Status:** 🔴 MANDATORY FOR ALL TECHNICAL DATA

## 1. The "Context Glue" Rule
Standard AI reads text linearly and loses context. Stryda must use **Cell-Level Context Injection**.
* **Requirement:** Every data point extracted from a table must be stored with its Headers attached.
* **Bad:** "24,000"
* **Good:** "Product: Hex Nut | Size: 1/2 inch | Property: Proof Load | Value: 24,000"

## 2. Vision-First Enforcement
* **Tables:** Detect gridlines. Do NOT flatten to plain text. Parse as structured Key-Value pairs.
* **Diagrams:** Use Vision to caption images (e.g., "Diagram showing rafter connection details").

## 3. The "Engineer" Agent
* This protocol activates the "Engineer" agent capability for all Ingestion tasks.
* The Engineer ensures every technical specification is self-contained and retrievable.
* No orphaned values - every number has its context permanently attached.

## 4. Implementation Requirements
```python
# CONTEXT GLUE PATTERN
chunk = f"Context: {{Product: {product} | Row: {row_header} | Col: {col_header}}} -> Value: {value}"
```

## 5. Quality Standard
* **Minimum:** Every table cell must be queryable independently
* **Target:** "What is the proof load for 1/2 inch hex nut?" returns exact value with full context
* **Validation:** Vision Verification test must PASS before production deployment

---
*Protocol Version: 2.5 (God-Tier) | Created: January 2026*
