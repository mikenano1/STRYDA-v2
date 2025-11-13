# STRYDA-v2 Complete Retrieval Validation

**Test Date:** 2025-11-13T10:04:50.141044

**Backend URL:** http://localhost:8001

## Summary Statistics

- **Total Queries:** 30
- **Pass Rate:** 19/30 (63.3%)
- **Cosine Operator Success:** 33.3%
- **Avg Vector Latency:** 10217ms
- **Avg Total Latency:** 10219ms

## Results by Category

### NZS 3604 (5 queries)

- **Citations Returned:** 5/5
- **Avg Latency:** 11932ms
- **Pass Rate:** 100.0%

### NZ Building Code (B1-G12) (5 queries)

- **Citations Returned:** 1/5
- **Avg Latency:** 6395ms
- **Pass Rate:** 20.0%

### E2/AS1 (5 queries)

- **Citations Returned:** 0/5
- **Avg Latency:** 12313ms
- **Pass Rate:** 0.0%

### NZS 4229 (5 queries)

- **Citations Returned:** 4/5
- **Avg Latency:** 13544ms
- **Pass Rate:** 80.0%

### General Builder Knowledge (5 queries)

- **Citations Returned:** 0/5
- **Avg Latency:** 8761ms
- **Pass Rate:** 80.0%

### Practical/Tool Questions (5 queries)

- **Citations Returned:** 0/5
- **Avg Latency:** 8372ms
- **Pass Rate:** 100.0%

## Anomalies Detected

- Query #6: "minimum barrier height f4 requirements" - Wrong intent: expected 'compliance_strict', got 'chitchat'
- Query #8: "fire stopping between floors c3 rules" - Wrong intent: expected 'compliance_strict', got 'chitchat'
- Query #9: "h1 insulation r-values for walls" - Wrong intent: expected 'compliance_strict', got 'chitchat'
- Query #10: "g12 hot water system safe temperatures" - Wrong intent: expected 'compliance_strict', got 'chitchat'
- Query #24: "how much clearance under cladding" - Over-classified: expected ['general_help', 'product_info', 'general_advice', 'chitchat'], got 'compliance_strict'

## Production Readiness

**❌ NOT READY**

## Detailed Query Results

### Query #1: nzs 3604 stud spacing requirements

- **Category:** nzs_3604
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 10583ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #2: nzs 3604 rafter span 4.2m

- **Category:** nzs_3604
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11491ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #3: nzs 3604 brace fixing pattern

- **Category:** nzs_3604
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11230ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #4: nzs 3604 pile embedment depth

- **Category:** nzs_3604
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 15439ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #5: nzs 3604 verandah beam sizing

- **Category:** nzs_3604
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 10917ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #6: minimum barrier height f4 requirements

- **Category:** nz_building_code
- **Verdict:** ❌ FAIL
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5424ms
- **Model:** server_fallback
- **Notes:** Wrong intent: expected 'compliance_strict', got 'chitchat'

### Query #7: b1 as1 footing depth for standard residential

- **Category:** nz_building_code
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 3
- **Latency:** 10294ms
- **Model:** gpt-4o
- **Sources:** B1/AS1, B1/AS1, B1/AS1
- **Notes:** ✅ Compliance query with 3 citations

### Query #8: fire stopping between floors c3 rules

- **Category:** nz_building_code
- **Verdict:** ❌ FAIL
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5438ms
- **Model:** server_fallback
- **Notes:** Wrong intent: expected 'compliance_strict', got 'chitchat'

### Query #9: h1 insulation r-values for walls

- **Category:** nz_building_code
- **Verdict:** ❌ FAIL
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5411ms
- **Model:** server_fallback
- **Notes:** Wrong intent: expected 'compliance_strict', got 'chitchat'

### Query #10: g12 hot water system safe temperatures

- **Category:** nz_building_code
- **Verdict:** ❌ FAIL
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5407ms
- **Model:** server_fallback
- **Notes:** Wrong intent: expected 'compliance_strict', got 'chitchat'

### Query #11: e2as1 minimum apron flashing cover

- **Category:** e2_as1
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 9045ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #12: e2as1 roof pitch requirements

- **Category:** e2_as1
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 14668ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #13: e2as1 cavity batten treatment levels

- **Category:** e2_as1
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 10845ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #14: e2as1 deck to cladding clearance

- **Category:** e2_as1
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 15325ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #15: e2as1 membrane fall requirements

- **Category:** e2_as1
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 11680ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #16: nzs 4229 minimum reinforcing for concrete masonry

- **Category:** nzs_4229
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11346ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #17: nzs 4229 lintel reinforcement schedule

- **Category:** nzs_4229
- **Verdict:** ⚠️ PARTIAL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 21618ms
- **Model:** gpt-4o
- **Notes:** Correct intent but 0 citations

### Query #18: nzs 4229 grout fill requirements

- **Category:** nzs_4229
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11488ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #19: nzs 4229 bond beam spacing rules

- **Category:** nzs_4229
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11660ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #20: nzs 4229 foundation block requirements

- **Category:** nzs_4229
- **Verdict:** ✅ PASS
- **Intent:** compliance_strict
- **Citations:** 1
- **Latency:** 11610ms
- **Model:** gpt-4o
- **Sources:** NZS 3604:2011
- **Notes:** ✅ Compliance query with 1 citations

### Query #21: how far can 140x45 joists span

- **Category:** general_builder
- **Verdict:** ✅ PASS
- **Intent:** general_help
- **Citations:** 0
- **Latency:** 10712ms
- **Model:** gpt-4o-mini
- **Notes:** ✅ General query with correct intent 'general_help'

### Query #22: best fixings for exterior pergola

- **Category:** general_builder
- **Verdict:** ✅ PASS
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5414ms
- **Model:** server_fallback
- **Notes:** ✅ General query with correct intent 'chitchat'

### Query #23: how to prevent decking cupping

- **Category:** general_builder
- **Verdict:** ✅ PASS
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5410ms
- **Model:** server_fallback
- **Notes:** ✅ General query with correct intent 'chitchat'

### Query #24: how much clearance under cladding

- **Category:** general_builder
- **Verdict:** ❌ FAIL
- **Intent:** compliance_strict
- **Citations:** 0
- **Latency:** 10735ms
- **Model:** gpt-4o
- **Notes:** Over-classified: expected ['general_help', 'product_info', 'general_advice', 'chitchat'], got 'compliance_strict'

### Query #25: what size posts for 3m veranda

- **Category:** general_builder
- **Verdict:** ✅ PASS
- **Intent:** general_help
- **Citations:** 0
- **Latency:** 11537ms
- **Model:** gpt-4o-mini
- **Notes:** ✅ General query with correct intent 'general_help'

### Query #26: whats the best laser level for framing

- **Category:** practical_tools
- **Verdict:** ✅ PASS
- **Intent:** general_help
- **Citations:** 0
- **Latency:** 13549ms
- **Model:** gpt-4o-mini
- **Notes:** ✅ General query with correct intent 'general_help'

### Query #27: how to stop doors sticking in winter

- **Category:** practical_tools
- **Verdict:** ✅ PASS
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5411ms
- **Model:** server_fallback
- **Notes:** ✅ General query with correct intent 'chitchat'

### Query #28: why is my deck moving when i walk on it

- **Category:** practical_tools
- **Verdict:** ✅ PASS
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5386ms
- **Model:** server_fallback
- **Notes:** ✅ General query with correct intent 'chitchat'

### Query #29: what is the best timber for outdoor steps

- **Category:** practical_tools
- **Verdict:** ✅ PASS
- **Intent:** general_help
- **Citations:** 0
- **Latency:** 12124ms
- **Model:** gpt-4o-mini
- **Notes:** ✅ General query with correct intent 'general_help'

### Query #30: best screws for treated pine

- **Category:** practical_tools
- **Verdict:** ✅ PASS
- **Intent:** chitchat
- **Citations:** 0
- **Latency:** 5388ms
- **Model:** server_fallback
- **Notes:** ✅ General query with correct intent 'chitchat'

