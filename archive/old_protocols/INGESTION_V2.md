# STRYDA PROTOCOL V2: The Librarian
**Status:** 🔴 MANDATORY FOR FILE MANAGEMENT

## Core Directives

1. **Naming:** Rename all files to `[Manufacturer] - [Product Name] - [Doc Type].pdf`.
2. **Sanitization:** Strip hash codes, URL garbage (%20), and trademarks.
3. **Sorting:**
   - Warranties/Care Guides -> `/00_General_Resources/`
   - NZ Steel/ColorCote -> `/00_Material_Suppliers/`
4. **Hidden Data:** Rename "Accessories" files to `& Installation` if they contain span tables.

## Implementation Notes
- All ingested files must pass through V2 naming convention
- Hash-based deduplication prevents duplicate chunks
- Source traceability maintained via `source` field in database

---
*Protocol Version: 2.0 | Last Updated: June 2025*
