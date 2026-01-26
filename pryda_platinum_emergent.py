#!/usr/bin/env python3
"""
⚡ PRYDA PLATINUM V3.0 INGESTION ENGINE (EMERGENT VERSION)
==========================================================
Using Emergent Integrations for Vision API

Target: 17 Pryda files → Supabase Vector DB
"""
import os
import sys
import json
import hashlib
import base64
import re
import asyncio
from datetime import datetime
from io import BytesIO

# Unbuffered output
print("=" * 80, flush=True)
print("   ⚡ PRYDA PLATINUM V3.0 - EMERGENT VISION ENGINE", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("=" * 80, flush=True)

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print(f"\n✅ Platinum Engine initialized (Emergent Vision)", flush=True)
print(f"   Vision Model: gemini-2.5-flash via Emergent", flush=True)
print(f"   Embedding Model: text-embedding-3-small", flush=True)

# ==============================================================================
# PRYDA VISION PROMPT
# ==============================================================================

PRYDA_VISION_PROMPT = """You are a structural engineering document parser for Pryda timber connectors.

TASK: Extract ALL technical specifications with FULL CONTEXT for construction compliance.

CRITICAL EXTRACTION RULES:

1. **LOAD TABLES**: For every kN value found:
   - ANCHOR to specific product code (e.g., "JH 120/45", "H2", "PB 90")
   - LINK to timber grade if shown (SG8, SG10, J2, JD4)
   - INCLUDE nailing pattern (e.g., "4/3.15 nails", "6/2.8 nails")
   - FORMAT: "Product: [CODE] | Timber: [GRADE] | Capacity: [X] kN | Nailing: [PATTERN]"

2. **CONNECTOR TABLES**: Extract complete rows with:
   - Product code and dimensions
   - Uplift capacity (kN)
   - Shear capacity (kN)
   - Fixing requirements

3. **JOINT GROUPS**: When you see JD4, JD5, J2, J3, J4, J5:
   - Always specify which timber species/grade applies
   - Link capacity values to the correct joint group

OUTPUT FORMAT:
## PRODUCT SPECIFICATIONS
[Product code with full specs]

## LOAD TABLES  
[Complete tables with every cell having row+column context]

## INSTALLATION REQUIREMENTS
[Fixing patterns, edge distances]

Be exhaustive - every number matters for structural design."""

# ==============================================================================
# EMERGENT VISION EXTRACTION
# ==============================================================================

async def extract_page_with_emergent_vision(img_base64, page_num, product_name):
    """Use Emergent Integrations for Gemini Vision"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"pryda-vision-{hashlib.md5(f'{product_name}_{page_num}'.encode()).hexdigest()[:8]}",
            system_message="You are a technical document parser for construction connectors."
        ).with_model("gemini", "gemini-2.5-flash")
        
        image_content = ImageContent(image_base64=img_base64)
        
        user_message = UserMessage(
            text=f"[Document: {product_name} | Page: {page_num}]\n\n{PRYDA_VISION_PROMPT}",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        print(f"      ⚠️ Vision error p{page_num}: {str(e)[:40]}", flush=True)
        return None


async def extract_with_vision(pdf_bytes, product_name, is_high_complexity=False):
    """Use Emergent Vision API to parse PDF pages"""
    all_content = []
    tables_found = 0
    kn_values_found = []
    
    try:
        dpi = 200
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='JPEG')
        total_pages = len(images)
        print(f"      📄 {total_pages} pages (DPI: {dpi})", flush=True)
        
        # Process pages (limit to avoid timeout)
        max_pages = min(total_pages, 15 if is_high_complexity else 10)
        
        for page_num in range(1, max_pages + 1):
            img = images[page_num - 1]
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_bytes = img_buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            page_content = await extract_page_with_emergent_vision(
                img_base64, page_num, product_name
            )
            
            if page_content:
                # Extract kN values
                kn_matches = re.findall(r'(\d+\.?\d*)\s*kN', page_content)
                kn_values_found.extend(kn_matches)
                
                # Count tables
                if '|' in page_content:
                    tables_found += 1
                
                # Add context prefix
                contextualized = f"[PRYDA CONNECTOR | {product_name} | Page: {page_num}]\n"
                contextualized += f"[Unit Law: kN primary | Joint Groups: JD4/J2 applicable]\n\n"
                contextualized += page_content
                
                all_content.append(contextualized)
                print(f"      ✅ Page {page_num}", flush=True)
            
            # Small delay between pages
            await asyncio.sleep(0.3)
        
        return all_content, total_pages, tables_found, list(set(kn_values_found))
        
    except Exception as e:
        print(f"      ❌ PDF error: {str(e)[:50]}", flush=True)
        return [], 0, 0, []


def chunk_pryda_content(content_pages, product_name, chunk_size=1200):
    """Smart chunking for Pryda content"""
    chunks = []
    
    for page_content in content_pages:
        # Split by sections
        sections = re.split(r'\n\n+', page_content)
        
        current_chunk = ""
        for section in sections:
            if len(current_chunk) + len(section) < chunk_size:
                current_chunk += section + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = section + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
    
    return chunks


def get_embedding(text):
    """Get embedding from OpenAI."""
    try:
        r = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return r.data[0].embedding
    except Exception as e:
        return None


# ==============================================================================
# MAIN INGESTION
# ==============================================================================

async def run_ingestion():
    """Execute Pryda Platinum Ingestion"""
    
    # Get files
    pryda_path = 'F_Manufacturers/Fasteners/Pryda'
    pryda_files = supabase.storage.from_('product-library').list(pryda_path, {'limit': 100})
    pryda_files = [f for f in pryda_files if f['name'].endswith('.pdf')]
    
    total_files = len(pryda_files)
    print(f"\n🔩 Found {total_files} Pryda files", flush=True)
    
    # High complexity files
    HIGH_COMPLEXITY = ['Brackets Fixes', 'Fasteners Design', 'Hangers Truss']
    
    # Check existing
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
    existing = cur.fetchone()[0]
    
    if existing > 0:
        print(f"   ⚠️ Purging {existing} legacy Pryda chunks...", flush=True)
        cur.execute("DELETE FROM documents WHERE source LIKE 'Pryda%'")
        conn.commit()
    conn.close()
    
    stats = {
        'processed': 0,
        'chunks': 0,
        'tables': 0,
        'kn_values': [],
        'pages': 0,
        'errors': 0
    }
    
    all_chunks_data = []
    
    for i, file_info in enumerate(pryda_files, 1):
        filename = file_info['name']
        filepath = f"{pryda_path}/{filename}"
        
        is_high = any(hc in filename for hc in HIGH_COMPLEXITY)
        marker = "🔴 HIGH" if is_high else "🟢 STD"
        
        print(f"\n[{i:2}/{total_files}] {marker} {filename[:45]}...", flush=True)
        
        try:
            # Download
            pdf_data = supabase.storage.from_('product-library').download(filepath)
            if not pdf_data:
                continue
            
            product = f"Pryda - {filename.replace('.pdf', '').replace('_', ' ')}"
            
            # Vision extraction
            content_pages, pages, tables, kn_vals = await extract_with_vision(
                pdf_data, product, is_high_complexity=is_high
            )
            
            if not content_pages:
                print(f"      ⏭️ Skip: No content", flush=True)
                continue
            
            stats['pages'] += pages
            stats['tables'] += tables
            stats['kn_values'].extend(kn_vals)
            
            # Chunk
            chunks = chunk_pryda_content(content_pages, product)
            all_chunks_data.extend(chunks)
            
            print(f"      📊 {pages}p | {len(chunks)} chunks | {tables} tables | {len(kn_vals)} kN", flush=True)
            
            # Insert
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cur = conn.cursor()
            
            inserted = 0
            for ci, chunk in enumerate(chunks):
                emb = get_embedding(chunk)
                if not emb:
                    print(f"         ⚠️ No embedding for chunk {ci}", flush=True)
                    continue
                
                doc_type = 'Load_Capacity_Table' if 'kN' in chunk or '|' in chunk else 'Technical_Data_Sheet'
                
                try:
                    cur.execute("""
                        INSERT INTO documents (
                            content, source, page, embedding, page_hash,
                            trade, priority, is_active, doc_type, hierarchy_level
                        ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                    """, (
                        chunk, product, ci + 1, emb,
                        hashlib.md5(f"{product}_{ci}".encode()).hexdigest()[:16],
                        'structural_connectors', 90, True, doc_type, 4
                    ))
                    inserted += 1
                except Exception as db_err:
                    print(f"         ❌ DB error chunk {ci}: {str(db_err)[:40]}", flush=True)
            
            conn.commit()
            conn.close()
            
            stats['processed'] += 1
            stats['chunks'] += inserted
            print(f"      ✅ {inserted} chunks [PLATINUM]", flush=True)
            
            # 50% Progress Report with Data Card
            if i == total_files // 2:
                print(f"\n{'='*60}", flush=True)
                print(f"   📊 50% PROGRESS REPORT", flush=True)
                print(f"{'='*60}", flush=True)
                print(f"   Files: {stats['processed']}/{total_files}", flush=True)
                print(f"   Chunks: {stats['chunks']}", flush=True)
                
                # Data Card for JH 120/45
                jh_data = [c for c in all_chunks_data if 'JH' in c or 'Hanger' in c.upper()]
                if jh_data:
                    print(f"\n   📋 SAMPLE DATA CARD: JH 120/45 (or similar)", flush=True)
                    print(f"   {'-'*50}", flush=True)
                    print(f"   {jh_data[0][:400]}...", flush=True)
                print(f"{'='*60}\n", flush=True)
            
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:50]}", flush=True)
            stats['errors'] += 1
    
    # Final Report
    unique_kn = sorted(set(stats['kn_values']), key=lambda x: float(x) if x else 0)
    
    print(f"\n{'='*80}", flush=True)
    print(f"   ⚡ PRYDA PLATINUM V3.0 INGESTION - COMPLETE", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"   ✅ Files: {stats['processed']}", flush=True)
    print(f"   📄 Chunks: {stats['chunks']}", flush=True)
    print(f"   📊 Tables: {stats['tables']}", flush=True)
    print(f"   ⚡ kN Values: {len(unique_kn)}", flush=True)
    print(f"   ❌ Errors: {stats['errors']}", flush=True)
    print(f"\n   kN Range: {unique_kn[:5]}...{unique_kn[-5:] if len(unique_kn) > 5 else ''}", flush=True)
    
    # DB status
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
    pryda_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM documents")
    total_count = cur.fetchone()[0]
    conn.close()
    
    print(f"\n   📈 DATABASE:", flush=True)
    print(f"      Pryda chunks: {pryda_count}", flush=True)
    print(f"      Total: {total_count}", flush=True)
    print(f"\n   Completed: {datetime.now().isoformat()}", flush=True)
    print("=" * 80, flush=True)
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'protocol': 'PLATINUM V3.0 (Emergent Vision)',
        'segment': 'Pryda',
        'stats': stats,
        'kn_values': unique_kn,
        'pryda_chunks': pryda_count,
        'total_db': total_count
    }
    
    with open('/app/pryda_platinum_report.json', 'w') as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    asyncio.run(run_ingestion())
