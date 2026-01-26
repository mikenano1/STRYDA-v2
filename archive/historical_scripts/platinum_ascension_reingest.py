#!/usr/bin/env python3
"""
⚡ PLATINUM ASCENSION - GRANULAR RE-INGESTION
=============================================
High-Zoom Vision on capacity tables for missing kN values.

Target Products:
- JH 120/45 (Joist Hanger)
- H2 connector
- TB (Truss Boot)
- C3 Cyclonic tie-down
- Flat strap
- Multi-grip connector
- NP (Nail plate)

Strategy:
- Re-scan Brackets Fixes and Hangers files
- DPI 300 for table capture
- Create unique chunk per nail/fixing option
- Context injection: Product | Timber Grade | Nailing | kN
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_KEY)

print("=" * 80, flush=True)
print("   ⚡ PLATINUM ASCENSION - GRANULAR RE-INGESTION", flush=True)
print(f"   Started: {datetime.now().isoformat()}", flush=True)
print("   Strategy: High-Zoom Vision (DPI 300) on Capacity Tables", flush=True)
print("=" * 80, flush=True)

# ==============================================================================
# TARGET FILES AND PRODUCTS
# ==============================================================================
TARGET_FILES = [
    'F_Manufacturers/Fasteners/Pryda/Pryda - Brackets Fixes Design Guide.pdf',
    'F_Manufacturers/Fasteners/Pryda/Pryda - Hangers And Brackets.pdf',
    'F_Manufacturers/Fasteners/Pryda/Pryda - Hangers Truss Boots Design Guide.pdf',
    'F_Manufacturers/Fasteners/Pryda/NZ_Pryda_Connectors_Tie-downs_Design_Guide.pdf',
    'F_Manufacturers/Fasteners/Pryda/Pryda - Nail Plates.pdf',
    'F_Manufacturers/Fasteners/Pryda/Pryda - Timber Connections And Straps.pdf',
]

# Products with missing kN values
TARGET_PRODUCTS = [
    'JH 120/45', 'JH120/45', 'JH', 'joist hanger',
    'H2', 'H-2', 'framing anchor',
    'TB', 'truss boot',
    'C3', 'cyclonic', 'tie-down', 'tie down',
    'flat strap', 'FS',
    'multi-grip', 'multigrip', 'MG',
    'NP', 'nail plate',
]

# ==============================================================================
# HIGH-ZOOM EXTRACTION PROMPT
# ==============================================================================
GRANULAR_EXTRACTION_PROMPT = """CRITICAL MISSION: Extract ALL load capacity values from this page.

You are looking for these specific products:
- JH (Joist Hanger) - especially JH 120/45, JH 140/45
- H2, H-2 (Framing Anchor)
- TB (Truss Boot) 
- Cyclonic tie-downs (C1, C2, C3, C4 ratings)
- Flat straps (FS)
- Multi-grip connectors
- Nail plates (NP)

FOR EACH PRODUCT FOUND, EXTRACT:

## PRODUCT: [Code]
- **Description**: [What it is]
- **Timber Grades**: [SG8, SG10, J2, JD4 etc if specified]
- **Capacities**:
  - Uplift: [X] kN
  - Shear: [X] kN  
  - Tension: [X] kN
- **Nailing Options** (CREATE SEPARATE ENTRY FOR EACH):
  - Option A: [X nails × Ømm] = [Y] kN
  - Option B: [X nails × Ømm] = [Y] kN
- **Notes**: [Any conditions, min timber size, edge distance]

CRITICAL RULES:
1. If a table shows DIFFERENT capacities for DIFFERENT nail patterns, list EACH ONE
2. If SG8 and SG10 have different values, specify BOTH
3. Include ALL numeric kN values visible
4. Format numbers exactly as shown (e.g., "12.5 kN" not "12.5kN")

Be exhaustive - every kN value matters for structural calculations."""

# ==============================================================================
# VISION EXTRACTION
# ==============================================================================
async def extract_page_high_zoom(image_base64, page_num, filename):
    """High-zoom vision extraction for capacity tables"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"granular-{hashlib.md5(f'{filename}_{page_num}'.encode()).hexdigest()[:8]}",
            system_message="You are an expert at reading structural connector load tables. Extract every kN value with full context."
        ).with_model("gemini", "gemini-2.5-flash")
        
        image_content = ImageContent(image_base64=image_base64)
        
        context = f"[HIGH-ZOOM SCAN | Document: {filename} | Page: {page_num}]"
        
        user_message = UserMessage(
            text=f"{context}\n\n{GRANULAR_EXTRACTION_PROMPT}",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        print(f"      ⚠️ Vision error p{page_num}: {str(e)[:40]}", flush=True)
        return None


def create_granular_chunks(content, filename, page_num):
    """
    Create granular chunks - one per product/nailing combination.
    """
    chunks = []
    
    # Split by product headers
    products = re.split(r'##\s*PRODUCT:', content)
    
    for product_section in products[1:]:  # Skip first empty split
        lines = product_section.strip().split('\n')
        if not lines:
            continue
        
        product_code = lines[0].strip()
        
        # Check if this is a target product
        is_target = any(tp.lower() in product_code.lower() or 
                       tp.lower() in product_section.lower() 
                       for tp in TARGET_PRODUCTS)
        
        if not is_target:
            continue
        
        # Extract nailing options if present
        nailing_matches = re.findall(
            r'Option\s*[A-Z]?:?\s*(\d+\s*nails?.*?=\s*[\d.]+\s*kN)',
            product_section, re.IGNORECASE
        )
        
        if nailing_matches:
            # Create separate chunk for each nailing option
            for option in nailing_matches:
                chunk = f"[PRYDA GRANULAR | {filename} | Page {page_num}]\n"
                chunk += f"[Product: {product_code}]\n"
                chunk += f"[Nailing Option: {option}]\n\n"
                chunk += product_section
                chunks.append(chunk)
        else:
            # Single chunk for product
            chunk = f"[PRYDA GRANULAR | {filename} | Page {page_num}]\n"
            chunk += f"[Product: {product_code}]\n\n"
            chunk += product_section
            chunks.append(chunk)
    
    # Also extract any kN values not in product sections
    kn_matches = re.findall(
        r'([A-Z]{1,3}[\s-]?\d*/?[\d]*)\s*[:\|]?\s*.*?(\d+\.?\d*)\s*kN',
        content, re.IGNORECASE
    )
    
    for code, value in kn_matches:
        if any(tp.lower() in code.lower() for tp in TARGET_PRODUCTS):
            chunk = f"[PRYDA kN VALUE | {filename} | Page {page_num}]\n"
            chunk += f"Product: {code} | Capacity: {value} kN\n"
            chunk += f"Source: Extracted from capacity table"
            
            # Avoid duplicate chunks
            if chunk not in chunks:
                chunks.append(chunk)
    
    return chunks


def get_embedding(text):
    """Get embedding"""
    try:
        r = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
            dimensions=1536
        )
        return r.data[0].embedding
    except:
        return None


# ==============================================================================
# MAIN RE-INGESTION
# ==============================================================================
async def run_granular_reingestion():
    """Execute granular re-ingestion"""
    
    stats = {
        'files_processed': 0,
        'pages_scanned': 0,
        'granular_chunks': 0,
        'target_products_found': [],
        'kn_values_extracted': []
    }
    
    for filepath in TARGET_FILES:
        filename = filepath.split('/')[-1]
        print(f"\n📄 {filename[:50]}...", flush=True)
        
        try:
            # Download
            pdf_data = supabase.storage.from_('product-library').download(filepath)
            if not pdf_data:
                print(f"   ⏭️ Download failed", flush=True)
                continue
            
            # High-zoom conversion (DPI 300)
            images = convert_from_bytes(pdf_data, dpi=300, fmt='JPEG')
            total_pages = len(images)
            print(f"   📄 {total_pages} pages @ DPI 300", flush=True)
            
            # Scan ALL pages for target products
            for page_num in range(1, min(total_pages + 1, 25)):  # First 25 pages
                img = images[page_num - 1]
                img_buffer = BytesIO()
                img.save(img_buffer, format='JPEG', quality=90)
                img_bytes = img_buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                content = await extract_page_high_zoom(img_base64, page_num, filename)
                
                if not content:
                    continue
                
                # Check if page has target products
                has_target = any(tp.lower() in content.lower() for tp in TARGET_PRODUCTS)
                
                if has_target:
                    print(f"   ✅ Page {page_num} - TARGET PRODUCTS FOUND", flush=True)
                    
                    # Create granular chunks
                    chunks = create_granular_chunks(content, filename, page_num)
                    
                    if chunks:
                        # Insert to DB
                        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                        cur = conn.cursor()
                        
                        for chunk in chunks:
                            emb = get_embedding(chunk)
                            if not emb:
                                continue
                            
                            # Extract product code for tracking
                            product_match = re.search(r'\[Product:\s*([^\]]+)\]', chunk)
                            if product_match:
                                stats['target_products_found'].append(product_match.group(1))
                            
                            # Extract kN values for tracking
                            kn_matches = re.findall(r'(\d+\.?\d*)\s*kN', chunk)
                            stats['kn_values_extracted'].extend(kn_matches)
                            
                            try:
                                cur.execute("""
                                    INSERT INTO documents (
                                        content, source, page, embedding, page_hash,
                                        trade, priority, is_active, doc_type, hierarchy_level
                                    ) VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                                """, (
                                    chunk, f"Pryda - {filename} [GRANULAR]", page_num, emb,
                                    hashlib.md5(chunk.encode()).hexdigest()[:16],
                                    'structural_connectors', 95, True, 'Load_Capacity_Table', 5
                                ))
                                stats['granular_chunks'] += 1
                            except Exception as e:
                                pass
                        
                        conn.commit()
                        conn.close()
                        
                        print(f"      📊 +{len(chunks)} granular chunks", flush=True)
                
                stats['pages_scanned'] += 1
                await asyncio.sleep(0.3)
            
            stats['files_processed'] += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}", flush=True)
    
    # Summary
    print(f"\n{'='*80}", flush=True)
    print(f"   ⚡ GRANULAR RE-INGESTION COMPLETE", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"   Files: {stats['files_processed']}", flush=True)
    print(f"   Pages Scanned: {stats['pages_scanned']}", flush=True)
    print(f"   Granular Chunks: {stats['granular_chunks']}", flush=True)
    print(f"   Target Products: {len(set(stats['target_products_found']))}", flush=True)
    print(f"   kN Values: {len(set(stats['kn_values_extracted']))}", flush=True)
    
    unique_products = list(set(stats['target_products_found']))[:10]
    print(f"\n   Products Found: {unique_products}", flush=True)
    
    unique_kn = sorted(set(stats['kn_values_extracted']), key=lambda x: float(x) if x else 0)[:15]
    print(f"   kN Values: {unique_kn}", flush=True)
    
    # DB status
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE source LIKE 'Pryda%'")
    pryda_count = cur.fetchone()[0]
    conn.close()
    
    print(f"\n   📈 Total Pryda chunks: {pryda_count}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    return stats


if __name__ == "__main__":
    asyncio.run(run_granular_reingestion())
