# STRYDA V2 Repository Cleanup Report
**Date:** 2025-10-30  
**Branch:** stabilize/v2-clean  
**Backup Tags:** backup/main-20251030, backup/release-v1.3.4-20251030

## Executive Summary

Performed safe repository cleanup with NO permanent deletions. All potentially unused code moved to `__quarantine__/20251030/` for review. Focus on consolidating to ONE active working branch and enforcing feature flags.

## Branch Analysis

### Current State
- **main**: 208 files (baseline)
- **release/v1.3.4**: 215 files (+7 files with citation fixes)
- **Conflict branches**: Not found in repository (already resolved or never pushed)

### Files Only in release/v1.3.4
1. `backend-minimal/clause_citations.py` - ✅ KEEP (citation system)
2. `backend-minimal/services/citations/__init__.py` - ✅ KEEP
3. `backend-minimal/services/citations/locator.py` - ✅ KEEP (page number fix)
4. `backend-minimal/tests/page_number_test.py` - ✅ KEEP (test suite)
5. `backend-minimal/tests/pills_regression.py` - ✅ KEEP (regression tests)
6. `frontend/yarn.lock` - ✅ KEEP (dependency lock)
7. `simple_backend.log` - ⚠️ QUARANTINE (log file)

## Core Application Files (KEEP - Directly Used)

### Backend Core
- `app.py` - Main FastAPI application
- `validation.py` - Input/output validation
- `profiler.py` - Performance profiling
- `intent_router.py` - Query intent classification
- `openai_structured.py` - Structured LLM responses
- `simple_tier1_retrieval.py` - Primary retrieval system
- `hybrid_retrieval_fixed.py` - B1 amendment bias detection
- `wganz_pdf_ingestion.py` - Active PDF ingestion

### RAG System (KEEP)
- `rag/retriever.py` - RAG core
- `rag/db.py` - Database interface
- `rag/llm.py` - LLM interface
- `rag/prompt.py` - Prompt engineering

### Services (KEEP)
- `services/retrieval/__init__.py` - Tier-1 retrieval
- `services/citations/locator.py` - Page number extraction
- `services/citations/__init__.py` - Citations module

### Citation System (KEEP)
- `clause_citations.py` - Clause/table/figure detection
- Feature-flagged with `CLAUSE_PILLS` (default: false)

## Files for Quarantine

### Category 1: Ingestion Scripts (One-time/Manual Use)
**Location:** `__quarantine__/20251030/ingestion/`

| File | Reason | Status |
|------|--------|--------|
| `ingest_b1_amendment13.py` | One-time ingestion script | QUARANTINE |
| `ingest_building_code.py` | Legacy ingestion | QUARANTINE |
| `ingest_full_building_code.py` | Legacy ingestion | QUARANTINE |
| `ingest_full_metal_roofing.py` | Legacy ingestion | QUARANTINE |
| `ingest_metal_roofing.py` | Legacy ingestion | QUARANTINE |
| `ingest_metal_roofing_quick.py` | Legacy ingestion | QUARANTINE |
| `ingest_nzs4229.py` | One-time ingestion | QUARANTINE |
| `monitor_ingestion.py` | Manual monitoring script | QUARANTINE |
| `tier1_pdf_ingestion.py` | Legacy tier-1 ingestion | QUARANTINE |
| `tier1_production_ingestion.py` | Legacy tier-1 ingestion | QUARANTINE |

**Rationale:** These are one-time data ingestion scripts. Supabase database already populated. Keep for reference but not needed in runtime.

### Category 2: Metadata Enrichment Scripts (One-time Processing)
**Location:** `__quarantine__/20251030/enrichment/`

| File | Reason | Status |
|------|--------|--------|
| `auto_loop_enrichment.py` | Post-processing script | QUARANTINE |
| `batch_enrichment.py` | Batch processing | QUARANTINE |
| `complete_metadata_enrichment.py` | One-time enrichment | QUARANTINE |
| `complete_metadata_extraction.py` | One-time extraction | QUARANTINE |
| `extract_metadata.py` | Legacy extraction | QUARANTINE |
| `interactive_enrichment.py` | Manual tool | QUARANTINE |
| `phase2_coverage_extension.py` | Migration script | QUARANTINE |
| `phase3_final_uplift.py` | Migration script | QUARANTINE |
| `safe_metadata_uplift.py` | One-time uplift | QUARANTINE |
| `self_monitoring_enrichment.py` | Monitoring script | QUARANTINE |
| `simple_monitoring_enrichment.py` | Monitoring script | QUARANTINE |
| `snippet_priority_enrichment.py` | Post-processing | QUARANTINE |

**Rationale:** Database metadata already enriched. These scripts were used during initial data processing. Not needed for runtime API.

### Category 3: QA/Testing Scripts (Development Tools)
**Location:** `__quarantine__/20251030/qa_testing/`

| File | Reason | Status |
|------|--------|--------|
| `chat_production_validation.py` | Manual validation script | QUARANTINE |
| `focused_production_qa.py` | QA testing script | QUARANTINE |
| `production_qa.py` | QA testing script | QUARANTINE |
| `seed_test_docs.py` | Test data seeding | QUARANTINE |
| `seed_test_docs_mock.py` | Mock test data | QUARANTINE |
| `stryda_production_soak.py` | Soak testing script | QUARANTINE |

**Rationale:** These are manual QA/testing scripts, not automated unit tests. Useful for development but not runtime.

### Category 4: Legacy/Deprecated Utilities
**Location:** `__quarantine__/20251030/utilities/`

| File | Reason | Status |
|------|--------|--------|
| `enhanced_retriever.py` | Superseded by simple_tier1_retrieval | QUARANTINE |
| `hybrid_retrieval.py` | Superseded by hybrid_retrieval_fixed | QUARANTINE |
| `multi_turn_chat.py` | Functionality integrated into app.py | QUARANTINE |
| `safe_corpus_expansion.py` | One-time corpus expansion | QUARANTINE |
| `snippet_focus.py` | Legacy snippet extraction | QUARANTINE |
| `type_safety.py` | Unused type definitions | QUARANTINE |
| `update_embeddings.py` | Manual embedding updates | QUARANTINE |
| `simple_backend.log` | Log file | QUARANTINE |
| `tmp/` directory | Temporary files | QUARANTINE |

**Rationale:** Legacy implementations superseded by current active modules, or temporary files.

## Files to KEEP (Not Quarantined)

### Active Runtime Files
- All files in `rag/` directory
- All files in `services/` directory
- `app.py`, `validation.py`, `profiler.py`, `intent_router.py`
- `openai_structured.py`, `simple_tier1_retrieval.py`, `hybrid_retrieval_fixed.py`
- `wganz_pdf_ingestion.py` (still used by /ingest endpoint)
- `clause_citations.py` (feature-flagged, but active when enabled)

### Tests to KEEP
- `backend-minimal/tests/pills_regression.py` - Automated regression suite
- `backend-minimal/tests/page_number_test.py` - Page number verification

## Feature Flag Policy Enforcement

### CLAUSE_PILLS Feature Flag
**Default:** `false` (disabled)  
**Location:** `backend-minimal/.env`

```bash
# Feature Flags - Clause/Table/Figure Pills (disabled by default)
CLAUSE_PILLS=false
```

**Behavior:**
- `CLAUSE_PILLS=false`: Page-level citations only (production-stable)
- `CLAUSE_PILLS=true`: Enhanced clause/table/figure pills (when enabled)

### Intent-Based Citation Rules
**Enforced in app.py:**

| Intent Type | Citations Behavior |
|-------------|-------------------|
| `compliance_strict` | ✅ Citations provided |
| `chitchat` | ❌ No citations |
| `general_help` | ❌ No citations |
| `product_info` | ❌ No citations |
| `clarify` | ❌ No citations |

**Code Location:** `app.py` lines 590-618

## Dependency Audit

### Backend (Python)
- **Total packages:** 103
- **Key dependencies:**
  - fastapi==0.115.0
  - psycopg2-binary (PostgreSQL)
  - openai>=1.0.0
  - pydantic==2.10.0
  - slowapi (rate limiting)

### Frontend (npm)
- **Total packages:** 40 direct dependencies
- **Key dependencies:**
  - expo@54.0.21
  - react-native@0.79.5
  - @react-navigation/* (navigation)
  - mobx@6.15.0 (state management)

### No Missing/Broken Dependencies Detected

## Git Diff Summary

### release/v1.3.4 → main
```
 11 files changed, 36 insertions(+), 8808 deletions(-)
```

**Key Changes:**
- Frontend `yarn.lock` (+7810 lines) - dependency lock file
- Citation system files (+660 lines) - page number fix
- Test files (+437 lines) - regression tests

## Recommended Actions

### Immediate (This PR)
1. ✅ Move 39 scripts to `__quarantine__/20251030/`
2. ✅ Keep all citation fixes from release/v1.3.4
3. ✅ Verify CLAUSE_PILLS=false in .env
4. ✅ Run regression tests
5. ✅ Document all moves in this report

### Short-term (Next Week)
1. Review quarantined files with team
2. Decide on permanent deletion vs archival
3. Update README with new structure
4. Create runbook for ingestion/enrichment workflows

### Long-term (Next Sprint)
1. Archive old ingestion scripts to separate repo
2. Convert useful QA scripts to automated tests
3. Document feature flag system
4. Set up branch protection for main

## Branch Strategy

### Recommended: Single Active Branch
- **Production:** `main` (protected)
- **Development:** Feature branches → PR → main
- **Risky Features:** Use environment flags (e.g., CLAUSE_PILLS)

### Delete After Merge
- `release/v1.3.4` - already merged
- Backup tags preserved: `backup/release-v1.3.4-20251030`

## Testing Results

### Regression Tests (CLAUSE_PILLS=false)
```bash
$ python3 tests/pills_regression.py
✅ 4/4 tests PASSED (100% pass rate)
- Compliance queries return page-level citations
- Chitchat queries return no citations
```

### Page Number Tests
```bash
$ python3 tests/page_number_test.py
✅ ALL TESTS PASSED
- Page numbers preserved correctly (no truncation)
- Module tests: 8/8 passed
- Integration tests: 3/3 passed
```

## Rollback Plan

If issues arise, full rollback available:
```bash
git checkout backup/main-20251030
# or
git reset --hard backup/main-20251030
```

All quarantined files remain accessible in `__quarantine__/20251030/`.

## Approval Checklist

- [ ] Review quarantine list (39 files)
- [ ] Confirm feature flag defaults (CLAUSE_PILLS=false)
- [ ] Verify regression tests pass
- [ ] Approve citation system integration
- [ ] Confirm branch deletion plan
- [ ] Review dependency audit
- [ ] Approve merge to main

## Summary Statistics

- **Files Analyzed:** 208 (main) + 215 (release)
- **Files Quarantined:** 39
- **Files Kept:** 176
- **New Files Added:** 7 (citation system + tests)
- **Tests Added:** 2 test suites
- **Zero Permanent Deletions:** ✅
- **Rollback Available:** ✅

---
**Next Steps:** Review this report, approve quarantine plan, merge PR, delete release branch.
