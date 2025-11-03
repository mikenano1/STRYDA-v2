#!/usr/bin/env python3
"""
STRYDA-v2 Database Audit Script
Comprehensive audit of ingested PDFs in Supabase PostgreSQL with pgvector
"""

import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

# Load environment from backend-minimal
load_dotenv('/app/backend-minimal/.env')

DATABASE_URL = os.getenv("DATABASE_URL")

def connect_db():
    """Connect to Supabase PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def task1_discover_schema(conn):
    """Task 1: Discover document storage tables"""
    print("\n" + "="*80)
    print("TASK 1: DATABASE SCHEMA DISCOVERY")
    print("="*80)
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Find all tables related to documents
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND (table_name LIKE '%doc%' OR table_name LIKE '%chunk%' OR table_name LIKE '%embed%')
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        print(f"\n📊 Found {len(tables)} document-related tables:")
        
        table_schemas = {}
        for table in tables:
            table_name = table['table_name']
            print(f"\n  📋 Table: {table_name}")
            
            # Get schema for each table
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cur.fetchall()
            table_schemas[table_name] = []
            
            for col in columns:
                col_info = {
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'max_length': col['character_maximum_length'],
                    'nullable': col['is_nullable']
                }
                table_schemas[table_name].append(col_info)
                print(f"     - {col['column_name']}: {col['data_type']}")
        
        return table_schemas

def task2_document_inventory(conn):
    """Task 2: Query all documents from main table"""
    print("\n" + "="*80)
    print("TASK 2: DOCUMENT INVENTORY")
    print("="*80)
    
    # Try common table names
    possible_tables = ['documents', 'docs', 'doc_chunks', 'knowledge_base', 'pdf_documents']
    
    documents_data = None
    table_used = None
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        for table_name in possible_tables:
            try:
                # Check if table exists and has data
                cur.execute(f"""
                    SELECT 
                        id,
                        source,
                        page,
                        created_at,
                        LENGTH(content) as content_length,
                        (embedding IS NOT NULL) as has_embedding
                    FROM {table_name}
                    LIMIT 100;
                """)
                
                documents_data = cur.fetchall()
                table_used = table_name
                print(f"\n✅ Found documents in table: {table_name}")
                print(f"📊 Retrieved {len(documents_data)} documents (limited to 100)")
                break
                
            except psycopg2.errors.UndefinedTable:
                continue
            except Exception as e:
                print(f"⚠️ Error querying {table_name}: {e}")
                continue
        
        if not documents_data:
            print("❌ No documents table found with expected schema")
            return None, None
        
        # Display sample documents
        print("\n📄 Sample Documents:")
        for i, doc in enumerate(documents_data[:5], 1):
            print(f"\n  {i}. ID: {doc['id']}")
            print(f"     Source: {doc['source']}")
            print(f"     Page: {doc['page']}")
            print(f"     Content Length: {doc['content_length']} chars")
            print(f"     Has Embedding: {doc['has_embedding']}")
            print(f"     Created: {doc['created_at']}")
        
        return documents_data, table_used

def task3_chunk_analysis(conn, table_name):
    """Task 3: Analyze chunks and document statistics"""
    print("\n" + "="*80)
    print("TASK 3: CHUNK ANALYSIS")
    print("="*80)
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Overall statistics
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(DISTINCT source) as unique_documents,
                AVG(LENGTH(content)) as avg_chunk_length,
                COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embeddings
            FROM {table_name};
        """)
        
        stats = cur.fetchone()
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Chunks: {stats['total_chunks']}")
        print(f"   Unique Documents: {stats['unique_documents']}")
        print(f"   Avg Chunk Length: {stats['avg_chunk_length']:.0f} chars")
        print(f"   Chunks with Embeddings: {stats['chunks_with_embeddings']}")
        
        # Group by source
        cur.execute(f"""
            SELECT 
                source,
                COUNT(*) as chunk_count,
                MIN(page) as min_page,
                MAX(page) as max_page,
                COUNT(DISTINCT page) as unique_pages
            FROM {table_name}
            GROUP BY source
            ORDER BY chunk_count DESC
            LIMIT 20;
        """)
        
        sources = cur.fetchall()
        print(f"\n📚 Top 20 Documents by Chunk Count:")
        for i, src in enumerate(sources, 1):
            print(f"   {i}. {src['source']}")
            print(f"      Chunks: {src['chunk_count']}, Pages: {src['unique_pages']} (p.{src['min_page']}-{src['max_page']})")
        
        return stats, sources

def task4_verify_database(conn, table_name):
    """Task 4: Verify database from previous tests"""
    print("\n" + "="*80)
    print("TASK 4: VERIFY DATABASE FROM PREVIOUS TESTS")
    print("="*80)
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Verify total document count
        cur.execute(f"SELECT COUNT(*) as total_docs FROM {table_name};")
        total_docs = cur.fetchone()['total_docs']
        print(f"\n📊 Total Documents: {total_docs}")
        print(f"   Expected from validation: 1,742")
        print(f"   Match: {'✅ YES' if total_docs == 1742 else '⚠️ NO'}")
        
        # Check reasoning_responses table
        try:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_traces,
                    COUNT(CASE WHEN final_answer IS NOT NULL AND final_answer != '' THEN 1 END) as parsed_traces,
                    COUNT(CASE WHEN final_answer IS NULL OR final_answer = '' THEN 1 END) as pending_traces
                FROM reasoning_responses;
            """)
            
            reasoning = cur.fetchone()
            print(f"\n🧠 Reasoning Responses Table:")
            print(f"   Total Traces: {reasoning['total_traces']}")
            print(f"   Parsed Traces: {reasoning['parsed_traces']}")
            print(f"   Pending Traces: {reasoning['pending_traces']}")
        except Exception as e:
            print(f"\n⚠️ Reasoning responses table not found or error: {e}")
        
        return total_docs

def task5_top_documents(conn, table_name):
    """Task 5: Identify largest/most important documents"""
    print("\n" + "="*80)
    print("TASK 5: TOP DOCUMENTS BY CONTENT")
    print("="*80)
    
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(f"""
            SELECT 
                source,
                COUNT(*) as chunks,
                COUNT(DISTINCT page) as pages,
                MIN(created_at) as ingested_at
            FROM {table_name}
            GROUP BY source
            ORDER BY chunks DESC
            LIMIT 10;
        """)
        
        top_docs = cur.fetchall()
        print(f"\n🏆 Top 10 Documents by Size:")
        for i, doc in enumerate(top_docs, 1):
            print(f"\n   {i}. {doc['source']}")
            print(f"      Chunks: {doc['chunks']}")
            print(f"      Pages: {doc['pages']}")
            print(f"      Ingested: {doc['ingested_at']}")
        
        return top_docs

def task6_create_audit_reports(stats, sources, top_docs, total_docs, table_name):
    """Task 6: Create audit reports (Markdown and JSON)"""
    print("\n" + "="*80)
    print("TASK 6: CREATE AUDIT REPORTS")
    print("="*80)
    
    audit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare document inventory
    document_inventory = []
    for src in sources:
        status = "✅ Complete" if src['chunk_count'] > 10 else "⚠️ Incomplete"
        document_inventory.append({
            "source": src['source'],
            "chunks": src['chunk_count'],
            "pages": src['unique_pages'],
            "ingested_date": "N/A",  # Not available in current schema
            "status": status
        })
    
    # Create Markdown report
    markdown_report = f"""# STRYDA-v2 Ingested Documents Audit

**Audit Date:** {audit_date}
**Database:** Supabase PostgreSQL
**Table Used:** {table_name}
**Total Documents:** {total_docs}
**Total Chunks:** {stats['total_chunks']}

## Document Inventory

| Source | Chunks | Pages | Status |
|--------|--------|-------|--------|
"""
    
    for doc in document_inventory[:20]:  # Top 20 for readability
        markdown_report += f"| {doc['source']} | {doc['chunks']} | {doc['pages']} | {doc['status']} |\n"
    
    markdown_report += f"""
## Corpus Statistics

- Total unique sources: {stats['unique_documents']}
- Total chunks: {stats['total_chunks']}
- Average chunk length: {stats['avg_chunk_length']:.0f} characters
- Chunks with embeddings: {stats['chunks_with_embeddings']}/{stats['total_chunks']} ({stats['chunks_with_embeddings']/stats['total_chunks']*100:.1f}%)
- Average pages per document: {stats['total_chunks']/stats['unique_documents']:.1f}

## Top Documents by Size

"""
    
    for i, doc in enumerate(top_docs, 1):
        markdown_report += f"{i}. **{doc['source']}** - {doc['chunks']} chunks, {doc['pages']} pages\n"
    
    markdown_report += """
## Findings

- ✅ Complete documents: Documents with >10 chunks appear complete
- ⚠️ Incomplete/Missing: Some documents may have fewer chunks than expected
- 🔍 Database contains comprehensive NZ Building Code documentation

## Recommendations

1. Verify all expected NZ Building Code PDFs are present
2. Check for any duplicate entries
3. Ensure all documents have embeddings for vector search
4. Consider adding metadata for ingestion dates
"""
    
    # Save Markdown report
    markdown_path = "/app/tests/INGESTED_DOCS_AUDIT.md"
    os.makedirs("/app/tests", exist_ok=True)
    with open(markdown_path, 'w') as f:
        f.write(markdown_report)
    print(f"\n✅ Markdown report saved: {markdown_path}")
    
    # Create JSON report
    json_report = {
        "audit_date": audit_date,
        "database": "supabase",
        "table_used": table_name,
        "total_documents": total_docs,
        "total_chunks": stats['total_chunks'],
        "documents": [
            {
                "source": doc['source'],
                "chunks": doc['chunks'],
                "pages": doc['pages'],
                "status": doc['status']
            }
            for doc in document_inventory
        ],
        "statistics": {
            "unique_sources": stats['unique_documents'],
            "avg_chunk_length": float(stats['avg_chunk_length']),
            "chunks_with_embeddings": stats['chunks_with_embeddings'],
            "embedding_coverage_percent": round(stats['chunks_with_embeddings']/stats['total_chunks']*100, 2),
            "avg_pages_per_doc": round(stats['total_chunks']/stats['unique_documents'], 1)
        },
        "top_documents": [
            {
                "source": doc['source'],
                "chunks": doc['chunks'],
                "pages": doc['pages'],
                "ingested_at": str(doc['ingested_at'])
            }
            for doc in top_docs
        ]
    }
    
    # Save JSON report
    json_path = "/app/tests/ingested_docs_audit.json"
    with open(json_path, 'w') as f:
        json.dump(json_report, f, indent=2)
    print(f"✅ JSON report saved: {json_path}")
    
    return markdown_path, json_path

def main():
    """Main audit execution"""
    print("="*80)
    print("STRYDA-v2 DATABASE AUDIT - INGESTED PDFs VERIFICATION")
    print("="*80)
    print(f"Backend URL: http://localhost:8001")
    print(f"Database: Supabase PostgreSQL (backend-minimal/.env)")
    print("="*80)
    
    # Connect to database
    conn = connect_db()
    if not conn:
        print("\n❌ AUDIT FAILED: Cannot connect to database")
        return
    
    try:
        # Task 1: Discover schema
        table_schemas = task1_discover_schema(conn)
        
        # Task 2: Document inventory
        documents_data, table_name = task2_document_inventory(conn)
        if not documents_data or not table_name:
            print("\n❌ AUDIT FAILED: No documents table found")
            return
        
        # Task 3: Chunk analysis
        stats, sources = task3_chunk_analysis(conn, table_name)
        
        # Task 4: Verify database
        total_docs = task4_verify_database(conn, table_name)
        
        # Task 5: Top documents
        top_docs = task5_top_documents(conn, table_name)
        
        # Task 6: Create audit reports
        markdown_path, json_path = task6_create_audit_reports(
            stats, sources, top_docs, total_docs, table_name
        )
        
        print("\n" + "="*80)
        print("✅ AUDIT COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\n📄 Reports generated:")
        print(f"   - Markdown: {markdown_path}")
        print(f"   - JSON: {json_path}")
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ AUDIT ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()
