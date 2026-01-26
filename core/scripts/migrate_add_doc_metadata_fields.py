#!/usr/bin/env python3
"""
STRYDA-v2 Document Metadata Migration
Adds metadata columns to documents table
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("="*80)
print("DOCUMENT METADATA MIGRATION")
print("="*80)

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

# Define columns to add
columns_to_add = [
    ("doc_type", "TEXT"),
    ("trade", "TEXT"),
    ("status", "TEXT"),
    ("phase", "INT"),
    ("version_label", "TEXT"),
    ("priority", "INT"),
    ("valid_from", "DATE"),
    ("valid_until", "DATE")
]

print("\nAdding metadata columns to documents table:")
print("-" * 80)

for column_name, column_type in columns_to_add:
    try:
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = %s;
        """, (column_name,))
        
        if cur.fetchone():
            print(f"   ✓ {column_name:20} {column_type:10} - Already exists")
        else:
            # Add column
            cur.execute(f"""
                ALTER TABLE documents 
                ADD COLUMN {column_name} {column_type};
            """)
            conn.commit()
            print(f"   ✅ {column_name:20} {column_type:10} - Added")
    
    except Exception as e:
        print(f"   ❌ {column_name:20} - Error: {e}")
        conn.rollback()

# Verify all columns
print("\n" + "="*80)
print("Verification:")
print("-" * 80)

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'documents'
    AND column_name IN ('doc_type', 'trade', 'status', 'phase', 'version_label', 'priority', 'valid_from', 'valid_until')
    ORDER BY column_name;
""")

columns = cur.fetchall()
for col_name, col_type in columns:
    print(f"   ✅ {col_name:20} {col_type}")

print(f"\n✅ Migration complete - {len(columns)}/8 metadata columns present")

conn.close()
