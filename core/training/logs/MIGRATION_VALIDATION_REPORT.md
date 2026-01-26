# STRYDA-v2 Training Dataset Migration Validation Report

**Migration Date:** 2025-11-29T10:30:00  
**Status:** ✅ COMPLETE

## Summary

- **Total entries:** 9,000
- **Expected:** 9,000
- **Status:** ✅ PASS
- **Source:** stryda_master_dataset.jsonl (Emergentagent customer assets)
- **Target Table:** training_questions_v2

## Distribution by Batch

| Batch | Count |
|-------|-------|
| 01 | 600 |
| 02 | 600 |
| 03 | 600 |
| 04 | 600 |
| 05 | 600 |
| 06 | 600 |
| 07 | 600 |
| 08 | 600 |
| 09 | 600 |
| 10 | 600 |
| 11 | 600 |
| 12 | 600 |
| 13 | 600 |
| 14 | 600 |
| 15 | 600 |

## Distribution by Trade (15 Trades × 600 entries each)

| Trade | Count |
|-------|-------|
| carpentry | 600 |
| cladding | 600 |
| concrete_foundations | 600 |
| council_consent | 600 |
| drainage | 600 |
| earthworks_stormwater | 600 |
| electrical | 600 |
| h1_energy | 600 |
| hvac_ventilation | 600 |
| interior_linings | 600 |
| joinery | 600 |
| passive_fire | 600 |
| plumbing | 600 |
| roofing | 600 |
| waterproofing | 600 |

## Distribution by Intent

| Intent | Count |
|--------|-------|
| implicit_compliance | 2,739 |
| compliance_strict | 2,608 |
| general_help | 1,837 |
| council_process | 916 |
| product_info | 900 |

## Distribution by Complexity

| Complexity | Count |
|------------|-------|
| basic | 3,633 |
| intermediate | 3,604 |
| advanced | 1,763 |

## Distribution by Category

| Category | Count |
|----------|-------|
| A | 1,500 |
| B | 1,500 |
| C | 1,500 |
| D | 1,500 |
| E | 1,500 |
| G | 1,500 |

## Legacy Data

- **Legacy table:** training_data_legacy (backup of old manual batches)
- **Legacy entries backed up:** 3,100
- **Legacy entries removed from active table:** 3,100
- **Legacy directories:** /app/backend-minimal/training/batches/ (archived, not in use)

## Migration Actions Completed

✅ Phase 1: Backed up 3,100 legacy entries to training_data_legacy  
✅ Phase 2: Created training_questions_v2 with locked schema + indexes  
✅ Phase 3: Ingested 9,000 entries from master JSONL file  
✅ Phase 4: (Pending) Update code to use training_questions_v2  
✅ Phase 5: Validation report generated  

## Next Steps

1. Update any code paths that reference old training tables to use training_questions_v2
2. Test intent routing with new training data
3. Archive legacy batch directories as reference only

