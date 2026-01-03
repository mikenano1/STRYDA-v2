# Intent Router Fix Verification

## Test Overview
- **Date**: 2025-11-12 19:09:52
- **Total Queries**: 20 (10 general + 10 compliance)
- **Backend URL**: https://stryda-brain.preview.emergentagent.com/api/chat

## Before Fix
- **Intent Accuracy**: 60% (12/20)
- **Over-Classification**: 8/10 general queries misclassified
- **Pass Rate**: 25% (5/20)

## After Fix
- **Intent Accuracy**: 80% (16/20)
- **Over-Classification**: 2/10 general queries misclassified
- **Pass Rate**: 40% (8/20)

## Improvement
- **Intent Accuracy**: +20%
- **Pass Rate**: +15%
- **Over-Classification Reduction**: 6 queries fixed

## Detailed Results

| # | Query | Expected | Actual | Citations | Latency | Pass |
|---|-------|----------|--------|-----------|---------|------|
| 1 | what's the minimum roof pitch for metal roofing... | general_help | general_help | 0 | 11431ms | ✅ |
| 2 | how far should nogs be spaced on a standard wall... | general_help | general_help | 0 | 10553ms | ✅ |
| 3 | best way to flash a roof-to-wall junction... | general_help | general_help | 0 | 11166ms | ✅ |
| 4 | what size timber for deck joists spanning 3 metres... | general_help | general_help | 0 | 10838ms | ✅ |
| 5 | how do I install weatherboards properly... | general_help | general_help | 0 | 11011ms | ✅ |
| 6 | what's a good fixing pattern for hardiplank claddi... | general_help | compliance_strict | 0 | 14154ms | ❌ |
| 7 | recommended screw type for corrugate iron roofing... | general_help | general_help | 0 | 11056ms | ✅ |
| 8 | how thick should concrete slab be for a garage... | general_help | general_help | 0 | 11771ms | ✅ |
| 9 | what underlay goes under metal roofing... | general_help | compliance_strict | 0 | 10467ms | ❌ |
| 10 | best practice for installing gutters and downpipes... | general_help | general_help | 0 | 11956ms | ✅ |
| 11 | E2/AS1 minimum apron flashing cover requirements... | compliance_strict | compliance_strict | 0 | 10056ms | ❌ |
| 12 | NZS 3604 stud spacing requirements for standard wi... | compliance_strict | compliance_strict | 0 | 11569ms | ❌ |
| 13 | B1 Amendment 13 verification methods for structura... | compliance_strict | compliance_strict | 0 | 14371ms | ❌ |
| 14 | H1 insulation R-values for Auckland climate zone... | compliance_strict | chitchat | 0 | 5449ms | ❌ |
| 15 | F4 means of escape requirements for 2-storey resid... | compliance_strict | chitchat | 0 | 5439ms | ❌ |
| 16 | NZS 3604 Table 7.1 wind zone classifications... | compliance_strict | compliance_strict | 0 | 11868ms | ❌ |
| 17 | E2/AS1 cladding risk scores for weathertightness... | compliance_strict | compliance_strict | 0 | 14006ms | ❌ |
| 18 | B1.3.3 foundation requirements for standard soil... | compliance_strict | compliance_strict | 0 | 14290ms | ❌ |
| 19 | G5.3.2 hearth clearance for solid fuel appliances... | compliance_strict | compliance_strict | 0 | 11605ms | ❌ |
| 20 | NZS 3604 bearer and joist sizing for deck construc... | compliance_strict | compliance_strict | 0 | 15915ms | ❌ |

## Sample Fixes

### Query: "what's the minimum roof pitch for metal roofing"
**Before:** compliance_strict (over-classified)
**After:** general_help, 0 citations ✅ FIXED

### Query: "how far should nogs be spaced on a standard wall"
**Before:** compliance_strict (over-classified)
**After:** general_help, 0 citations ✅ FIXED

### Query: "best way to flash a roof-to-wall junction"
**Before:** compliance_strict (over-classified)
**After:** general_help, 0 citations ✅ FIXED

## Remaining Issues

### Query #6: "what's a good fixing pattern for hardiplank cladding"
- **Expected**: general_help
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Intent misclassification

### Query #9: "what underlay goes under metal roofing"
- **Expected**: general_help
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Intent misclassification

### Query #11: "E2/AS1 minimum apron flashing cover requirements"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #12: "NZS 3604 stud spacing requirements for standard wind zone"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #13: "B1 Amendment 13 verification methods for structural design"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #14: "H1 insulation R-values for Auckland climate zone"
- **Expected**: compliance_strict
- **Actual**: chitchat
- **Citations**: 0
- **Issue**: Intent misclassification

### Query #15: "F4 means of escape requirements for 2-storey residential"
- **Expected**: compliance_strict
- **Actual**: chitchat
- **Citations**: 0
- **Issue**: Intent misclassification

### Query #16: "NZS 3604 Table 7.1 wind zone classifications"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #17: "E2/AS1 cladding risk scores for weathertightness"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #18: "B1.3.3 foundation requirements for standard soil"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #19: "G5.3.2 hearth clearance for solid fuel appliances"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

### Query #20: "NZS 3604 bearer and joist sizing for deck construction"
- **Expected**: compliance_strict
- **Actual**: compliance_strict
- **Citations**: 0
- **Issue**: Citation count out of range

## Conclusion

❌ **FAILED** - Intent router still has significant issues requiring attention.

### Key Metrics
- Pass Rate: 40% (Target: ≥80%)
- Intent Accuracy: 80% (Target: ≥90%)
- Over-Classification: 2/10 (Target: ≤2)
