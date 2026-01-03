#!/usr/bin/env python3
"""
STRYDA Big Brain - OPERATION HARDWARE STORE
Omnibus Fastener Connector for Category F: Consumables/Fasteners
Downloads ALL major NZ fastener brand technical documentation
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# ============================================================================
# MASTER FASTENER DOCUMENT LIBRARY
# ============================================================================

FASTENER_DOCUMENTS = [
    # ========== PASLODE ==========
    {
        "name": "Paslode NZ Nails BRANZ Appraisal 546",
        "url": "https://www.paslode.co.nz/wp-content/uploads/546_2022.pdf",
        "brand": "Paslode",
        "product_family": "Collated Nails",
        "doc_type": "BRANZ_Appraisal",
        "retailers": ["PlaceMakers", "Carters", "ITM", "Mitre 10"]
    },
    {
        "name": "Paslode Purlin Nails BRANZ Appraisal",
        "url": "https://www.paslode.co.nz/wp-content/uploads/1249-202-Latest-Purlin-BRANZ-Aug23.pdf",
        "brand": "Paslode",
        "product_family": "Purlin Nails",
        "doc_type": "BRANZ_Appraisal",
        "retailers": ["PlaceMakers", "Carters", "ITM"]
    },
    {
        "name": "Paslode 2020 Full Catalog",
        "url": "https://itwconstruction.ca/wp-content/uploads/2020/09/Paslode-2020-Catalog.pdf",
        "brand": "Paslode",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "Carters", "ITM", "Mitre 10"]
    },
    {
        "name": "Paslode Impulse Purlin Nails Technical",
        "url": "https://www.miproducts.co.nz/MasterspecPTS_Paslode-Impulse-Purlin-Nails_112946.pdf",
        "brand": "Paslode",
        "product_family": "Impulse Purlin",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Carters"]
    },
    {
        "name": "Paslode Fastener Selection Chart",
        "url": "https://paslode.ca/wp-content/uploads/sites/3/2020/07/918150-Fastener-Selection-Chart.pdf",
        "brand": "Paslode",
        "product_family": "Fastener Guide",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Carters", "ITM", "Mitre 10"]
    },
    
    # ========== MITEK / LUMBERLOK / BOWMAC ==========
    {
        "name": "MiTek LUMBERLOK Timber Connectors Characteristic Loadings",
        "url": "https://miteknz.co.nz/wp-content/uploads/2021/06/LUMBERLOK-Timber-Connectors-Characteristic-Loadings-Data.pdf",
        "brand": "MiTek",
        "product_family": "LUMBERLOK",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Carters", "ITM"]
    },
    {
        "name": "MiTek Stud-to-Top-Plate Fixing Schedule 2024",
        "url": "https://miteknz.co.nz/wp-content/uploads/2024/03/Stud-to-Top-Plate-Fixing-Schedule_2024-v1.pdf",
        "brand": "MiTek",
        "product_family": "Fixing Schedules",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Carters", "ITM"]
    },
    
    # ========== SIMPSON STRONG-TIE ==========
    {
        "name": "Simpson Strong-Tie NZS 3604 Timber Connectors",
        "url": "https://strongtie.com.au/sites/default/files/F-C-NZS3604-19_Timber_Connectors_NZS3604.pdf",
        "brand": "Simpson Strong-Tie",
        "product_family": "Timber Connectors",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Bunnings", "Mitre 10"]
    },
    {
        "name": "Simpson Strong-Tie Timber Construction Connectors Catalog",
        "url": "https://strongtie.com.au/sites/default/files/brochure_catalogues/C-C-AU16_Timber_Construction_Connectors.pdf",
        "brand": "Simpson Strong-Tie",
        "product_family": "Full Catalog",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "Bunnings", "Mitre 10"]
    },
    {
        "name": "Simpson Strong-Tie Mass Timber Connectors AUNZ",
        "url": "https://www.eboss.co.nz/assets/literature/449/34921/C-MT-AUNZ23.pdf",
        "brand": "Simpson Strong-Tie",
        "product_family": "Mass Timber",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "Bunnings"]
    },
    
    # ========== ITW BUILDEX (Roofing/Cladding Screws) ==========
    {
        "name": "ITW Buildex Catalog 2024-25",
        "url": "https://www.itwbuildex.com/pdf/Buildex_Catalog_2024_25.pdf",
        "brand": "Buildex",
        "product_family": "Roofing Screws",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "Carters", "Bunnings", "Mitre 10"]
    },
    {
        "name": "ITW Buildex 2020 Catalog",
        "url": "https://itwconstruction.ca/wp-content/uploads/2020/09/Buildex-2020-Catalog.pdf",
        "brand": "Buildex",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "Carters", "Bunnings"]
    },
    {
        "name": "Buildex Low Profile Roof Clip Fastener Guide",
        "url": "https://buildex.ca/wp-content/uploads/sites/8/2020/11/Low-Profile-Architectural-Metal-Roof-Clip-Fastener-TEKS-in-Catalog.pdf",
        "brand": "Buildex",
        "product_family": "Roof Clips",
        "doc_type": "Installation_Guide",
        "retailers": ["PlachecMakers", "Carters"]
    },
    
    # ========== RAMSET ==========
    {
        "name": "Ramset Technical Product Guide",
        "url": "https://ramset.com.hk/wp-content/uploads/2021/04/1287984851_2925.pdf",
        "brand": "Ramset",
        "product_family": "Anchors",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Bunnings", "Mitre 10", "PlaceMakers"]
    },
    
    # ========== SENCO ==========
    {
        "name": "Senco Fastener Catalog",
        "url": "https://www.senco.com/pub/media/downloads/senco-fastener-catalog.pdf",
        "brand": "Senco",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "ITM", "Mitre 10"]
    },
    
    # ========== AUSTRALIAN/NZ STANDARDS REFERENCES ==========
    {
        "name": "NZ SIP Technical Manual Fasteners Section",
        "url": "https://nzsip.co.nz/wp-content/uploads/2023/08/NZSIPTechnicalManualV2Aug2023.pdf",
        "brand": "NZSIP",
        "product_family": "SIP Fasteners",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Specialist"]
    },
]

FASTENER_METADATA = {
    "category_code": "F_Manufacturers",
    "trade": "fasteners",
    "country": "New Zealand"
}


class FastenerOmnibusConnector:
    """Downloads ALL fastener brand documentation"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/F_Manufacturers/Fasteners"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'STRYDA-BigBrain/1.0 (Construction Knowledge Engine)',
            'Accept': 'application/pdf,*/*'
        })
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create brand subdirectories
        brands = set(doc['brand'] for doc in FASTENER_DOCUMENTS)
        for brand in brands:
            safe_brand = brand.replace(' ', '_').replace('-', '_')
            os.makedirs(os.path.join(output_dir, safe_brand), exist_ok=True)
    
    def calculate_file_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
    
    def download_document(self, doc_info: Dict) -> Optional[Dict]:
        """Download a single document"""
        print(f"\n📥 [{doc_info['brand']}] {doc_info['name']}...")
        
        try:
            response = self.session.get(doc_info['url'], timeout=120, allow_redirects=True)
            response.raise_for_status()
            
            content = response.content
            file_hash = self.calculate_file_hash(content)
            
            safe_brand = doc_info['brand'].replace(' ', '_').replace('-', '_')
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-').replace(':', '')
            filename = f"{safe_name}.pdf"
            filepath = os.path.join(self.output_dir, safe_brand, filename)
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            record = {
                "source": doc_info['name'],
                "brand_name": doc_info['brand'],
                "category_code": FASTENER_METADATA['category_code'],
                "product_family": doc_info['product_family'],
                "doc_type": doc_info['doc_type'],
                "trade": FASTENER_METADATA['trade'],
                "original_url": doc_info['url'],
                "local_path": filepath,
                "file_hash": file_hash,
                "file_size_bytes": file_size,
                "retailer_availability": doc_info.get('retailers', []),
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
    
    def fetch_all_documents(self) -> Dict:
        """Fetch all fastener documents"""
        print("=" * 70)
        print("🧠 STRYDA Big Brain - OPERATION HARDWARE STORE")
        print("   Fastener Omnibus Connector")
        print("=" * 70)
        
        # Group by brand for display
        brands = {}
        for doc in FASTENER_DOCUMENTS:
            brand = doc['brand']
            if brand not in brands:
                brands[brand] = []
            brands[brand].append(doc)
        
        print(f"\n📚 Target Brands: {len(brands)}")
        for brand, docs in brands.items():
            print(f"   • {brand}: {len(docs)} documents")
        
        print(f"\n🔍 Total documents to fetch: {len(FASTENER_DOCUMENTS)}")
        
        downloaded = []
        failed = []
        brand_stats = {}
        
        for doc_info in FASTENER_DOCUMENTS:
            brand = doc_info['brand']
            if brand not in brand_stats:
                brand_stats[brand] = {"success": 0, "failed": 0}
            
            result = self.download_document(doc_info)
            if result:
                downloaded.append(result)
                brand_stats[brand]["success"] += 1
            else:
                failed.append(doc_info['name'])
                brand_stats[brand]["failed"] += 1
        
        # Save manifest
        manifest = {
            "operation": "HARDWARE_STORE",
            "category": FASTENER_METADATA,
            "fetch_date": datetime.now().isoformat(),
            "documents": downloaded,
            "failed": failed,
            "brand_stats": brand_stats,
            "stats": {
                "total_attempted": len(FASTENER_DOCUMENTS),
                "successful": len(downloaded),
                "failed": len(failed)
            }
        }
        
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Print summary
        print(f"\n" + "=" * 70)
        print(f"📊 OPERATION HARDWARE STORE - FETCH SUMMARY")
        print(f"=" * 70)
        
        total_size = sum(d['file_size_bytes'] for d in downloaded)
        print(f"\n   📦 Total downloaded: {len(downloaded)} documents ({total_size / 1024 / 1024:.1f} MB)")
        print(f"   ❌ Failed: {len(failed)}")
        
        print(f"\n   📋 By Brand:")
        for brand, stats in sorted(brand_stats.items()):
            status = "✅" if stats['failed'] == 0 else "⚠️"
            print(f"      {status} {brand}: {stats['success']}/{stats['success'] + stats['failed']}")
        
        if failed:
            print(f"\n   ❌ Failed documents:")
            for name in failed[:5]:
                print(f"      • {name}")
            if len(failed) > 5:
                print(f"      ... and {len(failed) - 5} more")
        
        print(f"\n📋 Manifest saved: {manifest_path}")
        
        return manifest


if __name__ == "__main__":
    connector = FastenerOmnibusConnector()
    connector.fetch_all_documents()
