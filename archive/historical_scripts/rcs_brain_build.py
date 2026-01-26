#!/usr/bin/env python3
"""
STRYDA Protocol V2.0 - RCS (Resene Construction Systems) Brain Build
=====================================================================
Automated Smart Ingest following the EO DIRECTIVE.

THREE PILLARS:
- Category A: Cladding Systems → /B_Enclosure/Wall_Cladding/Resene/
- Category B: Interior Systems → /C_Interiors/Plaster_Finishes/Resene/
- Category C: Construction Systems → /A_Structure/Foundations_Fencing/Resene/

Author: STRYDA Brain Build Team
Version: 2.0
"""

import os
import re
import time
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, quote
import hashlib

# Supabase Configuration
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
BUCKET = "product-library"

# RCS Base URL
RCS_BASE = "https://reseneconstruction.co.nz"
RCS_API = "https://api.reseneconstruction.co.nz"

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/pdf,*/*",
}

SUPABASE_HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
}

# =============================================================================
# DOCUMENT CATEGORIZATION (THREE PILLARS)
# =============================================================================

@dataclass
class RCSDocument:
    """RCS document with Protocol V2.0 metadata"""
    name: str
    url: str
    category: str           # A, B, or C
    pillar_path: str        # Supabase destination folder
    system: str             # Product system name
    doc_type: str           # BRANZ, CAD, TDS, Brochure, etc.
    agent_owner: List[str]  # Inspector, Engineer, Product_Rep
    hierarchy_level: int    # Always 3 for manufacturer
    dwg_id: Optional[str]   # Drawing ID if applicable

# Category A: Cladding Systems
CATEGORY_A_SYSTEMS = {
    "integra-lightweight-concrete-facade-system": {
        "name": "Integra_Facade",
        "path": "B_Enclosure/Wall_Cladding/Resene/Integra_Facade",
        "agents": ["Inspector", "Engineer"],
    },
    "integra-lightweight-concrete-firewall-solutions": {
        "name": "Integra_Firewall",
        "path": "B_Enclosure/Wall_Cladding/Resene/Integra_Firewall",
        "agents": ["Inspector", "Engineer"],
    },
    "graphex-insulated-facade-system": {
        "name": "Graphex_Facade",
        "path": "B_Enclosure/Wall_Cladding/Resene/Graphex_Facade",
        "agents": ["Inspector", "Engineer"],
    },
    "masonry-overlay-system-xtherm-blue": {
        "name": "XTherm_Blue",
        "path": "B_Enclosure/Wall_Cladding/Resene/XTherm_Blue",
        "agents": ["Inspector", "Engineer"],
    },
    "graphex-masonry-overlay-system": {
        "name": "Graphex_Masonry",
        "path": "B_Enclosure/Wall_Cladding/Resene/Graphex_Masonry",
        "agents": ["Inspector", "Engineer"],
    },
    "masonry-render-system": {
        "name": "Masonry_Render",
        "path": "B_Enclosure/Wall_Cladding/Resene/Masonry_Render",
        "agents": ["Inspector"],
    },
    "masonry-render-system-over-brick": {
        "name": "Masonry_Render_Brick",
        "path": "B_Enclosure/Wall_Cladding/Resene/Masonry_Render",
        "agents": ["Inspector"],
    },
    "monotek-finishing-system": {
        "name": "Monotek",
        "path": "B_Enclosure/Wall_Cladding/Resene/Monotek",
        "agents": ["Inspector", "Engineer"],
    },
    "icf-solid-render-system": {
        "name": "ICF_Render",
        "path": "B_Enclosure/Wall_Cladding/Resene/ICF_Render",
        "agents": ["Inspector"],
    },
    "seismolock-grc-restrengthening-system": {
        "name": "Seismolock",
        "path": "B_Enclosure/Wall_Cladding/Resene/Seismolock",
        "agents": ["Inspector", "Engineer"],
    },
}

# Category B: Interior Systems
CATEGORY_B_SYSTEMS = {
    "rockcote-earthen-natural-clay-interior-finishes": {
        "name": "Rockcote_Clay_Decor",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Clay",
        "agents": ["Product_Rep"],
    },
    "rockcote-marrakesh-lime-plaster-finishes": {
        "name": "Rockcote_Marrakesh",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Marrakesh",
        "agents": ["Product_Rep"],
    },
    "rockcote-otsumigaki-japanese-clay-lime-finishes": {
        "name": "Rockcote_Otsumigaki",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Otsumigaki",
        "agents": ["Product_Rep"],
    },
    "rockcote-velvetina": {
        "name": "Rockcote_Velvetina",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Velvetina",
        "agents": ["Product_Rep"],
    },
    "rockcote-venetian": {
        "name": "Rockcote_Venetian",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Venetian",
        "agents": ["Product_Rep"],
    },
    "marblestone-italian-lime-interior-finishes": {
        "name": "Marblestone",
        "path": "C_Interiors/Plaster_Finishes/Resene/Marblestone",
        "agents": ["Product_Rep"],
    },
    "concrete-finishes": {
        "name": "Concrete_Finishes",
        "path": "C_Interiors/Plaster_Finishes/Resene/Concrete_Finishes",
        "agents": ["Product_Rep"],
    },
    "ezyplast-interior-gypsum-hardwall-finish": {
        "name": "EzyPlast",
        "path": "C_Interiors/Plaster_Finishes/Resene/EzyPlast",
        "agents": ["Product_Rep"],
    },
}

# Category C: Construction Systems
CATEGORY_C_SYSTEMS = {
    "integra-lightweight-concrete-flooring-system": {
        "name": "Integra_Flooring",
        "path": "A_Structure/Foundations_Fencing/Resene/Integra_Flooring",
        "agents": ["Inspector", "Engineer"],
    },
    "integra-lightweight-concrete-intertenancy-system": {
        "name": "Integra_Intertenancy",
        "path": "A_Structure/Foundations_Fencing/Resene/Integra_Intertenancy",
        "agents": ["Inspector", "Engineer"],
    },
    "integra-lightweight-concrete-fencing-system": {
        "name": "Integra_Fencing",
        "path": "A_Structure/Foundations_Fencing/Resene/Integra_Fencing",
        "agents": ["Inspector"],
    },
    "insulated-foundation-system": {
        "name": "DuraTherm_Foundation",
        "path": "A_Structure/Foundations_Fencing/Resene/DuraTherm_Foundation",
        "agents": ["Inspector", "Engineer"],
    },
    "firewool": {
        "name": "FireWool",
        "path": "A_Structure/Foundations_Fencing/Resene/FireWool",
        "agents": ["Inspector"],
    },
}

# TDS products mapping
TDS_PRODUCTS = {
    # Cladding related
    "Integra Panel 50mm": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Integra"),
    "Integra Panel 75mm": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Integra"),
    "Graphex 50mm": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Graphex"),
    "XTherm Blue": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "XTherm"),
    "XTherm Gold": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "XTherm"),
    "DuraTherm Blue": ("A_Structure/Foundations_Fencing/Resene/00_TDS", "DuraTherm"),
    "DuraTherm Gold": ("A_Structure/Foundations_Fencing/Resene/00_TDS", "DuraTherm"),
    "Mono Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "Quick Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "Polymer Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "Seismolock Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "CoolPlast Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "RMaxx Render": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Render"),
    "Hydroplast": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Accessories"),
    "AAC Adhesive": ("B_Enclosure/Wall_Cladding/Resene/00_TDS", "Adhesives"),
    "Firewool": ("A_Structure/Foundations_Fencing/Resene/00_TDS", "FireWool"),
    # Interior related
    "Marrakesh": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Marrakesh"),
    "Venetian": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Venetian"),
    "Velvetina": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Velvetina"),
    "Earthen": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Earthen"),
    "Otsumigaki": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Otsumigaki"),
    "Lime Plaster": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Lime"),
    "Classico Texture": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Texture"),
    "Torino Sands": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Texture"),
    "Spectra Texture": ("C_Interiors/Plaster_Finishes/Resene/00_TDS", "Texture"),
}

# =============================================================================
# SCRAPER FUNCTIONS
# =============================================================================

def clean_filename(name: str) -> str:
    """Clean filename for storage"""
    # Remove special characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores for some parts
    name = name.strip()
    return name

def extract_dwg_id(text: str) -> Optional[str]:
    """Extract drawing ID from text (e.g., 84.02.00)"""
    patterns = [
        r'(\d{2}\.\d{2}\.\d{2})',  # 84.02.00 format
        r'([A-Z]{2,4}-\d{3,5})',    # Detail number format
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def determine_doc_type(name: str, url: str) -> str:
    """Determine document type from name/URL"""
    name_lower = name.lower()
    url_lower = url.lower()
    
    if 'branz' in name_lower or 'appraisal' in name_lower:
        return "BRANZ_Appraisal"
    elif 'fire' in name_lower and 'report' in name_lower:
        return "Fire_Report"
    elif 'acoustic' in name_lower:
        return "Acoustic_Report"
    elif 'thermal' in name_lower:
        return "Thermal_Report"
    elif 'structural' in name_lower or 'st0' in name_lower or 'st1' in name_lower:
        return "Structural_Report"
    elif 'drawing' in url_lower or 'panel' in name_lower and 'cavity' in name_lower:
        return "CAD_Drawing"
    elif 'brochure' in name_lower:
        return "Brochure"
    elif 'booklet' in name_lower:
        return "Technical_Booklet"
    elif 'warranty' in name_lower:
        return "Warranty"
    elif 'care' in name_lower or 'maintenance' in name_lower:
        return "Care_Guide"
    elif 'specification' in url_lower:
        return "Specification"
    elif 'tds' in url_lower or 'technical-data-sheet' in url_lower:
        return "TDS"
    elif 'voc' in name_lower:
        return "VOC_Declaration"
    elif 'epd' in name_lower or 'environmental' in name_lower:
        return "EPD"
    else:
        return "Technical_Document"

def scrape_system_documents(system_slug: str, system_info: dict, category: str) -> List[RCSDocument]:
    """Scrape all documents from a system page"""
    documents = []
    base_url = f"{RCS_BASE}/system/{system_slug}/documents"
    
    print(f"\n🔍 Scraping: {system_info['name']}")
    
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"   ⚠️ Failed to fetch {base_url}: {response.status_code}")
            return documents
        
        html = response.text
        
        # Extract direct download links
        # Pattern for API downloads
        api_pattern = r'href="(https://api\.reseneconstruction\.co\.nz/api\.cfm\?method=downloadfile&uploaduuid=[^"]+)"[^>]*>([^<]+)'
        for match in re.finditer(api_pattern, html):
            url, name = match.groups()
            name = name.strip()
            
            doc = RCSDocument(
                name=name,
                url=url,
                category=category,
                pillar_path=system_info['path'],
                system=system_info['name'],
                doc_type=determine_doc_type(name, url),
                agent_owner=system_info['agents'],
                hierarchy_level=3,
                dwg_id=extract_dwg_id(name),
            )
            documents.append(doc)
        
        # Pattern for drawing pages (need to navigate)
        drawing_pattern = r'href="(/system/[^/]+/drawing/[^"]+)"[^>]*>([^<]+)'
        for match in re.finditer(drawing_pattern, html):
            drawing_path, name = match.groups()
            name = name.strip()
            
            # Get the actual PDF from the drawing page
            drawing_url = f"{RCS_BASE}{drawing_path}"
            pdf_url = get_drawing_pdf_url(drawing_url)
            
            if pdf_url:
                doc = RCSDocument(
                    name=name,
                    url=pdf_url,
                    category=category,
                    pillar_path=f"{system_info['path']}/CAD_Details",
                    system=system_info['name'],
                    doc_type="CAD_Drawing",
                    agent_owner=["Engineer"] + system_info['agents'],
                    hierarchy_level=3,
                    dwg_id=extract_dwg_id(name),
                )
                documents.append(doc)
        
        print(f"   ✅ Found {len(documents)} documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return documents

def get_drawing_pdf_url(drawing_page_url: str) -> Optional[str]:
    """Get the actual PDF URL from a drawing page"""
    try:
        response = requests.get(drawing_page_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Look for PDF download link
        patterns = [
            r'href="(https://api\.reseneconstruction\.co\.nz/[^"]+\.pdf[^"]*)"',
            r'href="(https://api\.reseneconstruction\.co\.nz/api\.cfm\?method=downloadfile[^"]+)"',
            r'href="([^"]+download[^"]*\.pdf[^"]*)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                url = match.group(1)
                if not url.startswith('http'):
                    url = urljoin(RCS_BASE, url)
                return url
        
        # Try to find any downloadable content
        download_pattern = r'href="([^"]+)"[^>]*class="[^"]*download[^"]*"'
        match = re.search(download_pattern, html, re.IGNORECASE)
        if match:
            return urljoin(RCS_BASE, match.group(1))
            
    except Exception as e:
        print(f"      ⚠️ Error fetching drawing: {e}")
    
    return None

def scrape_tds_page() -> List[RCSDocument]:
    """Scrape all Technical Data Sheets"""
    documents = []
    tds_url = f"{RCS_BASE}/technical-library/technical-data-sheets/"
    
    print("\n🔍 Scraping Technical Data Sheets...")
    
    try:
        response = requests.get(tds_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"   ⚠️ Failed to fetch TDS page: {response.status_code}")
            return documents
        
        html = response.text
        
        # Extract TDS links
        pattern = r'href="(https://api\.reseneconstruction\.co\.nz/download\.cfm\?download=newtds&products=\d+)"[^>]*>([^<]+)'
        for match in re.finditer(pattern, html):
            url, name = match.groups()
            name = name.strip()
            
            # Determine category based on product name
            dest_path = "B_Enclosure/Wall_Cladding/Resene/00_TDS"  # Default
            for product_key, (path, _) in TDS_PRODUCTS.items():
                if product_key.lower() in name.lower():
                    dest_path = path
                    break
            
            doc = RCSDocument(
                name=name,
                url=url,
                category="TDS",
                pillar_path=dest_path,
                system="TDS",
                doc_type="TDS",
                agent_owner=["Inspector", "Product_Rep"],
                hierarchy_level=3,
                dwg_id=None,
            )
            documents.append(doc)
        
        print(f"   ✅ Found {len(documents)} TDS documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return documents

def scrape_generic_manual() -> Optional[RCSDocument]:
    """Scrape the Generic Substrates Technical Manual (Master Document)"""
    print("\n🔍 Getting Generic Substrates Manual (MASTER DOCUMENT)...")
    
    url = f"{RCS_API}/download.cfm?download=genericManual"
    
    return RCSDocument(
        name="RCS - Generic Substrates Technical Manual (MASTER)",
        url=url,
        category="A",
        pillar_path="B_Enclosure/Wall_Cladding/Resene/00_General_Resources",
        system="Master",
        doc_type="Master_Manual",
        agent_owner=["Inspector", "Engineer", "Product_Rep"],
        hierarchy_level=3,
        dwg_id=None,
    )

# =============================================================================
# DOWNLOAD AND UPLOAD FUNCTIONS
# =============================================================================

def download_document(doc: RCSDocument) -> Optional[bytes]:
    """Download a document from RCS"""
    try:
        response = requests.get(doc.url, headers=HEADERS, timeout=60, allow_redirects=True)
        if response.status_code == 200:
            return response.content
        else:
            print(f"      ⚠️ Download failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"      ❌ Download error: {e}")
        return None

def generate_protocol_filename(doc: RCSDocument) -> str:
    """Generate Protocol V2.0 compliant filename"""
    # Format: RCS - {System} - {DocType} - {Name}.pdf
    
    # Clean the name
    clean_name = clean_filename(doc.name)
    
    # Remove redundant prefixes
    for prefix in ['BRANZ ', 'RCS ', 'Resene ', 'Rockcote ']:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
    
    # Build filename
    if doc.doc_type == "CAD_Drawing":
        if doc.dwg_id:
            filename = f"RCS - {doc.system} - CAD - {doc.dwg_id} - {clean_name}.pdf"
        else:
            filename = f"RCS - {doc.system} - CAD - {clean_name}.pdf"
    elif doc.doc_type == "BRANZ_Appraisal":
        filename = f"RCS - {doc.system} - BRANZ - {clean_name}.pdf"
    elif doc.doc_type == "TDS":
        filename = f"RCS - TDS - {clean_name}.pdf"
    else:
        filename = f"RCS - {doc.system} - {clean_name}.pdf"
    
    # Clean up any double spaces or dashes
    filename = re.sub(r'\s+', ' ', filename)
    filename = re.sub(r'-\s*-', '-', filename)
    filename = re.sub(r'\s*-\s*\.pdf', '.pdf', filename)
    
    return filename

def upload_to_supabase(content: bytes, dest_path: str, filename: str) -> bool:
    """Upload file to Supabase Storage"""
    full_path = f"{dest_path}/{filename}"
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{quote(full_path, safe='/')}"
    
    headers = SUPABASE_HEADERS.copy()
    headers["Content-Type"] = "application/pdf"
    
    try:
        # Try to upload
        response = requests.post(url, headers=headers, data=content)
        
        if response.status_code in [200, 201]:
            return True
        elif "Duplicate" in response.text or "already exists" in response.text.lower():
            # Update existing
            response = requests.put(url, headers=headers, data=content)
            return response.status_code in [200, 201]
        else:
            print(f"      ⚠️ Upload failed: {response.status_code} - {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"      ❌ Upload error: {e}")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def execute_rcs_brain_build():
    """Execute the full RCS Brain Build"""
    print("=" * 70)
    print("🧠 STRYDA PROTOCOL V2.0 - RCS BRAIN BUILD")
    print("=" * 70)
    
    all_documents = []
    stats = {
        "category_a": 0,
        "category_b": 0,
        "category_c": 0,
        "tds": 0,
        "downloaded": 0,
        "uploaded": 0,
        "failed": 0,
    }
    
    # Step 1: Scrape Category A (Cladding Systems)
    print("\n" + "=" * 70)
    print("📦 CATEGORY A: CLADDING SYSTEMS")
    print("   Target: /B_Enclosure/Wall_Cladding/Resene/")
    print("=" * 70)
    
    for system_slug, system_info in CATEGORY_A_SYSTEMS.items():
        docs = scrape_system_documents(system_slug, system_info, "A")
        all_documents.extend(docs)
        stats["category_a"] += len(docs)
        time.sleep(0.5)  # Rate limiting
    
    # Step 2: Scrape Category B (Interior Systems)
    print("\n" + "=" * 70)
    print("📦 CATEGORY B: INTERIOR SYSTEMS")
    print("   Target: /C_Interiors/Plaster_Finishes/Resene/")
    print("=" * 70)
    
    for system_slug, system_info in CATEGORY_B_SYSTEMS.items():
        docs = scrape_system_documents(system_slug, system_info, "B")
        all_documents.extend(docs)
        stats["category_b"] += len(docs)
        time.sleep(0.5)
    
    # Step 3: Scrape Category C (Construction Systems)
    print("\n" + "=" * 70)
    print("📦 CATEGORY C: CONSTRUCTION SYSTEMS")
    print("   Target: /A_Structure/Foundations_Fencing/Resene/")
    print("=" * 70)
    
    for system_slug, system_info in CATEGORY_C_SYSTEMS.items():
        docs = scrape_system_documents(system_slug, system_info, "C")
        all_documents.extend(docs)
        stats["category_c"] += len(docs)
        time.sleep(0.5)
    
    # Step 4: Scrape TDS
    tds_docs = scrape_tds_page()
    all_documents.extend(tds_docs)
    stats["tds"] = len(tds_docs)
    
    # Step 5: Get Master Document
    master_doc = scrape_generic_manual()
    if master_doc:
        all_documents.append(master_doc)
    
    print("\n" + "=" * 70)
    print(f"📊 SCRAPING COMPLETE: {len(all_documents)} documents found")
    print(f"   Category A (Cladding): {stats['category_a']}")
    print(f"   Category B (Interior): {stats['category_b']}")
    print(f"   Category C (Construction): {stats['category_c']}")
    print(f"   TDS: {stats['tds']}")
    print("=" * 70)
    
    # Step 6: Download and Upload
    print("\n" + "=" * 70)
    print("📥 DOWNLOADING AND UPLOADING TO SUPABASE")
    print("=" * 70)
    
    for i, doc in enumerate(all_documents):
        print(f"\n[{i+1}/{len(all_documents)}] {doc.name[:50]}...")
        
        # Download
        content = download_document(doc)
        if not content:
            stats["failed"] += 1
            continue
        stats["downloaded"] += 1
        
        # Generate filename
        filename = generate_protocol_filename(doc)
        
        # Upload
        if upload_to_supabase(content, doc.pillar_path, filename):
            stats["uploaded"] += 1
            print(f"   ✅ → {doc.pillar_path}/{filename}")
        else:
            stats["failed"] += 1
        
        time.sleep(0.3)  # Rate limiting
    
    # Final Report
    print("\n" + "=" * 70)
    print("🏁 RCS BRAIN BUILD COMPLETE")
    print("=" * 70)
    print(f"\n📊 FINAL STATISTICS:")
    print(f"   Total documents found: {len(all_documents)}")
    print(f"   Successfully downloaded: {stats['downloaded']}")
    print(f"   Successfully uploaded: {stats['uploaded']}")
    print(f"   Failed: {stats['failed']}")
    print(f"\n📁 PILLAR DISTRIBUTION:")
    print(f"   Category A (Cladding): {stats['category_a']} docs")
    print(f"   Category B (Interior): {stats['category_b']} docs")
    print(f"   Category C (Construction): {stats['category_c']} docs")
    print(f"   TDS Documents: {stats['tds']} docs")
    print("=" * 70)
    
    return stats

if __name__ == "__main__":
    execute_rcs_brain_build()
