#!/usr/bin/env python3
"""
STRYDA Big Brain - GIB (Winstone Wallboards) Connector
Pilot connector for Category C: Interiors

Target Documents:
1. GIB Site Guide (Installation manual)
2. GIB EzyBrace System (Bracing patterns)
3. GIB Weatherline (Exterior systems)
4. GIB Fire Rated Systems
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Add backend to path
sys.path.insert(0, '/app/backend-minimal')

from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# GIB Document Library URLs
GIB_BASE_URL = "https://www.gib.co.nz"

# Known GIB Technical Documents (verified URLs)
GIB_DOCUMENTS = [
    {
        "name": "GIB Site Guide",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Site-Guide-Feb-2024.pdf",
        "doc_type": "Installation_Guide",
        "product_family": "GIB Plasterboard",
        "description": "Complete installation guide for GIB plasterboard systems"
    },
    {
        "name": "GIB EzyBrace System",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-EzyBrace-System-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB EzyBrace",
        "description": "Bracing system for residential buildings"
    },
    {
        "name": "GIB Weatherline System",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Weatherline-System-Literature.pdf",
        "doc_type": "Technical_Data_Sheet", 
        "product_family": "GIB Weatherline",
        "description": "External lining system for weather protection"
    },
    {
        "name": "GIB Fire Rated Systems",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Fire-Rated-Systems-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Fire Rated",
        "description": "Fire rated wall and ceiling systems"
    },
    {
        "name": "GIB Noise Control Systems",
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Noise-Control-Systems-Literature.pdf",
        "doc_type": "Technical_Data_Sheet",
        "product_family": "GIB Noise Control",
        "description": "Acoustic solutions for walls and ceilings"
    }
]

# Metadata for GIB brand
GIB_METADATA = {
    "brand_name": "GIB",
    "brand_full_name": "Winstone Wallboards Ltd",
    "category_code": "C_Interiors",
    "trade": "interior_linings",
    "country": "New Zealand",
    "website": "https://www.gib.co.nz"
}

class GIBConnector:
    """Connector for fetching and processing GIB technical documents"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/C_Interiors/Plasterboard_Linings"):
        self.output_dir = output_dir
        self.metadata = GIB_METADATA
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'STRYDA-BigBrain/1.0 (Construction Knowledge Engine)'
        })
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "GIB"), exist_ok=True)
        
    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def download_document(self, doc_info: Dict) -> Optional[Dict]:
        """Download a single document and return metadata"""
        print(f"\n📥 Downloading: {doc_info['name']}...")
        
        try:
            response = self.session.get(doc_info['url'], timeout=60)
            response.raise_for_status()
            
            content = response.content
            file_hash = self.calculate_file_hash(content)
            
            # Generate safe filename
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-')
            filename = f"{safe_name}.pdf"
            filepath = os.path.join(self.output_dir, "GIB", filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            # Build metadata record
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
                "status": "downloaded"
            }
            
            print(f"   ✅ Downloaded: {filename} ({file_size / 1024:.1f} KB)")
            return record
            
        except requests.exceptions.HTTPError as e:
            print(f"   ⚠️ HTTP Error for {doc_info['name']}: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error downloading {doc_info['name']}: {e}")
            return None
    
    def fetch_all_documents(self) -> List[Dict]:
        """Fetch all known GIB documents"""
        print("=" * 60)
        print("🧠 STRYDA Big Brain - GIB Connector")
        print("=" * 60)
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
        
        # Save manifest
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
        
        print(f"\n" + "=" * 60)
        print(f"📊 FETCH SUMMARY")
        print(f"=" * 60)
        print(f"   ✅ Downloaded: {len(downloaded)}")
        print(f"   ❌ Failed: {len(failed)}")
        if failed:
            print(f"   Failed documents: {', '.join(failed)}")
        print(f"\n📋 Manifest saved: {manifest_path}")
        
        return downloaded
    
    def get_download_status(self) -> Dict:
        """Check status of downloaded documents"""
        gib_dir = os.path.join(self.output_dir, "GIB")
        manifest_path = os.path.join(gib_dir, "manifest.json")
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                return json.load(f)
        return {"status": "not_initialized"}


def discover_gib_resources():
    """Discover available GIB resources by checking URLs"""
    print("\n🔍 Discovering GIB resources...")
    
    available = []
    unavailable = []
    
    for doc in GIB_DOCUMENTS:
        try:
            response = requests.head(doc['url'], timeout=10, allow_redirects=True)
            if response.status_code == 200:
                available.append(doc['name'])
                print(f"   ✅ {doc['name']}: Available")
            else:
                unavailable.append(doc['name'])
                print(f"   ⚠️ {doc['name']}: HTTP {response.status_code}")
        except Exception as e:
            unavailable.append(doc['name'])
            print(f"   ❌ {doc['name']}: {e}")
    
    return {"available": available, "unavailable": unavailable}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GIB Document Connector")
    parser.add_argument("--discover", action="store_true", help="Discover available resources")
    parser.add_argument("--fetch", action="store_true", help="Fetch all documents")
    parser.add_argument("--status", action="store_true", help="Check download status")
    
    args = parser.parse_args()
    
    connector = GIBConnector()
    
    if args.discover:
        discover_gib_resources()
    elif args.fetch:
        connector.fetch_all_documents()
    elif args.status:
        status = connector.get_download_status()
        print(json.dumps(status, indent=2))
    else:
        # Default: discover then fetch
        print("Running full pipeline: Discover -> Fetch")
        discovery = discover_gib_resources()
        if discovery['available']:
            print(f"\n{len(discovery['available'])} resources available. Starting fetch...")
            connector.fetch_all_documents()
        else:
            print("\n⚠️ No resources available. Check URLs.")
