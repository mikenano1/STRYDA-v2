#!/usr/bin/env python3
"""
STRYDA Big Brain - Database Schema Upgrade
Adds new columns for the Master Product Manifest hierarchy
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

SCHEMA_UPGRADE_SQL = """
-- ============================================
-- STRYDA Big Brain Schema Upgrade v1.0
-- Supports Master Product Manifest Categories A-G
-- ============================================

-- Add brand_name column for manufacturer/brand identification
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'brand_name') THEN
        ALTER TABLE documents ADD COLUMN brand_name TEXT;
        COMMENT ON COLUMN documents.brand_name IS 'Manufacturer or brand name (e.g., Paslode, GIB, James Hardie)';
    END IF;
END $$;

-- Add category_code column for Master Product Manifest categorization
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'category_code') THEN
        ALTER TABLE documents ADD COLUMN category_code TEXT;
        COMMENT ON COLUMN documents.category_code IS 'Master Product Manifest category (A_Structure, B_Enclosure, etc.)';
    END IF;
END $$;

-- Add product_family column for product line grouping
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'product_family') THEN
        ALTER TABLE documents ADD COLUMN product_family TEXT;
        COMMENT ON COLUMN documents.product_family IS 'Product family or line (e.g., Impulse Framer, Aqualine)';
    END IF;
END $$;

-- Add ingestion_source column to track where the document came from
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'ingestion_source') THEN
        ALTER TABLE documents ADD COLUMN ingestion_source TEXT;
        COMMENT ON COLUMN documents.ingestion_source IS 'Source of document (web_scrape, manual_upload, api_sync)';
    END IF;
END $$;

-- Add original_url column to track the source URL
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'original_url') THEN
        ALTER TABLE documents ADD COLUMN original_url TEXT;
        COMMENT ON COLUMN documents.original_url IS 'Original URL where the document was sourced';
    END IF;
END $$;

-- Add file_hash column for deduplication
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'file_hash') THEN
        ALTER TABLE documents ADD COLUMN file_hash TEXT;
        COMMENT ON COLUMN documents.file_hash IS 'SHA256 hash of source file for deduplication';
    END IF;
END $$;

-- Add ingested_at timestamp
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'ingested_at') THEN
        ALTER TABLE documents ADD COLUMN ingested_at TIMESTAMP DEFAULT NOW();
        COMMENT ON COLUMN documents.ingested_at IS 'Timestamp when document was ingested into Big Brain';
    END IF;
END $$;

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_documents_brand_name ON documents(brand_name);
CREATE INDEX IF NOT EXISTS idx_documents_category_code ON documents(category_code);
CREATE INDEX IF NOT EXISTS idx_documents_product_family ON documents(product_family);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);

-- Create a composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_documents_brand_category ON documents(brand_name, category_code);

-- Verify the schema upgrade
SELECT 'Schema upgrade complete!' as status;
"""

def upgrade_schema():
    """Execute the schema upgrade"""
    print("=" * 60)
    print("🧠 STRYDA Big Brain - Database Schema Upgrade")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("\n📊 Executing schema upgrade...")
        cursor.execute(SCHEMA_UPGRADE_SQL)
        
        # Verify new columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
            AND column_name IN ('brand_name', 'category_code', 'product_family', 
                               'ingestion_source', 'original_url', 'file_hash', 'ingested_at')
            ORDER BY column_name
        """)
        
        new_cols = cursor.fetchall()
        print(f"\n✅ New columns added ({len(new_cols)} total):")
        for col in new_cols:
            print(f"   - {col[0]}: {col[1]}")
        
        # Verify indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'documents'
            AND indexname LIKE 'idx_documents_%'
        """)
        
        indexes = cursor.fetchall()
        print(f"\n📑 Indexes created ({len(indexes)} total):")
        for idx in indexes:
            print(f"   - {idx[0]}")
        
        conn.close()
        print("\n✅ Schema upgrade complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema upgrade failed: {e}")
        return False

if __name__ == "__main__":
    upgrade_schema()
