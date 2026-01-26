#!/usr/bin/env python3
"""
STRYDA Protocol V2.0 - Schema Migration
========================================
Adds the required columns and tables for the 4-Agent Architecture.

Run this ONCE to prepare the database for intelligent ingestion.
"""

import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres')


def run_migration():
    print('=' * 70)
    print('STRYDA PROTOCOL V2.0 - SCHEMA MIGRATION')
    print('=' * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # ============================================================
    # 1. ADD NEW COLUMNS TO documents TABLE
    # ============================================================
    print('\n📊 Adding Protocol V2.0 columns to documents table...')
    
    new_columns = [
        # Deterministic Identity & Versioning
        ("page_hash", "TEXT", "SHA-256 hash of page content for deduplication"),
        ("version_id", "INTEGER DEFAULT 1", "Version number for document updates"),
        ("is_latest", "BOOLEAN DEFAULT TRUE", "Flag for current version"),
        
        # Hierarchy of Truth
        ("hierarchy_level", "INTEGER DEFAULT 3", "1=Authority, 2=Compliance, 3=Product"),
        ("role", "TEXT DEFAULT 'product'", "authority, compliance, product"),
        ("weight_modifier", "FLOAT DEFAULT 1.0", "Retrieval weight adjustment"),
        
        # Semantic Chunking & Mapping
        ("page_title", "TEXT", "Extracted from PDF title block"),
        ("dwg_id", "TEXT", "Drawing/detail identifier e.g. NW-HOC-00702"),
        ("agent_owner", "TEXT[]", "Which agents can access this chunk"),
        
        # Engineer Visual Extraction
        ("bounding_boxes", "JSONB", "Coordinates for visual crops"),
        ("has_table", "BOOLEAN DEFAULT FALSE", "Contains extractable table"),
        ("has_diagram", "BOOLEAN DEFAULT FALSE", "Contains technical diagram"),
        
        # Safety Shields
        ("unit_range", "JSONB", "Tagged measurements with min/max"),
        ("geo_context", "TEXT DEFAULT 'Universal'", "NZ_Specific, AU_Specific, Universal"),
        
        # Self-Correction Loop
        ("is_active", "BOOLEAN DEFAULT TRUE", "False = blacklisted from retrieval"),
        ("blacklist_reason", "TEXT", "Why chunk was blacklisted"),
        ("feedback_count", "INTEGER DEFAULT 0", "Number of feedback flags"),
    ]
    
    for col_name, col_type, description in new_columns:
        try:
            cur.execute(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
            print(f'   ✅ {col_name}: {description}')
        except Exception as e:
            print(f'   ⚠️ {col_name}: {str(e)[:50]}')
    
    conn.commit()
    
    # ============================================================
    # 2. CREATE chunk_feedback TABLE
    # ============================================================
    print('\n📊 Creating chunk_feedback table...')
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunk_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chunk_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            user_id TEXT,
            feedback_type TEXT NOT NULL CHECK (feedback_type IN ('incorrect', 'outdated', 'misleading', 'duplicate', 'metadata_error')),
            feedback_note TEXT,
            suggested_correction TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP,
            resolution_action TEXT CHECK (resolution_action IN ('blacklisted', 'reweighted', 'corrected', 'dismissed', NULL))
        );
    """)
    
    # Create indexes for chunk_feedback
    cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_feedback_chunk ON chunk_feedback(chunk_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_feedback_unresolved ON chunk_feedback(resolved) WHERE resolved = FALSE;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_feedback_type ON chunk_feedback(feedback_type);")
    
    print('   ✅ chunk_feedback table created with indexes')
    conn.commit()
    
    # ============================================================
    # 3. CREATE page_hashes TABLE FOR DEDUPLICATION
    # ============================================================
    print('\n📊 Creating page_hashes table for deduplication...')
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS page_hashes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            page_hash TEXT UNIQUE NOT NULL,
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            source_file TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            last_seen TIMESTAMP DEFAULT NOW()
        );
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_page_hashes_hash ON page_hashes(page_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_page_hashes_source ON page_hashes(source_file);")
    
    print('   ✅ page_hashes table created')
    conn.commit()
    
    # ============================================================
    # 4. CREATE INDEXES FOR PROTOCOL V2.0 QUERIES
    # ============================================================
    print('\n📊 Creating optimized indexes...')
    
    indexes = [
        ("idx_documents_hierarchy", "documents(hierarchy_level)"),
        ("idx_documents_geo_context", "documents(geo_context)"),
        ("idx_documents_is_latest", "documents(is_latest) WHERE is_latest = TRUE"),
        ("idx_documents_is_active", "documents(is_active) WHERE is_active = TRUE"),
        ("idx_documents_role", "documents(role)"),
        ("idx_documents_dwg_id", "documents(dwg_id) WHERE dwg_id IS NOT NULL"),
        ("idx_documents_has_diagram", "documents(has_diagram) WHERE has_diagram = TRUE"),
        ("idx_documents_page_hash", "documents(page_hash) WHERE page_hash IS NOT NULL"),
    ]
    
    for idx_name, idx_def in indexes:
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def};")
            print(f'   ✅ {idx_name}')
        except Exception as e:
            print(f'   ⚠️ {idx_name}: {str(e)[:50]}')
    
    conn.commit()
    
    # ============================================================
    # 5. CREATE ingestion_log TABLE
    # ============================================================
    print('\n📊 Creating ingestion_log table...')
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_file TEXT NOT NULL,
            total_pages INTEGER,
            pages_ingested INTEGER DEFAULT 0,
            pages_skipped INTEGER DEFAULT 0,
            pages_updated INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            error_message TEXT,
            started_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            protocol_version TEXT DEFAULT 'v2.0'
        );
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_log_status ON ingestion_log(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_log_source ON ingestion_log(source_file);")
    
    print('   ✅ ingestion_log table created')
    conn.commit()
    
    # ============================================================
    # 6. VERIFY MIGRATION
    # ============================================================
    print('\n📊 Verifying migration...')
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'documents'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print(f'\n   documents table now has {len(columns)} columns')
    
    # Check new columns
    new_col_names = [c[0] for c in new_columns]
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'documents' 
        AND column_name IN ({','.join([f"'{c[0]}'" for c in new_columns])});
    """)
    
    found_columns = [r[0] for r in cur.fetchall()]
    print(f'   Protocol V2.0 columns added: {len(found_columns)}/{len(new_columns)}')
    
    cur.close()
    conn.close()
    
    print('\n' + '=' * 70)
    print('✅ SCHEMA MIGRATION COMPLETE')
    print('=' * 70)
    print('\nThe database is now ready for Protocol V2.0 ingestion.')
    print('Run the ingestion engine to populate with intelligent metadata.')


if __name__ == '__main__':
    run_migration()
