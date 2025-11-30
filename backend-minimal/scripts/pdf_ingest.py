#!/usr/bin/env python3
"""
STRYDA-v2 PDF Ingestion Pipeline
Extracts text from PDFs in Supabase Storage and ingests into vector database
"""

import json
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client
from openai import OpenAI
import PyPDF2
from io import BytesIO

# Configuration
MANIFEST_PATH = "/app/backend-minimal/training/docs_manifest.jsonl"
ERROR_LOG_PATH = "/app/backend-minimal/training/logs/pdf_ingest_errors.log"
SUCCESS_LOG_PATH = "/app/backend-minimal/training/logs/pdf_ingest_success.log"

# Database config
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

# Supabase config
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMjM4NDg2OCwiZXhwIjoyMDQ3OTYwODY4fQ.IWxBqO5vSPxBkN-TQnH7yS-j7q1SwY-RvdBzqVmOCMM"

# OpenAI config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
EMBEDDING_MODEL = "text-embedding-3-small"

def log_error(message: str):
    """Write to error log"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    with open(ERROR_LOG_PATH, 'a') as f:
        f.write(log_line + '\n')

def log_success(message: str):
    """Write to success log"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    with open(SUCCESS_LOG_PATH, 'a') as f:
        f.write(log_line + '\n')

def download_pdf_from_supabase(bucket: str, path: str) -> bytes:
    """Download PDF from Supabase Storage"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        response = supabase.storage.from_(bucket).download(path)
        return response
    except Exception as e:
        raise Exception(f"Failed to download {bucket}/{path}: {e}")

def extract_text_from_pdf(pdf_bytes: bytes) -> list:
    """Extract text from PDF pages"""
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        
        pages = []
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            
            pages.append({
                "page_num": page_num + 1,
                "text": text,
                "char_count": len(text)
            })
        
        return pages
        
    except Exception as e:
        raise Exception(f"PDF text extraction failed: {e}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Chunk text into overlapping segments"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        chunks.append({
            "text": chunk,
            "start": start,
            "end": end
        })
        
        start += (chunk_size - overlap)
    
    return chunks

def generate_embeddings(texts: list, client: OpenAI) -> list:
    """Generate embeddings for text chunks"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        raise Exception(f"Embedding generation failed: {e}")

def ingest_pdf(entry: dict, conn, openai_client: OpenAI) -> dict:
    """Ingest a single PDF into the database"""
    pdf_name = entry["supabase_path"]
    bucket = entry.get("supabase_bucket", "pdfs")
    source_name = pdf_name.replace(".pdf", "")
    
    try:
        # Step 1: Download PDF
        log_success(f"Downloading {bucket}/{pdf_name}")
        pdf_bytes = download_pdf_from_supabase(bucket, pdf_name)
        log_success(f"   ✅ Downloaded {len(pdf_bytes):,} bytes")
        
        # Step 2: Extract text
        log_success(f"Extracting text from {pdf_name}")
        pages = extract_text_from_pdf(pdf_bytes)
        log_success(f"   ✅ Extracted {len(pages)} pages")
        
        # Step 3: Generate chunks and embeddings
        all_chunks = []
        for page_data in pages:
            page_num = page_data["page_num"]
            page_text = page_data["text"]
            
            # Chunk the page
            chunks = chunk_text(page_text, chunk_size=800, overlap=150)
            
            for chunk in chunks:
                all_chunks.append({
                    "page": page_num,
                    "text": chunk["text"],
                    "source": source_name
                })
        
        log_success(f"   ✅ Created {len(all_chunks)} chunks")
        
        # Step 4: Generate embeddings in batches
        log_success(f"Generating embeddings for {len(all_chunks)} chunks")
        BATCH_SIZE = 100
        embeddings = []
        
        for i in range(0, len(all_chunks), BATCH_SIZE):
            batch = all_chunks[i:i + BATCH_SIZE]
            batch_texts = [chunk["text"] for chunk in batch]
            batch_embeddings = generate_embeddings(batch_texts, openai_client)
            embeddings.extend(batch_embeddings)
            
            log_success(f"   [{len(embeddings)}/{len(all_chunks)}] Generated embeddings")
        
        # Step 5: Insert into database
        log_success(f"Inserting {len(all_chunks)} chunks into database")
        with conn.cursor() as cur:
            for idx, chunk in enumerate(all_chunks):
                cur.execute("""
                    INSERT INTO documents 
                    (source, page, content, snippet, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                """, (
                    chunk["source"],
                    chunk["page"],
                    chunk["text"],
                    chunk["text"][:200],
                    embeddings[idx]
                ))
        
        conn.commit()
        log_success(f"✅ Ingested {pdf_name}: {len(pages)} pages, {len(all_chunks)} chunks")
        
        return {
            "status": "success",
            "pages": len(pages),
            "chunks": len(all_chunks)
        }
        
    except Exception as e:
        log_error(f"❌ Failed to ingest {pdf_name}: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

def main():
    """Main ingestion function"""
    print("="*80)
    print("STRYDA-v2 PDF INGESTION - START")
    print("="*80)
    
    # Load manifest
    log_success(f"\n1. Loading manifest from {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, 'r') as f:
        entries = [json.loads(line) for line in f if line.strip()]
    
    log_success(f"   ✅ Loaded {len(entries)} PDF entries")
    
    # Connect to database
    log_success(f"\n2. Connecting to database")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Process each PDF
    log_success(f"\n3. Processing PDFs")
    
    stats = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "total_pages": 0,
        "total_chunks": 0
    }
    
    for idx, entry in enumerate(entries, 1):
        pdf_name = entry["supabase_path"]
        status = entry.get("status", "current")
        
        print(f"\n[{idx}/{len(entries)}] Processing: {pdf_name}")
        
        # Skip expired documents (optional)
        if status == "expired":
            log_success(f"   ⏭️  Skipping expired document")
            stats["skipped"] += 1
            continue
        
        # Ingest PDF
        result = ingest_pdf(entry, conn, openai_client)
        
        if result["status"] == "success":
            stats["success"] += 1
            stats["total_pages"] += result["pages"]
            stats["total_chunks"] += result["chunks"]
        else:
            stats["failed"] += 1
    
    conn.close()
    
    # Summary
    log_success(f"\n{'='*80}")
    log_success("INGESTION COMPLETE")
    log_success(f"{'='*80}")
    log_success(f"Success: {stats['success']}")
    log_success(f"Failed: {stats['failed']}")
    log_success(f"Skipped: {stats['skipped']}")
    log_success(f"Total pages ingested: {stats['total_pages']}")
    log_success(f"Total chunks created: {stats['total_chunks']}")

if __name__ == "__main__":
    main()
