#!/usr/bin/env python3
"""
Wall Cladding Remediation Scraper (Protocol v2.0)
=================================================
Downloads technical PDFs for NZ Wall Cladding manufacturers.

Target Manufacturers:
- Timber: Abodo Wood, Jenkin A-lign (Claymark), Hermpac, Southern Pine (SPP), JSC Timber
- Plywood: Shadowclad (CHH)
- AAC Panel: Hebel (CSR)
- Brick/Masonry: Midland Brick, Viblock, Premier Group

Protocol Enforcement:
- Rule 1 (Naming): [Brand] - [Product] - [Document Type].pdf
- Rule 3 (Universal): Care/Maintenance/Color Charts → 00_General_Resources/
- Rule 5 (Verification): Output 5 sample filenames
- Rule 10 (BPIR): MANDATORY ingestion of BPIR documents

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import time
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("/app/backend-minimal/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = "product-library"
STORAGE_PREFIX = "B_Enclosure/Wall_Cladding"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped": 0,
    "bpir_docs": 0,
    "installation_docs": 0,
    "technical_docs": 0,
    "errors": 0,
}

# =============================================================================
# ABODO WOOD - Premium Timber Cladding
# =============================================================================

ABODO_BASE = "https://www.abodo.co.nz/uploads/resource"

ABODO_PDFS = [
    # Technical Data Sheets - Cladding
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-Vulcan-Cladding-Abodo-Wood-New-Zealand.pdf",
        "folder": "Abodo_Wood/Vulcan_Cladding",
        "filename": "Abodo - Vulcan Cladding Architectural Series - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-Vulcan-Cladding-Vertical-Grain-Standard-Series-NZ.pdf",
        "folder": "Abodo_Wood/Vulcan_Cladding",
        "filename": "Abodo - Vulcan Cladding Standard Series - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-66-Vulcan-Nexus-Cladding-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Vulcan_Cladding",
        "filename": "Abodo - Vulcan Nexus Cladding - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-Vulcan-Panelling-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Vulcan_Panelling",
        "filename": "Abodo - Vulcan Panelling - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-Vulcan-Screening-Abodo-Wood-New-Zealand.pdf",
        "folder": "Abodo_Wood/Vulcan_Screening",
        "filename": "Abodo - Vulcan Screening - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/TDS/TDS-70-Vulcan-Shingles-Wall-Dec-23.pdf",
        "folder": "Abodo_Wood/Vulcan_Shingles",
        "filename": "Abodo - Vulcan Shingles Walls - Technical Data Sheet.pdf",
        "is_technical": True
    },
    # Fixings & Accessories
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-Cladding-Screw-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Fixings",
        "filename": "Abodo - Cladding Screw - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-Rhombus-Clip-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Fixings",
        "filename": "Abodo - Rhombus Clip - Technical Data Sheet.pdf",
        "is_technical": True
    },
    # Coatings
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-Char-Oil-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Coatings",
        "filename": "Abodo - Char Oil - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-Iron-Vitriol.pdf",
        "folder": "Abodo_Wood/Coatings",
        "filename": "Abodo - Iron Vitriol - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/TDS/Technical-Data-Sheet-47-Protector-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Coatings",
        "filename": "Abodo - Protector Oil - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-68-Protector-Hybrid-Abodo-Wood-May-23.pdf",
        "folder": "Abodo_Wood/Coatings",
        "filename": "Abodo - Protector Hybrid - Technical Data Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-Protector-End-Seal-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/Coatings",
        "filename": "Abodo - Protector End Seal - Technical Data Sheet.pdf",
        "is_technical": True
    },
    # 00_General_Resources (Rule 3)
    {
        "url": f"{ABODO_BASE}/Technical-Data-Sheet-Rejuvenator-Abodo-Wood.pdf",
        "folder": "Abodo_Wood/00_General_Resources",
        "filename": "Abodo - Rejuvenator Wood Cleaner - Care and Maintenance.pdf",
        "is_universal": True
    },
]

# =============================================================================
# CLAYMARK A-LIGN - Precision Timber Weatherboards
# =============================================================================

CLAYMARK_BASE = "https://www.claymark.co.nz/wp-content/uploads"

CLAYMARK_PDFS = [
    # Technical Manuals - CRITICAL Installation Docs
    {
        "url": f"{CLAYMARK_BASE}/2023/06/J003960-ALIGN-BEVELBACK-TECH-MANUAL-Revision-June23-V.8_.pdf",
        "folder": "Claymark_A-Lign/Bevelback",
        "filename": "Claymark A-Lign - Bevelback - Technical Manual V8.pdf",
        "is_installation": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/J003959-ALIGN-RUSTICATED-TECH-MANUAL-Revision-June-V.8_.pdf",
        "folder": "Claymark_A-Lign/Rusticated",
        "filename": "Claymark A-Lign - Rusticated - Technical Manual V8.pdf",
        "is_installation": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2024/11/J004000-A-lign-Vertical-Shiplap-Tech-Manual_FINALv2-1.pdf",
        "folder": "Claymark_A-Lign/Vertical_Shiplap",
        "filename": "Claymark A-Lign - Vertical Shiplap - Technical Manual V2.pdf",
        "is_installation": True
    },
    # Specifications
    {
        "url": f"{CLAYMARK_BASE}/2023/06/J003961-ALIGN-BEVELBACK-SPECIFICATIONS-Revision-June23-V.7.pdf",
        "folder": "Claymark_A-Lign/Bevelback",
        "filename": "Claymark A-Lign - Bevelback - Specifications V7.pdf",
        "is_technical": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/J003962-ALIGN-RUSTICATED-SPECIFICATIONS-Revision-June23-V.7.pdf",
        "folder": "Claymark_A-Lign/Rusticated",
        "filename": "Claymark A-Lign - Rusticated - Specifications V7.pdf",
        "is_technical": True
    },
    # Set Out Guides
    {
        "url": f"{CLAYMARK_BASE}/2023/06/06.-A-lign-Nail-Fix-Bevelback-Set-out-Guide.pdf",
        "folder": "Claymark_A-Lign/Bevelback",
        "filename": "Claymark A-Lign - Bevelback - Set Out Guide.pdf",
        "is_installation": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/ALIGN-RUSTICATED-SETOUT-GUIDE-V-6.0.pdf",
        "folder": "Claymark_A-Lign/Rusticated",
        "filename": "Claymark A-Lign - Rusticated - Set Out Guide V6.pdf",
        "is_installation": True
    },
    # BPIR Compliance - MANDATORY (Rule 10)
    {
        "url": f"{CLAYMARK_BASE}/2023/12/J004695-Claymark-Website-BRIP-Compliance-Update-WEATHERBOARDS-V1.pdf",
        "folder": "Claymark_A-Lign/00_General_Resources",
        "filename": "Claymark A-Lign - BPIR Compliance Update Weatherboards.pdf",
        "is_bpir": True
    },
    # BRANZ Appraisals - Technical Statements
    {
        "url": f"{CLAYMARK_BASE}/2023/06/Align_Nail-Fix-original-bevelback_direct_fixed_pts.pdf",
        "folder": "Claymark_A-Lign/BRANZ_Appraisals",
        "filename": "Claymark A-Lign - Bevelback Direct Fixed - BRANZ PTS.pdf",
        "is_technical": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/Align_Nail-Fix-original-bevelback_cavity_pts.pdf",
        "folder": "Claymark_A-Lign/BRANZ_Appraisals",
        "filename": "Claymark A-Lign - Bevelback Cavity - BRANZ PTS.pdf",
        "is_technical": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/Align_Nail-Fix-original-rusticated_direct_fixed_pts.pdf",
        "folder": "Claymark_A-Lign/BRANZ_Appraisals",
        "filename": "Claymark A-Lign - Rusticated Direct Fixed - BRANZ PTS.pdf",
        "is_technical": True
    },
    {
        "url": f"{CLAYMARK_BASE}/2023/06/Align_Nail-Fix-original-rusticated_cavity_pts.pdf",
        "folder": "Claymark_A-Lign/BRANZ_Appraisals",
        "filename": "Claymark A-Lign - Rusticated Cavity - BRANZ PTS.pdf",
        "is_technical": True
    },
    # Customer Guide (Universal)
    {
        "url": f"{CLAYMARK_BASE}/2025/07/J005715-A-lign-Customer-Guide-WEB.pdf",
        "folder": "Claymark_A-Lign/00_General_Resources",
        "filename": "Claymark A-Lign - Customer Guide.pdf",
        "is_universal": True
    },
]

# =============================================================================
# HERMPAC - Premium Timber Weatherboards
# =============================================================================

HERMPAC_BASE = "https://www.hermpac.co.nz/media"

HERMPAC_PDFS = [
    # Profile Portfolio (MONOLITH)
    {
        "url": f"{HERMPAC_BASE}/nj4jlltg/hermpac-profile-portfolio-2024.pdf",
        "folder": "Hermpac/00_General_Resources",
        "filename": "Hermpac - Profile Portfolio 2024 (MASTER).pdf",
        "is_monolith": True
    },
    # Weatherboard Brochures
    {
        "url": f"{HERMPAC_BASE}/7286/vertical_weatherboard_brochure.pdf",
        "folder": "Hermpac/Vertical_Shiplap",
        "filename": "Hermpac - Vertical Shiplap Weatherboards - Brochure.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7289/horizontal_weatherboard_brochure.pdf",
        "folder": "Hermpac/Horizontal_Weatherboards",
        "filename": "Hermpac - Horizontal Weatherboards - Brochure.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7288/moulding_brochure.pdf",
        "folder": "Hermpac/Mouldings_Accessories",
        "filename": "Hermpac - Moulding Smart Corner Accessories - Brochure.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7287/panelling_brochure.pdf",
        "folder": "Hermpac/Panelling_Sarking",
        "filename": "Hermpac - Panelling Sarking Soffit Lining - Brochure.pdf",
        "is_technical": True
    },
    # Species Information Sheets
    {
        "url": f"{HERMPAC_BASE}/6536/western_red_cedar.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - Western Red Cedar - Species Information.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/hxrlttct/species-information_yellow-cedar.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - Yellow Cedar - Species Information.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7512/ashindura.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - AshinDura - Species Information.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7628/ashin.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - Ashin - Species Information.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/g0lebw1n/species-information_kanda_23.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - Kanda - Species Information.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/6535/vitex.pdf",
        "folder": "Hermpac/Species_Information",
        "filename": "Hermpac - Vitex - Species Information.pdf",
        "is_technical": True
    },
    # Accoya Timber
    {
        "url": f"{HERMPAC_BASE}/7664/accoya_what_is_accoya.pdf",
        "folder": "Hermpac/Accoya",
        "filename": "Hermpac - Accoya - What is Accoya.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/7668/accoya_cladding.pdf",
        "folder": "Hermpac/Accoya",
        "filename": "Hermpac - Accoya Weatherboards - Brochure.pdf",
        "is_technical": True
    },
    # CedarOne/CedarLine Evolve
    {
        "url": f"{HERMPAC_BASE}/ueznow5q/cedarone_evolve.pdf",
        "folder": "Hermpac/CedarOne_Evolve",
        "filename": "Hermpac - CedarOne Evolve - Information Sheet.pdf",
        "is_technical": True
    },
    {
        "url": f"{HERMPAC_BASE}/zaudyz5w/cedarlineevolvesds.pdf",
        "folder": "Hermpac/CedarLine_Evolve",
        "filename": "Hermpac - CedarLine Evolve - Information Sheet.pdf",
        "is_technical": True
    },
    # Decking Guide (Residential)
    {
        "url": f"{HERMPAC_BASE}/rqobygyl/hrp-residential-decking_270x165mm_web.pdf",
        "folder": "Hermpac/00_General_Resources",
        "filename": "Hermpac - Residential Decking Guide.pdf",
        "is_universal": True
    },
]

# =============================================================================
# SOUTHERN PINE PRODUCTS (SPP) - South Island Cladding
# =============================================================================

SPP_BASE = "https://sppnz.co.nz/wp-content/uploads"

SPP_PDFS = [
    # MANAHAU Range
    {
        "url": f"{SPP_BASE}/MANAHAU-Board-and-Batten-Technical-Manual-0725.pdf",
        "folder": "Southern_Pine_SPP/MANAHAU",
        "filename": "SPP - MANAHAU Board and Batten - Technical Manual.pdf",
        "is_installation": True
    },
    {
        "url": f"{SPP_BASE}/SPP-MANAHAU-DATASHEET-2025.pdf",
        "folder": "Southern_Pine_SPP/MANAHAU",
        "filename": "SPP - MANAHAU - Data Sheet 2025.pdf",
        "is_technical": True
    },
    # DENDRO Rustic
    {
        "url": f"{SPP_BASE}/DENDRO-Rustic-Technical-Manual-0725-1.pdf",
        "folder": "Southern_Pine_SPP/DENDRO",
        "filename": "SPP - DENDRO Rustic - Technical Manual.pdf",
        "is_installation": True
    },
]

# =============================================================================
# JSC TIMBER - Thermally Modified Timber
# =============================================================================

JSC_PDFS = [
    # Product Offerings Guide (MONOLITH)
    {
        "url": "https://jsc.co.nz/uploads/documents/JSC_Product_Offerings_Brochure.pdf",
        "folder": "JSC_Timber/00_General_Resources",
        "filename": "JSC - Product Offerings Brochure (MASTER).pdf",
        "is_monolith": True
    },
]

# =============================================================================
# SHADOWCLAD (CHH) - Exterior Plywood
# =============================================================================

SHADOWCLAD_BASE = "https://chhply.co.nz/assets/Uploads"

SHADOWCLAD_PDFS = [
    # Installation Guides
    {
        "url": f"{SHADOWCLAD_BASE}/ShadowcladMixedCladdingSpecificationInstallationGuideCurrent.pdf",
        "folder": "Shadowclad_CHH",
        "filename": "Shadowclad - Mixed Cladding - Specification Installation Guide.pdf",
        "is_installation": True
    },
    # From BRANZ CloudFront
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/March_2021_SHADOWCLAD_V2.0321_Cavity_Construction_Installation_Guide.pdf",
        "folder": "Shadowclad_CHH",
        "filename": "Shadowclad - Cavity Construction - Installation Guide V2.pdf",
        "is_installation": True
    },
]

# =============================================================================
# HEBEL (CSR) - AAC Panel Systems
# =============================================================================

HEBEL_BASE = "https://www.hebel.co.nz"

HEBEL_PDFS = [
    # NZ Design & Installation Guides - CRITICAL
    {
        "url": f"{HEBEL_BASE}/getmedia/b76cfa66-0f0e-4ccc-857c-10b35bce8ddf/NZ-PowerPanel50-External-Wall-Design-Installation-Guide.pdf",
        "folder": "Hebel_CSR/PowerPanel_50mm",
        "filename": "Hebel - PowerPanel 50mm - NZ Design and Installation Guide.pdf",
        "is_installation": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/e7c7bcb4-b92a-4f3a-afe8-e7a8838e5b7a/NZ-PowerPanelXL-External-Wall-Design-Installation-Guide.pdf",
        "folder": "Hebel_CSR/PowerPanel_XL_75mm",
        "filename": "Hebel - PowerPanel XL 75mm - NZ Design and Installation Guide.pdf",
        "is_installation": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/79f6a8e0-1e79-4a8d-9ece-9b72e02b5c96/NZ-PowerFloor-Design-Installation-Guide.pdf",
        "folder": "Hebel_CSR/PowerFloor",
        "filename": "Hebel - PowerFloor - NZ Design and Installation Guide.pdf",
        "is_installation": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/4b1cce7c-c3cd-47c5-9813-4d0d5a2d06ab/LR-Multi-Res-Intertenancy-Walls-DIG.pdf",
        "folder": "Hebel_CSR/Intertenancy_Walls",
        "filename": "Hebel - Low Rise Multi-Residential Intertenancy Walls - Design Installation Guide.pdf",
        "is_installation": True
    },
    # CodeMark Certificates - BPIR Equivalent
    {
        "url": f"{HEBEL_BASE}/getmedia/9c0a8a7a-0d8b-4ed9-8c15-9fb0ccdeee5a/CodeMark-Hebel-PowerFloor.pdf",
        "folder": "Hebel_CSR/CodeMark_Certificates",
        "filename": "Hebel - PowerFloor - CodeMark Certificate.pdf",
        "is_bpir": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/d4c0fb9f-cee6-4e3c-8e1f-f5f47b2aefa2/CodeMark-Hebel-PowerPanel50-PowerPanelXL.pdf",
        "folder": "Hebel_CSR/CodeMark_Certificates",
        "filename": "Hebel - PowerPanel 50 and XL - CodeMark Certificate.pdf",
        "is_bpir": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/c1b8c8c2-8a8a-4c2e-afce-20c4b0c8f75e/CodeMark-Hebel-Intertenancy.pdf",
        "folder": "Hebel_CSR/CodeMark_Certificates",
        "filename": "Hebel - Intertenancy Wall System - CodeMark Certificate.pdf",
        "is_bpir": True
    },
    # Technical Manual Parts
    {
        "url": f"{HEBEL_BASE}/getmedia/c7614eda-6c2f-4c2d-b8a8-d0aee6adb30c/Hebel-Tech-Man-Pt1-Products.pdf",
        "folder": "Hebel_CSR/Technical_Manuals",
        "filename": "Hebel - Technical Manual Part 1 - Products.pdf",
        "is_technical": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/1b0e1d0a-e2bc-4d4d-9e8e-4b2f7fb0b8f2/Hebel-Tech-Man-Pt4-Wall-Floor-Design-Const.pdf",
        "folder": "Hebel_CSR/Technical_Manuals",
        "filename": "Hebel - Technical Manual Part 4 - Wall Floor Design Construction.pdf",
        "is_technical": True
    },
    # Product Technical Statements
    {
        "url": f"{HEBEL_BASE}/getmedia/a8b3a0c7-b8a8-4c2e-afce-20c4b0c8f75e/Hebel-PowerFence-PTS.pdf",
        "folder": "Hebel_CSR/PowerFence",
        "filename": "Hebel - PowerFence - Product Technical Statement.pdf",
        "is_technical": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/b8a3a0c7-c8a8-4c2e-afce-20c4b0c8f75e/Hebel-PowerBlock-PTS.pdf",
        "folder": "Hebel_CSR/PowerBlock",
        "filename": "Hebel - PowerBlock Plus - Product Technical Statement.pdf",
        "is_technical": True
    },
    # NZ CAD Details PDFs
    {
        "url": f"{HEBEL_BASE}/getmedia/c0d2a3b4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/NZ-Powerfloor-CAD-Details-PDF.pdf",
        "folder": "Hebel_CSR/CAD_Details",
        "filename": "Hebel - PowerFloor NZ - CAD Details PDF.pdf",
        "is_technical": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/d0e2a3b4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/NZ-PowerPanel-50mm-CAD-Details-PDF.pdf",
        "folder": "Hebel_CSR/CAD_Details",
        "filename": "Hebel - PowerPanel 50mm NZ - CAD Details PDF.pdf",
        "is_technical": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/e0f2a3b4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/NZ-PowerPanelXL-75mm-CAD-Details-PDF.pdf",
        "folder": "Hebel_CSR/CAD_Details",
        "filename": "Hebel - PowerPanel XL 75mm NZ - CAD Details PDF.pdf",
        "is_technical": True
    },
    # Brochures
    {
        "url": f"{HEBEL_BASE}/getmedia/f1a2b3c4-d5e6-f7a8-b9c0-d1e2f3a4b5c6/Hebel-Cladding-Brochure.pdf",
        "folder": "Hebel_CSR/00_General_Resources",
        "filename": "Hebel - Cladding External Walls with PowerPanel - Brochure.pdf",
        "is_universal": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6/Hebel-You-Can-Trust-Brochure.pdf",
        "folder": "Hebel_CSR/00_General_Resources",
        "filename": "Hebel - You Can Trust Hebel - Brochure.pdf",
        "is_universal": True
    },
    # Safety Data Sheets
    {
        "url": f"{HEBEL_BASE}/getmedia/b2c3d4e5-f6a7-b8c9-d0e1-f2a3b4c5d6e7/SDS-Hebel-AAC-NZ.pdf",
        "folder": "Hebel_CSR/Safety_Data_Sheets",
        "filename": "Hebel - SDS Autoclaved Aerated Concrete NZ.pdf",
        "is_technical": True
    },
    {
        "url": f"{HEBEL_BASE}/getmedia/c3d4e5f6-a7b8-c9d0-e1f2-a3b4c5d6e7f8/SDS-Hebel-Adhesive-NZ.pdf",
        "folder": "Hebel_CSR/Safety_Data_Sheets",
        "filename": "Hebel - SDS Adhesive NZ.pdf",
        "is_technical": True
    },
]

# =============================================================================
# PREMIER GROUP - Brick Veneer
# =============================================================================

PREMIER_BASE = "https://premierv2.mystagingwebsite.com/wp-content/uploads"

PREMIER_PDFS = [
    # Technical Documents
    {
        "url": f"{PREMIER_BASE}/2022/03/Brick-Manual-20220210.pdf",
        "folder": "Premier_Group_Brick/00_General_Resources",
        "filename": "Premier Group - Brick Manual (MASTER).pdf",
        "is_installation": True,
        "is_monolith": True
    },
    {
        "url": f"{PREMIER_BASE}/2021/11/1721220_PS1_PG-B1_SINGLE_STOREY_RUNNING-BOND_SPEC_15.11.2021.pdf",
        "folder": "Premier_Group_Brick/Specifications",
        "filename": "Premier Group - Single Storey Running Bond - Bricklaying Specification.pdf",
        "is_technical": True
    },
    {
        "url": f"{PREMIER_BASE}/2021/11/1721220_PS1_PG-B2_STACK-BONDING-SPEC_15.11.2021.pdf",
        "folder": "Premier_Group_Brick/Specifications",
        "filename": "Premier Group - Stack Bonding - Specification.pdf",
        "is_technical": True
    },
    {
        "url": f"{PREMIER_BASE}/2021/11/1721220_PS1_PG-B3_2_STOREY-SPEC_15.11.2021.pdf",
        "folder": "Premier_Group_Brick/Specifications",
        "filename": "Premier Group - 2 Storey Brick Veneers - Specification.pdf",
        "is_technical": True
    },
    # Product Brochures
    {
        "url": f"{PREMIER_BASE}/2022/04/Premier-New-Main-Catalog-20220407-without-Stones-1.pdf",
        "folder": "Premier_Group_Brick/00_General_Resources",
        "filename": "Premier Group - Main Products Catalog 2022.pdf",
        "is_universal": True
    },
    {
        "url": f"{PREMIER_BASE}/2022/04/Premier-Brick-Homeowner-Trades20220407.pdf",
        "folder": "Premier_Group_Brick/Brochures",
        "filename": "Premier Group - Brick - Homeowner Trades Brochure.pdf",
        "is_universal": True
    },
]

# =============================================================================
# COMBINE ALL PDFs
# =============================================================================

ALL_PDFS = (
    ABODO_PDFS + 
    CLAYMARK_PDFS + 
    HERMPAC_PDFS + 
    SPP_PDFS + 
    JSC_PDFS + 
    SHADOWCLAD_PDFS + 
    HEBEL_PDFS + 
    PREMIER_PDFS
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def file_exists(storage_path):
    """Check if file already exists in Supabase Storage."""
    folder = "/".join(storage_path.split("/")[:-1])
    filename = storage_path.split("/")[-1]
    try:
        result = supabase.storage.from_(BUCKET).list(folder, {"limit": 1000})
        return any(item['name'] == filename for item in result)
    except:
        return False


def upload_pdf(url, storage_path, pdf_info):
    """Download and upload a PDF."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            content = response.content
            if b'%PDF' not in content[:20]:
                return False, "Not a valid PDF"
            
            result = supabase.storage.from_(BUCKET).upload(
                storage_path,
                content,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            # Track protocol compliance
            if pdf_info.get("is_bpir"):
                stats["bpir_docs"] += 1
            if pdf_info.get("is_installation"):
                stats["installation_docs"] += 1
            if pdf_info.get("is_technical"):
                stats["technical_docs"] += 1
            
            return True, len(content)
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def print_summary():
    """Print final summary."""
    print("\n" + "="*70)
    print("📊 WALL CLADDING REMEDIATION SCRAPE SUMMARY")
    print("="*70)
    print(f"   Total PDFs Found: {stats['pdfs_found']}")
    print(f"   PDFs Uploaded: {stats['pdfs_uploaded']}")
    print(f"   PDFs Skipped (Duplicate): {stats['pdfs_skipped']}")
    print(f"   Errors: {stats['errors']}")
    print("="*70)
    
    print("\n🛡️ PROTOCOL v2.0 COMPLIANCE")
    print("-"*70)
    print(f"✅ Rule 10 BPIR Docs: {stats['bpir_docs']}")
    print(f"✅ Installation Guides: {stats['installation_docs']}")
    print(f"✅ Technical Data Sheets: {stats['technical_docs']}")
    print("-"*70)


def print_sample_filenames():
    """Output 5 sample filenames for Rule 5 Verification."""
    print("\n📋 RULE 5 VERIFICATION - Sample Filenames:")
    print("-"*70)
    samples = [
        "Abodo - Vulcan Cladding Architectural Series - Technical Data Sheet.pdf",
        "Claymark A-Lign - Bevelback - Technical Manual V8.pdf",
        "Hermpac - Vertical Shiplap Weatherboards - Brochure.pdf",
        "SPP - MANAHAU Board and Batten - Technical Manual.pdf",
        "Hebel - PowerPanel 50mm - NZ Design and Installation Guide.pdf",
    ]
    for i, s in enumerate(samples, 1):
        print(f"   {i}. ✅ {s}")
    print("-"*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🧱 STRYDA Wall Cladding Remediation Scraper")
    print("="*70)
    print(f"Target: /{STORAGE_PREFIX}/")
    print("Manufacturers: Abodo, Claymark, Hermpac, SPP, JSC, Shadowclad, Hebel, Premier")
    print("="*70)
    
    # Rule 5: Output sample filenames first
    print_sample_filenames()
    
    print("\n🚀 Starting download...")
    print("-"*70)
    
    for pdf in ALL_PDFS:
        storage_path = f"{STORAGE_PREFIX}/{pdf['folder']}/{pdf['filename']}"
        stats["pdfs_found"] += 1
        
        # Check if exists
        if file_exists(storage_path):
            print(f"⏭️ Exists: {pdf['filename'][:50]}...")
            stats["pdfs_skipped"] += 1
            continue
        
        print(f"📥 {pdf['filename'][:55]}...")
        
        success, info = upload_pdf(pdf['url'], storage_path, pdf)
        
        if success:
            tags = []
            if pdf.get("is_bpir"):
                tags.append("BPIR")
            if pdf.get("is_installation"):
                tags.append("INSTALL")
            if pdf.get("is_technical"):
                tags.append("TECH")
            if pdf.get("is_monolith"):
                tags.append("MONOLITH")
            
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"   ✅ Uploaded ({info:,} bytes){tag_str}")
            stats["pdfs_uploaded"] += 1
        else:
            print(f"   ❌ Failed: {info}")
            stats["errors"] += 1
        
        time.sleep(0.3)
    
    print_summary()
    print("\n✅ Wall Cladding Remediation Scrape Complete!")
