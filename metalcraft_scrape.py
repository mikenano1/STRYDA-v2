#!/usr/bin/env python3
"""
Metalcraft Roofing Scraper
===========================
Downloads technical PDFs from Metalcraft Roofing website to Supabase Storage.

Implements STRYDA MASTER PROTOCOL:
- Rule 1: Contextual naming based on profile and document type
- Rule 2: Sanitization (no trademark symbols)
- Rule 7: SKIP ColorSteel supplier documents (already in /00_Material_Suppliers/ColorSteel/)

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import re
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
BUCKET_NAME = "product-library"

print(f"🔗 Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ No SUPABASE_URL")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://www.metalcraftgroup.co.nz"
STORAGE_PREFIX = "B_Enclosure/Metalcraft_Roofing"

# ColorSteel keywords - documents with these are SKIPPED (Rule 7)
COLORSTEEL_SKIP_KEYWORDS = [
    "colorsteel", "colour brochure", "color brochure", "environmental categories",
    "maintenance recommendations", "fire testing", "maxam", "zincalume",
    "colorcote", "dridex", "alumigard", "zinacore", "nz steel"
]

# Universal docs that go to 00_General_Resources (deduplicated across profiles)
UNIVERSAL_KEYWORDS = [
    "nzmrm installation guide", "masterspec", "eco choice certificate",
    "company profile", "profile spec details"
]

# Stats tracking
stats = {
    "profiles_processed": 0,
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped_colorsteel": 0,
    "pdfs_skipped_duplicate": 0,
    "pdfs_skipped_universal": 0,
    "errors": 0,
}

# Track uploaded files for deduplication
uploaded_files = set()
universal_files_uploaded = set()

# Metalcraft profiles and their PDFs (from crawl data)
METALCRAFT_PROFILES = {
    "Espan_340": [
        ("Information Brochure", "https://www.metalcraftgroup.co.nz/media/544130/mc-a4-web-espan-brochuremarch2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/544159/mc-bpir-espan-340-revision-3-220925.pdf"),
        ("Loadspan Tables 0.55mm BMT Steel", "https://www.metalcraftgroup.co.nz/media/544163/loadspantablesespan340feb2018.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523943/pdf-mcrr-espan-340-470-similar.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/544012/pdf-mcrv-espan-340-470-similar.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523939/pdf-mccr-espan-340-470-similar.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/543985/pdf-mccv-espan-340-470-similar.pdf"),
        ("Espan Prickle Details", "https://www.metalcraftgroup.co.nz/media/544190/pdf-metalcraft-espan-340-470-similar-prickle-detailsjan23.pdf"),
        ("Penetration Details", "https://www.metalcraftgroup.co.nz/media/456194/pdf-metalcraft-espan-340-470-similar-penetration-detailsjan23.pdf"),
        ("Loadspan Table Aluminium", "https://www.metalcraftgroup.co.nz/media/544164/espanloadspan340alu06032016.pdf"),
    ],
    "Espan_470": [
        ("Information Brochure", "https://www.metalcraftgroup.co.nz/media/544130/mc-a4-web-espan-brochuremarch2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/544157/mc-bpir-espan-470-revision-3-220925.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544166/espan-470-steel.pdf"),
        ("Loadspan and Fixing Tables Aluminium", "https://www.metalcraftgroup.co.nz/media/544165/espan-470-alufeb2020.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523947/pdf-mcrr-espan-340-470-similar.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/544016/pdf-mcrv-espan-340-470-similar.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523950/pdf-mccr-espan-340-470-similar.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/544008/pdf-mccv-espan-340-470-similar.pdf"),
        ("Espan Prickle Details", "https://www.metalcraftgroup.co.nz/media/544190/pdf-metalcraft-espan-340-470-similar-prickle-detailsjan23.pdf"),
        ("Penetration Details", "https://www.metalcraftgroup.co.nz/media/456194/pdf-metalcraft-espan-340-470-similar-penetration-detailsjan23.pdf"),
    ],
    "Kahu": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544142/mc-kahu-product-flyersept2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541667/mc-bpis-kahu-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/456658/loadspanandfixingtableskahuoctober2023.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523935/pdf-mcrr-kahu.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456153/pdf-metalcraft-kahu-residential-vertical-claddingjan2023.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456152/pdf-metalcraft-kahu-residential-horizontal-claddingjan2023.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523931/pdf-mccr-kahu.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456163/pdf-metalcraft-kahu-commercial-vertical-claddingjan2023.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456161/pdf-metalcraft-kahu-commercial-horizontal-claddingjan2023.pdf"),
    ],
    "Corrugate": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544139/mc-corrugate-product-flyersept2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541671/mc-a4-web-corrugate-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544144/loadspanandfixingtablecorrugate_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523959/pdf-mcrr-corrugate.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456043/metalcraft-corrugate-residential-vertical-claddingjan2023.pdf"),
        ("Residential Vertical Direct Fixed", "https://www.metalcraftgroup.co.nz/media/523850/pdf-mcrvc-corrugate.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456228/metalcraft-corrugate-residential-horizontal-cladding.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523955/pdf-mccr-corrugate.pdf"),
        ("Commercial Vertical Wall Cladding", "https://www.metalcraftgroup.co.nz/media/456041/metalcraft-corrugate-commercial-vertical-claddingjan2023.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/523856/metalcraft-corrugate-commercial-horizontal-cladding.pdf"),
        ("Corrugate Shed Details", "https://www.metalcraftgroup.co.nz/media/544188/pdf-metalcraft-typical-shed-details-corrugate.pdf"),
    ],
    "T_Rib": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541692/mc-t-rib-product-flyersept20241.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541670/mc-bpir-trib-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544147/loadspan-and-fixing-tables-trib_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523991/pdf-mcrr-t-rib.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456317/pdf-metalcraft-t-rib-residential-vertical-claddingupload160323.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456309/pdfmetalcraft-t-rib-residential-horizontal-claddingupload160323.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523987/pdf-mccr-t-rib.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456321/pdfmetalcraft-t-rib-commercial-vertical-claddingupload160323.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456301/pdfmetalcraft-t-rib-commercial-horizontal-claddingupload160323.pdf"),
        ("Trapezoidal Shed Details", "https://www.metalcraftgroup.co.nz/media/544178/pdf-metalcraft-typical-shed-details-trapezoidal.pdf"),
    ],
    "MC760": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544140/mc-mc-760-product-flyersept25.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541662/mc-bpir-mc760-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544146/loadspan-and-fixing-tables-mc760_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523967/pdf-mcrr-mc760.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456073/pdf-metalcraft-mc760-residential-vertical-cladding-jan2023.pdf"),
        ("Residential Horizontal Wall Cladding", "https://www.metalcraftgroup.co.nz/media/456089/pdf-metalcraft-mc760-residential-horizontal-claddingan2023.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523962/pdf-mccr-mc760.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456075/pdf-metalcraft-mc760-commercial-vertical-claddingjan2023.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456096/pdf-metalcraft-mc760-commercial-horizontal-claddingjan2023.pdf"),
        ("Trapezoidal Shed Details", "https://www.metalcraftgroup.co.nz/media/544176/pdf-metalcraft-typical-shed-details-trapezoidal.pdf"),
    ],
    "Metrib_760": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541695/mc-metrib-760-product-flyersept2024.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541660/mc-bpir-metrib-760-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544145/loadspanandfixingtablesmetrib760_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523983/pdf-mcrr-metrib-760.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456401/pdfmetalcraft-metrib-760-residential-vertical-claddingupload160323.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456394/pdfmetalcraft-metrib-760-residential-horizontal-claddingupload160323.pdf"),
    ],
    "MC1000": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541687/mc-mc-1000-product-flyersept2024.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541672/mc-bpir-mc1000-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544150/loadspanandfixingtablemc1000_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523975/pdf-mcrr-mc1000.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456541/pdf-metalcraft-mc1000-residential-vertical-claddingjan23uploaded120523.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456546/pdf-metalcraft-mc1000-residential-horizontal-claddingjan23uploaded120523.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523971/pdf-mccr-mc1000.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456529/pdf-metalcraft-mc1000-commercial-vertical-claddingjan23-uploaded120523.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456526/pdf-metalcraft-mc1000-commercial-horizontal-claddingjan23uploaded120523.pdf"),
    ],
    "Metcom_7": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541697/mc-metcom-7-product-flyersept2024.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541664/mc-bpir-metcom-7-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544143/loadspanandfixingtablesmetcom7_19sept25.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/523999/pdf-mcrr-metcom-7.pdf"),
        ("Residential Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456244/pdf-metalcraft-metcom-7-residential-horizontal-cladding-uploadmarch-23.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456257/pdf-metalcraft-metcom-7-residential-vertical-cladding-upload-march-23.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523995/pdf-mccr-metcom-7.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456254/pdf-metalcraft-metcom-7-commercial-horizontal-cladding-uploadmarch23.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456241/pdf-metalcraft-metcom-7-commercial-vertical-cladding-upload-march-23.pdf"),
    ],
    "Metcom_965": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544137/mc965-product-flyersept2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541665/mc-bpir-metcom-965-revision-2-050924.pdf"),
        ("Loadspan and Fixing Table", "https://www.metalcraftgroup.co.nz/media/544191/metcom965loadspantableaugust2019.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/524015/pdf-mccr-metcom-965.pdf"),
        ("Commercial Vertical Cladding", "https://www.metalcraftgroup.co.nz/media/456356/pdfmetalcraft-metcom-965-commercial-vertical-claddinguploaded160323.pdf"),
        ("Commercial Horizontal Cladding", "https://www.metalcraftgroup.co.nz/media/456353/pdfmetalcraft-metcom-965-commercial-horizontal-claddinguploaded160323.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/524019/pdf-mcrr-metcom-965.pdf"),
        ("Residential Vertical Cladding", "https://www.metalcraftgroup.co.nz/media/456344/pdfmetalcraft-metcom-965-residentail-vertical-claddinguploaded160323.pdf"),
        ("Residential Horizontal Cladding", "https://www.metalcraftgroup.co.nz/media/456349/pdfmetalcraft-metcom-965-residential-horizontal-claddinguploaded160323.pdf"),
    ],
    "Metdek_500": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544141/mc-metdek-500-product-flyersept2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/544158/mc-bpir-metdek-500-revision-3-220925.pdf"),
        ("Loadspan and Fixing Tables", "https://www.metalcraftgroup.co.nz/media/544160/mc-metdek-500-product-loadspan-september-2025.pdf"),
        ("Residential Roof Details", "https://www.metalcraftgroup.co.nz/media/524011/pdf-mcrr-metdek-500.pdf"),
        ("Residential Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456380/pdfmetalcraft-metdek-500-residential-vertical-claddingupload160323.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/524007/pdf-mccr-metdek-500.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456372/pdfmetalcraft-metdek-500-commercial-vertical-claddingupload160323.pdf"),
    ],
    "Metdek_855": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541693/mc-metdek-855-product-flyersept2024.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/544161/mc-bpir-metdek-855-revision-3-220925.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/523979/pdf-mccr-metdek-855.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456389/pdf-metalcraft-metdek-855-commercial-vertical-claddingupload160323.pdf"),
    ],
    "Metcom_930": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/541694/mc-metcom-930-product-flyersept2024.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541663/mc-bpir-metcom-930-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544149/loadspansandfixingtablesmetcom930_19sept25.pdf"),
        ("Commercial Roof Details", "https://www.metalcraftgroup.co.nz/media/524001/pdf-mccr-metcom-930.pdf"),
        ("Commercial Vertical Details", "https://www.metalcraftgroup.co.nz/media/456336/pdf-metalcraft-metcom-930-commercial-vertical-claddinguploaded160323.pdf"),
        ("Commercial Horizontal Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456329/pdfmetalcraft-metcom-930-commercial-horizontal-cladding160323.pdf"),
    ],
    "Metclad_850": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544138/mc-metclad-850-product-flyersept2025.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541659/mc-bpir-metclad-850-revision-2-050924.pdf"),
        ("Loadspan and Fixing Tables Steel", "https://www.metalcraftgroup.co.nz/media/544148/loadspansandfixingstablesmetclad850_19sept25.pdf"),
        ("Commercial Vertical Wall Cladding Details", "https://www.metalcraftgroup.co.nz/media/456324/pdfmetalcraft-metalclad-850-commerical-verticaluploaded160323.pdf"),
    ],
    "Bevelback_Weatherboard": [
        ("Product Flyer", "https://www.metalcraftgroup.co.nz/media/544136/mc-bevelback-weatherboard-product-flyersept25.pdf"),
        ("BPIS Building Product Information Sheet", "https://www.metalcraftgroup.co.nz/media/541668/mc-bpir-bevelback-revision-2-050924.pdf"),
        ("Residential Horizontal Details", "https://www.metalcraftgroup.co.nz/media/456296/pdfmetalcraft-bevelback-weatherboard-residential-horizontal160323.pdf"),
        ("Commercial Horizontal Details", "https://www.metalcraftgroup.co.nz/media/456291/pdfmetalcraft-bevelback-weatherboards-commercial-horizontaluploaded160323.pdf"),
        ("Bevelback Data Sheet", "https://www.metalcraftgroup.co.nz/media/544197/mc-bevelback-weatherboard-spec-sheetsept2020.pdf"),
    ],
    "Ceiling_Batten": [
        ("Installation Guide", "https://www.metalcraftgroup.co.nz/media/544112/mc-6pp-batten-brochure-web10032025.pdf"),
        ("Branz Appraisal", "https://www.metalcraftgroup.co.nz/media/456734/mc-ceiling-batten-branz-appraisal-981_2022.pdf"),
    ],
    "Roof_Batten_MCRB40": [
        ("Design Guide and Loadspan Tables on Timber Trusses", "https://www.metalcraftgroup.co.nz/media/544192/mc-batten-design-and-installation-guide-brochure-04112025-web.pdf"),
        ("Specific Design Guide", "https://www.metalcraftgroup.co.nz/media/544193/mc-batten-specific-design-brochure-04112025-web.pdf"),
        ("Residential Roof Details for Metal Tiles", "https://www.metalcraftgroup.co.nz/media/544053/pdf-mc-rb40-roof-batten-metal-tiles.pdf"),
        ("Residential Roof Details for Long Run", "https://www.metalcraftgroup.co.nz/media/544057/pdf-mc-rb40-roof-batten-long-run-roofing.pdf"),
    ],
}

# Universal resources (stored once in 00_General_Resources)
UNIVERSAL_RESOURCES = [
    ("Eco Choice Certificate", "https://www.metalcraftgroup.co.nz/media/544119/nz-steel-ec-57-certificate-may-26.pdf"),
    ("NZMRM Installation Guide", "https://www.metalcraftgroup.co.nz/media/456689/nzmrm-installationmrmmay2022-2.pdf"),
    ("Masterspec Specification Links", "https://www.metalcraftgroup.co.nz/media/456687/mc-masterspec-roofing-links-nov23-uploaded-081123.pdf"),
    ("Company Profile", "https://www.metalcraftgroup.co.nz/media/1002/mc-company-profilejune2020.pdf"),
]


def sanitize_filename(name):
    """Clean filename - remove trademark symbols and invalid chars"""
    name = name.replace('™', '').replace('®', '').replace('©', '')
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 200:
        name = name[:200]
    return name


def is_colorsteel_doc(doc_title):
    """Check if document is a ColorSteel supplier document (Rule 7)"""
    title_lower = doc_title.lower()
    for keyword in COLORSTEEL_SKIP_KEYWORDS:
        if keyword in title_lower:
            return True
    return False


def is_universal_doc(doc_title):
    """Check if document is a universal resource"""
    title_lower = doc_title.lower()
    for keyword in UNIVERSAL_KEYWORDS:
        if keyword in title_lower:
            return True
    return False


def file_exists_in_supabase(storage_path):
    """Check if file already exists in Supabase storage"""
    try:
        result = supabase.storage.from_(BUCKET_NAME).list(path="/".join(storage_path.split("/")[:-1]))
        filename = storage_path.split("/")[-1]
        return any(f.get('name') == filename for f in result)
    except Exception:
        return False


def upload_to_supabase(pdf_url, storage_path, doc_title):
    """Download PDF and upload to Supabase storage"""
    try:
        # Download PDF
        print(f"  📥 Downloading: {doc_title[:50]}...")
        response = requests.get(pdf_url, timeout=60)
        if response.status_code != 200:
            print(f"  ❌ Failed to download (HTTP {response.status_code})")
            stats["errors"] += 1
            return False
        
        pdf_content = response.content
        
        # Check if it's actually a PDF
        if not pdf_content[:4] == b'%PDF':
            print(f"  ⚠️ Not a valid PDF file")
            stats["errors"] += 1
            return False
        
        # Upload to Supabase
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                storage_path,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            print(f"  ✅ Uploaded: {storage_path}")
            return True
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e).lower():
                print(f"  ⏭️ Already exists: {storage_path}")
                stats["pdfs_skipped_duplicate"] += 1
                return False
            else:
                print(f"  ❌ Upload error: {e}")
                stats["errors"] += 1
                return False
                
    except Exception as e:
        print(f"  ❌ Error: {e}")
        stats["errors"] += 1
        return False


def process_profile(profile_name, documents):
    """Process all documents for a profile"""
    print(f"\n📁 Processing profile: {profile_name}")
    stats["profiles_processed"] += 1
    
    profile_folder = f"{STORAGE_PREFIX}/{profile_name}"
    
    for doc_title, pdf_url in documents:
        stats["pdfs_found"] += 1
        
        # Rule 7: Skip ColorSteel supplier documents
        if is_colorsteel_doc(doc_title):
            print(f"  ⏭️ SKIPPED (ColorSteel): {doc_title[:40]}...")
            stats["pdfs_skipped_colorsteel"] += 1
            continue
        
        # Skip universal docs (handled separately)
        if is_universal_doc(doc_title):
            print(f"  ⏭️ SKIPPED (Universal): {doc_title[:40]}...")
            stats["pdfs_skipped_universal"] += 1
            continue
        
        # Generate filename
        clean_title = sanitize_filename(doc_title)
        filename = f"{profile_name} - {clean_title}.pdf"
        storage_path = f"{profile_folder}/{filename}"
        
        # Check for duplicates (same URL already uploaded)
        if pdf_url in uploaded_files:
            print(f"  ⏭️ SKIPPED (Duplicate URL): {clean_title[:40]}...")
            stats["pdfs_skipped_duplicate"] += 1
            continue
        
        # Upload
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            uploaded_files.add(pdf_url)
        
        time.sleep(0.5)  # Rate limiting


def process_universal_resources():
    """Upload universal resources to 00_General_Resources folder"""
    print(f"\n📁 Processing Universal Resources (00_General_Resources)")
    
    general_folder = f"{STORAGE_PREFIX}/00_General_Resources"
    
    for doc_title, pdf_url in UNIVERSAL_RESOURCES:
        stats["pdfs_found"] += 1
        
        if pdf_url in universal_files_uploaded:
            print(f"  ⏭️ SKIPPED (Already uploaded): {doc_title}")
            continue
        
        clean_title = sanitize_filename(doc_title)
        filename = f"Metalcraft - {clean_title}.pdf"
        storage_path = f"{general_folder}/{filename}"
        
        if upload_to_supabase(pdf_url, storage_path, doc_title):
            stats["pdfs_uploaded"] += 1
            universal_files_uploaded.add(pdf_url)
        
        time.sleep(0.5)


def main():
    """Main scraping function"""
    print("=" * 60)
    print("🏭 METALCRAFT ROOFING SCRAPER")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Storage: {BUCKET_NAME}/{STORAGE_PREFIX}")
    print(f"Profiles to process: {len(METALCRAFT_PROFILES)}")
    print()
    print("⚠️  RULE 7 ACTIVE: ColorSteel documents will be SKIPPED")
    print("    (Already centralized in /00_Material_Suppliers/ColorSteel/)")
    print("=" * 60)
    
    # Process universal resources first
    process_universal_resources()
    
    # Process each profile
    for profile_name, documents in METALCRAFT_PROFILES.items():
        process_profile(profile_name, documents)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SCRAPING SUMMARY")
    print("=" * 60)
    print(f"Profiles processed:        {stats['profiles_processed']}")
    print(f"PDFs found:                {stats['pdfs_found']}")
    print(f"PDFs uploaded:             {stats['pdfs_uploaded']}")
    print(f"PDFs skipped (ColorSteel): {stats['pdfs_skipped_colorsteel']}")
    print(f"PDFs skipped (duplicate):  {stats['pdfs_skipped_duplicate']}")
    print(f"PDFs skipped (universal):  {stats['pdfs_skipped_universal']}")
    print(f"Errors:                    {stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
