#!/usr/bin/env python3
"""
STRYDA Big Brain - OPERATION FINAL SWEEP (CORRECTED)
NZ Local Fastener Brands + Bunnings/ITM Ecosystem
Category F: Consumables/Fasteners - Complete Market Coverage

TARGET BRANDS (10 Total):
[ ] Delfast (Collated Nails - PlaceMakers/ITM)
[ ] Allfast Solutions (Structural - NZ)
[ ] Blacks Fasteners (South Island)
[ ] Ecko Fasteners (PlaceMakers Captain)
[ ] Pryda (Bunnings Brackets)
[ ] Bremick (Mitre 10 Anchors)
[ ] Zenith (Bunnings Hardware)
[ ] Titan (Trade Nails via NZ Nails)
[ ] MacSim (Packers/Anchors)
[ ] SPAX (ITM Premium Screws)
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
# FINAL SWEEP DOCUMENT LIBRARY - CORRECTED + BUNNINGS/ITM ECOSYSTEM
# ============================================================================

FINAL_SWEEP_DOCUMENTS = [
    # ==========================================================================
    # 1. DELFAST (NZ Local - PlaceMakers/ITM Captain)
    # ==========================================================================
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
    
    # ==========================================================================
    # 2. ALLFAST SOLUTIONS (NZ Structural)
    # ==========================================================================
    # Note: Allfast NZ doesn't have public PDF catalogs - using PlaceMakers fastenings catalog
    # which includes structural fastener specifications commonly sourced from Allfast
    
    # ==========================================================================
    # 3. BLACKS FASTENERS (South Island - National Coverage)
    # ==========================================================================
    {
        "name": "Blacks Fasteners Handbook Complete",
        "url": "https://www.blacksfasteners.co.nz/img/catalogue/Blacks_Fasteners_-_Handbook_2013_Compressed.pdf",
        "brand": "Blacks",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["Blacks Fasteners", "South Island Trade"]
    },
    {
        "name": "Mainland Fasteners Mini Catalogue",
        "url": "https://www.mainlandfasteners.co.nz/downloads/MiniCatalogue.pdf",
        "brand": "Mainland Fasteners",
        "product_family": "South Island Range",
        "doc_type": "Product_Catalog",
        "retailers": ["Mainland Fasteners", "South Island Trade"]
    },
    
    # ==========================================================================
    # 4. ECKO FASTENERS (PlaceMakers/ITM Captain)
    # ==========================================================================
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
    
    # ==========================================================================
    # 5. PRYDA (Bunnings Trade - Brackets/Bracing)
    # ==========================================================================
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
    
    # ==========================================================================
    # 6. BREMICK (Mitre 10 Trade / Industrial Anchors)
    # ==========================================================================
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
    
    # ==========================================================================
    # 7. ZENITH (Bunnings Hardware - ITW Proline)
    # ==========================================================================
    {
        "name": "Zenith Hardware Catalogue 2020",
        "url": "https://www.itwproline.com.au/wp-content/uploads/2019/11/03121_Zenith-Hardware_Catalogue-2020-V12-LR.pdf",
        "brand": "Zenith",
        "product_family": "Hardware",
        "doc_type": "Product_Catalog",
        "retailers": ["Bunnings"]
    },
    {
        "name": "Zenith Hardware Catalogue 2017",
        "url": "https://www.itwproline.com.au/wp-content/uploads/2019/11/Zenith-Hardware-Catalogue-2017.pdf",
        "brand": "Zenith",
        "product_family": "Hardware",
        "doc_type": "Product_Catalog",
        "retailers": ["Bunnings"]
    },
    {
        "name": "Zenith Fasteners Bolts Catalogue 2017",
        "url": "https://www.itwlyp.proline.com.au/wp-content/uploads/2019/11/Zenith_Fasteners_New_Bolts_Catalogue_2017.pdf",
        "brand": "Zenith",
        "product_family": "Bolts Fasteners",
        "doc_type": "Product_Catalog",
        "retailers": ["Bunnings"]
    },
    
    # ==========================================================================
    # 8. TITAN (Trade Nails via NZ Nails)
    # ==========================================================================
    {
        "name": "Titan Framing Nails BPIR Declaration",
        "url": "https://www.titanfasteners.co.nz/wp-content/uploads/2024/12/Airco-Brands-Titan-Framing-Nails-BPIR-Decl-v2.0.pdf",
        "brand": "Titan",
        "product_family": "Framing Nails",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["ITM", "Bunnings", "PlaceMakers"]
    },
    {
        "name": "NZ Nails Building Product Information Sheet",
        "url": "https://www.nznails.co.nz/download_file/view/428/162/",
        "brand": "NZ Nails",
        "product_family": "Loose Nails",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["ITM", "Trade"]
    },
    
    # ==========================================================================
    # 9. MACSIM (Packers/Anchors - Window Installation Essential)
    # ==========================================================================
    {
        "name": "MacSim Fill Fix Bond Foam TDS",
        "url": "https://shop.cnw.com.au/medias/MAC53MPF750.pdf",
        "brand": "MacSim",
        "product_family": "Foam Sealants",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["Bunnings", "Mitre 10", "Trade"]
    },
    {
        "name": "Fasteners Direct Catalogue (MacSim Products)",
        "url": "https://fastenersdirect.com.au/wp-content/uploads/2024/05/2140_HM_Fasteners-Direct-Catalogue-Updates_Aug22_INHOUSE-Lores.pdf",
        "brand": "MacSim",
        "product_family": "Anchors Fasteners",
        "doc_type": "Product_Catalog",
        "retailers": ["Trade Suppliers"]
    },
    
    # ==========================================================================
    # 10. SPAX (ITM Premium Screws - German Engineering)
    # ==========================================================================
    {
        "name": "SPAX Pacific Product Catalogue 2018-2019",
        "url": "https://www.spaxpacific.com/SPAX_Pacific_ProductCAT_2018-2019.pdf",
        "brand": "SPAX",
        "product_family": "Full Range",
        "doc_type": "Product_Catalog",
        "retailers": ["ITM", "Mitre 10", "Trade"]
    },
    {
        "name": "SPAX Decking Screw Guide",
        "url": "https://www.placemakers.co.nz/medias/sys_master/root/h37/he6/10202660470814/spax-decking-screw-guide/spax-decking-screw-guide.pdf",
        "brand": "SPAX",
        "product_family": "Decking Screws",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["PlaceMakers", "ITM"]
    },
    {
        "name": "SPAX Timber Construction NZS 3603 Design Guide",
        "url": "https://www.spaxpacific.com/SPAXTimberConstBroNZS-3603-Email.pdf",
        "brand": "SPAX",
        "product_family": "Timber Construction",
        "doc_type": "Technical_Data_Sheet",
        "retailers": ["ITM", "Trade"]
    },
    
    # ==========================================================================
    # BONUS: PLACEMAKERS MASTER CATALOGUE (Coverage for Allfast + Others)
    # ==========================================================================
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
    "operation": "FINAL_SWEEP_CORRECTED",
    "target_brands": [
        "Delfast", "Blacks", "Ecko", "Pryda", "Bremick",
        "Zenith", "Titan", "NZ Nails", "MacSim", "SPAX"
    ],
    "retailer_ecosystem": {
        "Bunnings": ["Zenith", "Pryda", "Bremick", "Titan", "MacSim"],
        "Mitre 10": ["Bremick", "Pryda", "SPAX", "MacSim"],
        "PlaceMakers": ["Delfast", "Ecko", "SPAX"],
        "ITM": ["Delfast", "Ecko", "Titan", "NZ Nails", "SPAX"]
    }
}


class FinalSweepConnector:
    """Downloads NZ Local and Bunnings/ITM Ecosystem fastener documentation"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/F_Manufacturers/Fasteners"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
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
            
            # Verify it's a PDF (some servers send HTML error pages)
            if not content[:4] == b'%PDF':
                # Try to detect if it's an HTML error page
                if b'<html' in content[:500].lower() or b'<!doctype' in content[:500].lower():
                    print(f"   ⚠️ Server returned HTML instead of PDF")
                    return None
                # Some PDFs have whitespace before the header
                if b'%PDF' in content[:100]:
                    pass  # Probably okay
                else:
                    print(f"   ⚠️ Not a valid PDF file (header check failed)")
                    return None
            
            file_hash = self.calculate_file_hash(content)
            
            safe_brand = doc_info['brand'].replace(' ', '_').replace('-', '_')
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-').replace(':', '').replace('%', '').replace('(', '').replace(')', '')
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
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Timeout - server took too long")
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def fetch_all_documents(self) -> Dict:
        """Fetch all final sweep documents"""
        print("=" * 70)
        print("🧠 STRYDA Big Brain - OPERATION FINAL SWEEP (CORRECTED)")
        print("   NZ Local Brands + Bunnings/ITM Ecosystem")
        print("=" * 70)
        
        # Group by brand
        brands = {}
        for doc in FINAL_SWEEP_DOCUMENTS:
            brand = doc['brand']
            if brand not in brands:
                brands[brand] = []
            brands[brand].append(doc)
        
        print(f"\n📚 Target Brands: {len(brands)}")
        for brand, docs in sorted(brands.items()):
            print(f"   • {brand}: {len(docs)} documents")
        
        print(f"\n🏪 Retailer Ecosystem Coverage:")
        for retailer, retailer_brands in FINAL_SWEEP_METADATA['retailer_ecosystem'].items():
            print(f"   • {retailer}: {', '.join(retailer_brands)}")
        
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
                failed.append({
                    "name": doc_info['name'],
                    "brand": doc_info['brand'],
                    "url": doc_info['url']
                })
                brand_stats[brand]["failed"] += 1
        
        # Save manifest
        manifest = {
            "operation": "FINAL_SWEEP_CORRECTED",
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
            for item in failed:
                print(f"      • [{item['brand']}] {item['name']}")
        
        print(f"\n📋 Manifest saved: {manifest_path}")
        print(f"\n🚀 Next Steps:")
        print(f"   1. Run Vision Pipeline: python /app/data/processing/pdf_chunker_v2.py --source_dir {self.output_dir}")
        print(f"   2. Run Ingestor: python /app/data/processing/ingestor.py --source_json <chunks_file>")
        print(f"   3. Update Retrieval Logic with new brand keywords")
        
        return manifest


if __name__ == "__main__":
    connector = FinalSweepConnector()
    connector.fetch_all_documents()
