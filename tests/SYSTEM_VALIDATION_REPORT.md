# STRYDA-v2 System Validation Report

Date: 2025-11-03 08:32:25
Model: gpt-4o
Database: Supabase PostgreSQL

## Summary

- **Total Queries**: 15
- **Pass Rate**: 46.7%
- **Average Latency**: 10226ms
- **Citation Issues**: 0

## System Health

### Version Check
- Model: gpt-4o
- Fallback: gpt-4o-mini
- GPT5 Shadow: True
- Status: ✅ PASS

### Database Health
- Documents: 1742
- Reasoning Responses: 1
- Status: ✅ PASS

### API Health
- /health: ✅ PASS
- /ready: ✅ PASS

## Detailed Query Results

| # | Query | Category | Verdict | Citations | Latency (ms) |
|---|-------|----------|---------|-----------|--------------|
| 1 | E2/AS1 minimum apron flashing cover... | clause_specific | accurate | 0 | 10651 |
| 2 | B1 Amendment 13 verification methods for structura... | clause_specific | partial | 0 | 12728 |
| 3 | G5.3.2 hearth clearance requirements... | clause_specific | partial | 0 | 5405 |
| 4 | H1 insulation R-values for Auckland climate zone... | clause_specific | partial | 0 | 5325 |
| 5 | F4 means of escape requirements for 2-storey build... | clause_specific | partial | 0 | 5328 |
| 6 | NZS 3604 Table 7.1 wind zones... | table_specific | accurate | 0 | 13896 |
| 7 | NZS 3604 stud spacing table for standard wind... | table_specific | accurate | 0 | 13906 |
| 8 | E2/AS1 table for cladding risk scores... | table_specific | partial | 0 | 12179 |
| 9 | difference between B1 and B2 compliance verificati... | cross_code | partial | 0 | 5397 |
| 10 | how does E2 weathertightness relate to H1 thermal ... | cross_code | partial | 0 | 5323 |
| 11 | NZS 3604 and B1 structural requirements for deck j... | cross_code | accurate | 0 | 13106 |
| 12 | what grade timber for external decks under NZS 360... | general_building | partial | 0 | 12107 |
| 13 | minimum bearer size for 3m span deck... | general_building | accurate | 0 | 12355 |
| 14 | what underlay is acceptable under corrugate roofin... | product_level | accurate | 0 | 11767 |
| 15 | recommended flashing tape for window installations... | product_level | accurate | 0 | 13910 |

## Stress Test Results

- All Completed: ✅ YES
- Max Latency: 12018ms
- Avg Latency: 11701ms
- Under 10s: ❌ NO

## Admin Endpoint

- Authentication: ✅ WORKING
- Records Retrieved: 1
- Status: ✅ PASS

## Findings

### ✅ What Works Well
- 7 queries returned accurate responses with proper NZ Building Code context
- Database contains 1742 documents with proper schema

### ⚠️ Partial Issues
- 8 queries returned partial responses (may need improvement)

### ❌ Critical Problems
- Stress test revealed performance or reliability issues

## Recommendations

- ⚠️ System pass rate (46.7%) below 80% target - needs improvement
- ⚠️ Consider optimizing query processing to reduce latency
