#!/usr/bin/env python3
"""
STRYDA Big Brain - Ingestion Folder Setup
Creates the physical directory structure for document ingestion
Based on Master Product Manifest Categories A-G
"""

import os
import json
from datetime import datetime

# Base path for ingestion data
BASE_PATH = "/app/data"

# Master Product Manifest Category Structure
CATEGORIES = {
    "A_Structure": {
        "description": "Structural components - framing, fasteners, steel, concrete",
        "subcategories": [
            "Timber_Framing",
            "Steel_Framing", 
            "Fasteners_Fixings",
            "Concrete_Masonry",
            "Foundation_Systems",
            "Structural_Hardware"
        ],
        "example_brands": ["Paslode", "Mitek", "Pryda", "Hyne", "Carter Holt Harvey"]
    },
    "B_Enclosure": {
        "description": "Building envelope - roofing, cladding, windows, insulation",
        "subcategories": [
            "Roofing_Metal",
            "Roofing_Tiles",
            "Wall_Cladding",
            "Windows_Doors",
            "Insulation",
            "Membranes_Wraps",
            "Flashings_Trim"
        ],
        "example_brands": ["Colorsteel", "Monier", "James Hardie", "Thermakraft", "Knauf"]
    },
    "C_Interiors": {
        "description": "Interior systems - plasterboard, flooring, ceilings",
        "subcategories": [
            "Plasterboard_Linings",
            "Flooring_Systems",
            "Ceiling_Systems",
            "Interior_Doors",
            "Wet_Area_Systems",
            "Acoustic_Systems"
        ],
        "example_brands": ["GIB", "Forman", "Armstrong", "Tarkett", "Altro"]
    },
    "D_Landscaping": {
        "description": "External works - decking, fencing, retaining, drainage",
        "subcategories": [
            "Decking_Outdoor",
            "Fencing_Gates",
            "Retaining_Walls",
            "Drainage_Systems",
            "Paving_Hardscape",
            "Garden_Structures"
        ],
        "example_brands": ["Firth", "Keystone", "Ezydeck", "Marley", "Naylor"]
    },
    "E_Specialty": {
        "description": "Specialty systems - fire, HVAC, plumbing, electrical",
        "subcategories": [
            "Fire_Protection",
            "HVAC_Ventilation",
            "Plumbing_Systems",
            "Electrical_Systems",
            "Security_Access",
            "Renewable_Energy"
        ],
        "example_brands": ["Tyco", "Daikin", "Marley", "Clipsal", "Rheem"]
    },
    "F_Manufacturers": {
        "description": "Major manufacturer technical libraries",
        "subcategories": [
            "Installation_Guides",
            "Technical_Data_Sheets",
            "BRANZ_Appraisals",
            "Safety_Data_Sheets",
            "Warranty_Documents",
            "CAD_BIM_Files"
        ],
        "example_brands": ["Multi-brand technical documentation"]
    },
    "G_Merchants": {
        "description": "Merchant-specific product information",
        "subcategories": [
            "PlaceMakers",
            "Mitre10",
            "Bunnings",
            "ITM",
            "Carters",
            "Regional_Merchants"
        ],
        "example_brands": ["Merchant-specific catalogs and guides"]
    }
}

# Document types for classification
DOC_TYPES = [
    "Installation_Guide",
    "Technical_Data_Sheet",
    "BRANZ_Appraisal",
    "Safety_Data_Sheet",
    "Warranty_Document",
    "Product_Catalog",
    "Training_Material",
    "Compliance_Certificate"
]

def create_directory_structure():
    """Create the full ingestion directory structure"""
    print("=" * 60)
    print("🧠 STRYDA Big Brain - Ingestion Folder Setup")
    print("=" * 60)
    
    created_dirs = []
    
    # Create base directories
    ingestion_path = os.path.join(BASE_PATH, "ingestion")
    processing_path = os.path.join(BASE_PATH, "processing")
    archive_path = os.path.join(BASE_PATH, "archive")
    logs_path = os.path.join(BASE_PATH, "logs")
    
    for base_dir in [ingestion_path, processing_path, archive_path, logs_path]:
        os.makedirs(base_dir, exist_ok=True)
        created_dirs.append(base_dir)
    
    print(f"\n📁 Creating category structure in {ingestion_path}...")
    
    # Create category directories with subcategories
    for category_code, category_info in CATEGORIES.items():
        category_path = os.path.join(ingestion_path, category_code)
        os.makedirs(category_path, exist_ok=True)
        created_dirs.append(category_path)
        
        # Create README for category
        readme_path = os.path.join(category_path, "README.md")
        with open(readme_path, "w") as f:
            f.write(f"# {category_code}\n\n")
            f.write(f"**Description:** {category_info['description']}\n\n")
            f.write("## Subcategories\n")
            for sub in category_info['subcategories']:
                f.write(f"- {sub}\n")
            f.write("\n## Example Brands\n")
            for brand in category_info['example_brands']:
                f.write(f"- {brand}\n")
        
        # Create subcategory directories
        for subcategory in category_info['subcategories']:
            subcat_path = os.path.join(category_path, subcategory)
            os.makedirs(subcat_path, exist_ok=True)
            created_dirs.append(subcat_path)
        
        print(f"   ✅ {category_code}: {len(category_info['subcategories'])} subcategories")
    
    # Create scrapers directory
    scrapers_path = os.path.join(BASE_PATH, "scrapers")
    os.makedirs(scrapers_path, exist_ok=True)
    created_dirs.append(scrapers_path)
    
    # Create manifest file
    manifest = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "categories": CATEGORIES,
        "doc_types": DOC_TYPES,
        "paths": {
            "ingestion": ingestion_path,
            "processing": processing_path,
            "archive": archive_path,
            "logs": logs_path,
            "scrapers": scrapers_path
        }
    }
    
    manifest_path = os.path.join(BASE_PATH, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n📋 Created manifest: {manifest_path}")
    print(f"\n✅ Total directories created: {len(created_dirs)}")
    
    # Print summary tree
    print("\n📂 Directory Structure:")
    print(f"   {BASE_PATH}/")
    print(f"   ├── ingestion/")
    for cat in CATEGORIES.keys():
        print(f"   │   ├── {cat}/")
    print(f"   ├── processing/")
    print(f"   ├── archive/")
    print(f"   ├── logs/")
    print(f"   ├── scrapers/")
    print(f"   └── manifest.json")
    
    return created_dirs

def verify_structure():
    """Verify the directory structure exists"""
    print("\n🔍 Verifying structure...")
    
    ingestion_path = os.path.join(BASE_PATH, "ingestion")
    
    if not os.path.exists(ingestion_path):
        print("❌ Ingestion path does not exist!")
        return False
    
    missing = []
    for category in CATEGORIES.keys():
        cat_path = os.path.join(ingestion_path, category)
        if not os.path.exists(cat_path):
            missing.append(category)
    
    if missing:
        print(f"❌ Missing categories: {missing}")
        return False
    
    print("✅ All category directories verified!")
    return True

if __name__ == "__main__":
    create_directory_structure()
    verify_structure()
    print("\n🧠 Big Brain infrastructure ready for ingestion!")
