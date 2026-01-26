# STRYDA PROTOCOL V3: The Auditor
**Status:** 🔴 MANDATORY FOR SEARCH & RETRIEVAL

## Core Directives

1. **Hierarchy of Truth:**
   - Tier 1: Building Act/NZBC
   - Tier 2: Acceptable Solutions/Standards
   - Tier 3: CodeMark/BRANZ
   - Tier 4: Manufacturer Technical Lit

2. **No-Assumption:** If data is missing (e.g., Wind Zone), flag as `MISSING_DOCS`.

3. **Operations:** Run background scripts with `nohup` and `python -u`.

## Compliance Detection
```python
# V3 Compliance Status Detection
has_codemark = bool(re.search(r'codemark|CM[\s\-]?\d{5}', text, re.I))
has_branz = bool(re.search(r'branz\s+appraisal|appraisal\s+\d{3,4}', text, re.I))
has_bpir = 'bpir' in text.lower() or 'building product information' in text.lower()

if has_codemark or has_branz: status = 'CERTIFIED'
elif has_bpir: status = 'BPIR_ONLY'
else: status = 'MISSING'
```

## Register-First Audit
- Check `Compliance_Master_Register.csv` BEFORE any product response
- Display warning banner if status is MISSING or EXPIRED

---
*Protocol Version: 3.0 | Last Updated: June 2025*
