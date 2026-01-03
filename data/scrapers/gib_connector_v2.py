#!/usr/bin/env python3
"""
STRYDA Big Brain - GIB Connector v2 (Full Suite)
Complete library of GIB Winstone Wallboards technical documentation
Category C: Interiors
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# GIB Full Document Library
GIB_DOCUMENTS = [
    # === SITE GUIDE (MAIN) ===
    {
        "name": "GIB Site Guide 2024",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB0107_GIB_Site_Guide_PAGES_WEB.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Plasterboard",
        "description": "Complete installation guide for GIB plasterboard systems - 2024 Edition"
    },
    {
        "name": "GIB Performance Systems",
        "url": "https://www.gib.co.nz/assets/Site-Guide-2024/6-GIB-PERFORMANCE-SYSTEMS_GIB0107_GIB_Site_Guide_v11.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Performance",
        "description": "GIB performance systems including bracing and fire ratings"
    },
    
    # === WEATHERLINE (Rigid Air Barrier) ===
    {
        "name": "GIB Weatherline Design and Construction Manual",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Weatherline-Design-and-Construction-Manual-0522.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Weatherline",
        "description": "Design and construction manual for GIB Weatherline rigid air barrier systems"
    },
    
    # === BARRIERLINE (Intertenancy) ===
    {
        "name": "GIB Intertenancy Barrier System Manual",
        "url": "https://productspec.co.nz/media/p2enbeam/gib-intertenancy-barrier-system-manual-1222.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Barrierline",
        "description": "Installation manual for GIB Barrierline intertenancy barrier systems"
    },
    
    # === AQUALINE (Wet Areas) ===
    {
        "name": "GIB Aqualine Wet Wall System Installation",
        "url": "https://builderscrack.co.nz/blog/wp-content/uploads/2023/06/09-Approved-Documents-Supporting_Documentation_-_GIB_Aqualine_wet_wall_system_installation_instruction_Cat.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Aqualine",
        "description": "Installation instructions for GIB Aqualine wet area systems"
    },
    
    # === FIRE RATED SYSTEMS ===
    {
        "name": "GIB Fire Rated Systems",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Fire-Rated-Systems-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Fire Rated",
        "description": "Fire rated wall and ceiling system specifications"
    },
    {
        "name": "GIB Fire and Noise Rated System Tables",
        "url": "https://s.hougarden.com/ps/file/7d3f0cb6d317441bacd3fc2e5dd53879.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Fire Rated",
        "description": "Fire and noise rating tables for GIB systems"
    },
    
    # === NOISE CONTROL ===
    {
        "name": "GIB Noise Control Systems",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Noise-Control-Systems-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Noise Control",
        "description": "Acoustic solutions for walls and ceilings"
    },
    
    # === RONDO (Metal Battens) ===
    {
        "name": "GIB Rondo Wall and Ceiling Systems",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Rondo-Wall-and-Ceiling-Systems.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Rondo",
        "description": "Metal batten systems for walls and ceilings"
    },
    
    # === BRACELINE / EZYBRACE ===
    {
        "name": "GIB EzyBrace System Literature",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-EzyBrace-System-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB EzyBrace",
        "description": "Bracing system specifications for residential buildings"
    },
    
    # === FYRELINE ===
    {
        "name": "GIB Fyreline Overview",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Fyreline-Product-Overview.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Fyreline",
        "description": "GIB Fyreline fire-resistant plasterboard overview"
    }
]

GIB_METADATA = {
    "brand_name": "GIB",
    "brand_full_name": "Winstone Wallboards Ltd",
    "category_code": "C_Interiors",
    "trade": "interior_linings",
    "country": "New Zealand",
    "website": "https://www.gib.co.nz"
}


class GIBConnectorV2:
    """Full Suite connector for GIB technical documents"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/C_Interiors/Plasterboard_Linings"):
        self.output_dir = output_dir
        self.metadata = GIB_METADATA
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'STRYDA-BigBrain/1.0 (Construction Knowledge Engine)',
            'Accept': 'application/pdf,*/*'
        })
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "GIB"), exist_ok=True)
    
    def calculate_file_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
    
    def download_document(self, doc_info: Dict) -> Optional[Dict]:
        """Download a single document"""
        print(f"\n📥 Downloading: {doc_info['name']}...")
        
        try:
            response = self.session.get(doc_info['url'], timeout=120, allow_redirects=True)
            response.raise_for_status()
            
            content = response.content
            file_hash = self.calculate_file_hash(content)
            
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-')
            filename = f"{safe_name}.pdf"
            filepath = os.path.join(self.output_dir, "GIB", filename)
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            record = {
                "source": doc_info['name'],
                "brand_name": self.metadata['brand_name'],
                "category_code": self.metadata['category_code'],
                "product_family": doc_info['product_family'],
                "doc_type": doc_info['doc_type'],
                "trade": self.metadata['trade'],
                "original_url": doc_info['url'],
                "local_path": filepath,
                "file_hash": file_hash,
                "file_size_bytes": file_size,
                "description": doc_info['description'],
                "ingestion_source": "web_scrape",
                "ingested_at": datetime.now().isoformat(),
                "status": "downloaded",
                "has_diagrams": True
            }
            
            print(f"   ✅ Downloaded: {filename} ({file_size / 1024:.1f} KB)")
            return record
            
        except requests.exceptions.HTTPError as e:
            print(f"   ⚠️ HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def fetch_all_documents(self) -> List[Dict]:
        """Fetch all documents"""
        print("=" * 70)
        print("🧠 STRYDA Big Brain - GIB Full Suite Connector v2")
        print("=" * 70)
        print(f"\n📚 Brand: {self.metadata['brand_full_name']}")
        print(f"📂 Category: {self.metadata['category_code']}")
        print(f"📁 Output: {self.output_dir}/GIB/")
        print(f"\n🔍 Found {len(GIB_DOCUMENTS)} documents to fetch...")
        
        downloaded = []
        failed = []
        
        for doc_info in GIB_DOCUMENTS:
            result = self.download_document(doc_info)
            if result:
                downloaded.append(result)
            else:
                failed.append(doc_info['name'])
        
        manifest = {
            "brand": self.metadata,
            "fetch_date": datetime.now().isoformat(),
            "documents": downloaded,
            "failed": failed,
            "stats": {
                "total_attempted": len(GIB_DOCUMENTS),
                "successful": len(downloaded),
                "failed": len(failed)
            }
        }
        
        manifest_path = os.path.join(self.output_dir, "GIB", "manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n" + "=" * 70)
        print(f"📊 FETCH SUMMARY")
        print(f"=" * 70)
        print(f"   ✅ Downloaded: {len(downloaded)}")
        print(f"   ❌ Failed: {len(failed)}")
        if failed:
            print(f"   Failed docs: {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
        print(f"\n📋 Manifest saved: {manifest_path}")
        
        return downloaded


if __name__ == "__main__":
    connector = GIBConnectorV2()
    connector.fetch_all_documents()
