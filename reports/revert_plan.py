#!/usr/bin/env python3
"""
PRECISE REVERT PLAN - Phase 3 Metadata Over-filling
Execute ONLY when instructed - this script will clean up problematic metadata
"""

REVERT_PLAN = """
🚨 CRITICAL METADATA VALIDATION FAILURES DETECTED

ISSUES FOUND:
1. 100% section/clause coverage indicates systematic over-filling
2. 24.5% regex mismatch rate (threshold: 5%)
3. 139 documents with empty string sections
4. All 819 clauses missing provenance tracking (NULL clause_source)
5. Process artifacts extracted as clauses ("0 - Clause Removed", "2 - Editing")
6. Document headers extracted as sections instead of content sections

REVERT ACTIONS (DO NOT EXECUTE WITHOUT EXPLICIT PERMISSION):

Step 1: Clean Empty Sections
UPDATE documents SET section = NULL WHERE section = '';

Step 2: Clean Process Artifact Clauses  
UPDATE documents SET clause = NULL 
WHERE clause LIKE '%Clause%Removed%' 
OR clause LIKE '%Editing and%'
OR clause LIKE '% - %';

Step 3: Clean Document Header Sections
UPDATE documents SET section = NULL, section_source = NULL
WHERE section LIKE '%MINISTRY%' 
OR section LIKE '%DEPARTMENT%'
OR section LIKE '%HANDBOOK%'
OR section LIKE '%NEW ZEALAND BUILDING CODE%';

Step 4: Reset Suspicious Clauses (keep only high-confidence)
UPDATE documents SET clause = NULL, clause_source = NULL
WHERE source = 'NZ Metal Roofing' 
AND clause IS NOT NULL
AND clause NOT IN (
    SELECT DISTINCT clause FROM documents 
    WHERE source = 'NZ Building Code' 
    AND clause LIKE '[A-H][0-9]%'
);

Step 5: Preserve Only Legitimate Standards
-- Keep only clauses matching exact standards patterns:
UPDATE documents SET clause = NULL, clause_source = NULL
WHERE clause IS NOT NULL 
AND clause NOT REGEXP '\b(AS/)?NZS\s*[0-9]{3,4}|\b[A-H][0-9]{1,2}(/[A-Z]{2,4}[0-9]*)?\b|\b[GHZ][0-9]{2,3}\b';

Step 6: Update Timestamps
UPDATE documents SET updated_at = NOW() 
WHERE section IS NULL OR clause IS NULL OR section_source IS NULL;

EXPECTED RESULT AFTER REVERT:
- Section coverage: ~30-50% (realistic level)
- Clause coverage: ~25-40% (realistic for technical manuals)
- All metadata entries have proper provenance
- Full content and embeddings remain untouched
- Only high-confidence, verifiable metadata retained

SAFETY VERIFICATION:
Before executing, verify:
1. Full backup of current metadata state
2. Content and embedding columns are never touched
3. Only section/clause/provenance columns modified
"""

def create_backup_script():
    """Create backup script before any revert"""
    backup_sql = """
    -- BACKUP CURRENT METADATA STATE
    CREATE TABLE metadata_backup_$(date +%Y%m%d_%H%M%S) AS 
    SELECT id, section, clause, section_source, clause_source, snippet, updated_at
    FROM documents 
    WHERE section IS NOT NULL OR clause IS NOT NULL;
    """
    return backup_sql

print(REVERT_PLAN)
print("\n🛠️ BACKUP SQL BEFORE REVERT:")
print(create_backup_script())