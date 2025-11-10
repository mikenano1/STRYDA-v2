# Citation Repair Validation Report

## Test Information

- **Test Date**: 2025-11-10 07:04:01 UTC
- **Backend URL**: https://citation-guard.preview.emergentagent.com
- **Total Queries**: 20
- **Fixes Applied**: Intent router clause patterns, comparative query detection

## Before vs After Comparison

| Query # | Query | Before Intent | After Intent | Before Citations | After Citations | Before Verdict | After Verdict |
|---------|-------|---------------|--------------|------------------|-----------------|----------------|---------------|
| 1 | E2/AS1 minimum apron flashing cover... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 2 | B1 Amendment 13 verification methods for... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 3 | G5.3.2 hearth clearance requirements for... | compliance_strict | compliance_strict | 0 | 3 | ❌ FAIL - No citations provided | ⚠️ PARTIAL |
| 4 | H1 insulation R-values for Auckland clim... | compliance_strict | chitchat | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 5 | F4 means of escape requirements for 2-st... | compliance_strict | chitchat | 0 | 0 | ❌ FAIL - No citations provided | ❌ FAIL |
| 6 | E2.3.7 cladding requirements for horizon... | compliance_strict | compliance_strict | 1 | 1 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 7 | B1.3.3 foundation requirements for stand... | compliance_strict | compliance_strict | 0 | 1 | ❌ FAIL - No citations provided | ⚠️ PARTIAL |
| 8 | NZS 3604 clause 5.4.2 bracing requiremen... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 9 | NZS 3604 Table 7.1 wind zones for New Ze... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 10 | NZS 3604 stud spacing table for standard... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 11 | E2/AS1 table for cladding risk scores an... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 12 | NZS 3604 Table 8.3 bearer and joist sizi... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 13 | difference between B1 and B2 structural ... | compliance_strict | compliance_strict | 0 | 3 | ❌ FAIL - No citations provided | ⚠️ PARTIAL |
| 14 | how does E2 weathertightness relate to H... | compliance_strict | compliance_strict | 0 | 3 | ❌ FAIL - No citations provided | ⚠️ PARTIAL |
| 15 | NZS 3604 and B1 Amendment 13 requirement... | compliance_strict | compliance_strict | 3 | 3 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 16 | relationship between F7 warning systems ... | compliance_strict | compliance_strict | 0 | 3 | ❌ FAIL - No citations provided | ⚠️ PARTIAL |
| 17 | what underlay is acceptable under corrug... | compliance_strict | compliance_strict | 1 | 1 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 18 | recommended flashing tape specifications... | compliance_strict | compliance_strict | 3 | 3 | ✅ PASS | ⚠️ PARTIAL |
| 19 | what grade timber for external deck jois... | compliance_strict | compliance_strict | 2 | 2 | ⚠️ PARTIAL | ⚠️ PARTIAL |
| 20 | minimum fixing requirements for cladding... | compliance_strict | compliance_strict | 3 | 3 | ✅ PASS | ❌ FAIL |

## Summary Statistics

### Before Fixes (Previous Audit)
- **Pass Rate**: 2/20 (10.0%)
- **Avg Latency**: 9,347ms
- **Citation Accuracy**: 65.0%

### After Fixes (Current Test)
- **Pass Rate**: 0/20 (0.0%)
- **Avg Latency**: 11981ms
- **Citation Accuracy**: 100.0%

### Improvement
- **Pass Rate Change**: -2 (-10.0%)
- **Latency Change**: +2634ms
- **Citation Accuracy Change**: +35.0%

## Detailed Results by Category

### CLAUSE SPECIFIC

**Query 1**: E2/AS1 minimum apron flashing cover
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 122
- **Latency**: 14371ms
- **Sources**: E2/AS1 (3)

**Query 2**: B1 Amendment 13 verification methods for structural design
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 125
- **Latency**: 13594ms
- **Sources**: B1 Amendment 13 (3)

**Query 3**: G5.3.2 hearth clearance requirements for solid fuel appliances
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 125
- **Latency**: 11999ms
- **Sources**: NZS 3604:2011 (1), E2/AS1 (2)

**Query 4**: H1 insulation R-values for Auckland climate zone
- **Verdict**: ❌ FAIL
- **Intent**: chitchat
- **Citations**: 0
- **Word Count**: 16
- **Latency**: 6258ms

**Query 5**: F4 means of escape requirements for 2-storey residential buildings
- **Verdict**: ❌ FAIL
- **Intent**: chitchat
- **Citations**: 0
- **Word Count**: 16
- **Latency**: 5428ms

**Query 6**: E2.3.7 cladding requirements for horizontal weatherboards
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 1
- **Word Count**: 140
- **Latency**: 11467ms
- **Sources**: E2/AS1 (1)

**Query 7**: B1.3.3 foundation requirements for standard soil conditions
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 1
- **Word Count**: 157
- **Latency**: 11755ms
- **Sources**: B1/AS1 (1)

**Query 8**: NZS 3604 clause 5.4.2 bracing requirements
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 147
- **Latency**: 13010ms
- **Sources**: B1/AS1 (3)

### TABLE SPECIFIC

**Query 9**: NZS 3604 Table 7.1 wind zones for New Zealand regions
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 162
- **Latency**: 14251ms
- **Sources**: NZS 3604:2011 (3)

**Query 10**: NZS 3604 stud spacing table for standard wind zone
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 169
- **Latency**: 12095ms
- **Sources**: NZS 3604:2011 (3)

**Query 11**: E2/AS1 table for cladding risk scores and weathertightness
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 169
- **Latency**: 11688ms
- **Sources**: E2/AS1 (3)

**Query 12**: NZS 3604 Table 8.3 bearer and joist sizing for decks
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 176
- **Latency**: 12444ms
- **Sources**: NZS 3604:2011 (3)

### CROSS REFERENCE

**Query 13**: difference between B1 and B2 structural compliance verification methods
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 182
- **Latency**: 12070ms
- **Sources**: B1 Amendment 13 (2), B1/AS1 (1)

**Query 14**: how does E2 weathertightness relate to H1 thermal performance at wall penetrations
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 190
- **Latency**: 12397ms
- **Sources**: E2/AS1 (3)

**Query 15**: NZS 3604 and B1 Amendment 13 requirements for deck joist connections
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 184
- **Latency**: 11776ms
- **Sources**: NZS 3604:2011 (2), B1 Amendment 13 (1)

**Query 16**: relationship between F7 warning systems and G5 solid fuel heating
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 172
- **Latency**: 12684ms
- **Sources**: NZS 3604:2011 (2), E2/AS1 (1)

### PRODUCT PRACTICAL

**Query 17**: what underlay is acceptable under corrugate metal roofing per NZMRM
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 1
- **Word Count**: 146
- **Latency**: 11184ms
- **Sources**: E2/AS1 (1)

**Query 18**: recommended flashing tape specifications for window installations
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 206
- **Latency**: 12099ms
- **Sources**: E2/AS1 (3)

**Query 19**: what grade timber for external deck joists under NZS 3604
- **Verdict**: ⚠️ PARTIAL
- **Intent**: compliance_strict
- **Citations**: 2
- **Word Count**: 161
- **Latency**: 12169ms
- **Sources**: NZS 3604:2011 (2)

**Query 20**: minimum fixing requirements for cladding in Very High wind zone
- **Verdict**: ❌ FAIL
- **Intent**: compliance_strict
- **Citations**: 3
- **Word Count**: 180
- **Latency**: 16889ms
- **Sources**: NZS 3604:2011 (2), E2/AS1 (1)

## Sample Fixed Queries

## Citation Source Mapping

✅ No 'Unknown' sources found - all citations properly mapped

**Known Sources Found**:
- B1 Amendment 13
- B1/AS1
- E2/AS1
- NZS 3604:2011

## Conclusion

❌ **INSUFFICIENT**: Intent router fixes not achieving expected results (<40% pass rate)
