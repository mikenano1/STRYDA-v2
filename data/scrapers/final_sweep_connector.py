#!/usr/bin/env python3
"""
STRYDA Big Brain - OPERATION FINAL SWEEP
NZ Local Fastener Brands + Merchant Staples
Category F: Consumables/Fasteners - Complete Coverage
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

# ============================================================================
# FINAL SWEEP DOCUMENT LIBRARY - NZ Locals & Merchant Brands
# ============================================================================

FINAL_SWEEP_DOCUMENTS = [
    # ========== DELFAST (NZ Local) ==========
    {
        "name": "Delfast PlaceMakers Nail Guide 2023",
        "url": "https://www.placemakers.co.nz/medias/sys_master/root/h71/h46/11685411487774/Delfast-PlaceMakers%20Nail%20Guide%2003-23/Delfast-PlaceMakers-Nail-Guide-03-23.pdf",
        "brand": "Delfast",
        "product_family": "Collated Nails",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "ITM"]
    },
    {
        "name": "Delfast PlaceMakers Rural Range 2021",
        "url": "https://www.placemakers.co.nz/medias/sys_master/root/h02/h02/10202659455006/delfast-placemakers-rural-range-compressed-v1-june-2021/delfast-placemakers-rural-range-compressed-v1-june-2021.pdf",
        "brand": "Delfast",
        "product_family": "Staples Rural",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers"]
    },
    {
        "name": "Delfast Nails BRANZ Appraisal 1154",
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/01_1154_2021_-_A1.pdf",
        "brand": "Delfast",
        "product_family": "Collated Nails",
        "doc_type": "BRANZ_Appraisal",
        "retailers": ["PlaceMakers", "ITM", "Mitre 10"]
    },
    
    # ========== ECKO FASTENERS (PlaceMakers/ITM) ==========
    {
        "name": "ECKO Fasteners Catalogue 2024 Screws",
        "url": "https://www.ecko.co.nz/wp-content/uploads/0.-ECKO-Fasteners-Catalogue-2024-SCREWS.pdf",
        "brand": "Ecko",
        "product_family": "T-Rex Screws",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "ITM", "Mitre 10"]
    },
    {
        "name": "ECKO Fasteners Full Catalogue 2024",
        "url": "https://www.ecko.co.nz/wp-content/uploads/0.-ECKO-Fasteners-Catalogue-2024-1.pdf",
        "brand": "Ecko",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "ITM", "Mitre 10"]
    },
    {
        "name": "ECKO Fasteners Catalogue 2022",
        "url": "https://www.ecko.co.nz/wp-content/uploads/ECKO-Fasteners-Catalogue-2022.pdf",
        "brand": "Ecko",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers", "ITM"]
    },
    {
        "name": "ECKO T-Rex 17 Screws BPIR Declaration",
        "url": "https://ajfasteners.co.nz/wp-content/uploads/2023/11/ECKO-TRex-17-Screws-BPIR-Decl-V1.0.pdf",
        "brand": "Ecko",
        "product_family": "T-Rex 17",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "ITM"]
    },
    
    # ========== PRYDA (Bunnings Trade) ==========
    {
        "name": "NZ Pryda Connectors Tie-downs Design Guide",
        "url": "https://www.pryda.co.nz/wp-content/uploads/NZ-Pryda-Connectors-Tie-downs-Design-Guide.pdf",
        "brand": "Pryda",
        "product_family": "Connectors",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Bunnings", "Mitre 10"]
    },
    {
        "name": "NZ Pryda Bracing Design Guide V1.02",
        "url": "https://www.pryda.co.nz/wp-content/uploads/NZ-Pryda-Bracing-Design-Guide-V1.02.pdf",
        "brand": "Pryda",
        "product_family": "Bracing",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Bunnings", "Mitre 10"]
    },
    {
        "name": "NZ Pryda Bracing Anchor PDS",
        "url": "https://www.pryda.co.nz/wp-content/uploads/NZ-Bracing-Anchor-PDS.pdf",
        "brand": "Pryda",
        "product_family": "Bracing Anchor",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Bunnings"]
    },
    {
        "name": "Pryda Builders Guide NZ",
        "url": "https://sheds4u.co.nz/wp-content/uploads/2021/09/Pryda-Builders-Guide-Web.pdf",
        "brand": "Pryda",
        "product_family": "Builders Guide",
        "doc_type": "Installation_Guide",
        "retailers": ["Bunnings", "Mitre 10"]
    },
    {
        "name": "SP Fasteners Pryda Product Catalogue",
        "url": "https://spfasteners.co.nz/wp-content/uploads/2024/01/Product-Catalogue-Web-Oct-14.pdf",
        "brand": "Pryda",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["SP Fasteners", "Trade"]
    },
    
    # ========== BREMICK (Mitre 10 Trade / Industrial) ==========
    {
        "name": "Bremick Industrial Fasteners Catalogue",
        "url": "https://new.bremick.com.au/images/site/Industrial_catalogue_web.pdf",
        "brand": "Bremick",
        "product_family": "Industrial",
        "doc_type": "Product_Catalog",
        "retailers": ["Mitre 10", "Trade Suppliers"]
    },
    {
        "name": "Bremick Stainless Steel Catalogue",
        "url": "https://www.osfs.com.au/wp-content/uploads/2022/05/bremick_Stainless_Steel_web.pdf",
        "brand": "Bremick",
        "product_family": "Stainless Steel",
        "doc_type": "Product_Catalog",
        "retailers": ["Mitre 10", "Trade Suppliers"]
    },
    {
        "name": "Bremick Socket Screws Catalogue",
        "url": "https://www.nationalwelding.com.au/assets/PDF/Socket_Screws_web.pdf",
        "brand": "Bremick",
        "product_family": "Socket Screws",
        "doc_type": "Product_Catalog",
        "retailers": ["Mitre 10", "Trade Suppliers"]
    },
    {
        "name": "Bremick Masonry Anchor Catalogue",
        "url": "https://bremick.com.au/wp-content/uploads/2024/02/Masonry_Anchor_Catalogue.pdf",
        "brand": "Bremick",
        "product_family": "Masonry Anchors",
        "doc_type": "Product_Catalog",
        "retailers": ["Mitre 10", "Bunnings", "Trade"]
    },
    
    # ========== PLACEMAKERS MASTER CATALOGUE ==========
    {
        "name": "PlaceMakers Fastenings Catalogue 2020",
        "url": "https://www.placemakers.co.nz/medias/sys_master/root/h94/he4/10202791477278/fastenings-catalogue-2020/fastenings-catalogue-2020.pdf",
        "brand": "PlaceMakers",
        "product_family": "Master Catalogue",
        "doc_type": "Product_Catalog",
        "retailers": ["PlaceMakers"]
    },
]

FINAL_SWEEP_METADATA = {
    "category_code": "F_Manufacturers",
    "trade": "fasteners",
    "country": "New Zealand",
    "operation": "FINAL_SWEEP"
}


class FinalSweepConnector:
    """Downloads NZ Local and Merchant brand fastener documentation"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/F_Manufacturers/Fasteners"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'STRYDA-BigBrain/1.0 (Construction Knowledge Engine)',
            'Accept': 'application/pdf,*/*'
        })
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create brand subdirectories
        brands = set(doc['brand'] for doc in FINAL_SWEEP_DOCUMENTS)
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
            
            # Verify it's a PDF
            if not content[:4] == b'%PDF':
                print(f"   ⚠️ Not a valid PDF file")
                return None
            
            file_hash = self.calculate_file_hash(content)
            
            safe_brand = doc_info['brand'].replace(' ', '_').replace('-', '_')
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-').replace(':', '').replace('%', '')
            filename = f"{safe_name}.pdf"
            filepath = os.path.join(self.output_dir, safe_brand, filename)
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            record = {
                "source": doc_info['name'],
                "brand_name": doc_info['brand'],
                "category_code": FINAL_SWEEP_METADATA['category_code'],
                "product_family": doc_info['product_family'],
                "doc_type": doc_info['doc_type'],
                "trade": FINAL_SWEEP_METADATA['trade'],
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
        """Fetch all final sweep documents"""
        print("=" * 70)
        print("🧠 STRYDA Big Brain - OPERATION FINAL SWEEP")
        print("   NZ Local Brands + Merchant Staples")
        print("=" * 70)
        
        # Group by brand
        brands = {}
        for doc in FINAL_SWEEP_DOCUMENTS:
            brand = doc['brand']
            if brand not in brands:
                brands[brand] = []
            brands[brand].append(doc)
        
        print(f"\n📚 Target Brands: {len(brands)}")
        for brand, docs in brands.items():
            print(f"   • {brand}: {len(docs)} documents")
        
        print(f"\n🔍 Total documents to fetch: {len(FINAL_SWEEP_DOCUMENTS)}")
        
        downloaded = []
        failed = []
        brand_stats = {}
        
        for doc_info in FINAL_SWEEP_DOCUMENTS:
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
            "operation": "FINAL_SWEEP",
            "category": FINAL_SWEEP_METADATA,
            "fetch_date": datetime.now().isoformat(),
            "documents": downloaded,
            "failed": failed,
            "brand_stats": brand_stats,
            "stats": {
                "total_attempted": len(FINAL_SWEEP_DOCUMENTS),
                "successful": len(downloaded),
                "failed": len(failed)
            }
        }
        
        manifest_path = os.path.join(self.output_dir, "manifest_final_sweep.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Print summary
        print(f"\n" + "=" * 70)
        print(f"📊 OPERATION FINAL SWEEP - SUMMARY")
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
            for name in failed:
                print(f"      • {name}")
        
        print(f"\n📋 Manifest saved: {manifest_path}")
        
        return manifest


if __name__ == "__main__":
    connector = FinalSweepConnector()
    connector.fetch_all_documents()
