# SOURCE FILTERING VALIDATION REPORT

**Test Date:** 2025-11-25T06:30:31.409292

**Backend URL:** https://nzconstructai.preview.emergentagent.com/api/chat

**Total Queries Tested:** 20

## Executive Summary

- **Overall Pass Rate:** 30.0%
- **Queries Passed:** 6/20
- **Average Latency:** 8769ms

## Validation Criteria Results

### Source Filtering Working: ❌ FAIL
6/20 queries returned expected sources

### Fallback Logic Working: ❌ FAIL
Only 4/20 queries returned 0 citations

### Citations Present (≥80%): ✅ PASS
16/20 queries have citations

### No 'Unknown' Sources: ✅ PASS
0/20 queries have 'Unknown' sources

### Response Quality: ✅ PASS
Average response length: 771 chars

## Category Breakdown

### E2/AS1 (0/5 passed - 0.0%)

❌ **Query:** What is the minimum apron flashing cover required for E2/AS1?
   - Citations: 3
   - Sources: NZS 3604:2011 x3
   - Issues: Expected source 'E2/AS1' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 11693ms
   - Intent: compliance_strict

❌ **Query:** What roof pitch is acceptable for direct fix cladding under E2?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'E2/AS1' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 9196ms
   - Intent: compliance_strict

❌ **Query:** What are the cavity batten requirements in E2/AS1?
   - Citations: 3
   - Sources: NZS 4229:2013 x3
   - Issues: Expected source 'E2/AS1' not found in citations. Got: ['NZS 4229:2013']
   - Latency: 11159ms
   - Intent: compliance_strict

❌ **Query:** What is the minimum clearance under deck to ground per E2/AS1?
   - Citations: 3
   - Sources: NZS 3604:2011 x3
   - Issues: Expected source 'E2/AS1' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 9899ms
   - Intent: compliance_strict

❌ **Query:** What is the minimum fall for roof membrane in E2?
   - Citations: 3
   - Sources: NZS 3604:2011 x3
   - Issues: Expected source 'E2/AS1' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 10254ms
   - Intent: compliance_strict

### NZS 3604 (5/5 passed - 100.0%)

✅ **Query:** What is the stud spacing for NZS 3604?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 10247ms
   - Intent: compliance_strict

✅ **Query:** What are the requirements in NZS 3604 Table 7.1?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 10131ms
   - Intent: compliance_strict

✅ **Query:** What bearer and joist sizing does NZS 3604 require?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 10668ms
   - Intent: compliance_strict

✅ **Query:** What lintel span is permitted in NZS 3604?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 10231ms
   - Intent: compliance_strict

✅ **Query:** What nog spacing is required per NZS 3604?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 10824ms
   - Intent: compliance_strict

### NZ Building Code (1/5 passed - 20.0%)

❌ **Query:** What are H1 insulation R-values for Auckland?
   - Citations: 0
   - Issues: 0 citations returned (CRITICAL ISSUE)
   - Latency: 0ms
   - Intent: unknown

❌ **Query:** What are F4 means of escape requirements?
   - Citations: 0
   - Issues: 0 citations returned (CRITICAL ISSUE)
   - Latency: 0ms
   - Intent: unknown

✅ **Query:** What are G5.3.2 hearth clearance requirements?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Latency: 15644ms
   - Intent: compliance_strict

❌ **Query:** What are C3 fire stopping requirements?
   - Citations: 0
   - Issues: 0 citations returned (CRITICAL ISSUE)
   - Latency: 0ms
   - Intent: unknown

❌ **Query:** What are G12 water supply requirements?
   - Citations: 0
   - Issues: 0 citations returned (CRITICAL ISSUE)
   - Latency: 0ms
   - Intent: unknown

### NZS 4229 (0/5 passed - 0.0%)

❌ **Query:** What are reinforcement requirements in NZS 4229?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'NZS 4229' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 10312ms
   - Intent: compliance_strict

❌ **Query:** What concrete masonry block requirements are in NZS 4229?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'NZS 4229' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 11054ms
   - Intent: compliance_strict

❌ **Query:** What steel mesh sizing does NZS 4229 specify?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'NZS 4229' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 10445ms
   - Intent: compliance_strict

❌ **Query:** What rebar spacing is required per NZS 4229?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'NZS 4229' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 13024ms
   - Intent: compliance_strict

❌ **Query:** What lintel reinforcement does NZS 4229 require?
   - Citations: 1
   - Sources: NZS 3604:2011 x1
   - Issues: Expected source 'NZS 4229' not found in citations. Got: ['NZS 3604:2011']
   - Latency: 10594ms
   - Intent: compliance_strict

## Detailed Query Results

| # | Query | Expected Source | Citations | Sources | Pass | Issues |
|---|-------|----------------|-----------|---------|------|--------|
| 1 | What is the minimum apron flashing cover required ... | E2/AS1 | 3 | NZS 3604:2011(3) | ❌ | Expected source 'E2/AS1' not found in citations. G |
| 2 | What roof pitch is acceptable for direct fix cladd... | E2/AS1 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'E2/AS1' not found in citations. G |
| 3 | What are the cavity batten requirements in E2/AS1? | E2/AS1 | 3 | NZS 4229:2013(3) | ❌ | Expected source 'E2/AS1' not found in citations. G |
| 4 | What is the minimum clearance under deck to ground... | E2/AS1 | 3 | NZS 3604:2011(3) | ❌ | Expected source 'E2/AS1' not found in citations. G |
| 5 | What is the minimum fall for roof membrane in E2? | E2/AS1 | 3 | NZS 3604:2011(3) | ❌ | Expected source 'E2/AS1' not found in citations. G |
| 6 | What is the stud spacing for NZS 3604? | NZS 3604 | 1 | NZS 3604:2011(1) | ✅ |  |
| 7 | What are the requirements in NZS 3604 Table 7.1? | NZS 3604 | 1 | NZS 3604:2011(1) | ✅ |  |
| 8 | What bearer and joist sizing does NZS 3604 require... | NZS 3604 | 1 | NZS 3604:2011(1) | ✅ |  |
| 9 | What lintel span is permitted in NZS 3604? | NZS 3604 | 1 | NZS 3604:2011(1) | ✅ |  |
| 10 | What nog spacing is required per NZS 3604? | NZS 3604 | 1 | NZS 3604:2011(1) | ✅ |  |
| 11 | What are H1 insulation R-values for Auckland? | NZ Building Code | 0 |  | ❌ | 0 citations returned (CRITICAL ISSUE) |
| 12 | What are F4 means of escape requirements? | NZ Building Code | 0 |  | ❌ | 0 citations returned (CRITICAL ISSUE) |
| 13 | What are G5.3.2 hearth clearance requirements? | NZ Building Code | 1 | NZS 3604:2011(1) | ✅ |  |
| 14 | What are C3 fire stopping requirements? | NZ Building Code | 0 |  | ❌ | 0 citations returned (CRITICAL ISSUE) |
| 15 | What are G12 water supply requirements? | NZ Building Code | 0 |  | ❌ | 0 citations returned (CRITICAL ISSUE) |
| 16 | What are reinforcement requirements in NZS 4229? | NZS 4229 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'NZS 4229' not found in citations. |
| 17 | What concrete masonry block requirements are in NZ... | NZS 4229 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'NZS 4229' not found in citations. |
| 18 | What steel mesh sizing does NZS 4229 specify? | NZS 4229 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'NZS 4229' not found in citations. |
| 19 | What rebar spacing is required per NZS 4229? | NZS 4229 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'NZS 4229' not found in citations. |
| 20 | What lintel reinforcement does NZS 4229 require? | NZS 4229 | 1 | NZS 3604:2011(1) | ❌ | Expected source 'NZS 4229' not found in citations. |

## Conclusion

❌ **Source filtering needs significant improvement.** The system is not meeting the expected performance criteria.
