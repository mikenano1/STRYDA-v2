# STRYDA PROJECT MASTER MANIFEST
**Current State:** ⚡ PLATINUM CERTIFIED
**Core Database:** 106,311 Chunks (Supabase)
**Active Agents:** Neo (Logic), Stryda (Search)
**Protocol Version:** 3.1

---

## 📊 Database Status

| Metric | Value |
|--------|-------|
| **Total Chunks** | 106,311 |
| **Total PDFs** | 4,200+ |
| **Vision Engine** | Gemini 2.5 Flash (Emergent) |
| **Embedding Model** | text-embedding-3-small |

---

## ⚡ Segment Certification

| Segment | Files | Chunks | Audit Pass | Status |
|---------|-------|--------|------------|--------|
| **Bremick Fasteners** | 291 | 8,361 | 90.0% | ⚡ PLATINUM |
| **Pryda Connectors** | 17 | 357 | 100.0% | ⚡ PLATINUM |
| General Library | 3,900+ | 97,593 | - | ✅ Ingested |

---

## 📂 Protocol Registry

| Protocol | File | Status |
|----------|------|--------|
| **V3.1 Master Protocol** | `/docs/STRYDA_MASTER_PROTOCOL.md` | ⚡ **ACTIVE** |
| V3.0 PLATINUM Vision | `/protocols/INGESTION_V3_PLATINUM.md` | ⚡ Active (Engine) |
| V4 Shadow Audit | `/app/services/nightly_auditor.py` | ⚡ Active (QA) |
| V2.5 Hybrid OCR | `/protocols/PARSING_STANDARD_V2_5.md` | 📦 Fallback |
| V2 Ingestion | `/protocols/INGESTION_V2.md` | 📦 Legacy |
| V3 Compliance | `/protocols/COMPLIANCE_V3.md` | ✅ Active |

---

## 🔧 Core Configuration

### Vision Engine
```python
VISION_MODEL_PROVIDER = 'gemini'
VISION_MODEL_NAME = 'gemini-2.5-flash'
PDF_DPI_STANDARD = 200
PDF_DPI_HIGH_COMPLEXITY = 300
```

### Dependencies (Locked)
```
emergentintegrations==0.1.0
pdf2image==1.17.0
poppler-utils (system)
openai==1.99.9
supabase==2.24.0
```

---

## 🛡️ Anti-Hallucination Locks

### Pryda Segment
```python
STRICT_EXCLUSIONS = [
    'nzs 3604', 'timber span', 'rafter span',
    'joist span', 'bearer span', 'wind zone calculation'
]

EXCLUSION_RESPONSE = "Data not in Pryda Spec. Referring to Manufacturer Loadings only."
```

---

## 📁 Key Files

```
/app/
├── MASTER_MANIFEST.md              # This file
├── docs/
│   └── STRYDA_MASTER_PROTOCOL.md   # V3.1 Protocol (8 Laws + 8 Boundaries)
├── core/
│   ├── config.py                   # System configuration
│   ├── vision_engine.py            # Emergent Vision wrapper
│   └── requirements_platinum.txt   # Locked dependencies
├── services/
│   └── nightly_auditor.py          # V4 Shadow Audit
├── protocols/
│   ├── INGESTION_V3_PLATINUM.md
│   ├── COMPLIANCE_V3.md
│   └── Compliance_Master_Register.csv
├── logs/
│   ├── nightly_mastery.log
│   └── audit_reports/
└── backend-minimal/
    └── app.py                      # FastAPI + RAG Engine
```

---

## ⚓ Nightly Audit Service

```
Service: /app/services/nightly_auditor.py
Schedule: Daily at 02:00 AM
Log: /app/logs/nightly_mastery.log
Reports: /app/logs/audit_reports/
```

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jun 2025 | Initial manifest |
| 2.0 | Jan 2026 | Total Market Lockdown (97,593 chunks) |
| **3.0** | **Jan 2026** | **Bremick PLATINUM (8,361 chunks, 90% audit)** |
| **3.1** | **Jan 2026** | **Pryda PLATINUM (357 chunks, 100% audit), Protocol merge** |

---

## 🏆 Certification History

| Date | Segment | Queries | Pass Rate | Result |
|------|---------|---------|-----------|--------|
| 2026-01-25 | Bremick | 30 | 90.0% | ⚡ PLATINUM |
| 2026-01-26 | Pryda | 10 (reaudit) | 100.0% | ⚡ PLATINUM |

---

*Manifest Version: 3.1 | Last Updated: January 2026*
