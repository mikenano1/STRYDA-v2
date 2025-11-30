# STRYDA-v2 Intent Classifier V2.3 – Validation Report

**Date:** 2025-11-30T09:07:51.417609
**Classifier Version:** V2.3 (Hybrid Scoring + Few-Shots)

## Overall Stats

- Total questions: 50
- Overall accuracy: 25/50 (50.0%)

## Intent Distribution

- **general_help**: 20/50 (40.0%)
- **compliance_strict**: 17/50 (34.0%)
- **product_info**: 9/50 (18.0%)
- **implicit_compliance**: 4/50 (8.0%)

## Citation Behavior (100% Correct Expected)

- **compliance_strict**: 16/17 (94.1%) showed citations
- **general_help**: 0/20 (0.0%) showed citations
- **implicit_compliance**: 0/4 (0.0%) showed citations
- **product_info**: 0/9 (0.0%) showed citations

## Confusion Matrix

| Gold Intent | compliance_strict | implicit_compliance | general_help | product_info | council_process |
|-------------|-------------------|---------------------|--------------|--------------|------------------|
| compliance_strict | 1 | 0 | 0 | 0 | 0 |
| general_help | 16 | 4 | 20 | 5 | 0 |
| product_info | 0 | 0 | 0 | 4 | 0 |

## Key Findings

✅ **Overall Accuracy:** 50.0%

⚠️ **Below Target:** Accuracy 50.0% (target: 90%)

**Citation Control:**
- compliance_strict: 16/17 with citations
- Other intents: 0 with citations (should be 0)

✅ **Citation Behavior:** 100% correct

