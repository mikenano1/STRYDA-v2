# STRYDA-v2 POST-REGENERATION VALIDATION REPORT

**Test Date:** 2025-11-25 07:16:43  
**Backend URL:** https://buildai-15.preview.emergentagent.com  
**Total Queries:** 30

---

## Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Total Pass Rate** | 10/30 (33.3%) | ≥90% | ❌ FAIL |
| **Expected Citations** | 0/20 | 20/20 | ❌ FAIL |
| **Expected No Citations** | 10/10 | 10/10 | ✅ PASS |
| **Cosine Operator Success** | 0/30 (0.0%) | >30% | ❌ FAIL |
| **Fallback Usage** | 20 queries | - | ℹ️ INFO |
| **Avg Vector Latency** | 0ms | <5000ms | ✅ PASS |
| **Avg Total Latency** | 9493ms | <15000ms | ✅ PASS |

---

## Category Breakdown

### NZS 3604
- **Pass Rate:** 0/5 (0.0%)
- **Avg Latency:** 11114ms
- **Citations Provided:** 0/5

### E2/AS1
- **Pass Rate:** 0/5 (0.0%)
- **Avg Latency:** 11113ms
- **Citations Provided:** 0/5

### NZ Building Code
- **Pass Rate:** 0/5 (0.0%)
- **Avg Latency:** 6238ms
- **Citations Provided:** 0/5

### NZS 4229
- **Pass Rate:** 0/5 (0.0%)
- **Avg Latency:** 13714ms
- **Citations Provided:** 0/5

### General Builder
- **Pass Rate:** 5/5 (100.0%)
- **Avg Latency:** 8076ms
- **Citations Provided:** 0/5

### Practical/Tool
- **Pass Rate:** 5/5 (100.0%)
- **Avg Latency:** 6704ms
- **Citations Provided:** 0/5

---

## Failed Queries (20)

| Query | Category | Reason | Citations | Latency |
|-------|----------|--------|-----------|---------|
| nzs 3604 stud spacing requirements... | NZS 3604 | Expected 1-3 citations, got 0 | 0 | 11317ms |
| nzs 3604 rafter span 4.2m... | NZS 3604 | Expected 1-3 citations, got 0 | 0 | 11640ms |
| nzs 3604 brace fixing pattern... | NZS 3604 | Expected 1-3 citations, got 0 | 0 | 10063ms |
| nzs 3604 pile embedment depth... | NZS 3604 | Expected 1-3 citations, got 0 | 0 | 10955ms |
| nzs 3604 verandah beam sizing... | NZS 3604 | Expected 1-3 citations, got 0 | 0 | 11594ms |
| e2as1 minimum apron flashing cover... | E2/AS1 | Expected 1-3 citations, got 0 | 0 | 10627ms |
| e2as1 roof pitch requirements... | E2/AS1 | Expected 1-3 citations, got 0 | 0 | 11901ms |
| e2as1 cavity batten treatment levels... | E2/AS1 | Expected 1-3 citations, got 0 | 0 | 10956ms |
| e2as1 deck to cladding clearance... | E2/AS1 | Expected 1-3 citations, got 0 | 0 | 12349ms |
| e2as1 membrane fall requirements... | E2/AS1 | Expected 1-3 citations, got 0 | 0 | 9731ms |
| minimum barrier height f4 requirements... | NZ Building Code | Expected 1-3 citations, got 0 | 0 | 5053ms |
| b1 as1 footing depth for standard residential... | NZ Building Code | Expected 1-3 citations, got 0 | 0 | 10953ms |
| fire stopping between floors c3 rules... | NZ Building Code | Expected 1-3 citations, got 0 | 0 | 5082ms |
| h1 insulation r-values for walls... | NZ Building Code | Expected 1-3 citations, got 0 | 0 | 5058ms |
| g12 hot water system safe temperatures... | NZ Building Code | Expected 1-3 citations, got 0 | 0 | 5043ms |
| nzs 4229 minimum reinforcing for concrete masonry... | NZS 4229 | Expected 1-3 citations, got 0 | 0 | 10732ms |
| nzs 4229 lintel reinforcement schedule... | NZS 4229 | Expected 1-3 citations, got 0 | 0 | 11055ms |
| nzs 4229 grout fill requirements... | NZS 4229 | Expected 1-3 citations, got 0 | 0 | 16694ms |
| nzs 4229 bond beam spacing rules... | NZS 4229 | Expected 1-3 citations, got 0 | 0 | 12015ms |
| nzs 4229 foundation block requirements... | NZS 4229 | Expected 1-3 citations, got 0 | 0 | 18076ms |

---

## Detailed Results

| # | Query | Category | Intent | Citations | Sources | Latency | Pass/Fail |
|---|-------|----------|--------|-----------|---------|---------|-----------|
| 1 | nzs 3604 stud spacing requirements... | NZS 3604 | compliance_strict | 0 | None | 11317ms | FAIL |
| 2 | nzs 3604 rafter span 4.2m... | NZS 3604 | compliance_strict | 0 | None | 11640ms | FAIL |
| 3 | nzs 3604 brace fixing pattern... | NZS 3604 | compliance_strict | 0 | None | 10063ms | FAIL |
| 4 | nzs 3604 pile embedment depth... | NZS 3604 | compliance_strict | 0 | None | 10955ms | FAIL |
| 5 | nzs 3604 verandah beam sizing... | NZS 3604 | compliance_strict | 0 | None | 11594ms | FAIL |
| 6 | e2as1 minimum apron flashing cover... | E2/AS1 | compliance_strict | 0 | None | 10627ms | FAIL |
| 7 | e2as1 roof pitch requirements... | E2/AS1 | compliance_strict | 0 | None | 11901ms | FAIL |
| 8 | e2as1 cavity batten treatment levels... | E2/AS1 | compliance_strict | 0 | None | 10956ms | FAIL |
| 9 | e2as1 deck to cladding clearance... | E2/AS1 | compliance_strict | 0 | None | 12349ms | FAIL |
| 10 | e2as1 membrane fall requirements... | E2/AS1 | compliance_strict | 0 | None | 9731ms | FAIL |
| 11 | minimum barrier height f4 requirements... | NZ Building Code | chitchat | 0 | None | 5053ms | FAIL |
| 12 | b1 as1 footing depth for standard reside... | NZ Building Code | compliance_strict | 0 | None | 10953ms | FAIL |
| 13 | fire stopping between floors c3 rules... | NZ Building Code | chitchat | 0 | None | 5082ms | FAIL |
| 14 | h1 insulation r-values for walls... | NZ Building Code | chitchat | 0 | None | 5058ms | FAIL |
| 15 | g12 hot water system safe temperatures... | NZ Building Code | chitchat | 0 | None | 5043ms | FAIL |
| 16 | nzs 4229 minimum reinforcing for concret... | NZS 4229 | compliance_strict | 0 | None | 10732ms | FAIL |
| 17 | nzs 4229 lintel reinforcement schedule... | NZS 4229 | compliance_strict | 0 | None | 11055ms | FAIL |
| 18 | nzs 4229 grout fill requirements... | NZS 4229 | compliance_strict | 0 | None | 16694ms | FAIL |
| 19 | nzs 4229 bond beam spacing rules... | NZS 4229 | compliance_strict | 0 | None | 12015ms | FAIL |
| 20 | nzs 4229 foundation block requirements... | NZS 4229 | compliance_strict | 0 | None | 18076ms | FAIL |
| 21 | how far can 140x45 joists span... | General Builder | general_help | 0 | None | 9426ms | PASS |
| 22 | best fixings for exterior pergola... | General Builder | chitchat | 0 | None | 5029ms | PASS |
| 23 | how to prevent decking cupping... | General Builder | chitchat | 0 | None | 5046ms | PASS |
| 24 | how much clearance under cladding... | General Builder | compliance_strict | 0 | None | 10318ms | PASS |
| 25 | what size posts for 3m veranda... | General Builder | general_help | 0 | None | 10561ms | PASS |
| 26 | whats the best laser level for framing... | Practical/Tool | general_help | 0 | None | 9141ms | PASS |
| 27 | how to stop doors sticking in winter... | Practical/Tool | chitchat | 0 | None | 5169ms | PASS |
| 28 | why is my deck moving when i walk on it... | Practical/Tool | chitchat | 0 | None | 5065ms | PASS |
| 29 | what is the best timber for outdoor step... | Practical/Tool | general_help | 0 | None | 9106ms | PASS |
| 30 | best screws for treated pine... | Practical/Tool | chitchat | 0 | None | 5037ms | PASS |

---

## Critical Findings

### E2/AS1 Source Targeting
- **Queries with citations:** 0/5
- **Correct E2/AS1 source:** 0/5
- **Status:** ❌ Failed

### NZS 4229 Source Targeting
- **Queries with citations:** 0/5
- **Correct NZS 4229 source:** 0/5
- **Status:** ❌ Failed

### Fallback Logic
- **Fallback triggered:** 20 queries
- **Status:** ⚠️ High usage

### Source Filtering
- **Source filter applied:** 20/30 queries
- **Status:** ℹ️ Detected based on query content

