# STRYDA PROJECT MASTER MANIFEST
**Current State:** Stabilized
**Core Database:** 97,593 Chunks (Supabase)
**Active Agents:** Neo (Logic), Stryda (Search)

## 📂 Protocol Registry
| Protocol | File | Status |
|----------|------|--------|
| **V3.0 PLATINUM** | `/protocols/INGESTION_V3_PLATINUM.md` | ⚡ **ACTIVE (Primary Engine)** |
| V2.5 Hybrid OCR | `/protocols/PARSING_STANDARD_V2_5.md` | 📦 Legacy/Fallback |
| V2 Ingestion | `/protocols/INGESTION_V2.md` | 📦 Legacy/Fallback (File Hygiene) |
| V3 Compliance | `/protocols/COMPLIANCE_V3.md` | ✅ Active (Hierarchy of Law) |
| V4 Auto-Auditor | `/protocols/AUTO_AUDITOR_V4.md` | ✅ Active (Logic Engine) |

## 📊 Data Assets
| Asset | Location | Records |
|-------|----------|--------|
| Vector Database | Supabase PostgreSQL | 97,593 chunks |
| Compliance Register | `/protocols/Compliance_Master_Register.csv` | 2,428 products |
| File Manifest | `/app/full_library_audit_files.json` | 4,184 PDFs |
| Ingestion Log | `/app/total_lockdown.log` | Complete |

## ⚓ Daily Anchor Protocol
Neo must update `PROJECT_STATE.md` at the end of every session with:
- Current ingest count
- Commit hash (if applicable)
- Any protocol changes
- Outstanding issues

## 🔗 Key Files
```
/app/
├── MASTER_MANIFEST.md          # This file
├── PROJECT_STATE.md            # Daily state anchor
├── protocols/
│   ├── INGESTION_V2.md         # File naming & hygiene
│   ├── COMPLIANCE_V3.md        # Audit & hierarchy rules
│   ├── AUTO_AUDITOR_V4.md      # Logic engine specs
│   └── Compliance_Master_Register.csv
├── backend-minimal/
│   └── app.py                  # FastAPI + RAG Engine
├── resume_lockdown.py          # V3 Ingestion Script
└── full_library_audit_files.json
```

---
*Manifest Version: 1.0 | Created: June 2025*

* **/protocols/PARSING_STANDARD_V2_5.md**: Active (Hybrid OCR + Vision Logic)
