#!/usr/bin/env python3
"""
STRYDA Big Brain - FIRTH DEEP DIVE
Complete Technical Library for Firth (The Concrete & Masonry Giant)

Categories Covered:
- A_Structure: Foundations (RibRaft, X-Pod), Masonry
- B_Enclosure: Masonry cladding
- G_Landscaping: Paving, Retaining

Vision Pipeline CRITICAL for:
- RibRaft Edge Details
- Masonry Reinforcing Layouts
- Paving Cross-Sections
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
# FIRTH COMPLETE TECHNICAL LIBRARY
# ============================================================================

FIRTH_DOCUMENTS = [
    # =========================================================================
    # CATEGORY A: FOUNDATIONS - RibRaft System
    # =========================================================================
    {
        "name": "RibRaft Technical Manual CodeMark 2024",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/RibRaft-Technical-Manual-CodeMark-2024-web.pdf",
        "product_family": "RibRaft Foundations",
        "doc_type": "Technical_Manual",
        "category": "A_Structure",
        "has_diagrams": True,
        "vision_priority": "HIGH",  # Edge details, reinforcing layouts
    },
    {
        "name": "RibRaft HotEdge Installation Guide",
        "url": "https://productspec.co.nz/media/fuqndu0x/rr-hotedge-installation-guide-interim_web.pdf",
        "product_family": "RibRaft HotEdge",
        "doc_type": "Installation_Guide",
        "category": "A_Structure",
        "has_diagrams": True,
        "vision_priority": "HIGH",
    },
    
    # =========================================================================
    # CATEGORY A: FOUNDATIONS - X-Pod System (TC3)
    # =========================================================================
    {
        "name": "X-Pod Structural Designers Guide July 2025",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/RR-X-Pod-Structural-Designers-Guide-July-2025-Web.pdf",
        "product_family": "X-Pod TC3",
        "doc_type": "Design_Guide",
        "category": "A_Structure",
        "has_diagrams": True,
        "vision_priority": "HIGH",  # TC3 details, soil interaction diagrams
    },
    {
        "name": "X-Pod Installation Guide July 2025",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/RibRaft-X-Pod-Installation-Guide-PRINT-July-2025.pdf",
        "product_family": "X-Pod TC3",
        "doc_type": "Installation_Guide",
        "category": "A_Structure",
        "has_diagrams": True,
        "vision_priority": "HIGH",
    },
    {
        "name": "X-Pod Installers Guide Dec 2018",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Brochures/X-Pod-Installers-Guide-Dec-2018.pdf",
        "product_family": "X-Pod TC3",
        "doc_type": "Installation_Guide",
        "category": "A_Structure",
        "has_diagrams": True,
    },
    
    # =========================================================================
    # CATEGORY A/B: MASONRY SYSTEMS
    # =========================================================================
    {
        "name": "Structural Masonry Product Technical Statement",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/Structural-Masonry-PTS.pdf",
        "product_family": "Structural Masonry",
        "doc_type": "Technical_Data_Sheet",
        "category": "A_Structure",
        "has_diagrams": True,
        "vision_priority": "HIGH",  # Steel spacing, bond beam details
    },
    {
        "name": "Hollow Masonry Brochure 2023",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Brochures/Hollow-Masonry-Brochure_16102023.pdf",
        "product_family": "Hollow Masonry",
        "doc_type": "Product_Catalog",
        "category": "A_Structure",
        "has_diagrams": True,
    },
    {
        "name": "Two Storey Masonry Veneer Solutions",
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/967.pdf",
        "product_family": "Masonry Veneer",
        "doc_type": "Technical_Manual",
        "category": "B_Enclosure",
        "has_diagrams": True,
    },
    
    # =========================================================================
    # CATEGORY G: PAVING SYSTEMS
    # =========================================================================
    {
        "name": "Firth Paving Installation Guide 2025",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/FIRTH-Paving-Installation-Guide-2025-web-v2.pdf",
        "product_family": "Paving",
        "doc_type": "Installation_Guide",
        "category": "G_Landscaping",
        "has_diagrams": True,
        "vision_priority": "HIGH",  # Cross-sections, laying patterns
    },
    {
        "name": "EcoPave Installation Guide Aug 2024",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/Firth-EcoPave-Installation-Guide-Aug-2024_WEB.pdf",
        "product_family": "EcoPave Permeable",
        "doc_type": "Installation_Guide",
        "category": "G_Landscaping",
        "has_diagrams": True,
        "vision_priority": "HIGH",
    },
    {
        "name": "EcoPave Designers Guide",
        "url": "https://productspec.co.nz/media/kp5aibsp/fir0378-ecopave-designers-guide.pdf",
        "product_family": "EcoPave Permeable",
        "doc_type": "Design_Guide",
        "category": "G_Landscaping",
        "has_diagrams": True,
    },
    {
        "name": "Firth Paving Category Flyer 2025",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Documents/Firth-Paving-Category-Flyer-2025-web.pdf",
        "product_family": "Paving",
        "doc_type": "Product_Catalog",
        "category": "G_Landscaping",
        "has_diagrams": True,
    },
    {
        "name": "Firth Paving Concepts Brochure",
        "url": "https://www.firth.co.nz/assets/Uploads/Resources/Brochures/Firth-Paving-Concepts-Brochure.pdf",
        "product_family": "Paving",
        "doc_type": "Product_Catalog",
        "category": "G_Landscaping",
        "has_diagrams": True,
    },
    {
        "name": "Paving and Retaining Outdoor Concepts",
        "url": "https://productspec.co.nz/media/idrhp1qs/firth-paving-retaining-outdoor-concepts-brochure.pdf",
        "product_family": "Paving Retaining",
        "doc_type": "Product_Catalog",
        "category": "G_Landscaping",
        "has_diagrams": True,
    },
]

FIRTH_METADATA = {
    "brand": "Firth",
    "trade": "concrete",
    "retailer_availability": ["PlaceMakers", "Carters", "ITM", "Bunnings", "Allied Concrete", "Universal"],
    "country": "New Zealand",
    "operation": "BRAND_DEEP_DIVE",
}


class FirthDeepDiveConnector:
    """Downloads complete Firth technical library"""
    
    def __init__(self, output_dir: str = "/app/data/ingestion/A_Structure/Firth"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
        })
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create category subdirectories
        for doc in FIRTH_DOCUMENTS:
            cat = doc.get('category', 'A_Structure')
            os.makedirs(os.path.join(output_dir, cat), exist_ok=True)
    
    def download_document(self, doc_info: Dict) -> Optional[Dict]:
        """Download a single document"""
        print(f"\n📥 [{doc_info['product_family']}] {doc_info['name']}...")
        
        try:
            response = self.session.get(doc_info['url'], timeout=120, allow_redirects=True)
            response.raise_for_status()
            
            content = response.content
            
            # Verify PDF
            if not content[:4] == b'%PDF' and b'%PDF' not in content[:100]:
                print(f"   ⚠️ Not a valid PDF")
                return None
            
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Save to category folder
            cat = doc_info.get('category', 'A_Structure')
            safe_name = doc_info['name'].replace(' ', '_').replace('/', '-').replace(':', '')
            filename = f"{safe_name}.pdf"
            filepath = os.path.join(self.output_dir, cat, filename)
            
            with open(filepath, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            record = {
                "source": f"Firth - {doc_info['name']}",
                "brand_name": FIRTH_METADATA['brand'],
                "category_code": cat,
                "product_family": doc_info['product_family'],
                "doc_type": doc_info['doc_type'],
                "trade": FIRTH_METADATA['trade'],
                "original_url": doc_info['url'],
                "local_path": filepath,
                "file_hash": file_hash,
                "file_size_bytes": file_size,
                "retailer_availability": FIRTH_METADATA['retailer_availability'],
                "has_diagrams": doc_info.get('has_diagrams', True),
                "vision_priority": doc_info.get('vision_priority', 'NORMAL'),
                "ingested_at": datetime.now().isoformat(),
                "status": "downloaded",
            }
            
            print(f"   ✅ Downloaded: {filename} ({file_size / 1024:.1f} KB)")
            return record
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def fetch_all_documents(self) -> Dict:
        """Fetch complete Firth library"""
        print("=" * 70)
        print("🏗️ FIRTH DEEP DIVE - Complete Technical Library")
        print("=" * 70)
        print(f"   Brand: {FIRTH_METADATA['brand']}")
        print(f"   Availability: {', '.join(FIRTH_METADATA['retailer_availability'])}")
        print(f"   Documents: {len(FIRTH_DOCUMENTS)}")
        
        # Group by category
        by_category = {}
        for doc in FIRTH_DOCUMENTS:
            cat = doc.get('category', 'A_Structure')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(doc)
        
        print(f"\n📂 Categories:")
        for cat, docs in by_category.items():
            high_priority = sum(1 for d in docs if d.get('vision_priority') == 'HIGH')
            print(f"   • {cat}: {len(docs)} docs ({high_priority} high-priority vision)")
        
        downloaded = []
        failed = []
        
        for doc_info in FIRTH_DOCUMENTS:
            result = self.download_document(doc_info)
            if result:
                downloaded.append(result)
            else:
                failed.append({"name": doc_info['name'], "url": doc_info['url']})
        
        # Save manifest
        manifest = {
            "operation": "FIRTH_DEEP_DIVE",
            "brand": FIRTH_METADATA,
            "fetch_date": datetime.now().isoformat(),
            "documents": downloaded,
            "failed": failed,
            "stats": {
                "total_attempted": len(FIRTH_DOCUMENTS),
                "successful": len(downloaded),
                "failed": len(failed),
                "high_priority_vision": sum(1 for d in downloaded if d.get('vision_priority') == 'HIGH'),
            }
        }
        
        manifest_path = os.path.join(self.output_dir, "manifest_firth_deep_dive.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Summary
        total_size = sum(d['file_size_bytes'] for d in downloaded)
        print(f"\n" + "=" * 70)
        print(f"📊 FIRTH DEEP DIVE SUMMARY")
        print(f"=" * 70)
        print(f"   📦 Downloaded: {len(downloaded)} documents ({total_size / 1024 / 1024:.1f} MB)")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   🔬 High-Priority Vision: {manifest['stats']['high_priority_vision']}")
        print(f"\n   📋 Manifest: {manifest_path}")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Run Vision Pipeline (CRITICAL for edge details)")
        print(f"   2. Ingest with brand='Firth', retailer='Universal'")
        print(f"   3. Test: 'What is the steel spacing for 20 Series Firth block wall?'")
        
        return manifest


if __name__ == "__main__":
    connector = FirthDeepDiveConnector()
    connector.fetch_all_documents()
