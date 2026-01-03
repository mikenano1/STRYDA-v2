#!/usr/bin/env python3
"""
STRYDA Big Brain - James Hardie Connector
Fetches cladding and external products documentation
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

# James Hardie Document Library
HARDIE_BASE_URL = "https://www.jameshardie.com.au"

# Known James Hardie Technical Documents (NZ/AU versions)
HARDIE_DOCUMENTS = [
    {
        "name": "Linea Weatherboard Direct Fix Technical Specification",
        "url": "https://www.jameshardie.co.nz/web/assets/general/Linea-Weatherboard-Direct-Fix-Technical-Specification.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Linea Weatherboard",
        "description": "Technical specification for Linea Weatherboard direct fix installation"
    },
    {
        "name": "Linea Weatherboard Installation Guide",
        "url": "https://agnew-cdn.n2erp.co.nz/cdn/images/productdocument/LineaWeatherboardsInstallationGuideApr23.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Linea Weatherboard",
        "description": "Practical installation guide for Linea Weatherboard April 2023"
    },
    {
        "name": "Linea Weatherboard Installation Checklist",
        "url": "https://www.jameshardie.co.nz/web/assets/general/INSTALLATION-Checklist-Linea-Weatherboard.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Linea Weatherboard",
        "description": "Step-by-step installation checklist for NZBC E2/AS1 compliance"
    },
    {
        "name": "James Hardie Facades Installation Manual",
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/446.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "Facades",
        "description": "General installation manual for James Hardie fibre cement facades"
    }
]

# Metadata
HARDIE_METADATA = {
    "brand_name": "James Hardie",
    "brand_full_name": "James Hardie Industries plc",
    "category_code": "B_Enclosure",
    "trade": "cladding",
    "country": "New Zealand",
    "website": "https://www.jameshardie.co.nz"
}


class HardieConnector:
    """Connector for fetching James Hardie technical documents"""
    
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
                "has_diagrams": True  # Hardie docs are diagram-heavy
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
        """Fetch all known Hardie documents"""
        print("=" * 60)
        print("🧠 STRYDA Big Brain - James Hardie Connector")
        print("=" * 60)
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
        
        print(f"\n" + "=" * 60)
        print(f"📊 FETCH SUMMARY")
        print(f"=" * 60)
        print(f"   ✅ Downloaded: {len(downloaded)}")
        print(f"   ❌ Failed: {len(failed)}")
        if failed:
            print(f"   Failed: {', '.join(failed)}")
        print(f"\n📋 Manifest saved: {manifest_path}")
        
        return downloaded


def discover_hardie_resources():
    """Check availability of Hardie resources"""
    print("\n🔍 Discovering James Hardie resources...")
    
    available = []
    unavailable = []
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'STRYDA-BigBrain/1.0'
    })
    
    for doc in HARDIE_DOCUMENTS:
        try:
            response = session.head(doc['url'], timeout=15, allow_redirects=True)
            if response.status_code == 200:
                available.append(doc['name'])
                print(f"   ✅ {doc['name']}: Available")
            else:
                unavailable.append(doc['name'])
                print(f"   ⚠️ {doc['name']}: HTTP {response.status_code}")
        except Exception as e:
            unavailable.append(doc['name'])
            print(f"   ❌ {doc['name']}: {str(e)[:50]}")
    
    return {"available": available, "unavailable": unavailable}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="James Hardie Document Connector")
    parser.add_argument("--discover", action="store_true", help="Discover available resources")
    parser.add_argument("--fetch", action="store_true", help="Fetch all documents")
    
    args = parser.parse_args()
    
    connector = HardieConnector()
    
    if args.discover:
        discover_hardie_resources()
    elif args.fetch:
        connector.fetch_all_documents()
    else:
        print("Running full pipeline: Discover -> Fetch")
        discovery = discover_hardie_resources()
        if discovery['available']:
            print(f"\n{len(discovery['available'])} resources available. Starting fetch...")
            connector.fetch_all_documents()
