#!/usr/bin/env python3
"""
Fibre Cement Cladding Scraper (Protocol v2.0)
=============================================
Downloads technical PDFs for James Hardie and BGC/Innova wall cladding products.

Protocol Enforcement:
- Rule 1 (CRITICAL): Separate Direct Fix from Cavity Fix systems for Linea
- Rule 8 (Monolith): Fire and Acoustic Design Manual → 00_General_Resources
- Rule 3 (Universal): Care & Maintenance, Warranty → 00_General_Resources

Target Structure:
/B_Enclosure/Wall_Cladding/
├── James_Hardie/
│   ├── Linea_Weatherboard/
│   │   ├── Cavity_Fix_System/
│   │   └── Direct_Fix_System/
│   ├── Oblique_Weatherboard/
│   ├── Stria_Cladding/
│   ├── Axon_Panel/
│   ├── ExoTec_Facade/
│   ├── Hardie_Plank/
│   └── 00_General_Resources/
└── Innova_Fibre_Cement/
    ├── Stratum/
    ├── Nuline/
    ├── Duragrid/
    └── 00_General_Resources/

Author: STRYDA Data Pipeline
Date: 2025-01
"""

import os
import sys
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
    "monoliths": 0,
    "cavity_fix": 0,
    "direct_fix": 0,
    "errors": 0,
}

# =============================================================================
# JAMES HARDIE CLADDING PRODUCTS
# =============================================================================

JAMES_HARDIE_BASE = "https://www.jameshardie.co.nz/web/assets/general"

JAMES_HARDIE_PDFS = [
    # =========================================================================
    # 00_General_Resources - MONOLITHS and Universal Docs (Rule 8 & Rule 3)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Fire-Acoustic-Design-Manual-2025.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Fire and Acoustic Design Manual 2025 (MASTER).pdf",
        "is_monolith": True
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Fire-Acoustic-1285_2025.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - BRANZ Appraisal 1285 Fire Acoustic Systems.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Bracing-Design-Manual.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Bracing Design Manual.pdf",
        "is_monolith": True
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Cladding-Junction-Details-Design-Manual.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Cladding Junction Details Design Manual.pdf",
        "is_monolith": True
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Best-Practice-Book-September-2024.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Best Practice Guide September 2024.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/JH-Cladding-to-Steel-Framing-Technical-Supplement.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Cladding to Steel Framing Technical Supplement.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/James-Hardie-Design-Handbook-2025.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Design Handbook 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/James-Hardie-Cavity-Batten-Range-Flyer.pdf",
        "folder": "James_Hardie/00_General_Resources",
        "filename": "Hardie - 00 General - Cavity Batten Range Flyer.pdf"
    },
    
    # =========================================================================
    # Linea Weatherboard - CAVITY FIX SYSTEM (Rule 1 Critical)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboad-Cavity-Fix-Technical-Specification.pdf",
        "folder": "James_Hardie/Linea_Weatherboard/Cavity_Fix_System",
        "filename": "Hardie - Linea - Cavity Fix Technical Specification.pdf",
        "system": "cavity"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-cavity-fixed-447_2020.pdf",
        "folder": "James_Hardie/Linea_Weatherboard/Cavity_Fix_System",
        "filename": "Hardie - Linea - BRANZ Appraisal 447 Cavity Fixed.pdf",
        "system": "cavity"
    },
    
    # =========================================================================
    # Linea Weatherboard - DIRECT FIX SYSTEM (Rule 1 Critical)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-Direct-Fix-Technical-Specification.pdf",
        "folder": "James_Hardie/Linea_Weatherboard/Direct_Fix_System",
        "filename": "Hardie - Linea - Direct Fix Technical Specification.pdf",
        "system": "direct"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-direct-fixed-446_2020.pdf",
        "folder": "James_Hardie/Linea_Weatherboard/Direct_Fix_System",
        "filename": "Hardie - Linea - BRANZ Appraisal 446 Direct Fixed.pdf",
        "system": "direct"
    },
    
    # =========================================================================
    # Linea Weatherboard - Shared Documents (Product Root)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-product-Warranty_2025-02-12-211259_qini.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-Product-Technical-Statement-April-2025.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Product Technical Statement April 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-Product-Brochure.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Product Brochure.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/INSTALLATION-Checklist-Linea-Weatherboard.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Installation Checklist.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Linea-Weatherboard-Technical-Supplement-fixing-to-brick-veneer-framing.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - Technical Supplement Brick Veneer Framing.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/30018-CodeMark-Linea-Weatherboard-Sep-25.pdf",
        "folder": "James_Hardie/Linea_Weatherboard",
        "filename": "Hardie - Linea - CodeMark Certificate 30018.pdf"
    },
    
    # =========================================================================
    # Oblique Weatherboard (Vertical & Horizontal)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-14mm-Vertical-Installation-Tech-Spec.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - 14mm Vertical Installation Tech Spec.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-14mm-Horizontal-Installation-Tech-Spec.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - 14mm Horizontal Installation Tech Spec.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-14mm-Vertical-40mm-Structural-Cavity-Batten-Tech-Spec.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - 14mm Vertical 40mm Structural Cavity Batten Tech Spec.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-Product-Warranty.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique%E2%84%A2-Weatherboard-Product-Technical-Statement-April-2025.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - Product Technical Statement April 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-Product-Brochure_2024-06-06-220815_ecct.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - Product Brochure.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Oblique-Weatherboard-Installation-Checklist.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - Installation Checklist.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/BRANZ-Appraisal-Oblique-Weatherboard-14mm-Vertical.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - BRANZ Appraisal 14mm Vertical.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/BRANZ-Appraisal-Oblique-Weatherboard-14mm-horizontal.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - BRANZ Appraisal 14mm Horizontal.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/30147-CodeMark-Oblique-Weatherboard-Oct-24.pdf",
        "folder": "James_Hardie/Oblique_Weatherboard",
        "filename": "Hardie - Oblique - CodeMark Certificate 30147.pdf"
    },
    
    # =========================================================================
    # Stria Cladding
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Vertical-Installation-Technical-Specification.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Vertical Installation Technical Specification.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Timber-Cavity-Batten-Horizontal-Technical-Specification.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Timber Cavity Batten Horizontal Technical Specification.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-CLD-Structural-Cavity-Batten-Technical-Specification.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - CLD Structural Cavity Batten Technical Specification.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Vertical-40mm-Strutural-Cavity-Batten-Installation-Manual.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Vertical 40mm Structural Cavity Batten Installation Manual.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon_Stria-Technical-Supplement-fixing-to-tilt-slab-or-block.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Technical Supplement Tilt Slab or Block.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Product-Warranty.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria%E2%84%A2-Cladding-Product-Technical-Statement-April-2025.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Product Technical Statement April 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Stria-Cladding-Product-Brochure_2024-06-06-220919_wkxs.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Product Brochure.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/INSTALLATION-Checklist-Stria-Cladding-CLD.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - Installation Checklist CLD.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/30109-Stria-Cladding-CodeMark-Oct-24.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - CodeMark Certificate 30109.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/BRANZ-Appraisal-Stria-Cladding-Horizontal-Installation.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - BRANZ Appraisal Horizontal Installation.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/BRANZ-Appraisal-Stria-Cladding-Vertical-Installation.pdf",
        "folder": "James_Hardie/Stria_Cladding",
        "filename": "Hardie - Stria - BRANZ Appraisal Vertical Installation.pdf"
    },
    
    # =========================================================================
    # Axon Panel
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Hardie-CLD-Structural-Cavity-Batten-Technical-Specification.pdf",
        "folder": "James_Hardie/Axon_Panel/Cavity_Fix_System",
        "filename": "Hardie - Axon - CLD Structural Cavity Batten Technical Specification.pdf",
        "system": "cavity"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Timber-Cavity-Batten-Technical-Specification.pdf",
        "folder": "James_Hardie/Axon_Panel/Cavity_Fix_System",
        "filename": "Hardie - Axon - Timber Cavity Batten Technical Specification.pdf",
        "system": "cavity"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Direct-Fix-Technical-Specification.pdf",
        "folder": "James_Hardie/Axon_Panel/Direct_Fix_System",
        "filename": "Hardie - Axon - Direct Fix Technical Specification.pdf",
        "system": "direct"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Product-Warranty.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Product-Technical-Statement.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Product Technical Statement.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Product-Brochure.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Product Brochure.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/INSTALLATION-Checklist-Axon-Panel.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Installation Checklist.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/CodeMark-Axon-Panel-30165-RevA.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - CodeMark Certificate 30165.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/BRANZ-Appraisal-1211-Axon-Panel.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - BRANZ Appraisal 1211.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Smooth-to-Stone-Installation-Manual-November-2024.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Smooth to Stone Installation Manual November 2024.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Axon-Panel-Texture-Coating-Technical-Specification.pdf",
        "folder": "James_Hardie/Axon_Panel",
        "filename": "Hardie - Axon - Texture Coating Technical Specification.pdf"
    },
    
    # =========================================================================
    # ExoTec Facade Panel (Commercial)
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/ExoTec-Top-Hat-Rainscreen-Technical-Specification.pdf",
        "folder": "James_Hardie/ExoTec_Facade",
        "filename": "Hardie - ExoTec - Top Hat Rainscreen Technical Specification.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/ExoTec-Facade-Panel-Product-Warranty.pdf",
        "folder": "James_Hardie/ExoTec_Facade",
        "filename": "Hardie - ExoTec - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/ExoTec%E2%84%A2-Facade-Panel-Product-Technical-Statement-April-2025.pdf",
        "folder": "James_Hardie/ExoTec_Facade",
        "filename": "Hardie - ExoTec - Product Technical Statement April 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/ExoTec-Facade-Panel-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/ExoTec_Facade",
        "filename": "Hardie - ExoTec - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/INSTALLATION-Checklist-ExoTec-Top-Hat-Rainscreen.pdf",
        "folder": "James_Hardie/ExoTec_Facade",
        "filename": "Hardie - ExoTec - Installation Checklist Top Hat Rainscreen.pdf"
    },
    
    # =========================================================================
    # Hardie Plank Weatherboard
    # =========================================================================
    {
        "url": f"{JAMES_HARDIE_BASE}/Hardie-Plank-Weatherboard-Technical-Specification.pdf",
        "folder": "James_Hardie/Hardie_Plank",
        "filename": "Hardie - Plank - Technical Specification.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Hardie-Plank-Weatherboard-Product-Warranty.pdf",
        "folder": "James_Hardie/Hardie_Plank",
        "filename": "Hardie - Plank - Product Warranty.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Hardie%E2%84%A2-Plank-Weatherboard-Product-Technical-Statement-April-2025.pdf",
        "folder": "James_Hardie/Hardie_Plank",
        "filename": "Hardie - Plank - Product Technical Statement April 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/Hardie-Plank-Weatherboard-Care-Maintenance-Guide-2025.pdf",
        "folder": "James_Hardie/Hardie_Plank",
        "filename": "Hardie - Plank - Care and Maintenance Guide 2025.pdf"
    },
    {
        "url": f"{JAMES_HARDIE_BASE}/INSTALLATION-Checklist-HardiePlank-Weatherboard.pdf",
        "folder": "James_Hardie/Hardie_Plank",
        "filename": "Hardie - Plank - Installation Checklist.pdf"
    },
]

# =============================================================================
# INNOVA (formerly BGC) FIBRE CEMENT PRODUCTS
# =============================================================================

INNOVA_BASE = "https://etex.azureedge.net"

INNOVA_PDFS = [
    # =========================================================================
    # 00_General_Resources
    # =========================================================================
    {
        "url": f"{INNOVA_BASE}/pi865582/original/-35931105/innova-product-guide-nz-aug-2025---web-ver.pdf",
        "folder": "Innova_Fibre_Cement/00_General_Resources",
        "filename": "Innova - 00 General - Product Guide NZ August 2025.pdf"
    },
    
    # =========================================================================
    # Stratum Weatherboard
    # =========================================================================
    {
        "url": f"{INNOVA_BASE}/pi864116/original/-2021048005/innova-stratum-design--installation-guide-nz-august-2024.pdf",
        "folder": "Innova_Fibre_Cement/Stratum",
        "filename": "Innova - Stratum - Design and Installation Guide NZ August 2024.pdf"
    },
    
    # =========================================================================
    # Nuline Weatherboard
    # =========================================================================
    {
        "url": f"{INNOVA_BASE}/pi864114/original/-2021048005/innova-nuline-design--installation-guide-nz-august-2024.pdf",
        "folder": "Innova_Fibre_Cement/Nuline",
        "filename": "Innova - Nuline - Design and Installation Guide NZ August 2024.pdf"
    },
    
    # =========================================================================
    # Duragrid (Light Commercial Facade)
    # =========================================================================
    {
        "url": f"{INNOVA_BASE}/pi864118/original/1526239545/innova-duragrid-design--installation-guide-nz-august-2025.pdf",
        "folder": "Innova_Fibre_Cement/Duragrid",
        "filename": "Innova - Duragrid - Design and Installation Guide NZ August 2025.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi865583/original/-101979071/innova-duragrid---technical-data-sheet-nz.pdf",
        "folder": "Innova_Fibre_Cement/Duragrid",
        "filename": "Innova - Duragrid - Technical Data Sheet NZ.pdf"
    },
    
    # =========================================================================
    # Additional Products
    # =========================================================================
    {
        "url": f"{INNOVA_BASE}/pi864119/original/-2021048005/innova-duragroove--durascape-design--installation-guide-nz-august-2024.pdf",
        "folder": "Innova_Fibre_Cement/Duragroove",
        "filename": "Innova - Duragroove Durascape - Design and Installation Guide NZ August 2024.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi864117/original/-2021048005/innova-duralux--duraliner-design--installation-guide-nz-aug-2024.pdf",
        "folder": "Innova_Fibre_Cement/Duralux",
        "filename": "Innova - Duralux Duraliner - Design and Installation Guide NZ August 2024.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi864115/original/-2021048005/innova-ctu-design--installation-guide-nz-aug-2024.pdf",
        "folder": "Innova_Fibre_Cement/CTU",
        "filename": "Innova - CTU - Design and Installation Guide NZ August 2024.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi871291/original/-1445142174/nz_montage_november-2025.pdf",
        "folder": "Innova_Fibre_Cement/Montage",
        "filename": "Innova - Montage - Design and Installation Guide NZ November 2025.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi871292/original/-1445142174/nz-montage---technical-data-sheet.pdf",
        "folder": "Innova_Fibre_Cement/Montage",
        "filename": "Innova - Montage - Technical Data Sheet NZ November 2025.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi866240/original/-1848628231/nz_effects-trims_october-2025.pdf",
        "folder": "Innova_Fibre_Cement/Effects_Trims",
        "filename": "Innova - Effects Trims - Design and Installation Guide NZ October 2025.pdf"
    },
    {
        "url": f"{INNOVA_BASE}/pi865585/original/-1131017632/nz_floor-loading-solutions_december-2025.pdf",
        "folder": "Innova_Fibre_Cement/Flooring",
        "filename": "Innova - Floor Loading Solutions - Durafloor and Compressed Flooring December 2025.pdf"
    },
]

ALL_PDFS = JAMES_HARDIE_PDFS + INNOVA_PDFS


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
            if content[:4] != b'%PDF':
                return False, "Not a valid PDF"
            
            result = supabase.storage.from_(BUCKET).upload(
                storage_path,
                content,
                {"content-type": "application/pdf", "upsert": "true"}
            )
            
            # Track protocol compliance
            if pdf_info.get("is_monolith"):
                stats["monoliths"] += 1
            if pdf_info.get("system") == "cavity":
                stats["cavity_fix"] += 1
            if pdf_info.get("system") == "direct":
                stats["direct_fix"] += 1
            
            return True, len(content)
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def print_summary():
    """Print final summary."""
    print("\n" + "="*70)
    print("📊 FIBRE CEMENT CLADDING SCRAPE SUMMARY")
    print("="*70)
    print(f"   Total PDFs Found: {stats['pdfs_found']}")
    print(f"   PDFs Uploaded: {stats['pdfs_uploaded']}")
    print(f"   PDFs Skipped (Duplicate): {stats['pdfs_skipped']}")
    print(f"   Errors: {stats['errors']}")
    print("="*70)
    
    print("\n🛡️ PROTOCOL v2.0 COMPLIANCE")
    print("-"*70)
    print(f"✅ Rule 8 Monoliths Detected: {stats['monoliths']}")
    print(f"✅ Rule 1 Cavity Fix Docs: {stats['cavity_fix']}")
    print(f"✅ Rule 1 Direct Fix Docs: {stats['direct_fix']}")
    print("-"*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🏠 STRYDA Fibre Cement Cladding Scraper")
    print("="*70)
    print(f"Target: /{STORAGE_PREFIX}/")
    print("Manufacturers: James Hardie, Innova (BGC)")
    print("="*70)
    
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
            tag = ""
            if pdf.get("is_monolith"):
                tag = " [MONOLITH]"
            elif pdf.get("system") == "cavity":
                tag = " [CAVITY FIX]"
            elif pdf.get("system") == "direct":
                tag = " [DIRECT FIX]"
            print(f"   ✅ Uploaded ({info:,} bytes){tag}")
            stats["pdfs_uploaded"] += 1
        else:
            print(f"   ❌ Failed: {info}")
            stats["errors"] += 1
        
        time.sleep(0.2)
    
    print_summary()
    print("\n✅ Fibre Cement Cladding Scrape Complete!")
