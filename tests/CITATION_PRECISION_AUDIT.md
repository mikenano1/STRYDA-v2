# STRYDA-v2 Citation Precision & Retrieval Accuracy Audit

**Audit Date:** 2025-11-08 15:36:57 UTC

**Backend URL:** https://eng-image-extract.preview.emergentagent.com

**Total Documents Ingested:** 1,742 (NZ Building Code, NZS 3604, E2/AS1, NZMRM, etc.)

## Executive Summary

- **Total Queries Tested:** 20
- **Pass Rate:** 10.0% (2/20)
- **Partial Pass:** 11
- **Failures:** 7
- **Average Latency:** 9348ms (9.3s)
- **Citation Accuracy:** 65.0%
- **Fabricated Citations:** 0

## Expected Outcomes vs Actual

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Pass Rate | ≥80% | 10.0% | ❌ FAIL |
| Avg Latency | <7s | 9.3s | ❌ FAIL |
| Fabricated Citations | 0 | 0 | ✅ PASS |
| Citation Accuracy | ≥90% | 65.0% | ❌ FAIL |

## Detailed Query Results

| # | Query | Category | Citations | Latency | Verdict |
|---|-------|----------|-----------|---------|----------|
| 1 | E2/AS1 minimum apron flashing cover | Clause Specific | 3 | 10650ms | ⚠️ PARTIAL |
| 2 | B1 Amendment 13 verification methods for structura... | Clause Specific | 3 | 11044ms | ⚠️ PARTIAL |
| 3 | G5.3.2 hearth clearance requirements for solid fue... | Clause Specific | 0 | 5474ms | ❌ FAIL - No citations provided |
| 4 | H1 insulation R-values for Auckland climate zone | Clause Specific | 0 | 5441ms | ❌ FAIL - No citations provided |
| 5 | F4 means of escape requirements for 2-storey resid... | Clause Specific | 0 | 5407ms | ❌ FAIL - No citations provided |
| 6 | E2.3.7 cladding requirements for horizontal weathe... | Clause Specific | 1 | 10584ms | ⚠️ PARTIAL |
| 7 | B1.3.3 foundation requirements for standard soil c... | Clause Specific | 0 | 5468ms | ❌ FAIL - No citations provided |
| 8 | NZS 3604 clause 5.4.2 bracing requirements | Clause Specific | 3 | 10876ms | ⚠️ PARTIAL |
| 9 | NZS 3604 Table 7.1 wind zones for New Zealand regi... | Table Specific | 3 | 10895ms | ⚠️ PARTIAL |
| 10 | NZS 3604 stud spacing table for standard wind zone | Table Specific | 3 | 10890ms | ⚠️ PARTIAL |
| 11 | E2/AS1 table for cladding risk scores and weathert... | Table Specific | 3 | 10563ms | ⚠️ PARTIAL |
| 12 | NZS 3604 Table 8.3 bearer and joist sizing for dec... | Table Specific | 3 | 15909ms | ⚠️ PARTIAL |
| 13 | difference between B1 and B2 structural compliance... | Cross Reference | 0 | 5469ms | ❌ FAIL - No citations provided |
| 14 | how does E2 weathertightness relate to H1 thermal ... | Cross Reference | 0 | 5458ms | ❌ FAIL - No citations provided |
| 15 | NZS 3604 and B1 Amendment 13 requirements for deck... | Cross Reference | 3 | 11965ms | ⚠️ PARTIAL |
| 16 | relationship between F7 warning systems and G5 sol... | Cross Reference | 0 | 5457ms | ❌ FAIL - No citations provided |
| 17 | what underlay is acceptable under corrugate metal ... | Product Practical | 1 | 10551ms | ⚠️ PARTIAL |
| 18 | recommended flashing tape specifications for windo... | Product Practical | 3 | 12143ms | ✅ PASS |
| 19 | what grade timber for external deck joists under N... | Product Practical | 2 | 11176ms | ⚠️ PARTIAL |
| 20 | minimum fixing requirements for cladding in Very H... | Product Practical | 3 | 11528ms | ✅ PASS |

## Semantic Relevance Analysis (10 Samples)

| Query | Relevance Score |
|-------|----------------|
| E2/AS1 minimum apron flashing cover | ✅ Highly Relevant |
| G5.3.2 hearth clearance requirements for solid fuel applianc... | ❌ No citations |
| F4 means of escape requirements for 2-storey residential bui... | ❌ No citations |
| B1.3.3 foundation requirements for standard soil conditions | ❌ No citations |
| NZS 3604 Table 7.1 wind zones for New Zealand regions | ✅ Highly Relevant |
| E2/AS1 table for cladding risk scores and weathertightness | ✅ Highly Relevant |
| difference between B1 and B2 structural compliance verificat... | ❌ No citations |
| NZS 3604 and B1 Amendment 13 requirements for deck joist con... | ✅ Highly Relevant |
| what underlay is acceptable under corrugate metal roofing pe... | ✅ Highly Relevant |
| what grade timber for external deck joists under NZS 3604 | ✅ Highly Relevant |

## Top Cited Documents

- **Unknown**: 34 citations

## Off-Target Patterns & Issues

### Failed Queries:

- **Query:** G5.3.2 hearth clearance requirements for solid fuel appliances
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** H1 insulation R-values for Auckland climate zone
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** F4 means of escape requirements for 2-storey residential buildings
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** B1.3.3 foundation requirements for standard soil conditions
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** difference between B1 and B2 structural compliance verification methods
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** how does E2 weathertightness relate to H1 thermal performance at wall penetrations
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

- **Query:** relationship between F7 warning systems and G5 solid fuel heating
  - **Reason:** ❌ FAIL - No citations provided
  - **Citations:** 0
  - **Word Count:** 16

## Recommendations

- ⚠️ **Pass rate below 80%**: Review citation generation logic and document retrieval relevance
- ⚠️ **Latency above 7s**: Consider optimizing vector search or implementing caching
- ⚠️ **7 queries failed**: Review specific failure patterns above

---

*Report generated on 2025-11-08T15:36:57.017736*
