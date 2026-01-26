#!/usr/bin/env python3
"""
STRYDA Protocol V2.0 - RCS (Resene Construction Systems) Brain Build V2
========================================================================
Fixed version with proper HTML entity handling.
"""

import os
import re
import time
import requests
import html
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote

# Supabase Configuration
SUPABASE_URL = "https://qxqisgjhbjwvoxsjibes.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4cWlzZ2poYmp3dm94c2ppYmVzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTQ3MDY5NSwiZXhwIjoyMDc1MDQ2Njk1fQ.iOaE9PsoN1NPjDiUOlTmzcaqiRbjbdtPMNDAKGtbFsk"
BUCKET = "product-library"

RCS_BASE = "https://reseneconstruction.co.nz"
RCS_API = "https://api.reseneconstruction.co.nz"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

SUPABASE_HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
}

@dataclass
class RCSDocument:
    name: str
    url: str
    pillar_path: str
    system: str
    doc_type: str
    agent_owner: List[str]

# System configurations
SYSTEMS = {
    # Category A: Cladding
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
    # Category B: Interior
    "rockcote-earthen-natural-clay-interior-finishes": {
        "name": "Rockcote_Clay",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Clay",
        "agents": ["Product_Rep"],
    },
    "rockcote-marrakesh-lime-plaster-finishes": {
        "name": "Rockcote_Marrakesh",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Marrakesh",
        "agents": ["Product_Rep"],
    },
    "rockcote-venetian": {
        "name": "Rockcote_Venetian",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Venetian",
        "agents": ["Product_Rep"],
    },
    "rockcote-velvetina": {
        "name": "Rockcote_Velvetina",
        "path": "C_Interiors/Plaster_Finishes/Resene/Rockcote_Velvetina",
        "agents": ["Product_Rep"],
    },
    # Category C: Construction
    "integra-lightweight-concrete-flooring-system": {
        "name": "Integra_Flooring",
        "path": "A_Structure/Foundations_Fencing/Resene/Integra_Flooring",
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

def determine_doc_type(name: str) -> str:
    name_lower = name.lower()
    if 'branz' in name_lower and 'appraisal' in name_lower:
        return "BRANZ"
    elif 'fire' in name_lower:
        return "Fire_Report"
    elif 'acoustic' in name_lower:
        return "Acoustic"
    elif 'thermal' in name_lower:
        return "Thermal"
    elif 'structural' in name_lower:
        return "Structural"
    elif 'brochure' in name_lower:
        return "Brochure"
    elif 'booklet' in name_lower:
        return "Booklet"
    elif 'warranty' in name_lower:
        return "Warranty"
    elif 'specification' in name_lower:
        return "Spec"
    else:
        return "Technical"

def clean_name(name: str) -> str:
    name = html.unescape(name)
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def scrape_system(system_slug: str, system_info: dict) -> List[RCSDocument]:
    """Scrape documents from a system page"""
    docs = []
    url = f"{RCS_BASE}/system/{system_slug}/documents"
    
    print(f"\n🔍 {system_info['name']}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"   ⚠️ HTTP {response.status_code}")
            return docs
        
        content = html.unescape(response.text)  # Decode HTML entities
        
        # Find direct download links
        pattern = r'href="(https://api\.reseneconstruction\.co\.nz/api\.cfm\?method=downloadfile&uploaduuid=[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, content)
        
        for url_match, name_match in matches:
            name = clean_name(name_match)
            doc = RCSDocument(
                name=name,
                url=url_match,
                pillar_path=system_info['path'],
                system=system_info['name'],
                doc_type=determine_doc_type(name),
                agent_owner=system_info['agents'],
            )
            docs.append(doc)
        
        # Find drawing page links and get PDFs from them
        drawing_pattern = r'href="(https://reseneconstruction\.co\.nz/system/[^/]+/drawing/[^"]+)"[^>]*>([^<]+)</a>'
        drawing_matches = re.findall(drawing_pattern, content)
        
        for drawing_url, drawing_name in drawing_matches:
            drawing_name = clean_name(drawing_name)
            pdf_url = get_drawing_pdf(drawing_url)
            if pdf_url:
                doc = RCSDocument(
                    name=drawing_name,
                    url=pdf_url,
                    pillar_path=f"{system_info['path']}/CAD_Details",
                    system=system_info['name'],
                    doc_type="CAD",
                    agent_owner=["Engineer"] + system_info['agents'],
                )
                docs.append(doc)
            time.sleep(0.2)
        
        print(f"   ✅ Found {len(docs)} documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return docs

def get_drawing_pdf(drawing_url: str) -> Optional[str]:
    """Get PDF URL from drawing page"""
    try:
        response = requests.get(drawing_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        
        content = html.unescape(response.text)
        
        # Find PDF download link
        pattern = r'href="(https://api\.reseneconstruction\.co\.nz/api\.cfm\?method=downloadfile&uploaduuid=[^"]+)"'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
            
    except Exception as e:
        pass
    return None

def scrape_tds() -> List[RCSDocument]:
    """Scrape Technical Data Sheets"""
    docs = []
    url = f"{RCS_BASE}/technical-library/technical-data-sheets/"
    
    print("\n🔍 Technical Data Sheets...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return docs
        
        content = html.unescape(response.text)
        
        pattern = r'href="(https://api\.reseneconstruction\.co\.nz/download\.cfm\?download=newtds&products=\d+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, content)
        
        for url_match, name_match in matches:
            name = clean_name(name_match)
            
            # Determine path based on product type
            path = "B_Enclosure/Wall_Cladding/Resene/00_TDS"
            if any(x in name.lower() for x in ['marrakesh', 'venetian', 'velvetina', 'earthen', 'lime plaster']):
                path = "C_Interiors/Plaster_Finishes/Resene/00_TDS"
            elif any(x in name.lower() for x in ['duratherm', 'firewool']):
                path = "A_Structure/Foundations_Fencing/Resene/00_TDS"
            
            doc = RCSDocument(
                name=name,
                url=url_match,
                pillar_path=path,
                system="TDS",
                doc_type="TDS",
                agent_owner=["Inspector", "Product_Rep"],
            )
            docs.append(doc)
        
        print(f"   ✅ Found {len(docs)} TDS documents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return docs

def download_and_upload(doc: RCSDocument) -> bool:
    """Download from RCS and upload to Supabase"""
    try:
        # Download
        response = requests.get(doc.url, headers=HEADERS, timeout=60)
        if response.status_code != 200:
            return False
        content = response.content
        
        # Generate filename
        filename = f"RCS - {doc.system} - {doc.doc_type} - {doc.name}.pdf"
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', ' ', filename)
        
        # Upload to Supabase
        full_path = f"{doc.pillar_path}/{filename}"
        url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{quote(full_path, safe='/')}"
        
        headers = SUPABASE_HEADERS.copy()
        headers["Content-Type"] = "application/pdf"
        
        response = requests.post(url, headers=headers, data=content)
        if response.status_code in [200, 201]:
            return True
        elif "Duplicate" in response.text:
            response = requests.put(url, headers=headers, data=content)
            return response.status_code in [200, 201]
        
        return False
        
    except Exception as e:
        return False

def main():
    print("=" * 70)
    print("🧠 STRYDA PROTOCOL V2.0 - RCS BRAIN BUILD")
    print("=" * 70)
    
    all_docs = []
    
    # Scrape all systems
    for system_slug, system_info in SYSTEMS.items():
        docs = scrape_system(system_slug, system_info)
        all_docs.extend(docs)
        time.sleep(0.3)
    
    # Scrape TDS
    tds_docs = scrape_tds()
    all_docs.extend(tds_docs)
    
    # Add master document
    all_docs.append(RCSDocument(
        name="Generic Substrates Technical Manual (MASTER)",
        url=f"{RCS_API}/download.cfm?download=genericManual",
        pillar_path="B_Enclosure/Wall_Cladding/Resene/00_General_Resources",
        system="Master",
        doc_type="Manual",
        agent_owner=["Inspector", "Engineer", "Product_Rep"],
    ))
    
    print(f"\n📊 Total documents found: {len(all_docs)}")
    
    # Download and upload
    print("\n" + "=" * 70)
    print("📥 DOWNLOADING AND UPLOADING")
    print("=" * 70)
    
    success = 0
    failed = 0
    
    for i, doc in enumerate(all_docs):
        print(f"\n[{i+1}/{len(all_docs)}] {doc.name[:50]}...")
        if download_and_upload(doc):
            success += 1
            print(f"   ✅ → {doc.pillar_path}")
        else:
            failed += 1
            print(f"   ❌ Failed")
        time.sleep(0.3)
    
    print("\n" + "=" * 70)
    print(f"🏁 COMPLETE: {success} uploaded, {failed} failed")
    print("=" * 70)

if __name__ == "__main__":
    main()
