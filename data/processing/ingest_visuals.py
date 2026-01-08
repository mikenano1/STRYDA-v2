#!/usr/bin/env python3
"""
STRYDA Visual Ingestion Engine
===============================

Agent #4: The Engineer - Visual Extraction Pipeline

This script:
1. Scans PDFs from product_rep and inspector documents
2. Extracts images/tables using LlamaParse (Premium Mode)
3. Analyzes each visual with Claude 3.5 Sonnet
4. Stores images in Supabase Storage
5. Stores metadata + embeddings in visuals table
"""

import os
import sys
import json
import hashlib
import base64
import time
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

# LlamaParse import
try:
    from llama_parse import LlamaParse
except ImportError:
    print("❌ llama-parse not installed. Run: pip install llama-parse")
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
MIN_IMAGE_SIZE_KB = 20

# Batch size for processing
BATCH_SIZE = 5

# Claude system prompt for image analysis
CLAUDE_SYSTEM_PROMPT = """You are a Senior Structural Engineer analyzing construction documents for New Zealand building compliance.

Your task is to analyze the provided image and extract technical information.

For EACH image, determine:
1. IMAGE_TYPE: One of [span_table, detail_drawing, map, diagram, chart, specification, photo, other]
2. RELEVANCE: Is this technically useful for construction? (true/false)
3. BRAND: If visible, identify the manufacturer (e.g., "Kingspan", "GIB", "EXPOL")
4. TECHNICAL_VARIABLES: Extract key values like:
   - Spans (mm), spacings, dimensions
   - Load ratings, wind zones
   - Material grades (SG8, H3.2, etc.)
   - R-values, fire ratings
   - Installation requirements

Return ONLY valid JSON in this format:
{
    "image_type": "span_table",
    "relevance": true,
    "brand": "Kingspan",
    "summary": "Span table for QuadCore roof panels showing maximum spans for various wind zones",
    "technical_variables": {
        "max_span_mm": 6000,
        "wind_zones": ["Low", "Medium", "High", "Very High"],
        "panel_thickness_mm": [80, 100, 120],
        "support_spacing_mm": 1200
    },
    "confidence": 0.92
}

If the image is not technically relevant (decorative, logo, generic photo), return:
{
    "image_type": "other",
    "relevance": false,
    "brand": null,
    "summary": "Non-technical image - [brief description]",
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
    
    print("   ✅ Supabase client initialized")
    print("   ✅ Anthropic client initialized")
    print("   ✅ OpenAI client initialized")


# =============================================================================
# DOCUMENT DISCOVERY
# =============================================================================

def get_documents_to_process(limit: int = None, doc_types: List[str] = None) -> List[Dict]:
    """
    Get list of unique source documents to process.
    
    Filters:
    - product_rep and inspector doc_types
    - Excludes legislation (text-only)
    - Excludes already processed documents
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Default doc_types for visual extraction
    if doc_types is None:
        doc_types = [
            # Product Rep - High visual content
            'Technical_Data_Sheet', 'Installation_Guide', 'Technical_Manual',
            'Product_Catalog', 'Product_Manual', 'Product_Guide',
            'CAD_Detail', 'CAD_Files', 'Specification',
            # Inspector - Tables and figures
            'Compliance_Document', 'NZS_Standard', 'MBIE_Guidance',
            'acceptable_solution', 'verification_method',
        ]
    
    # Get distinct sources
    placeholders = ", ".join(["%s"] * len(doc_types))
    query = f"""
        SELECT DISTINCT source, doc_type, brand_name
        FROM documents 
        WHERE doc_type IN ({placeholders})
        AND source NOT LIKE '%%legislation%%'
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


def get_storage_url_for_source(source: str) -> Optional[str]:
    """
    Get the Supabase Storage URL for a source document.
    
    Searches the product-library bucket for matching PDFs.
    Source format: "Brand - Document Name"
    """
    from supabase import create_client
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        return None
    
    supabase_client = create_client(supabase_url, supabase_key)
    
    # Parse source name: "Brand - Document Name" -> ("Brand", "Document Name")
    if ' - ' in source:
        brand_raw, doc_name = source.split(' - ', 1)
    else:
        brand_raw = source
        doc_name = source
    
    # Normalize brand name to match folder structure
    brand_mapping = {
        'Abodo Wood': ('A_Structure', 'Abodo_Wood'),
        'Kingspan': ('B_Enclosure', 'Kingspan'),
        'Bradford Deep Dive': ('C_Interiors', 'Bradford'),
        'Autex Deep Dive': ('C_Interiors', 'Autex'),
        'Mammoth Deep Dive': ('C_Interiors', 'Mammoth'),
        'Asona Deep Dive': ('C_Interiors', 'Asona_Acoustics'),
    }
    
    # Try to find the brand in mapping
    category, brand_folder = None, None
    for key, (cat, folder) in brand_mapping.items():
        if key.lower() in brand_raw.lower():
            category, brand_folder = cat, folder
            break
    
    if not category:
        # Try pdfs bucket as fallback
        pdf_name = f"{doc_name}.pdf"
        try:
            signed = supabase_client.storage.from_('pdfs').create_signed_url(pdf_name, 3600)
            if signed and signed.get('signedURL'):
                return signed['signedURL']
        except:
            pass
        return None
    
    # Search through document type subfolders
    doc_type_folders = [
        'Brochures_Fact_Sheets', 'Technical_Data_Sheets', 'Guides_Manuals',
        'Profile_Drawings', 'Certificates_Warranties', 'Safety_Data_Sheets',
        'Environmental_Product_Declaration', 'Reports', 'Color_Finishes_Textures'
    ]
    
    # Build expected filename
    pdf_name = f"{doc_name}.pdf"
    
    for doc_folder in doc_type_folders:
        path = f"{category}/{brand_folder}/{doc_folder}/{pdf_name}"
        try:
            signed = supabase_client.storage.from_('product-library').create_signed_url(path, 3600)
            if signed and signed.get('signedURL'):
                print(f"      📂 Found PDF at: {path}")
                return signed['signedURL']
        except:
            continue
    
    print(f"      ⚠️ Could not find PDF for: {source[:50]}")
    return None


# =============================================================================
# LLAMAPARSE EXTRACTION
# =============================================================================

def extract_images_with_llamaparse(pdf_path_or_url: str, source_name: str) -> List[Dict]:
    """
    Use LlamaParse to extract images from a PDF.
    
    Returns list of image objects with base64 data.
    """
    print(f"   📄 Parsing: {source_name[:50]}...")
    
    try:
        # Configure LlamaParse - use auto_mode for best results
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            auto_mode=True,  # Auto-selects best parsing mode
            verbose=False,
        )
        
        # Parse document
        documents = parser.load_data(pdf_path_or_url)
        
        # LlamaParse returns markdown with embedded images
        # We need to extract image references from the markdown
        images = []
        
        for doc_idx, doc in enumerate(documents):
            content = doc.text if hasattr(doc, 'text') else str(doc)
            
            # Look for image references in markdown
            # Format: ![description](image_url) or embedded base64
            import re
            
            # Find markdown image references
            img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            matches = re.findall(img_pattern, content)
            
            for idx, (desc, url) in enumerate(matches):
                # Skip small placeholder images
                if 'placeholder' in url.lower() or len(url) < 50:
                    continue
                    
                images.append({
                    'description': desc,
                    'url': url,
                    'page': doc_idx + 1,
                    'source': source_name,
                })
            
            # Also look for base64 embedded images
            base64_pattern = r'data:image/(png|jpeg|jpg);base64,([A-Za-z0-9+/=]+)'
            base64_matches = re.findall(base64_pattern, content)
            
            for idx, (img_type, img_data) in enumerate(base64_matches):
                # Check size (base64 is ~1.33x original size)
                if len(img_data) > MIN_IMAGE_SIZE_KB * 1024 * 1.33:
                    images.append({
                        'data': img_data,
                        'type': f'image/{img_type}',
                        'page': doc_idx + 1,
                        'source': source_name,
                    })
        
        print(f"      Found {len(images)} images/references")
        return images
        
    except Exception as e:
        print(f"      ⚠️ LlamaParse error: {e}")
        return []


# =============================================================================
# CLAUDE ANALYSIS
# =============================================================================

def analyze_image_with_claude(image_base64: str, mime_type: str = "image/png") -> Dict:
    """
    Send image to Claude for structural analysis.
    
    Returns parsed JSON response.
    """
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
                        "text": "Analyze this construction document image and extract technical information. Return JSON only."
                    }
                ]
            }]
        )
        
        # Parse JSON from response
        text = response.content[0].text
        
        # Try to extract JSON from response
        if "{" in text and "}" in text:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        return {"error": "No JSON in response", "raw": text[:200]}
        
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": text[:200] if 'text' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# EMBEDDING GENERATION
# =============================================================================

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
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
# STORAGE & DATABASE
# =============================================================================

def upload_to_storage(image_data: bytes, filename: str) -> Optional[str]:
    """Upload image to visual_assets bucket."""
    try:
        # Generate unique path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(image_data).hexdigest()[:8]
        storage_path = f"images/{timestamp}_{hash_suffix}_{filename}"
        
        # Upload
        result = supabase.storage.from_('visual_assets').upload(
            storage_path,
            image_data,
            {"content-type": "image/png"}
        )
        
        return storage_path
        
    except Exception as e:
        print(f"      ⚠️ Upload error: {e}")
        return None


def save_to_database(visual_data: Dict) -> bool:
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
        print(f"      ⚠️ Database error: {e}")
        return False


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def process_document(source: str, doc_type: str, brand: str = None) -> Dict:
    """
    Process a single document through the visual pipeline.
    
    Returns stats dict.
    """
    stats = {
        'source': source,
        'images_found': 0,
        'images_processed': 0,
        'images_relevant': 0,
        'errors': []
    }
    
    # Get storage URL
    pdf_url = get_storage_url_for_source(source)
    if not pdf_url:
        # Try to construct URL from bucket
        # Format: https://{supabase_url}/storage/v1/object/public/documents/{source}.pdf
        pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{source}"
    
    # Extract images with LlamaParse
    images = extract_images_with_llamaparse(pdf_url, source)
    stats['images_found'] = len(images)
    
    for img in images:
        try:
            # Analyze with Claude
            analysis = analyze_image_with_claude(img['data'], img.get('type', 'image/png'))
            
            if 'error' in analysis:
                stats['errors'].append(analysis['error'])
                continue
            
            # Skip non-relevant images
            if not analysis.get('relevance', False):
                continue
            
            stats['images_relevant'] += 1
            
            # Upload to storage
            img_bytes = base64.b64decode(img['data'])
            storage_path = upload_to_storage(img_bytes, f"{source[:30]}_p{img.get('page', 0)}.png")
            
            if not storage_path:
                continue
            
            # Generate embedding from summary + technical vars
            embed_text = f"{analysis.get('summary', '')} {json.dumps(analysis.get('technical_variables', {}))}"
            embedding = generate_embedding(embed_text)
            
            # Save to database
            visual_data = {
                'source_document': source,
                'source_page': img.get('page'),
                'image_type': analysis.get('image_type', 'other'),
                'brand': analysis.get('brand') or brand,
                'storage_path': storage_path,
                'file_size': len(img_bytes),
                'summary': analysis.get('summary'),
                'technical_variables': analysis.get('technical_variables', {}),
                'confidence': analysis.get('confidence', 0.0),
                'embedding': embedding,
            }
            
            if save_to_database(visual_data):
                stats['images_processed'] += 1
            
        except Exception as e:
            stats['errors'].append(str(e))
    
    return stats


def run_pipeline(limit: int = None, doc_types: List[str] = None, dry_run: bool = False):
    """
    Run the full visual ingestion pipeline.
    """
    print("\n" + "="*70)
    print("🔧 STRYDA VISUAL INGESTION ENGINE")
    print("   Agent #4: The Engineer")
    print("="*70)
    
    # Initialize clients
    print("\n📡 Initializing API clients...")
    init_clients()
    
    # Get documents to process
    print("\n📥 Discovering documents...")
    documents = get_documents_to_process(limit=limit, doc_types=doc_types)
    print(f"   Found {len(documents)} documents to process")
    
    if dry_run:
        print("\n⚠️ DRY RUN - No processing will occur")
        print("\n📋 Sample documents:")
        for doc in documents[:10]:
            print(f"   • {doc['source'][:60]}... [{doc['doc_type']}]")
        return
    
    # Process documents
    print(f"\n🔄 Processing {len(documents)} documents...")
    
    total_stats = {
        'documents_processed': 0,
        'total_images_found': 0,
        'total_images_processed': 0,
        'total_images_relevant': 0,
        'errors': []
    }
    
    for i, doc in enumerate(documents):
        print(f"\n[{i+1}/{len(documents)}] Processing: {doc['source'][:50]}...")
        
        stats = process_document(doc['source'], doc['doc_type'], doc.get('brand_name'))
        
        total_stats['documents_processed'] += 1
        total_stats['total_images_found'] += stats['images_found']
        total_stats['total_images_processed'] += stats['images_processed']
        total_stats['total_images_relevant'] += stats['images_relevant']
        total_stats['errors'].extend(stats['errors'])
        
        print(f"   ✅ Found: {stats['images_found']} | Relevant: {stats['images_relevant']} | Saved: {stats['images_processed']}")
        
        # Rate limiting
        time.sleep(1)
    
    # Final report
    print("\n" + "="*70)
    print("📊 INGESTION COMPLETE")
    print("="*70)
    print(f"\n📦 Documents Processed: {total_stats['documents_processed']}")
    print(f"🖼️ Images Found: {total_stats['total_images_found']}")
    print(f"✅ Images Relevant: {total_stats['total_images_relevant']}")
    print(f"💾 Images Saved: {total_stats['total_images_processed']}")
    print(f"❌ Errors: {len(total_stats['errors'])}")
    
    if total_stats['errors']:
        print("\n⚠️ Sample Errors:")
        for err in total_stats['errors'][:5]:
            print(f"   • {err[:80]}...")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='STRYDA Visual Ingestion Engine')
    parser.add_argument('--limit', type=int, help='Limit number of documents to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no processing')
    parser.add_argument('--doc-types', nargs='+', help='Specific doc_types to process')
    args = parser.parse_args()
    
    run_pipeline(
        limit=args.limit,
        doc_types=args.doc_types,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
