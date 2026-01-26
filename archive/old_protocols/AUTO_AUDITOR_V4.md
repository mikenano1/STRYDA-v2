# STRYDA PROTOCOL V4: The Auto-Auditor
**Status:** 🔴 MANDATORY FOR LOGIC & TESTING

## Core Directives

1. **Intent Router:** Categorize queries into:
   - Direct Audit
   - Solution Finder
   - Conflict Check
   - Missing Context

2. **Context Gate:** BLOCK answers if Wind Zone/Exposure Zone is required but missing.

3. **Multi-Source Handshake:** Recommendations must cite:
   - Law (NZBC Clause)
   - Standard (E2/AS1, NZMRM, etc.)
   - Manufacturer (Technical Document)

4. **Shadow Tester:** Overnight loop of 500+ generated questions to test logic drift.

## Response Standard
The ONLY acceptable answer format:
- **The Specific Value**: (e.g., "Fix at every rib at end-laps")
- **The Source File**: (e.g., "NZMRM Code of Practice, Version 24.12")
- **The Page/Table**: (e.g., "Table 3.10.1, Page 86")

## Retrieval Parameters
- Installation queries: top_k = 50 chunks minimum
- Specification queries: top_k = 30 chunks
- General queries: top_k = 20 chunks

---
*Protocol Version: 4.0 | Last Updated: June 2025*
