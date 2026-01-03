#!/usr/bin/env python3
"""
STRYDA Big Brain - James Hardie Connector v2 (Full Suite)
Complete library of James Hardie NZ technical documentation
Category B: Enclosure
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

# James Hardie Full Document Library (NZ Versions)
HARDIE_DOCUMENTS = [
    # === LINEA WEATHERBOARD ===
    {
        "name": "Linea Weatherboard Direct Fix Technical Specification",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Linea-Weatherboard-Direct-Fix-Technical-Specification.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Linea Weatherboard",
        "description": "Technical specification for Linea Weatherboard direct fix installation"
    },
    {
        "name": "Linea Weatherboard Installation Guide Apr23",
        "url": "https://agnew-cdn.n2erp.co.nz/cdn/images/productdocument/LineaWeatherboardsInstallationGuideApr23.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Linea Weatherboard",
        "description": "Practical installation guide for Linea Weatherboard"
    },
    
    # === STRIA CLADDING ===
    {
        "name": "Stria Cladding Vertical Installation Technical Specification",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Stria-Cladding-Vertical-Installation-Technical-Specification.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Stria Cladding",
        "description": "Vertical installation specification for Stria Cladding panels"
    },
    {
        "name": "Stria Cladding Vertical 40mm Structural Cavity Batten",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Stria-Cladding-Vertical-40mm-Strutural-Cavity-Batten-Installation-Manual.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Stria Cladding",
        "description": "Installation manual for Stria with structural cavity battens"
    },
    
    # === OBLIQUE WEATHERBOARD ===
    {
        "name": "Hardie Oblique and Stria Cladding Vertical Installation Guide",
        "url": "https://www.csparchitectural.com.au/wp-content/uploads/2024/06/Hardie_Oblique_and_Stria_Cladding_Installation_Guide_Vertical_May24.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Oblique Weatherboard",
        "description": "Combined installation guide for Oblique and Stria vertical cladding"
    },
    
    # === RAB BOARD / HomeRAB ===
    {
        "name": "HomeRAB Pre-Cladding and RAB Board Installation Manual",
        "url": "https://www.jameshardie.co.nz/web/assets/general/HomeRAB-Pre-Cladding-and-RAB-Board-Installation-Manual.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "RAB Board",
        "description": "Complete installation manual for HomeRAB and RAB Board rigid air barrier"
    },
    {
        "name": "RAB Board Installation Guide Legacy",
        "url": "https://agnew-cdn.n2erp.co.nz/cdn/images/productdocument/RAB-Board-Installation-Guide.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "RAB Board",
        "description": "RAB Board installation guide - additional details"
    },
    
    # === AXON PANEL ===
    {
        "name": "Axon Panel Installation Guide",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Axon-Panel-Installation-Manual.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Axon Panel",
        "description": "Installation manual for Axon cladding panels"
    },
    
    # === VILLABOARD ===
    {
        "name": "Villaboard Lining Installation Guide",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Villaboard-Lining-Technical-Specification.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Villaboard",
        "description": "Villaboard wet area lining installation specification"
    },
    
    # === SECURA FLOORING ===
    {
        "name": "Secura Interior Flooring Installation Guide",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Secura-Interior-Flooring-Installation-Manual.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Secura Flooring",
        "description": "Secura interior flooring system installation"
    },
    
    # === FIRE & ACOUSTIC ===
    {
        "name": "James Hardie Fire and Acoustic Design Manual",
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/446.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "Fire Acoustic",
        "description": "Comprehensive fire and acoustic design manual for all Hardie systems"
    },
    
    # === BRACING ===
    {
        "name": "James Hardie Bracing Design Manual",
        "url": "https://www.jameshardie.co.nz/web/assets/general/James-Hardie-Bracing-Design-Manual.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "Bracing",
        "description": "Bracing design manual for James Hardie systems"
    }
]

HARDIE_METADATA = {
    "brand_name": "James Hardie",
    "brand_full_name": "James Hardie Industries plc",
    "category_code": "B_Enclosure",
    "trade": "cladding",
    "country": "New Zealand",
    "website": "https://www.jameshardie.co.nz"
}


class HardieConnectorV2:
    """Full Suite connector for James Hardie technical documents"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/B_Enclosure/Wall_Cladding"):
        self.output_dir = output_dir
        self.metadata = HARDIE_METADATA
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'STRYDA-BigBrain/1.0 (Construction Knowledge Engine)',
            'Accept': 'application/pdf,*/*'
        })
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "James_Hardie"), exist_ok=True)
    
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
            filepath = os.path.join(self.output_dir, "James_Hardie", filename)
            
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
        print("🧠 STRYDA Big Brain - James Hardie Full Suite Connector v2")
        print("=" * 70)
        print(f"\n📚 Brand: {self.metadata['brand_full_name']}")
        print(f"📂 Category: {self.metadata['category_code']}")
        print(f"📁 Output: {self.output_dir}/James_Hardie/")
        print(f"\n🔍 Found {len(HARDIE_DOCUMENTS)} documents to fetch...")
        
        downloaded = []
        failed = []
        
        for doc_info in HARDIE_DOCUMENTS:
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
                "total_attempted": len(HARDIE_DOCUMENTS),
                "successful": len(downloaded),
                "failed": len(failed)
            }
        }
        
        manifest_path = os.path.join(self.output_dir, "James_Hardie", "manifest.json")
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
    connector = HardieConnectorV2()
    connector.fetch_all_documents()
