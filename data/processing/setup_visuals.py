#!/usr/bin/env python3
"""
STRYDA Visual Agent Infrastructure Setup
==========================================

Sets up the Supabase infrastructure for Agent #4: The Engineer (Visual Agent)
- Creates 'visual_assets' storage bucket for images
- Creates 'visuals' table for image metadata and embeddings
"""

import os
import sys
sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
from supabase import create_client, Client

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

print("="*70)
print("🔧 STRYDA VISUAL AGENT - INFRASTRUCTURE SETUP")
print("="*70)
print(f"\n📡 Connecting to Supabase: {SUPABASE_URL}")

# =============================================================================
# STEP 1: CREATE STORAGE BUCKET
# =============================================================================

def setup_storage_bucket():
    """Create the visual_assets storage bucket."""
    print("\n" + "-"*50)
    print("📦 STEP 1: Storage Bucket Setup")
    print("-"*50)
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Check if bucket exists
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if 'visual_assets' in bucket_names:
            print("   ✅ Bucket 'visual_assets' already exists")
            return True
        
        # Create bucket
        print("   📁 Creating bucket 'visual_assets'...")
        result = supabase.storage.create_bucket(
            'visual_assets',
            options={
                'public': False,
                'allowed_mime_types': ['image/png', 'image/jpeg', 'image/webp'],
                'file_size_limit': 10485760  # 10MB limit
            }
        )
        print("   ✅ Bucket 'visual_assets' created successfully")
        return True
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ✅ Bucket 'visual_assets' already exists")
            return True
        print(f"   ❌ Error creating bucket: {e}")
        return False


# =============================================================================
# STEP 2: CREATE VISUALS TABLE
# =============================================================================

def setup_visuals_table():
    """Create the visuals table for storing image metadata."""
    print("\n" + "-"*50)
    print("🗃️ STEP 2: Visuals Table Setup")
    print("-"*50)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'visuals'
            )
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("   ✅ Table 'visuals' already exists")
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM visuals")
            count = cursor.fetchone()[0]
            print(f"   📊 Current rows: {count}")
            conn.close()
            return True
        
        # Create table with vector support
        print("   📋 Creating table 'visuals'...")
        cursor.execute("""
            CREATE TABLE visuals (
                -- Primary Key
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                
                -- Source Document Reference
                source_document TEXT NOT NULL,              -- Original PDF filename
                source_page INTEGER,                        -- Page number in PDF
                
                -- Image Classification
                image_type TEXT NOT NULL,                   -- 'span_table', 'detail_drawing', 'map', 'diagram', 'photo'
                brand TEXT,                                 -- Brand if identified (e.g., 'Kingspan', 'GIB')
                
                -- Storage
                storage_path TEXT NOT NULL,                 -- Path in visual_assets bucket
                image_url TEXT,                             -- Signed URL (regenerated on access)
                file_size INTEGER,                          -- Size in bytes
                
                -- AI Analysis (Claude Output)
                summary TEXT,                               -- Natural language summary
                technical_variables JSONB,                  -- Extracted variables (e.g., {"span_mm": 4800, "wind_zone": "HIGH"})
                confidence FLOAT DEFAULT 0.0,               -- Claude's confidence in analysis (0-1)
                
                -- Vector Embedding for Semantic Search
                -- Using same 1536 dimensions as main documents table
                embedding vector(1536),
                
                -- Metadata
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                llama_job_id TEXT,                          -- LlamaParse job reference
                
                -- Indexes
                CONSTRAINT valid_image_type CHECK (image_type IN (
                    'span_table', 'detail_drawing', 'map', 'diagram', 
                    'photo', 'chart', 'specification', 'other'
                ))
            )
        """)
        
        # Create indexes for common queries
        print("   📑 Creating indexes...")
        
        # Index for filtering by type
        cursor.execute("""
            CREATE INDEX idx_visuals_image_type ON visuals(image_type)
        """)
        
        # Index for brand searches
        cursor.execute("""
            CREATE INDEX idx_visuals_brand ON visuals(brand)
        """)
        
        # Index for source document lookups
        cursor.execute("""
            CREATE INDEX idx_visuals_source ON visuals(source_document)
        """)
        
        # Vector similarity index (IVFFlat for performance)
        cursor.execute("""
            CREATE INDEX idx_visuals_embedding ON visuals 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        
        conn.commit()
        print("   ✅ Table 'visuals' created successfully")
        print("   ✅ Indexes created")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating table: {e}")
        return False


# =============================================================================
# STEP 3: VERIFY SETUP
# =============================================================================

def verify_setup():
    """Verify the infrastructure is ready."""
    print("\n" + "-"*50)
    print("✅ VERIFICATION")
    print("-"*50)
    
    try:
        # Check bucket
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if 'visual_assets' in bucket_names:
            print("   ✅ Storage bucket 'visual_assets': READY")
        else:
            print("   ❌ Storage bucket 'visual_assets': NOT FOUND")
            return False
        
        # Check table
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'visuals'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("   ✅ Table 'visuals': READY")
            print(f"      Columns: {len(columns)}")
        else:
            print("   ❌ Table 'visuals': NOT FOUND")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    success = True
    
    # Step 1: Storage bucket
    if not setup_storage_bucket():
        success = False
    
    # Step 2: Visuals table
    if not setup_visuals_table():
        success = False
    
    # Step 3: Verify
    if not verify_setup():
        success = False
    
    print("\n" + "="*70)
    if success:
        print("🎉 INFRASTRUCTURE SETUP COMPLETE")
        print("="*70)
        print("\n📋 Next Steps:")
        print("   1. Run ingest_visuals.py to process documents")
        print("   2. The Engineer agent will query the 'visuals' collection")
    else:
        print("⚠️ SETUP INCOMPLETE - Please check errors above")
        print("="*70)
    
    return success


if __name__ == '__main__':
    main()
