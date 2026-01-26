#!/usr/bin/env python3
"""
STRYDA-v2 Training Dataset Migration Script
Migrates from legacy training_data to training_questions_v2
"""

import psycopg2
import json
import time
from datetime import datetime
from supabase import create_client, Client
import os

# Configuration
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# Extract Supabase credentials from DATABASE_URL
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMjM4NDg2OCwiZXhwIjoyMDQ3OTYwODY4fQ.IWxBqO5vSPxBkN-TQnH7yS-j7q1SwY-RvdBzqVmOCMM"

print("="*80)
print("STRYDA-v2 TRAINING DATASET MIGRATION")
print("="*80)
print(f"Start time: {datetime.now().isoformat()}\n")

# PHASE 1: Backup Legacy Data
print("\n" + "="*80)
print("PHASE 1: BACKUP LEGACY TRAINING DATA")
print("="*80)

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    
    # Check if training_data exists
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name = 'training_data';
    """)
    
    if cur.fetchone()[0] == 0:
        print("⚠️ training_data table does not exist, skipping backup")
    else:
        # Get count of legacy data
        cur.execute("SELECT COUNT(*) FROM training_data;")
        legacy_count = cur.fetchone()[0]
        print(f"✅ Found {legacy_count} legacy training entries")
        
        # Create backup table
        print("\n1. Creating backup table: training_data_legacy")
        cur.execute("DROP TABLE IF EXISTS training_data_legacy;")
        cur.execute("""
            CREATE TABLE training_data_legacy AS 
            SELECT * FROM training_data;
        """)
        conn.commit()
        
        # Verify backup
        cur.execute("SELECT COUNT(*) FROM training_data_legacy;")
        backup_count = cur.fetchone()[0]
        print(f"   ✅ Backed up {backup_count} rows to training_data_legacy")
        
        # Delete legacy batches from active table
        print("\n2. Removing legacy batches 01-11 from training_data")
        cur.execute("DELETE FROM training_data WHERE batch_id IN %s;", 
                   (tuple([f'batch_{i:02d}' for i in range(1, 12)]),))
        deleted = cur.rowcount
        conn.commit()
        print(f"   ✅ Deleted {deleted} legacy entries")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM training_data;")
        remaining = cur.fetchone()[0]
        print(f"   ✅ Remaining in training_data: {remaining}")
    
    cur.close()
    conn.close()
    print("\n✅ Phase 1 complete")
    
except Exception as e:
    print(f"❌ Phase 1 failed: {e}")
    raise

# PHASE 2: Create V2 Table
print("\n" + "="*80)
print("PHASE 2: CREATE TRAINING_QUESTIONS_V2 TABLE")
print("="*80)

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    
    # Drop if exists (fresh start)
    print("\n1. Dropping existing training_questions_v2 if present")
    cur.execute("DROP TABLE IF EXISTS training_questions_v2;")
    conn.commit()
    
    # Create new table with locked schema
    print("\n2. Creating training_questions_v2 with locked schema")
    cur.execute("""
        CREATE TABLE training_questions_v2 (
            id                  TEXT PRIMARY KEY,
            batch               SMALLINT NOT NULL,
            trade               TEXT NOT NULL,
            trade_type_detailed TEXT[] NOT NULL,
            category            TEXT NOT NULL,
            intent              TEXT NOT NULL,
            complexity          TEXT NOT NULL,
            question            TEXT NOT NULL,
            created_at          TIMESTAMPTZ DEFAULT now()
        );
    """)
    conn.commit()
    print("   ✅ Table created")
    
    # Create indexes
    print("\n3. Creating indexes")
    cur.execute("CREATE INDEX idx_batch ON training_questions_v2(batch);")
    cur.execute("CREATE INDEX idx_trade ON training_questions_v2(trade);")
    cur.execute("CREATE INDEX idx_intent ON training_questions_v2(intent);")
    cur.execute("CREATE INDEX idx_trade_type_detailed ON training_questions_v2 USING GIN(trade_type_detailed);")
    conn.commit()
    print("   ✅ Indexes created (batch, trade, intent, trade_type_detailed)")
    
    cur.close()
    conn.close()
    print("\n✅ Phase 2 complete")
    
except Exception as e:
    print(f"❌ Phase 2 failed: {e}")
    raise

# PHASE 3: Download and Ingest Master Dataset
print("\n" + "="*80)
print("PHASE 3: INGEST MASTER DATASET FROM SUPABASE STORAGE")
print("="*80)

try:
    # Initialize Supabase client
    print("\n1. Connecting to Supabase Storage")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Download JSONL file
    print("\n2. Downloading stryda_master_dataset.jsonl from bucket 'datasets'")
    response = supabase.storage.from_('datasets').download('stryda_master_dataset.jsonl')
    
    if not response:
        raise Exception("Failed to download file from Supabase Storage")
    
    # Decode bytes to string
    jsonl_content = response.decode('utf-8')
    lines = jsonl_content.strip().split('\n')
    print(f"   ✅ Downloaded {len(lines)} lines")
    
    # Parse and validate
    print("\n3. Parsing and validating entries")
    valid_entries = []
    invalid_count = 0
    
    valid_categories = ['A', 'B', 'C', 'D', 'E', 'G']
    valid_intents = ['general_help', 'compliance_strict', 'product_info', 'implicit_compliance', 'council_process']
    valid_complexity = ['basic', 'intermediate', 'advanced']
    
    for idx, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
            
            # Validate required fields
            if not all(key in entry for key in ['id', 'batch', 'trade', 'trade_type_detailed', 'category', 'intent', 'complexity', 'question']):
                invalid_count += 1
                continue
            
            # Validate constraints
            if not (1 <= entry['batch'] <= 15):
                print(f"   ⚠️ Row {idx}: Invalid batch {entry['batch']}")
                invalid_count += 1
                continue
            
            if entry['category'] not in valid_categories:
                print(f"   ⚠️ Row {idx}: Invalid category {entry['category']}")
                invalid_count += 1
                continue
            
            if entry['intent'] not in valid_intents:
                print(f"   ⚠️ Row {idx}: Invalid intent {entry['intent']}")
                invalid_count += 1
                continue
            
            if entry['complexity'] not in valid_complexity:
                print(f"   ⚠️ Row {idx}: Invalid complexity {entry['complexity']}")
                invalid_count += 1
                continue
            
            if not isinstance(entry['trade_type_detailed'], list) or len(entry['trade_type_detailed']) == 0:
                print(f"   ⚠️ Row {idx}: Invalid trade_type_detailed")
                invalid_count += 1
                continue
            
            if not entry['question'] or len(entry['question'].strip()) == 0:
                print(f"   ⚠️ Row {idx}: Empty question")
                invalid_count += 1
                continue
            
            valid_entries.append(entry)
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Row {idx}: JSON parse error - {e}")
            invalid_count += 1
            continue
    
    print(f"   ✅ Valid entries: {len(valid_entries)}")
    print(f"   ⚠️ Invalid entries: {invalid_count}")
    
    # Insert into database
    print("\n4. Inserting entries into training_questions_v2")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    inserted = 0
    failed = 0
    BATCH_SIZE = 500
    
    for i in range(0, len(valid_entries), BATCH_SIZE):
        batch = valid_entries[i:i + BATCH_SIZE]
        
        try:
            with conn.cursor() as cur:
                for entry in batch:
                    cur.execute("""
                        INSERT INTO training_questions_v2 
                        (id, batch, trade, trade_type_detailed, category, intent, complexity, question)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        entry['id'],
                        entry['batch'],
                        entry['trade'],
                        entry['trade_type_detailed'],
                        entry['category'],
                        entry['intent'],
                        entry['complexity'],
                        entry['question']
                    ))
                    inserted += 1
            
            conn.commit()
            print(f"   [{inserted}/{len(valid_entries)}] Inserted batch {i//BATCH_SIZE + 1}")
            
        except Exception as e:
            print(f"   ❌ Batch {i//BATCH_SIZE + 1} failed: {e}")
            conn.rollback()
            failed += len(batch)
    
    conn.close()
    print(f"\n✅ Phase 3 complete")
    print(f"   Total inserted: {inserted}")
    print(f"   Total failed: {failed}")
    
except Exception as e:
    print(f"❌ Phase 3 failed: {e}")
    raise

# PHASE 5: Validation Report
print("\n" + "="*80)
print("PHASE 5: VALIDATION REPORT")
print("="*80)

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    
    # Total count
    print("\n1. Total Row Count")
    cur.execute("SELECT COUNT(*) FROM training_questions_v2;")
    total = cur.fetchone()[0]
    print(f"   Total: {total:,} (Expected: 9,000)")
    
    if total != 9000:
        print(f"   ⚠️ WARNING: Expected 9,000 rows, got {total}")
    
    # By batch
    print("\n2. Distribution by Batch")
    cur.execute("""
        SELECT batch, COUNT(*) as count
        FROM training_questions_v2
        GROUP BY batch
        ORDER BY batch;
    """)
    batch_stats = cur.fetchall()
    for batch, count in batch_stats:
        print(f"   Batch {batch:02d}: {count:,} entries")
    
    # By trade
    print("\n3. Distribution by Trade")
    cur.execute("""
        SELECT trade, COUNT(*) as count
        FROM training_questions_v2
        GROUP BY trade
        ORDER BY count DESC;
    """)
    trade_stats = cur.fetchall()
    for trade, count in trade_stats:
        print(f"   {trade:30}: {count:,} entries")
    
    # By intent
    print("\n4. Distribution by Intent")
    cur.execute("""
        SELECT intent, COUNT(*) as count
        FROM training_questions_v2
        GROUP BY intent
        ORDER BY count DESC;
    """)
    intent_stats = cur.fetchall()
    for intent, count in intent_stats:
        print(f"   {intent:25}: {count:,} entries")
    
    # By complexity
    print("\n5. Distribution by Complexity")
    cur.execute("""
        SELECT complexity, COUNT(*) as count
        FROM training_questions_v2
        GROUP BY complexity
        ORDER BY count DESC;
    """)
    complexity_stats = cur.fetchall()
    for complexity, count in complexity_stats:
        print(f"   {complexity:15}: {count:,} entries")
    
    # Sample entries
    print("\n6. Sample Entries")
    cur.execute("""
        SELECT id, batch, trade, category, intent, LEFT(question, 60)
        FROM training_questions_v2
        LIMIT 5;
    """)
    samples = cur.fetchall()
    for id, batch, trade, category, intent, question in samples:
        print(f"   {id}: [{trade}] {question}...")
    
    cur.close()
    conn.close()
    
    # Write validation report
    report_path = "/app/backend-minimal/training/logs/migration_validation_report.md"
    with open(report_path, 'w') as f:
        f.write("# STRYDA-v2 Training Dataset Migration Report\n\n")
        f.write(f"**Migration Date:** {datetime.now().isoformat()}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total entries: {total:,}\n")
        f.write(f"- Expected: 9,000\n")
        f.write(f"- Status: {'✅ PASS' if total == 9000 else '⚠️ MISMATCH'}\n\n")
        
        f.write(f"## Distribution by Batch\n\n")
        f.write("| Batch | Count |\n")
        f.write("|-------|-------|\n")
        for batch, count in batch_stats:
            f.write(f"| {batch:02d} | {count:,} |\n")
        
        f.write(f"\n## Distribution by Trade\n\n")
        f.write("| Trade | Count |\n")
        f.write("|-------|-------|\n")
        for trade, count in trade_stats:
            f.write(f"| {trade} | {count:,} |\n")
        
        f.write(f"\n## Distribution by Intent\n\n")
        f.write("| Intent | Count |\n")
        f.write("|--------|-------|\n")
        for intent, count in intent_stats:
            f.write(f"| {intent} | {count:,} |\n")
        
        f.write(f"\n## Distribution by Complexity\n\n")
        f.write("| Complexity | Count |\n")
        f.write("|------------|-------|\n")
        for complexity, count in complexity_stats:
            f.write(f"| {complexity} | {count:,} |\n")
    
    print(f"\n✅ Validation report saved to {report_path}")
    print("\n✅ Phase 5 complete")
    
except Exception as e:
    print(f"❌ Phase 5 failed: {e}")
    raise

print("\n" + "="*80)
print("MIGRATION COMPLETE")
print("="*80)
print(f"End time: {datetime.now().isoformat()}")
print(f"\n✅ Training dataset v2 is ready with {total:,} entries")
print("✅ Legacy data backed up to training_data_legacy")
print("✅ All code should now use training_questions_v2")
