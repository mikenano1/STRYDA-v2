#!/usr/bin/env python3
"""
STRYDA Visual Ingestion Engine v2.0
====================================

Agent #4: The Engineer - REAL Image Extraction Pipeline

This script:
1. Uses LlamaParse with premium_mode to extract ACTUAL images
2. Downloads the image files
3. Uploads PNG/JPG files to Supabase visual_assets bucket
4. Analyzes each image with Claude for technical data
5. Stores metadata + signed URL reference in visuals table
"""

import os
import sys
import json
import hashlib
import base64
import time
import requests
import tempfile
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import psycopg2.extras
from supabase import create_client, Client
import openai
import anthropic

# LlamaParse import (for text) + PyMuPDF for images
try:
    from llama_parse import LlamaParse
    import fitz  # PyMuPDF for image extraction
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install llama-parse pymupdf")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
LLAMA_CLOUD_API_KEY = os.getenv('LLAMA_CLOUD_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Minimum image size to process (skip tiny icons)
MIN_IMAGE_SIZE_KB = 10

# Claude system prompt for image analysis
CLAUDE_SYSTEM_PROMPT = """You are a Senior Structural Engineer analyzing construction document images for New Zealand building compliance.

Analyze the provided image and extract technical information.

Determine:
1. IMAGE_TYPE: One of [span_table, detail_drawing, diagram, chart, specification, flashing_detail, section_view, photo, logo, other]
2. RELEVANCE: Is this technically useful for construction? (true/false) - Logos, decorative images = false
3. BRAND: If visible, identify the manufacturer (e.g., "Kingspan", "GIB", "Abodo")
4. TECHNICAL_VARIABLES: Extract key values visible in the image

Return ONLY valid JSON:
{
    "image_type": "detail_drawing",
    "relevance": true,
    "brand": "Abodo",
    "summary": "External corner flashing detail for weatherboard cladding showing overlap dimensions",
    "technical_variables": {
        "overlap_mm": 50,
        "material": "galvanized steel",
        "application": "external corner"
    },
    "confidence": 0.90
}

For non-technical images (logos, photos, decorations):
{
    "image_type": "logo",
    "relevance": false,
    "brand": null,
    "summary": "Company logo or decorative image",
    "technical_variables": {},
    "confidence": 0.95
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
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing Supabase credentials")
    if not LLAMA_CLOUD_API_KEY:
        raise ValueError("Missing LLAMA_CLOUD_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError("Missing ANTHROPIC_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    print("   ✅ All API clients initialized")


# =============================================================================
# PDF URL DISCOVERY
# =============================================================================

def get_storage_url_for_source(source: str) -> Optional[str]:
    """Get the Supabase Storage URL for a source document."""
    
    # Parse source name: "Brand - Document Name"
    if ' - ' in source:
        brand_raw, doc_name = source.split(' - ', 1)
    else:
        brand_raw = source
        doc_name = source
    
    # Brand to folder mapping
    brand_mapping = {
        'Abodo Wood': ('A_Structure', 'Abodo_Wood'),
        'Kingspan': ('B_Enclosure', 'Kingspan'),
        'Kingspan Deep Dive': ('B_Enclosure', 'Kingspan'),
        'Bradford Deep Dive': ('C_Interiors', 'Bradford'),
        'Autex Deep Dive': ('C_Interiors', 'Autex'),
        'Mammoth Deep Dive': ('C_Interiors', 'Mammoth'),
        'Asona Deep Dive': ('C_Interiors', 'Asona_Acoustics'),
    }
    
    category, brand_folder = None, None
    for key, (cat, folder) in brand_mapping.items():
        if key.lower() in brand_raw.lower():
            category, brand_folder = cat, folder
            break
    
    if not category:
        return None
    
    # Document type subfolders to search
    doc_type_folders = [
        'Brochures_Fact_Sheets', 'Technical_Data_Sheets', 'Guides_Manuals',
        'Profile_Drawings', 'Certificates_Warranties', 'Safety_Data_Sheets',
        'Environmental_Product_Declaration', 'Reports', 'Color_Finishes_Textures'
    ]
    
    pdf_name = f"{doc_name}.pdf"
    
    for doc_folder in doc_type_folders:
        path = f"{category}/{brand_folder}/{doc_folder}/{pdf_name}"
        try:
            signed = supabase.storage.from_('product-library').create_signed_url(path, 3600)
            if signed and signed.get('signedURL'):
                print(f"      📂 Found PDF at: {path}")
                return signed['signedURL']
        except:
            continue
    
    return None


# =============================================================================
# LLAMAPARSE IMAGE EXTRACTION
# =============================================================================

def extract_images_with_llamaparse(pdf_url: str, source_name: str) -> List[Dict]:
    """
    Use LlamaParse with PREMIUM MODE to extract actual images from PDF.
    
    Returns list of image dictionaries with downloaded image data.
    """
    print(f"   📄 LlamaParse Premium: {source_name[:50]}...")
    
    try:
        # Configure LlamaParse for IMAGE EXTRACTION
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            premium_mode=True,  # CRITICAL: Enables image extraction
            verbose=False,
        )
        
        # Create temp directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Parse and extract images
            print(f"      🔄 Parsing document...")
            
            # Use get_images to download actual image files
            try:
                images_result = parser.get_images([pdf_url], download_path=temp_dir)
                print(f"      📥 get_images returned: {type(images_result)}")
            except Exception as e:
                print(f"      ⚠️ get_images failed: {e}")
                images_result = []
            
            # Check what files were downloaded
            downloaded_files = list(Path(temp_dir).glob("**/*"))
            image_files = [f for f in downloaded_files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']]
            
            print(f"      📁 Downloaded {len(image_files)} image files")
            
            images = []
            for img_path in image_files:
                # Read image data
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                
                # Skip tiny images (likely icons/bullets)
                if len(img_data) < MIN_IMAGE_SIZE_KB * 1024:
                    continue
                
                # Determine mime type
                suffix = img_path.suffix.lower()
                mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
                mime_type = mime_map.get(suffix, 'image/png')
                
                # Extract page number from filename if available
                page_num = 1
                fname = img_path.stem
                if '_page_' in fname:
                    try:
                        page_num = int(fname.split('_page_')[1].split('_')[0])
                    except:
                        pass
                
                images.append({
                    'data': img_data,
                    'base64': base64.b64encode(img_data).decode('utf-8'),
                    'mime_type': mime_type,
                    'filename': img_path.name,
                    'size_kb': len(img_data) / 1024,
                    'page': page_num,
                    'source': source_name,
                })
            
            print(f"      ✅ Extracted {len(images)} valid images (>{MIN_IMAGE_SIZE_KB}KB)")
            return images
            
    except Exception as e:
        print(f"      ❌ LlamaParse error: {e}")
        return []


# =============================================================================
# CLAUDE IMAGE ANALYSIS
# =============================================================================

def analyze_image_with_claude(image_base64: str, mime_type: str = "image/png") -> Dict:
    """Send actual image to Claude for visual analysis."""
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=CLAUDE_SYSTEM_PROMPT,
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
                        "text": "Analyze this construction document image. Extract technical information. Return JSON only."
                    }
                ]
            }]
        )
        
        text = response.content[0].text
        
        # Extract JSON from response
        if "{" in text and "}" in text:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            return json.loads(text[json_start:json_end])
        
        return {"error": "No JSON in response", "relevance": False}
        
    except Exception as e:
        return {"error": str(e), "relevance": False}


# =============================================================================
# SUPABASE UPLOAD
# =============================================================================

def upload_image_to_bucket(image_data: bytes, filename: str, mime_type: str) -> Optional[str]:
    """Upload actual image file to visual_assets bucket."""
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(image_data).hexdigest()[:8]
        ext = '.png' if 'png' in mime_type else '.jpg'
        storage_path = f"images/{timestamp}_{file_hash}_{filename.replace(' ', '_')[:30]}{ext}"
        
        # Upload to bucket
        result = supabase.storage.from_('visual_assets').upload(
            storage_path,
            image_data,
            {"content-type": mime_type}
        )
        
        print(f"         📤 Uploaded: {storage_path}")
        return storage_path
        
    except Exception as e:
        print(f"         ❌ Upload failed: {e}")
        return None


# =============================================================================
# EMBEDDING GENERATION
# =============================================================================

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=1536
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"      ⚠️ Embedding error: {e}")
        return None


# =============================================================================
# DATABASE STORAGE
# =============================================================================

def save_visual_to_database(visual_data: Dict) -> bool:
    """Save visual metadata to visuals table."""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO visuals (
                source_document, source_page, image_type, brand,
                storage_path, file_size, summary, technical_variables,
                confidence, embedding
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            visual_data['source_document'],
            visual_data.get('source_page'),
            visual_data['image_type'],
            visual_data.get('brand'),
            visual_data['storage_path'],
            visual_data.get('file_size'),
            visual_data.get('summary'),
            json.dumps(visual_data.get('technical_variables', {})),
            visual_data.get('confidence', 0.0),
            visual_data.get('embedding')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"      ❌ Database error: {e}")
        return False


# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

def get_documents_to_process(limit: int = None) -> List[Dict]:
    """Get source documents to process for visual extraction."""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Target doc types with visual content
    doc_types = [
        'Technical_Data_Sheet', 'Installation_Guide', 'Technical_Manual',
        'Product_Catalog', 'Product_Guide', 'CAD_Detail',
    ]
    
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
    
    # Filter out already processed
    cursor.execute("SELECT DISTINCT source_document FROM visuals")
    processed = {r['source_document'] for r in cursor.fetchall()}
    sources = [s for s in sources if s['source'] not in processed]
    
    cursor.close()
    conn.close()
    return sources


def process_document(source: str, doc_type: str, brand: str = None) -> Dict:
    """Process a single document - extract images, analyze, upload, store."""
    stats = {
        'source': source,
        'images_found': 0,
        'images_uploaded': 0,
        'images_relevant': 0,
        'errors': []
    }
    
    # Get PDF URL
    pdf_url = get_storage_url_for_source(source)
    if not pdf_url:
        stats['errors'].append(f"PDF not found: {source[:50]}")
        return stats
    
    # Extract images with LlamaParse
    images = extract_images_with_llamaparse(pdf_url, source)
    stats['images_found'] = len(images)
    
    if not images:
        return stats
    
    for img in images:
        try:
            # Analyze with Claude
            print(f"      🤖 Analyzing image ({img['size_kb']:.1f}KB)...")
            analysis = analyze_image_with_claude(img['base64'], img['mime_type'])
            
            if analysis.get('error'):
                stats['errors'].append(f"Claude: {analysis['error']}")
                continue
            
            # Skip non-relevant images (logos, decorative)
            if not analysis.get('relevance', False):
                print(f"         ⏭️ Skipped (not relevant): {analysis.get('image_type', 'unknown')}")
                continue
            
            stats['images_relevant'] += 1
            
            # Upload to Supabase bucket
            storage_path = upload_image_to_bucket(
                img['data'],
                img['filename'],
                img['mime_type']
            )
            
            if not storage_path:
                continue
            
            stats['images_uploaded'] += 1
            
            # Generate embedding
            embed_text = f"{analysis.get('summary', '')} {json.dumps(analysis.get('technical_variables', {}))}"
            embedding = generate_embedding(embed_text)
            
            # Save to database
            visual_data = {
                'source_document': source,
                'source_page': img.get('page', 1),
                'image_type': analysis.get('image_type', 'other'),
                'brand': analysis.get('brand') or brand,
                'storage_path': storage_path,
                'file_size': int(img['size_kb'] * 1024),
                'summary': analysis.get('summary'),
                'technical_variables': analysis.get('technical_variables', {}),
                'confidence': analysis.get('confidence', 0.0),
                'embedding': embedding,
            }
            
            save_visual_to_database(visual_data)
            print(f"         ✅ Saved: {analysis.get('image_type')} - {analysis.get('summary', '')[:50]}...")
            
        except Exception as e:
            stats['errors'].append(str(e))
    
    return stats


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline(limit: int = None, dry_run: bool = False):
    """Run the full visual ingestion pipeline."""
    print("\n" + "="*70)
    print("🔧 STRYDA VISUAL INGESTION ENGINE v2.0")
    print("   Agent #4: The Engineer - REAL IMAGE EXTRACTION")
    print("="*70)
    
    # Initialize clients
    print("\n📡 Initializing API clients...")
    init_clients()
    
    # Get documents
    print("\n📥 Discovering documents...")
    documents = get_documents_to_process(limit=limit)
    print(f"   Found {len(documents)} documents to process")
    
    if dry_run:
        print("\n⚠️ DRY RUN - No processing")
        for doc in documents[:10]:
            print(f"   • {doc['source'][:60]}... [{doc['doc_type']}]")
        return
    
    # Process
    print(f"\n🔄 Processing {len(documents)} documents...")
    
    totals = {'docs': 0, 'found': 0, 'uploaded': 0, 'relevant': 0, 'errors': []}
    
    for i, doc in enumerate(documents):
        print(f"\n[{i+1}/{len(documents)}] {doc['source'][:50]}...")
        
        stats = process_document(doc['source'], doc['doc_type'], doc.get('brand_name'))
        
        totals['docs'] += 1
        totals['found'] += stats['images_found']
        totals['uploaded'] += stats['images_uploaded']
        totals['relevant'] += stats['images_relevant']
        totals['errors'].extend(stats['errors'])
        
        print(f"   📊 Found: {stats['images_found']} | Relevant: {stats['images_relevant']} | Uploaded: {stats['images_uploaded']}")
        
        time.sleep(1)  # Rate limiting
    
    # Report
    print("\n" + "="*70)
    print("📊 INGESTION COMPLETE")
    print("="*70)
    print(f"📦 Documents: {totals['docs']}")
    print(f"🖼️ Images Found: {totals['found']}")
    print(f"✅ Relevant: {totals['relevant']}")
    print(f"📤 Uploaded: {totals['uploaded']}")
    print(f"❌ Errors: {len(totals['errors'])}")


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='STRYDA Visual Ingestion v2.0')
    parser.add_argument('--limit', type=int, help='Limit documents')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    args = parser.parse_args()
    
    run_pipeline(limit=args.limit, dry_run=args.dry_run)
