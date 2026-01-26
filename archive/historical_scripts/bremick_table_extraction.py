#!/usr/bin/env python3
"""
BREMICK TABLE-FIRST VISION EXTRACTION
=====================================
Uses Gemini Vision to extract tables from image-based PDFs
Targets: Pilot Hole Charts, Proof Load Tables, Torque Tables

Protocol: PLATINUM V3.0 + TABLE-FIRST extraction
"""
import os
import sys
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from io import BytesIO
import base64

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

import psycopg2
import openai
from supabase import create_client
import fitz
import google.generativeai as genai

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('EMERGENT_LLM_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)
genai.configure(api_key=GEMINI_KEY)

print("=" * 80)
print("📊 BREMICK TABLE-FIRST VISION EXTRACTION")
print(f"   Started: {datetime.now().isoformat()}")
print("   Protocol: Gemini Vision for image-based tables")
print("=" * 80)

# ============================================================================
# TABLE EXTRACTION PROMPT
# ============================================================================

TABLE_EXTRACTION_PROMPT = """
You are a precision data extractor for engineering technical documents.

TASK: Extract ALL tabular data from this page image.

For each table found, output in this EXACT JSON format:
{
  "tables": [
    {
      "table_name": "Descriptive name of the table",
      "table_type": "pilot_hole|proof_load|torque|dimensions|capacity",
      "columns": ["Column1", "Column2", "Column3"],
      "rows": [
        {"Column1": "value1", "Column2": "value2", "Column3": "value3"},
        {"Column1": "value4", "Column2": "value5", "Column3": "value6"}
      ],
      "units": {"Column2": "mm", "Column3": "kN"},
      "notes": "Any footnotes or special conditions"
    }
  ],
  "page_title": "Title if visible",
  "product_codes": ["M12", "3/8", etc]
}

CRITICAL RULES:
1. Extract EVERY row and column - do not summarize
2. Preserve exact numerical values - no rounding
3. Include ALL size variants (M6, M8, M10, M12, etc.)
4. Note units (mm, kN, Nm, inch, etc.)
5. For pilot hole tables: capture timber species AND hole diameters
6. If a cell is empty, use null
7. Output ONLY valid JSON - no markdown, no explanation

If no tables are found, return: {"tables": [], "page_title": "No tables found"}
"""

# ============================================================================
# VISION EXTRACTION
# ============================================================================

def extract_tables_with_vision(page_image_bytes, page_num):
    """Use Gemini Vision to extract tables from page image"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convert to base64
        img_b64 = base64.b64encode(page_image_bytes).decode('utf-8')
        
        response = model.generate_content([
            TABLE_EXTRACTION_PROMPT,
            {
                "mime_type": "image/png",
                "data": img_b64
            }
        ])
        
        # Parse JSON response
        text = response.text.strip()
        
        # Clean markdown if present
        if text.startswith('```'):
            text = re.sub(r'^```json?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        try:
            data = json.loads(text)
            return data
        except json.JSONDecodeError:
            print(f"      ⚠️ JSON parse error on page {page_num}")
            return {"tables": [], "raw_text": text[:500]}
            
    except Exception as e:
        print(f"      ❌ Vision error: {str(e)[:50]}")
        return {"tables": [], "error": str(e)}


def pdf_page_to_image(pdf_doc, page_num, dpi=200):
    """Convert PDF page to high-res PNG bytes"""
    page = pdf_doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


# ============================================================================
# CONTEXT INJECTION FOR TABLES
# ============================================================================

def table_to_context_chunks(table_data, source_name, page_num):
    """Convert extracted table to searchable context chunks"""
    chunks = []
    
    for table in table_data.get('tables', []):
        table_name = table.get('table_name', 'Unknown Table')
        table_type = table.get('table_type', 'data')
        columns = table.get('columns', [])
        rows = table.get('rows', [])
        units = table.get('units', {})
        notes = table.get('notes', '')
        
        # Create context-rich chunk for each row
        for row in rows:
            # Build context sentence
            parts = []
            for col in columns:
                val = row.get(col)
                if val is not None:
                    unit = units.get(col, '')
                    parts.append(f"{col}: {val}{unit}")
            
            row_context = " | ".join(parts)
            
            chunk = f"""[BRAND: BREMICK]
[Document: {source_name} | Page: {page_num + 1} | Table: {table_name}]
[Table Type: {table_type}]

{row_context}

{f'Notes: {notes}' if notes else ''}
"""
            chunks.append(chunk.strip())
    
    return chunks


# ============================================================================
# EMBEDDING & STORAGE
# ============================================================================

def get_embedding(text):
    """Get embedding from OpenAI"""
    try:
        r = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return r.data[0].embedding
    except Exception as e:
        print(f"      ⚠️ Embedding error: {str(e)[:30]}")
        return None


# ============================================================================
# SCAN FOR BREMICK TABLE FILES
# ============================================================================

# Target files with tables
TABLE_FILE_PATTERNS = [
    'Technical',
    'Catalogue', 
    'Manual',
    'Data Sheet',
    'Specification',
    'Appendix',
    'Tables'
]

print("\n📂 SCANNING FOR BREMICK TABLE FILES...")

def get_bremick_files():
    """Get list of Bremick PDFs likely to have tables"""
    files = []
    try:
        # Scan Bremick folder
        base_path = 'F_Manufacturers/Fasteners/Bremick'
        items = supabase.storage.from_('product-library').list(base_path, {'limit': 300})
        
        for item in items:
            if item['name'].endswith('.pdf'):
                # Prioritize files likely to have tables
                priority = 1
                name_lower = item['name'].lower()
                for pattern in TABLE_FILE_PATTERNS:
                    if pattern.lower() in name_lower:
                        priority = 0
                        break
                
                files.append({
                    'name': item['name'],
                    'path': f"{base_path}/{item['name']}",
                    'priority': priority
                })
        
        # Also check subfolders
        for item in items:
            if item.get('id') is None:  # Folder
                subfolder = f"{base_path}/{item['name']}"
                try:
                    sub_items = supabase.storage.from_('product-library').list(subfolder, {'limit': 100})
                    for sub in sub_items:
                        if sub['name'].endswith('.pdf'):
                            files.append({
                                'name': sub['name'],
                                'path': f"{subfolder}/{sub['name']}",
                                'priority': 1
                            })
                except:
                    pass
    except Exception as e:
        print(f"   ❌ Scan error: {e}")
    
    # Sort by priority (table files first)
    files.sort(key=lambda x: x['priority'])
    return files

bremick_files = get_bremick_files()
print(f"   Found {len(bremick_files)} Bremick PDFs")

# ============================================================================
# MAIN EXTRACTION LOOP
# ============================================================================

stats = {
    'files_processed': 0,
    'pages_scanned': 0,
    'tables_extracted': 0,
    'chunks_created': 0,
    'errors': 0
}

# Limit to first 10 files for initial run
MAX_FILES = 10

print(f"\n🔄 PROCESSING TOP {MAX_FILES} TABLE FILES...")
print("=" * 80)

for i, file_info in enumerate(bremick_files[:MAX_FILES], 1):
    filename = file_info['name']
    filepath = file_info['path']
    
    print(f"\n[{i:2}/{MAX_FILES}] {filename[:55]}...")
    
    try:
        # Download PDF
        pdf_data = supabase.storage.from_('product-library').download(filepath)
        
        if not pdf_data:
            print(f"      ⚠️ Download failed")
            stats['errors'] += 1
            continue
        
        if isinstance(pdf_data, memoryview):
            pdf_data = bytes(pdf_data)
        
        # Open PDF
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        doc_name = f"Bremick - {filename.replace('.pdf', '')}"
        
        print(f"      📑 {len(doc)} pages")
        
        file_tables = 0
        file_chunks = 0
        
        # Process each page
        for page_num in range(len(doc)):
            # Convert to image
            img_bytes = pdf_page_to_image(doc, page_num)
            
            # Extract tables with vision
            table_data = extract_tables_with_vision(img_bytes, page_num)
            
            tables_found = len(table_data.get('tables', []))
            if tables_found > 0:
                print(f"      📊 Page {page_num + 1}: {tables_found} tables found")
                file_tables += tables_found
                stats['tables_extracted'] += tables_found
                
                # Convert to context chunks
                chunks = table_to_context_chunks(table_data, doc_name, page_num)
                
                # Store in database
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                cur = conn.cursor()
                
                for ci, chunk in enumerate(chunks):
                    emb = get_embedding(chunk)
                    if not emb:
                        continue
                    
                    content_hash = hashlib.sha256(f"{filename}_{page_num}_{ci}".encode()).hexdigest()[:16]
                    
                    try:
                        cur.execute("""
                            INSERT INTO documents (
                                content, source, page, embedding, page_hash,
                                trade, priority, is_active, doc_type, hierarchy_level
                            ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                        """, (
                            chunk,
                            doc_name,
                            page_num + 1,
                            emb,
                            f"bremick_table_{content_hash}",
                            'fasteners',
                            95,  # High priority for table data
                            True,
                            'Technical_Table',
                            2  # High hierarchy for tables
                        ))
                        file_chunks += 1
                        stats['chunks_created'] += 1
                    except Exception as e:
                        pass
                
                conn.commit()
                conn.close()
            
            stats['pages_scanned'] += 1
        
        doc.close()
        
        if file_tables > 0:
            print(f"      ✅ Extracted {file_tables} tables → {file_chunks} chunks")
            stats['files_processed'] += 1
        else:
            print(f"      ⏭️ No tables found")
        
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}")
        stats['errors'] += 1

# ============================================================================
# FINAL REPORT
# ============================================================================

print("\n" + "=" * 80)
print("📊 BREMICK TABLE-FIRST EXTRACTION - COMPLETE")
print("=" * 80)
print(f"\n✅ Files with tables: {stats['files_processed']}")
print(f"📑 Pages scanned: {stats['pages_scanned']}")
print(f"📊 Tables extracted: {stats['tables_extracted']}")
print(f"📄 Chunks created: {stats['chunks_created']}")
print(f"❌ Errors: {stats['errors']}")
print(f"\n   Completed: {datetime.now().isoformat()}")
print("=" * 80)

# Save report
with open('/app/bremick_table_extraction_report.json', 'w') as f:
    json.dump({**stats, 'completed': datetime.now().isoformat()}, f, indent=2)

print(f"\n💾 Report saved to: /app/bremick_table_extraction_report.json")
