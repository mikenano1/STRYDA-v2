# 📜 STRYDA CODE CONSTITUTION
## The Four Laws of STRYDA Development
**Version:** 1.0 | **Effective:** January 2026 | **Authority:** SUPREME

---

## 🚫 LAW I: THE FLAT ROOT

> **You are FORBIDDEN from creating new files in the root directory.**

### Permitted Root Files (EXHAUSTIVE LIST):
- `.env` - Environment configuration
- `.gitignore` - Git ignore rules
- `.gitconfig` - Git configuration
- `README.md` - Repository overview
- `requirements.txt` - Python dependencies

### Violation Penalty:
Any file created in `/app/` root that is not in the permitted list MUST be immediately moved to the appropriate subdirectory.

---

## 📦 LAW II: THE ARCHIVE

> **All "one-off" fix scripts, temporary ingestion tools, and historical files must be moved to `/archive/` immediately after a successful run.**

### Archive Structure:
```
/archive/
├── historical_scripts/   # Completed Python scripts
├── historical_reports/   # Old .md, .json reports
├── historical_logs/      # Execution logs
├── legacy_backend/       # Deprecated backend code
└── old_protocols/        # Superseded protocol files
```

### Archive Trigger Conditions:
1. Script has completed its task successfully
2. Script has not been modified in 48+ hours
3. Script is a "fix_*.py" or "audit_*.py" one-off

---

## 🏛️ LAW III: UNIFIED TRUTH

> **There shall be only ONE active core.**

### Active Directories:
| Directory | Purpose | Status |
|-----------|---------|--------|
| `/app/core/` | Active reasoning & retrieval engine | 🟢 PRIMARY |
| `/app/ingestion/` | Data processing scripts | 🟢 ACTIVE |
| `/app/mastery/` | Brand laws & protocols | 🟢 ACTIVE |
| `/app/frontend/` | Expo mobile application | 🟢 ACTIVE |
| `/app/tests/` | Unified testing suite | 🟢 ACTIVE |

### Deprecated (DO NOT USE):
- `/app/backend/` → ARCHIVED
- `/app/backend-minimal/` → SUPERSEDED by `/app/core/`
- `/app/src/` → MIGRATED to `/app/ingestion/`
- `/app/protocols/` → MIGRATED to `/app/mastery/protocols/`

---

## ✅ LAW IV: PLATINUM VERIFICATION

> **You are VETOED from self-certifying a "Pass" unless the test response contains ALL THREE:**

### Mandatory Verification Criteria:

**A. Document Citation**
```
✅ PASS: "Source: BRANZ Appraisal 1154, Page 3"
❌ FAIL: "Based on available data..."
```

**B. Technical Value**
```
✅ PASS: "Withdrawal capacity: 1.2 kN"
✅ PASS: "Minimum penetration: 32mm"
✅ PASS: "Grade 316 Stainless Steel required"
❌ FAIL: "Check the specifications..."
```

**C. Consultative Follow-up**
```
✅ PASS: "What durability zone is this for?"
✅ PASS: "Is this for structural or decorative application?"
❌ FAIL: Response ends without clarifying question
```

### Verification Code:
```python
def verify_platinum_response(response: str) -> bool:
    has_citation = bool(re.search(r'(Source|BRANZ|Appraisal|Page \d)', response))
    has_value = bool(re.search(r'\d+(\.\d+)?\s*(kN|mm|MPa|Grade|%)', response))
    has_consultative = bool(re.search(r'\?$|zone|application|timber', response, re.I))
    return has_citation and has_value and has_consultative
```

---

## 📁 THE NEW ARCHITECTURE

```
/app/
├── .env                    # Environment config
├── .gitignore              # Git ignore
├── README.md               # Repository overview
├── requirements.txt        # Dependencies
│
├── core/                   # 🟢 ACTIVE REASONING ENGINE
│   ├── app.py              # FastAPI main application
│   ├── retrieval_service.py # V3.0 GOD TIER retrieval
│   ├── delfast_consultative.py # LAW 5 hardened triggers
│   └── ...                 # All active backend modules
│
├── frontend/               # 🟢 EXPO MOBILE APP
│   ├── app/                # Expo router screens
│   └── ...
│
├── ingestion/              # 🟢 DATA PROCESSING
│   ├── active/             # Current ingestion scripts
│   └── completed/          # Finished but retained for reference
│
├── mastery/                # 🟢 BRAND LAWS & PROTOCOLS
│   ├── CODE_CONSTITUTION.md # THIS FILE
│   ├── brand_shields/      # Brand protection rules
│   │   └── DELFAST.md
│   └── protocols/          # Active protocol definitions
│       ├── INGESTION_V3_PLATINUM.md
│       └── ...
│
├── tests/                  # 🟢 UNIFIED TESTING
│   └── ...
│
└── archive/                # 🔴 HISTORICAL (READ-ONLY)
    ├── historical_scripts/
    ├── historical_reports/
    ├── historical_logs/
    ├── legacy_backend/
    └── old_protocols/
```

---

## 🔐 ENFORCEMENT

Before ANY write operation, Neo MUST:

1. **CHECK** this file exists at `/app/mastery/CODE_CONSTITUTION.md`
2. **VERIFY** the target path complies with Law I (Flat Root)
3. **CONFIRM** one-off scripts are flagged for archival (Law II)
4. **ENSURE** no duplicate backends are created (Law III)
5. **VALIDATE** test responses meet Platinum criteria (Law IV)

### Violation Response:
```
⚠️ CODE CONSTITUTION VIOLATION DETECTED
Law: [I/II/III/IV]
Violation: [Description]
Remediation: [Required action]
```

---

*Ratified by STRYDA Mastery System | January 2026*
