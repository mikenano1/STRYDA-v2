# STRYDA-v2 Chat & Citation Verification Test

**Test Date:** 2025-11-12 18:41:04  
**Version:** v2.3.0-opt  
**Queries Tested:** 20 (10 general + 10 compliance)

## Summary Results

- **Total Queries:** 20
- **Passed:** 5/20 (25.0%)
- **Partial:** 4/20 (20.0%)
- **Failed:** 11/20 (55.0%)
- **p50 Latency:** 11.9s
- **p95 Latency:** 17.0s
- **Intent Accuracy:** 60.0% (12/20 correct)
- **Citation Accuracy:** 100.0% (26/26 correct)
- **Fabricated Citations:** 0

## Latency Distribution

- **Min:** 5373ms
- **p50:** 11860ms
- **p90:** 13093ms
- **p95:** 17011ms
- **Max:** 17215ms

## General Queries (1-10)

| # | Query | Intent | Citations | Latency | Verdict |
|---|-------|--------|-----------|---------|---------|
| 1 | what's the minimum roof pitch for metal ... | compliance_strict | 3 | 17,215ms | ❌ |
| 2 | how far should nogs be spaced on a stand... | compliance_strict | 3 | 10,422ms | ❌ |
| 3 | best way to flash a roof-to-wall junctio... | compliance_strict | 0 | 11,179ms | ❌ |
| 4 | what size timber for deck joists spannin... | compliance_strict | 0 | 10,448ms | ❌ |
| 5 | how do I install weatherboards properly | chitchat | 0 | 5,383ms | ✅ |
| 6 | what's a good fixing pattern for hardipl... | compliance_strict | 1 | 11,460ms | ❌ |
| 7 | recommended screw type for corrugate iro... | compliance_strict | 0 | 12,379ms | ❌ |
| 8 | how thick should concrete slab be for a ... | chitchat | 0 | 5,373ms | ✅ |
| 9 | what underlay goes under metal roofing | compliance_strict | 0 | 11,994ms | ❌ |
| 10 | best practice for installing gutters and... | compliance_strict | 1 | 11,597ms | ❌ |

## Compliance Queries (11-20)

| # | Query | Intent | Citations | Sources | Latency | Verdict |
|---|-------|--------|-----------|---------|---------|---------|  
| 11 | E2/AS1 minimum apron flashing cover... | compliance_strict | 3 | E2/AS1 | 13,149ms | ✅ |
| 12 | NZS 3604 stud spacing requirements ... | compliance_strict | 0 | None | 12,469ms | ⚠️ |
| 13 | B1 Amendment 13 verification method... | compliance_strict | 3 | B1/AS1 | 11,233ms | ✅ |
| 14 | H1 insulation R-values for Auckland... | compliance_strict | 3 | E2/AS1 | 11,726ms | ❌ |
| 15 | F4 means of escape requirements for... | compliance_strict | 3 | E2/AS1 | 12,209ms | ❌ |
| 16 | NZS 3604 Table 7.1 wind zone classi... | compliance_strict | 0 | None | 12,499ms | ⚠️ |
| 17 | E2/AS1 cladding risk scores for wea... | compliance_strict | 0 | None | 12,591ms | ⚠️ |
| 18 | B1.3.3 foundation requirements for ... | compliance_strict | 3 | B1/AS1 | 12,112ms | ✅ |
| 19 | G5.3.2 hearth clearance for solid f... | compliance_strict | 3 | E2/AS1 | 11,207ms | ❌ |
| 20 | NZS 3604 bearer and joist sizing fo... | compliance_strict | 0 | None | 12,010ms | ⚠️ |

## Citation Quality Analysis

**Total Citations:** 26  
**Correct Sources:** 26/26 (100.0%)  
**Fabricated:** 0  
**Invalid Pages:** 0  

**Source Distribution:**
- E2/AS1: 18 citations
- B1/AS1: 6 citations
- TEST_GUIDE: 2 citations

## Intent Classification Breakdown

- **Correct:** 12/20 (60.0%)
- **Misclassified:** 8/20

**Misclassifications:**
- Query #1: Expected general_help, got compliance_strict
- Query #2: Expected general_help, got compliance_strict
- Query #3: Expected general_help, got compliance_strict
- Query #4: Expected general_help, got compliance_strict
- Query #6: Expected general_help, got compliance_strict
- Query #7: Expected general_help, got compliance_strict
- Query #9: Expected general_help, got compliance_strict
- Query #10: Expected general_help, got compliance_strict

## Issues Detected

**Query #1:** what's the minimum roof pitch for metal roofing
- Intent mismatch: expected general, got compliance_strict
- Over-citation: 3 citations (expected 0-1)
- Latency too high: 17215ms (expected <15s)

**Query #2:** how far should nogs be spaced on a standard wall
- Intent mismatch: expected general, got compliance_strict
- Over-citation: 3 citations (expected 0-1)

**Query #3:** best way to flash a roof-to-wall junction
- Intent mismatch: expected general, got compliance_strict

**Query #4:** what size timber for deck joists spanning 3 metres
- Intent mismatch: expected general, got compliance_strict

**Query #6:** what's a good fixing pattern for hardiplank cladding
- Intent mismatch: expected general, got compliance_strict

**Query #7:** recommended screw type for corrugate iron roofing
- Intent mismatch: expected general, got compliance_strict

**Query #9:** what underlay goes under metal roofing
- Intent mismatch: expected general, got compliance_strict

**Query #10:** best practice for installing gutters and downpipes
- Intent mismatch: expected general, got compliance_strict

**Query #12:** NZS 3604 stud spacing requirements for standard wind zone
- No citations provided

**Query #14:** H1 insulation R-values for Auckland climate zone
- Source mismatch: expected H1 citations

**Query #15:** F4 means of escape requirements for 2-storey residential
- Source mismatch: expected F4 citations

**Query #16:** NZS 3604 Table 7.1 wind zone classifications
- No citations provided

**Query #17:** E2/AS1 cladding risk scores for weathertightness
- No citations provided

**Query #19:** G5.3.2 hearth clearance for solid fuel appliances
- Source mismatch: expected G5 citations

**Query #20:** NZS 3604 bearer and joist sizing for deck construction
- No citations provided


## Production Readiness Verdict

**❌ NO-GO**

**Rationale:**
- Citation Accuracy: 100.0% (target 100%) ✅
- Intent Accuracy: 60.0% (target ≥90%) ❌
- p95 Latency: 17.0s (target ≤12s) ❌
- Fabrications: 0 (target 0) ✅
- Stability: 25.0% success rate ❌

**Conclusion:** System does not meet production readiness criteria. Critical issues must be resolved before deployment.
