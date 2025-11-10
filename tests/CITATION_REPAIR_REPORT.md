# Citation Repair Validation Report

## Test Information

- **Test Date**: 2025-11-10 06:55:43 UTC
- **Backend URL**: https://citation-guard.preview.emergentagent.com
- **Total Queries**: 20
- **Fixes Applied**: Intent router clause patterns, comparative query detection

## Before vs After Comparison

| Query # | Query | Before Intent | After Intent | Before Citations | After Citations | Before Verdict | After Verdict |
|---------|-------|---------------|--------------|------------------|-----------------|----------------|---------------|
| 1 | E2/AS1 minimum apron flashing cover... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 2 | B1 Amendment 13 verification methods for... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 3 | G5.3.2 hearth clearance requirements for... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 4 | H1 insulation R-values for Auckland clim... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 5 | F4 means of escape requirements for 2-st... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 6 | E2.3.7 cladding requirements for horizon... | compliance_strict | N/A | 1 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 7 | B1.3.3 foundation requirements for stand... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 8 | NZS 3604 clause 5.4.2 bracing requiremen... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 9 | NZS 3604 Table 7.1 wind zones for New Ze... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 10 | NZS 3604 stud spacing table for standard... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 11 | E2/AS1 table for cladding risk scores an... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 12 | NZS 3604 Table 8.3 bearer and joist sizi... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 13 | difference between B1 and B2 structural ... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 14 | how does E2 weathertightness relate to H... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 15 | NZS 3604 and B1 Amendment 13 requirement... | compliance_strict | N/A | 3 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 16 | relationship between F7 warning systems ... | compliance_strict | N/A | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 17 | what underlay is acceptable under corrug... | compliance_strict | N/A | 1 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 18 | recommended flashing tape specifications... | compliance_strict | N/A | 3 | 0 | ✅ PASS | ❌ FAIL |
| 19 | what grade timber for external deck jois... | compliance_strict | N/A | 2 | 0 | ⚠️ PARTIAL | ❌ FAIL |
| 20 | minimum fixing requirements for cladding... | compliance_strict | N/A | 3 | 0 | ✅ PASS | ❌ FAIL |

## Summary Statistics

### Before Fixes (Previous Audit)
- **Pass Rate**: 2/20 (10.0%)
- **Avg Latency**: 9,347ms
- **Citation Accuracy**: 65.0%

### After Fixes (Current Test)
- **Pass Rate**: 0/20 (0.0%)
- **Avg Latency**: 37ms
- **Citation Accuracy**: 0.0%

### Improvement
- **Pass Rate Change**: -2 (-10.0%)
- **Latency Change**: -9310ms
- **Citation Accuracy Change**: -65.0%

## Detailed Results by Category

### CLAUSE SPECIFIC

**Query 1**: E2/AS1 minimum apron flashing cover
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 70ms

**Query 2**: B1 Amendment 13 verification methods for structural design
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 38ms

**Query 3**: G5.3.2 hearth clearance requirements for solid fuel appliances
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 38ms

**Query 4**: H1 insulation R-values for Auckland climate zone
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 34ms

**Query 5**: F4 means of escape requirements for 2-storey residential buildings
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 38ms

**Query 6**: E2.3.7 cladding requirements for horizontal weatherboards
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 40ms

**Query 7**: B1.3.3 foundation requirements for standard soil conditions
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 40ms

**Query 8**: NZS 3604 clause 5.4.2 bracing requirements
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 36ms

### TABLE SPECIFIC

**Query 9**: NZS 3604 Table 7.1 wind zones for New Zealand regions
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 34ms

**Query 10**: NZS 3604 stud spacing table for standard wind zone
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 31ms

**Query 11**: E2/AS1 table for cladding risk scores and weathertightness
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 52ms

**Query 12**: NZS 3604 Table 8.3 bearer and joist sizing for decks
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 32ms

### CROSS REFERENCE

**Query 13**: difference between B1 and B2 structural compliance verification methods
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 32ms

**Query 14**: how does E2 weathertightness relate to H1 thermal performance at wall penetrations
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 36ms

**Query 15**: NZS 3604 and B1 Amendment 13 requirements for deck joist connections
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 32ms

**Query 16**: relationship between F7 warning systems and G5 solid fuel heating
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 34ms

### PRODUCT PRACTICAL

**Query 17**: what underlay is acceptable under corrugate metal roofing per NZMRM
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 35ms

**Query 18**: recommended flashing tape specifications for window installations
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 34ms

**Query 19**: what grade timber for external deck joists under NZS 3604
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 31ms

**Query 20**: minimum fixing requirements for cladding in Very High wind zone
- **Verdict**: ❌ FAIL
- **Intent**: unknown
- **Citations**: 0
- **Word Count**: 0
- **Latency**: 35ms

## Sample Fixed Queries

## Citation Source Mapping

✅ No 'Unknown' sources found - all citations properly mapped


## Conclusion

❌ **INSUFFICIENT**: Intent router fixes not achieving expected results (<40% pass rate)
