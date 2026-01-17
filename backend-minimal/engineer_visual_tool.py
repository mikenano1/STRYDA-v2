#!/usr/bin/env python3
"""
STRYDA Protocol V2.0 - Engineer Agent Visual Extraction Tool
=============================================================
Implements the `get_technical_diagram` tool for the Engineer Agent.

The Engineer Agent fetches visuals, not text. This tool:
1. Retrieves technical diagrams by dwg_id or page coordinates
2. Returns cropped high-res images from bounding boxes
3. Provides sheet title and deep-link to source PDF

Author: STRYDA Brain Build Team
Version: 2.0
"""

import os
import io
import base64
import hashlib
import psycopg2
import psycopg2.extras
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF for PDF manipulation
except ImportError:
    fitz = None
    print("⚠️ PyMuPDF not installed. Visual extraction will be limited.")

try:
    from PIL import Image
except ImportError:
    Image = None
    print("⚠️ Pillow not installed. Image processing will be limited.")


# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres')

# Supabase Storage configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://qxqisgjhbjwvoxsjibes.supabase.co')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'product-library')


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class TechnicalDiagramResponse:
    """
    Response schema for get_technical_diagram tool.
    Matches Protocol V2.0 specification.
    """
    image_base64: str           # Base64 encoded cropped image
    image_url: Optional[str]    # Cached image URL (if stored)
    sheet_title: str            # From title block (e.g., "Typical Window Head Detail")
    dwg_id: str                 # Drawing ID (e.g., "NW-HOC-01702")
    source_pdf: str             # Deep link to Supabase Storage
    page_number: int
    bounding_box: List[float]   # [x1, y1, x2, y2]
    content_type: str           # 'table', 'diagram', 'image', 'drawing'
    dimensions: Dict[str, int]  # {'width': px, 'height': px}
    
    def to_dict(self) -> dict:
        return {
            'image_base64': self.image_base64,
            'image_url': self.image_url,
            'sheet_title': self.sheet_title,
            'dwg_id': self.dwg_id,
            'source_pdf': self.source_pdf,
            'page_number': self.page_number,
            'bounding_box': self.bounding_box,
            'content_type': self.content_type,
            'dimensions': self.dimensions,
        }


@dataclass
class VisualAsset:
    """
    A visual asset from the document database.
    """
    chunk_id: str
    source: str
    page: int
    dwg_id: Optional[str]
    page_title: Optional[str]
    bounding_boxes: List[Dict]
    has_table: bool
    has_diagram: bool
    content_snippet: str


# ============================================================
# DATABASE QUERIES
# ============================================================

def find_visual_by_dwg_id(dwg_id: str) -> Optional[VisualAsset]:
    """
    Find a visual asset by its drawing ID.
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    source,
                    page,
                    dwg_id,
                    page_title,
                    bounding_boxes,
                    has_table,
                    has_diagram,
                    LEFT(content, 500) as content_snippet
                FROM documents
                WHERE dwg_id = %s
                AND COALESCE(is_active, TRUE) = TRUE
                AND COALESCE(is_latest, TRUE) = TRUE
                LIMIT 1;
            """, (dwg_id,))
            
            row = cur.fetchone()
            
            if row:
                return VisualAsset(
                    chunk_id=str(row['id']),
                    source=row['source'],
                    page=row['page'],
                    dwg_id=row['dwg_id'],
                    page_title=row['page_title'],
                    bounding_boxes=row['bounding_boxes'] or [],
                    has_table=row['has_table'] or False,
                    has_diagram=row['has_diagram'] or False,
                    content_snippet=row['content_snippet'] or '',
                )
            return None
            
    finally:
        conn.close()


def search_visuals_by_query(
    query: str,
    visual_type: Optional[str] = None,
    top_k: int = 5
) -> List[VisualAsset]:
    """
    Search for visual assets related to a query.
    
    Args:
        query: Natural language search query
        visual_type: Filter by 'table', 'diagram', or None for all
        top_k: Maximum number of results
    
    Returns:
        List of VisualAsset objects with diagrams/tables
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        # Build filter based on visual type
        type_filter = ""
        if visual_type == 'table':
            type_filter = "AND COALESCE(has_table, FALSE) = TRUE"
        elif visual_type == 'diagram':
            type_filter = "AND COALESCE(has_diagram, FALSE) = TRUE"
        else:
            type_filter = "AND (COALESCE(has_table, FALSE) = TRUE OR COALESCE(has_diagram, FALSE) = TRUE)"
        
        # Simple text search with visual filter
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"""
                SELECT 
                    id,
                    source,
                    page,
                    dwg_id,
                    page_title,
                    bounding_boxes,
                    has_table,
                    has_diagram,
                    LEFT(content, 500) as content_snippet
                FROM documents
                WHERE COALESCE(is_active, TRUE) = TRUE
                AND COALESCE(is_latest, TRUE) = TRUE
                {type_filter}
                AND (
                    content ILIKE %s
                    OR page_title ILIKE %s
                    OR dwg_id ILIKE %s
                )
                ORDER BY 
                    CASE WHEN dwg_id ILIKE %s THEN 0 ELSE 1 END,
                    created_at DESC
                LIMIT %s;
            """, (
                f'%{query}%', 
                f'%{query}%', 
                f'%{query}%',
                f'%{query}%',
                top_k
            ))
            
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                results.append(VisualAsset(
                    chunk_id=str(row['id']),
                    source=row['source'],
                    page=row['page'],
                    dwg_id=row['dwg_id'],
                    page_title=row['page_title'],
                    bounding_boxes=row['bounding_boxes'] or [],
                    has_table=row['has_table'] or False,
                    has_diagram=row['has_diagram'] or False,
                    content_snippet=row['content_snippet'] or '',
                ))
            
            return results
            
    finally:
        conn.close()


# ============================================================
# PDF / IMAGE EXTRACTION
# ============================================================

def crop_image_from_pdf(
    pdf_bytes: bytes,
    page_number: int,
    bounding_box: List[float],
    dpi: int = 150
) -> Tuple[bytes, Dict[str, int]]:
    """
    Crop a region from a PDF page and return as PNG bytes.
    
    Args:
        pdf_bytes: Raw PDF file content
        page_number: 1-indexed page number
        bounding_box: [x1, y1, x2, y2] coordinates
        dpi: Resolution for rendering (default 150)
    
    Returns:
        Tuple of (PNG bytes, dimensions dict)
    """
    if not fitz:
        raise ImportError("PyMuPDF required for PDF extraction")
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    try:
        # Page number is 1-indexed, fitz is 0-indexed
        page = doc[page_number - 1]
        
        # Bounding box: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bounding_box
        rect = fitz.Rect(x1, y1, x2, y2)
        
        # Render the cropped region
        mat = fitz.Matrix(dpi / 72, dpi / 72)  # Scale for DPI
        clip = rect
        pix = page.get_pixmap(matrix=mat, clip=clip)
        
        # Convert to PNG bytes
        png_bytes = pix.tobytes("png")
        
        dimensions = {
            'width': pix.width,
            'height': pix.height,
        }
        
        return png_bytes, dimensions
        
    finally:
        doc.close()


def get_full_page_image(
    pdf_bytes: bytes,
    page_number: int,
    dpi: int = 150
) -> Tuple[bytes, Dict[str, int]]:
    """
    Render a full PDF page as an image.
    
    Args:
        pdf_bytes: Raw PDF file content
        page_number: 1-indexed page number
        dpi: Resolution for rendering
    
    Returns:
        Tuple of (PNG bytes, dimensions dict)
    """
    if not fitz:
        raise ImportError("PyMuPDF required for PDF extraction")
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    try:
        page = doc[page_number - 1]
        
        # Render full page
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        png_bytes = pix.tobytes("png")
        
        dimensions = {
            'width': pix.width,
            'height': pix.height,
        }
        
        return png_bytes, dimensions
        
    finally:
        doc.close()


# ============================================================
# SUPABASE STORAGE INTEGRATION
# ============================================================

def download_pdf_from_supabase(source_path: str) -> Optional[bytes]:
    """
    Download a PDF from Supabase Storage.
    
    Args:
        source_path: Path within the bucket (e.g., "B_Enclosure/Cladding/Nu-Wall/NW-HOC-00702.pdf")
    
    Returns:
        PDF file bytes or None if not found
    """
    import requests
    
    # Build public URL
    url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{source_path}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠️ Failed to download PDF: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Error downloading PDF: {e}")
        return None


def build_deep_link(source: str, page: int) -> str:
    """
    Build a deep link to a specific page in Supabase Storage.
    """
    source_encoded = source.replace(' ', '%20')
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{source_encoded}#page={page}"


# ============================================================
# MAIN TOOL: get_technical_diagram
# ============================================================

def get_technical_diagram(
    dwg_id: Optional[str] = None,
    query: Optional[str] = None,
    page_source: Optional[str] = None,
    page_number: Optional[int] = None,
    box_index: int = 0,
    full_page: bool = False,
    dpi: int = 150,
) -> Optional[TechnicalDiagramResponse]:
    """
    Engineer Agent's primary tool for visual extraction.
    
    This tool retrieves technical diagrams, tables, and drawings from the
    STRYDA document library. It returns cropped high-res images suitable
    for on-site reference.
    
    Usage patterns:
    1. By Drawing ID: get_technical_diagram(dwg_id="NW-HOC-00702")
    2. By Search: get_technical_diagram(query="window head flashing")
    3. By Page: get_technical_diagram(page_source="Nu-Wall/...", page_number=1)
    
    Args:
        dwg_id: Specific drawing ID to retrieve (e.g., "NW-HOC-00702")
        query: Natural language query to search for diagrams
        page_source: Source document path for direct page access
        page_number: Page number within source document
        box_index: Which bounding box to extract (default 0 = first)
        full_page: If True, return full page instead of cropped box
        dpi: Image resolution (default 150 for balance of quality/size)
    
    Returns:
        TechnicalDiagramResponse with image and metadata, or None if not found
    """
    visual_asset = None
    
    # Strategy 1: Find by drawing ID
    if dwg_id:
        visual_asset = find_visual_by_dwg_id(dwg_id)
        if not visual_asset:
            print(f"⚠️ Drawing ID '{dwg_id}' not found in database")
    
    # Strategy 2: Search by query
    if not visual_asset and query:
        results = search_visuals_by_query(query, visual_type='diagram', top_k=1)
        if results:
            visual_asset = results[0]
    
    # Strategy 3: Direct page lookup
    if not visual_asset and page_source and page_number:
        # Query database for this specific page
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, source, page, dwg_id, page_title,
                        bounding_boxes, has_table, has_diagram,
                        LEFT(content, 500) as content_snippet
                    FROM documents
                    WHERE source = %s AND page = %s
                    AND COALESCE(is_active, TRUE) = TRUE
                    LIMIT 1;
                """, (page_source, page_number))
                
                row = cur.fetchone()
                if row:
                    visual_asset = VisualAsset(
                        chunk_id=str(row['id']),
                        source=row['source'],
                        page=row['page'],
                        dwg_id=row['dwg_id'],
                        page_title=row['page_title'],
                        bounding_boxes=row['bounding_boxes'] or [],
                        has_table=row['has_table'] or False,
                        has_diagram=row['has_diagram'] or False,
                        content_snippet=row['content_snippet'] or '',
                    )
        finally:
            conn.close()
    
    if not visual_asset:
        print("⚠️ No visual asset found for the given criteria")
        return None
    
    # Download the source PDF
    pdf_bytes = download_pdf_from_supabase(visual_asset.source)
    
    if not pdf_bytes:
        print(f"⚠️ Could not download source PDF: {visual_asset.source}")
        return None
    
    # Determine bounding box to use
    bounding_box = None
    content_type = 'diagram'
    
    if visual_asset.bounding_boxes and not full_page:
        if box_index < len(visual_asset.bounding_boxes):
            box_data = visual_asset.bounding_boxes[box_index]
            if isinstance(box_data, dict):
                bounding_box = box_data.get('coords', box_data.get('bounding_box'))
                content_type = box_data.get('type', 'diagram')
            elif isinstance(box_data, list):
                bounding_box = box_data
    
    # Extract image
    try:
        if full_page or not bounding_box:
            # Full page extraction
            png_bytes, dimensions = get_full_page_image(
                pdf_bytes, 
                visual_asset.page, 
                dpi=dpi
            )
            bounding_box = bounding_box or [0, 0, 0, 0]  # Placeholder
        else:
            # Cropped extraction
            png_bytes, dimensions = crop_image_from_pdf(
                pdf_bytes,
                visual_asset.page,
                bounding_box,
                dpi=dpi
            )
    except Exception as e:
        print(f"⚠️ Image extraction failed: {e}")
        return None
    
    # Encode image as base64
    image_base64 = base64.b64encode(png_bytes).decode('utf-8')
    
    # Build response
    return TechnicalDiagramResponse(
        image_base64=image_base64,
        image_url=None,  # Would be set if we cache to Supabase
        sheet_title=visual_asset.page_title or visual_asset.source,
        dwg_id=visual_asset.dwg_id or 'UNKNOWN',
        source_pdf=build_deep_link(visual_asset.source, visual_asset.page),
        page_number=visual_asset.page,
        bounding_box=bounding_box or [0, 0, 0, 0],
        content_type=content_type,
        dimensions=dimensions,
    )


def list_available_drawings(
    brand: Optional[str] = None,
    visual_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    List all available technical drawings in the database.
    Useful for discovering what diagrams are available.
    
    Args:
        brand: Filter by brand name (e.g., "Nu-Wall", "James Hardie")
        visual_type: Filter by 'table', 'diagram', or None for all
        limit: Maximum results to return
    
    Returns:
        List of drawing summaries with dwg_id, title, and source
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    
    try:
        # Build filters
        filters = ["COALESCE(is_active, TRUE) = TRUE"]
        params = []
        
        if brand:
            filters.append("source ILIKE %s")
            params.append(f'%{brand}%')
        
        if visual_type == 'table':
            filters.append("COALESCE(has_table, FALSE) = TRUE")
        elif visual_type == 'diagram':
            filters.append("COALESCE(has_diagram, FALSE) = TRUE")
        else:
            filters.append("(COALESCE(has_table, FALSE) = TRUE OR COALESCE(has_diagram, FALSE) = TRUE)")
        
        # Only include docs with dwg_id
        filters.append("dwg_id IS NOT NULL")
        
        where_clause = " AND ".join(filters)
        params.append(limit)
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(f"""
                SELECT DISTINCT ON (dwg_id)
                    dwg_id,
                    page_title,
                    source,
                    page,
                    has_table,
                    has_diagram
                FROM documents
                WHERE {where_clause}
                ORDER BY dwg_id, created_at DESC
                LIMIT %s;
            """, tuple(params))
            
            rows = cur.fetchall()
            
            return [
                {
                    'dwg_id': row['dwg_id'],
                    'title': row['page_title'] or row['source'],
                    'source': row['source'],
                    'page': row['page'],
                    'has_table': row['has_table'],
                    'has_diagram': row['has_diagram'],
                }
                for row in rows
            ]
            
    finally:
        conn.close()


# ============================================================
# VALIDATION
# ============================================================

def validate_engineer_tool():
    """
    Validate the Engineer's visual extraction tool.
    """
    print("=" * 70)
    print("PROTOCOL V2.0 - ENGINEER TOOL VALIDATION")
    print("=" * 70)
    
    # Test 1: List available drawings
    print("\n1️⃣ Listing available drawings...")
    drawings = list_available_drawings(limit=5)
    print(f"   Found {len(drawings)} drawings with dwg_id")
    for d in drawings[:3]:
        print(f"   - {d['dwg_id']}: {d['title'][:50]}...")
    
    # Test 2: Search by query (no download)
    print("\n2️⃣ Testing visual search...")
    results = search_visuals_by_query("window detail", top_k=3)
    print(f"   Found {len(results)} results for 'window detail'")
    for r in results[:2]:
        print(f"   - {r.source} (Page {r.page})")
        print(f"     dwg_id: {r.dwg_id}, has_diagram: {r.has_diagram}")
    
    # Test 3: Database connectivity check
    print("\n3️⃣ Checking database for visual metadata...")
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE has_diagram = TRUE) as diagrams,
                    COUNT(*) FILTER (WHERE has_table = TRUE) as tables,
                    COUNT(*) FILTER (WHERE dwg_id IS NOT NULL) as with_dwg_id,
                    COUNT(*) FILTER (WHERE bounding_boxes IS NOT NULL) as with_bbox
                FROM documents;
            """)
            stats = cur.fetchone()
            print(f"   📊 Visual Stats:")
            print(f"      - Diagrams: {stats[0]}")
            print(f"      - Tables: {stats[1]}")
            print(f"      - With dwg_id: {stats[2]}")
            print(f"      - With bounding_boxes: {stats[3]}")
    finally:
        conn.close()
    
    print("\n" + "=" * 70)
    print("✅ ENGINEER TOOL VALIDATION COMPLETE")
    print("=" * 70)
    print("\nNote: Full image extraction requires PDF download from Supabase.")
    print("Run with a specific dwg_id to test full extraction pipeline.")


if __name__ == '__main__':
    validate_engineer_tool()
