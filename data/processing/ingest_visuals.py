#!/usr/bin/env python3
"""
STRYDA Visual Ingestion Engine v3.0 - "The Gatekeeper"
=======================================================

World-Class Strict Classification Pipeline

This script:
1. Extracts images from PDFs using PyMuPDF
2. GATEKEEPER: Classifies each image with strict rules
   - KEEP: TECHNICAL_DRAWING, SPAN_TABLE, SPEC_SHEET
   - REJECT: SITE_PHOTO, MARKETING_RENDER, LOGO, OTHER
3. Only uploads KEPT images to Supabase
4. Extracts surrounding text context for better search
"""

import os
import sys
import json
import hashlib
import base64
import time
import requests
import tempfile
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import psycopg2.extras
from supabase import create_client, Client
import openai
import anthropic
import fitz  # PyMuPDF

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Minimum image size (skip tiny icons)
MIN_IMAGE_SIZE_KB = 15

# Categories to KEEP
KEEP_CATEGORIES = ['TECHNICAL_DRAWING', 'SPAN_TABLE', 'SPEC_SHEET']

# Categories to REJECT
REJECT_CATEGORIES = ['SITE_PHOTO', 'MARKETING_RENDER', 'LOGO', 'OTHER']

# =============================================================================
# THE GATEKEEPER - Strict Classification Prompt
# =============================================================================

GATEKEEPER_PROMPT = """You are THE GATEKEEPER. Your job is to ruthlessly filter construction document images.

Classify this image into EXACTLY ONE category:
- TECHNICAL_DRAWING: Black-and-white CAD drawings, architectural details, cross-sections, flashing details, junction details, construction diagrams with dimensions
- SPAN_TABLE: Grid of numbers, data tables, specification tables with rows and columns
- SPEC_SHEET: Technical specification pages with measurements, product codes, material lists
- SITE_PHOTO: Photographs of buildings, houses, construction sites, people, installed products
- MARKETING_RENDER: 3D color renders, artistic visualizations, promotional imagery
- LOGO: Company logos, brand marks, icons, certification stamps
- OTHER: Anything else that doesn't fit above categories

CRITICAL RULES:
1. If you see a PHOTOGRAPH of a real building/house/person → SITE_PHOTO (REJECT)
2. If you see COLORS and a 3D visualization → MARKETING_RENDER (REJECT)
3. If you see just a logo or small icon → LOGO (REJECT)
4. ONLY line drawings, CAD, tables, or spec sheets should be KEPT

Return ONLY this JSON (no other text):
{"category": "TECHNICAL_DRAWING", "keep": true, "reason": "Black and white detail drawing showing eaves junction"}

OR

{"category": "SITE_PHOTO", "keep": false, "reason": "Photograph of completed house with timber cladding"}"""

# =============================================================================
# ANALYSIS PROMPT (for kept images only)
# =============================================================================

ANALYSIS_PROMPT = """You are a Senior Structural Engineer. Analyze this technical drawing/table for NZ construction.

Extract:
1. image_type: "detail_drawing", "span_table", "spec_sheet", "section_view", "flashing_detail"
2. brand: Manufacturer name if visible
3. summary: 1-2 sentence description of what this drawing shows
4. technical_variables: Key measurements, codes, specifications visible

Return JSON only:
{
    "image_type": "detail_drawing",
    "brand": "Abodo",
    "summary": "External corner junction detail for weatherboard cladding showing flashing overlap",
    "technical_variables": {
        "overlap_mm": 50,
        "cavity_depth_mm": 20,
        "fixing_type": "stainless steel screws"
    }
}"""

# =============================================================================
# CLIENTS
# =============================================================================

supabase: Client = None
anthropic_client: anthropic.Anthropic = None
openai_client: openai.OpenAI = None

def init_clients():
    """Initialize API clients."""
    global supabase, anthropic_client, openai_client
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("   ✅ API clients initialized")


# =============================================================================
# PDF URL DISCOVERY
# =============================================================================

def get_storage_url_for_source(source: str) -> Optional[str]:
    """Get Supabase Storage URL for a source document."""
    if ' - ' in source:
        brand_raw, doc_name = source.split(' - ', 1)
    else:
        brand_raw, doc_name = source, source
    
    brand_mapping = {
        'Abodo Wood': ('A_Structure', 'Abodo_Wood'),
        'Kingspan': ('B_Enclosure', 'Kingspan'),
        'Kingspan Deep Dive': ('B_Enclosure', 'Kingspan'),
    }
    
    category, brand_folder = None, None
    for key, (cat, folder) in brand_mapping.items():
        if key.lower() in brand_raw.lower():
            category, brand_folder = cat, folder
            break
    
    if not category:
        return None
    
    doc_type_folders = [
        'Brochures_Fact_Sheets', 'Technical_Data_Sheets', 'Guides_Manuals',
        'Profile_Drawings', 'Certificates_Warranties'
    ]
    
    pdf_name = f"{doc_name}.pdf"
    
    for doc_folder in doc_type_folders:
        path = f"{category}/{brand_folder}/{doc_folder}/{pdf_name}"
        try:
            signed = supabase.storage.from_('product-library').create_signed_url(path, 3600)
            if signed and signed.get('signedURL'):
                return signed['signedURL']
        except:
            continue
    
    return None


# =============================================================================
# IMAGE EXTRACTION WITH CONTEXT
# =============================================================================

def extract_images_with_context(pdf_url: str, source_name: str) -> List[Dict]:
    """
    Extract images from PDF along with surrounding text context.
    """
    print(f"   📄 Extracting: {source_name[:50]}...")
    
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=60)
        if response.status_code != 200:
            return []
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        print(f"      📑 Pages: {len(doc)}")
        
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get page text for context
            page_text = page.get_text()
            
            # Get images from page
            image_list = page.get_images()
            
            for img_idx, img in enumerate(image_list):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    size_kb = len(image_bytes) / 1024
                    
                    if size_kb < MIN_IMAGE_SIZE_KB:
                        continue
                    
                    # Extract surrounding context (nearby text)
                    # Split text into chunks and find relevant section
                    context = extract_context_for_image(page_text, img_idx, page_num)
                    
                    mime_map = {'jpeg': 'image/jpeg', 'jpg': 'image/jpeg', 'png': 'image/png'}
                    mime_type = mime_map.get(image_ext.lower(), 'image/png')
                    
                    images.append({
                        'data': image_bytes,
                        'base64': base64.b64encode(image_bytes).decode('utf-8'),
                        'mime_type': mime_type,
                        'ext': image_ext,
                        'filename': f"img_p{page_num+1}_{xref}.{image_ext}",
                        'size_kb': size_kb,
                        'page': page_num + 1,
                        'source': source_name,
                        'context': context,
                    })
                except:
                    continue
        
        doc.close()
        os.unlink(tmp_path)
        
        print(f"      📷 Found {len(images)} images (>{MIN_IMAGE_SIZE_KB}KB)")
        return images
        
    except Exception as e:
        print(f"      ❌ Extraction error: {e}")
        return []


def extract_context_for_image(page_text: str, img_idx: int, page_num: int) -> str:
    """
    Extract meaningful context text for an image.
    Looks for figure references, captions, nearby technical terms.
    """
    # Look for figure/diagram references
    figure_patterns = [
        r'(?i)fig(?:ure)?\.?\s*\d+[:\s]*[^\n]{0,100}',
        r'(?i)diagram\s*\d*[:\s]*[^\n]{0,100}',
        r'(?i)detail\s*\d*[:\s]*[^\n]{0,100}',
        r'(?i)table\s*\d+[:\s]*[^\n]{0,100}',
        r'(?i)drawing[:\s]*[^\n]{0,100}',
    ]
    
    context_parts = []
    
    for pattern in figure_patterns:
        matches = re.findall(pattern, page_text)
        context_parts.extend(matches[:2])  # Max 2 matches per pattern
    
    # Also grab technical terms if present
    tech_terms = re.findall(r'\b(?:mm|NZS|BRANZ|E2|AS1|spacing|fixing|batten|flashing)\b[^\n]{0,50}', page_text, re.I)
    context_parts.extend(tech_terms[:3])
    
    # Build context string
    context = ' | '.join(set(context_parts))[:300]  # Max 300 chars
    
    if not context:
        context = f"Page {page_num + 1}, Image {img_idx + 1}"
    
    return context


# =============================================================================
# THE GATEKEEPER - Classification
# =============================================================================

def gatekeeper_classify(image_base64: str, mime_type: str) -> Dict:
    """
    THE GATEKEEPER: Strictly classify image as KEEP or REJECT.
    """
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_base64,
                        }
                    },
                    {"type": "text", "text": GATEKEEPER_PROMPT}
                ]
            }]
        )
        
        text = response.content[0].text.strip()
        
        # Parse JSON
        if "{" in text:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            result = json.loads(text[json_start:json_end])
            return result
        
        return {"category": "OTHER", "keep": False, "reason": "Parse error"}
        
    except Exception as e:
        return {"category": "OTHER", "keep": False, "reason": str(e)}


# =============================================================================
# TECHNICAL ANALYSIS (for kept images only)
# =============================================================================

def analyze_technical_image(image_base64: str, mime_type: str, context: str) -> Dict:
    """Analyze a KEPT image for technical content."""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_base64,
                        }
                    },
                    {
                        "type": "text", 
                        "text": f"{ANALYSIS_PROMPT}\n\nContext from document: {context}"
                    }
                ]
            }]
        )
        
        text = response.content[0].text.strip()
        
        if "{" in text:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            return json.loads(text[json_start:json_end])
        
        return {"image_type": "other", "summary": "Analysis unavailable"}
        
    except Exception as e:
        return {"image_type": "other", "summary": str(e)}


# =============================================================================
# STORAGE & DATABASE
# =============================================================================

def upload_to_bucket(image_data: bytes, filename: str, mime_type: str) -> Optional[str]:
    """Upload image to visual_assets bucket."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(image_data).hexdigest()[:8]
        ext = '.png' if 'png' in mime_type else '.jpg'
        storage_path = f"images/{timestamp}_{file_hash}_{filename[:20]}{ext}"
        
        supabase.storage.from_('visual_assets').upload(
            storage_path, image_data, {"content-type": mime_type}
        )
        return storage_path
    except Exception as e:
        print(f"         ❌ Upload error: {e}")
        return None


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for search."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=1536
        )
        return response.data[0].embedding
    except:
        return None


def save_to_database(visual_data: Dict) -> bool:
    """Save visual to database."""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO visuals (
                source_document, source_page, image_type, brand,
                storage_path, file_size, summary, technical_variables,
                confidence, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            visual_data['source_document'],
            visual_data.get('source_page'),
            visual_data['image_type'],
            visual_data.get('brand'),
            visual_data['storage_path'],
            visual_data.get('file_size'),
            visual_data.get('summary'),
            json.dumps(visual_data.get('technical_variables', {})),
            visual_data.get('confidence', 0.9),
            visual_data.get('embedding')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"         ❌ DB error: {e}")
        return False


# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

def get_documents_to_process(limit: int = None) -> List[Dict]:
    """Get source documents for visual extraction."""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    doc_types = ['Technical_Data_Sheet', 'Installation_Guide', 'Product_Catalog', 'Product_Guide']
    
    placeholders = ", ".join(["%s"] * len(doc_types))
    query = f"""
        SELECT DISTINCT source, doc_type, brand_name
        FROM documents 
        WHERE doc_type IN ({placeholders})
        ORDER BY source
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query, tuple(doc_types))
    sources = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT source_document FROM visuals")
    processed = {r['source_document'] for r in cursor.fetchall()}
    sources = [s for s in sources if s['source'] not in processed]
    
    cursor.close()
    conn.close()
    return sources


def process_document(source: str, doc_type: str, brand: str = None) -> Dict:
    """Process a single document with Gatekeeper filtering."""
    stats = {
        'source': source,
        'images_found': 0,
        'kept': 0,
        'rejected': 0,
        'rejection_reasons': {}
    }
    
    pdf_url = get_storage_url_for_source(source)
    if not pdf_url:
        return stats
    
    images = extract_images_with_context(pdf_url, source)
    stats['images_found'] = len(images)
    
    for img in images:
        # === THE GATEKEEPER ===
        print(f"      🚪 Gatekeeper checking {img['size_kb']:.0f}KB image...")
        
        classification = gatekeeper_classify(img['base64'], img['mime_type'])
        category = classification.get('category', 'OTHER')
        keep = classification.get('keep', False)
        reason = classification.get('reason', 'Unknown')
        
        if not keep:
            # REJECTED
            stats['rejected'] += 1
            stats['rejection_reasons'][category] = stats['rejection_reasons'].get(category, 0) + 1
            print(f"         ❌ REJECTED: {category} - {reason[:50]}")
            continue
        
        # KEPT - Proceed with full analysis
        print(f"         ✅ KEPT: {category} - {reason[:50]}")
        stats['kept'] += 1
        
        # Deep analysis
        analysis = analyze_technical_image(img['base64'], img['mime_type'], img['context'])
        
        # Upload to bucket
        storage_path = upload_to_bucket(img['data'], img['filename'], img['mime_type'])
        if not storage_path:
            continue
        
        # Generate embedding from context + summary
        embed_text = f"{img['context']} {analysis.get('summary', '')} {json.dumps(analysis.get('technical_variables', {}))}"
        embedding = generate_embedding(embed_text)
        
        # Save to database
        visual_data = {
            'source_document': source,
            'source_page': img['page'],
            'image_type': analysis.get('image_type', category.lower()),
            'brand': analysis.get('brand') or brand,
            'storage_path': storage_path,
            'file_size': int(img['size_kb'] * 1024),
            'summary': analysis.get('summary'),
            'technical_variables': analysis.get('technical_variables', {}),
            'confidence': 0.95,
            'embedding': embedding,
        }
        
        save_to_database(visual_data)
        print(f"         💾 Saved: {analysis.get('summary', 'N/A')[:50]}...")
    
    return stats


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline(limit: int = None):
    """Run the Gatekeeper pipeline."""
    print("\n" + "="*70)
    print("🚪 STRYDA VISUAL INGESTION v3.0 - THE GATEKEEPER")
    print("   World-Class Strict Classification Pipeline")
    print("="*70)
    
    print("\n📡 Initializing...")
    init_clients()
    
    print("\n📥 Discovering documents...")
    documents = get_documents_to_process(limit=limit)
    print(f"   Found {len(documents)} documents")
    
    print(f"\n🔄 Processing with STRICT filtering...\n")
    
    totals = {'docs': 0, 'found': 0, 'kept': 0, 'rejected': 0, 'reasons': {}}
    
    for i, doc in enumerate(documents):
        print(f"\n[{i+1}/{len(documents)}] {doc['source'][:50]}...")
        
        stats = process_document(doc['source'], doc['doc_type'], doc.get('brand_name'))
        
        totals['docs'] += 1
        totals['found'] += stats['images_found']
        totals['kept'] += stats['kept']
        totals['rejected'] += stats['rejected']
        
        for cat, count in stats['rejection_reasons'].items():
            totals['reasons'][cat] = totals['reasons'].get(cat, 0) + count
        
        print(f"   📊 Found: {stats['images_found']} | ✅ Kept: {stats['kept']} | ❌ Rejected: {stats['rejected']}")
        
        time.sleep(0.5)
    
    # Final Report
    print("\n" + "="*70)
    print("📊 GATEKEEPER REPORT")
    print("="*70)
    print(f"\n📦 Documents Processed: {totals['docs']}")
    print(f"🖼️ Total Images Found: {totals['found']}")
    print(f"✅ KEPT (Technical): {totals['kept']}")
    print(f"❌ REJECTED (Garbage): {totals['rejected']}")
    
    if totals['reasons']:
        print(f"\n🗑️ Rejection Breakdown:")
        for cat, count in sorted(totals['reasons'].items(), key=lambda x: -x[1]):
            print(f"   • {cat}: {count}")
    
    keep_rate = (totals['kept'] / totals['found'] * 100) if totals['found'] > 0 else 0
    print(f"\n📈 Quality Rate: {keep_rate:.1f}% kept")
    print("="*70)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='STRYDA Gatekeeper v3.0')
    parser.add_argument('--limit', type=int, help='Limit documents')
    args = parser.parse_args()
    
    run_pipeline(limit=args.limit)
