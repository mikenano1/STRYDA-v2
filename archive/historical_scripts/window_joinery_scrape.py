#!/usr/bin/env python3
"""
Window Joinery Scraper (Protocol v2.0)
======================================
Downloads technical PDFs for NZ Window Joinery manufacturers:
- Big 3 Aluminium: APL (Vantage/Altherm), Altus Window Systems, Fairview/Omega
- uPVC Leaders: NK Windows, Starke/Ambiance

Protocol Enforcement:
- Rule 1 (CRITICAL): Separate Smartfit_Windows from Pacific_Series
- Rule 6 (Hidden Tech Data): Capture H1 Compliance Tables, Isothermal Analysis
- Rule 8 (Monolith): Specifier Guides → 00_General_Resources
- Rule 3 (Universal): Care & Maintenance, Warranty → product root

Target Structure:
/B_Enclosure/Joinery/
├── APL_Window_Solutions/
│   ├── ThermalHEART/
│   ├── Metro_Series/
│   └── 00_General_Resources/
├── Altus_Window_Systems/
│   ├── Pacific_Series/
│   ├── Smartfit_Windows/       ← CRITICAL SEPARATION
│   ├── Fisher_Windows/
│   ├── Nebulite/
│   ├── Nulook/
│   └── 00_General_Resources/
├── Omega_Windows/
│   ├── 800_Series_Thermal_Residential/
│   ├── 400_Series_Thermal_Architectural/
│   ├── 500_Series_Standard_Architectural/
│   ├── 600_Series_Commercial/
│   └── 00_General_Resources/
└── High_Performance_uPVC/
    ├── NK_Windows/
    └── Starke_Joinery/

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
STORAGE_PREFIX = "B_Enclosure/Joinery"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

stats = {
    "pdfs_found": 0,
    "pdfs_uploaded": 0,
    "pdfs_skipped": 0,
    "monoliths": 0,
    "smartfit": 0,
    "pacific": 0,
    "h1_compliance": 0,
    "upvc": 0,
    "errors": 0,
}

# =============================================================================
# ALTUS WINDOW SYSTEMS (Fisher, Rylock, Nebulite, Nulook, Pacific, Smartfit)
# =============================================================================

ALTUS_BASE = "https://altus.co.nz/assets"

ALTUS_PDFS = [
    # =========================================================================
    # 00_General_Resources - MONOLITHS and Universal Docs (Rule 8)
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/221014-ALTUS-H1-Energy-Efficiency-Guide-BPIR.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - H1 Energy Efficiency Guide (MASTER).pdf",
        "is_monolith": True,
        "h1_compliance": True
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Sustainability/Altus-EPD-Aluminium-and-Window-Systems-EPD-version-2.0.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - Environmental Product Declaration EPD v2.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/The-WGANZ-Guide-To-Window-Installation-2022.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - WGANZ Guide to Window Installation 2022.pdf",
        "is_monolith": True
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/WGANZ_Website-Guide_Condensation_V1.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - WGANZ Guide to Condensation.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/NZS-4223.3.2016-Change-Of-Affects-Glazing-In-Buildings-.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - NZS 4223.3 2016 Glazing Changes Guide.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/altus-thermal-planitherm-xn-2018.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - Double vs Triple Glazing Comparison Chart.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Care-and-Maintenance-Guide-WEB-21OCT2022.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - Care and Maintenance Guide.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Care-Maintenance-Guide-basic-flyer-covering-surface-finish.pdf",
        "folder": "Altus_Window_Systems/00_General_Resources",
        "filename": "Altus - 00 General - Care and Maintenance Flyer Surface Finish.pdf"
    },
    
    # =========================================================================
    # Smartfit Windows - CRITICAL SEPARATION (Rule 1)
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Smartfit-Window-Installation-Guide.pdf",
        "folder": "Altus_Window_Systems/Smartfit_Windows",
        "filename": "Altus - Smartfit - Window Installation Guide.pdf",
        "is_smartfit": True
    },
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/868.pdf",
        "folder": "Altus_Window_Systems/Smartfit_Windows",
        "filename": "Altus - Smartfit - BRANZ Appraisal 868.pdf",
        "is_smartfit": True
    },
    
    # =========================================================================
    # Pacific Series Thermal Systems
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Pacific41-Brochure-WEB-v2-BPIR-v2.pdf",
        "folder": "Altus_Window_Systems/Pacific_Series",
        "filename": "Altus - Pacific41 - Thermal System Brochure.pdf",
        "is_pacific": True
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Pacific52-Pacific60-Thermal-A4-Digital-Broch-BPIR.pdf",
        "folder": "Altus_Window_Systems/Pacific_Series",
        "filename": "Altus - Pacific52 Pacific60 - Thermal System Brochure.pdf",
        "is_pacific": True
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Southern41-Thermal-A4-digital-Brochure-BPIR.pdf",
        "folder": "Altus_Window_Systems/Pacific_Series",
        "filename": "Altus - Southern41 - Thermal System Brochure.pdf",
        "is_pacific": True
    },
    {
        "url": "https://www.miproducts.co.nz/MasterspecPTS_Altus-Window-Systems-Pacific-Thermal-52--60mm-System_102403.pdf",
        "folder": "Altus_Window_Systems/Pacific_Series",
        "filename": "Altus - Pacific Thermal 52-60mm - Masterspec Technical Statement.pdf",
        "is_pacific": True
    },
    
    # =========================================================================
    # Fisher Windows
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/221205-Fisher-Brochure-FINAL-BPIR.pdf",
        "folder": "Altus_Window_Systems/Fisher_Windows",
        "filename": "Altus - Fisher - Product Brochure.pdf"
    },
    
    # =========================================================================
    # Nebulite
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/221205-Nebulite-brochure-FINAL-BPIR.pdf",
        "folder": "Altus_Window_Systems/Nebulite",
        "filename": "Altus - Nebulite - Product Brochure.pdf"
    },
    
    # =========================================================================
    # Nulook
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/221205-Nulook-brochure-FINAL-BPIR-v3.pdf",
        "folder": "Altus_Window_Systems/Nulook",
        "filename": "Altus - Nulook - Product Brochure.pdf"
    },
    
    # =========================================================================
    # Tasman35 Glass System
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Tasman35-Brochure-BPIR.pdf",
        "folder": "Altus_Window_Systems/Tasman_Glass",
        "filename": "Altus - Tasman35 - IGU System Brochure.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Tasman35-Brochure-CHINESE-WEB-22APR2022-BPIR.pdf",
        "folder": "Altus_Window_Systems/Tasman_Glass",
        "filename": "Altus - Tasman35 - IGU System Brochure (Chinese).pdf"
    },
    
    # =========================================================================
    # Door Systems
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Bifold-Door-Installation-Details.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Bifold Door - Installation Details.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Euroslider-Door-Installation-Details.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Euroslider Door - Installation Details.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Eurostacker-Door-Installation-Details.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Eurostacker Door - Installation Details.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Foldback-Bifold-Installation-Details.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Foldback Bifold - Installation Details.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Stellar_Doors_Brochure-v2.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Stellar Doors - Product Brochure.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Bifold-Foldback-Door-Conifguration-Size-Limitations.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Bifold Foldback - Configuration and Size Limitations.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Sliding-Stacking-Door-Conifguration-Size-Limitations.pdf",
        "folder": "Altus_Window_Systems/Door_Systems",
        "filename": "Altus - Sliding Stacking Door - Configuration and Size Limitations.pdf"
    },
    
    # =========================================================================
    # Hardware
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Lucerne_Architectural_Hardware_Brochure.pdf",
        "folder": "Altus_Window_Systems/Hardware",
        "filename": "Altus - Lucerne - Architectural Hardware Brochure.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Malta-Brochure-WEB-07JUN2022.pdf",
        "folder": "Altus_Window_Systems/Hardware",
        "filename": "Altus - Malta - Hardware Brochure.pdf"
    },
    
    # =========================================================================
    # Finishes
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Anoguard-Anodising-Brochure-Altus-Window-Systems-BPIR.pdf",
        "folder": "Altus_Window_Systems/Finishes",
        "filename": "Altus - Anoguard - Anodising Brochure.pdf"
    },
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/Altus-ColourScape-Full-Brochure-DIGITAL-140922.pdf",
        "folder": "Altus_Window_Systems/Finishes",
        "filename": "Altus - ColourScape - Powdercoat Colour Brochure.pdf"
    },
    
    # =========================================================================
    # Dual Glaze Retrofit
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/dual-GLAZE-Brochure-BPIR.pdf",
        "folder": "Altus_Window_Systems/Dual_Glaze",
        "filename": "Altus - dual GLAZE - Retrofit System Brochure.pdf"
    },
    
    # =========================================================================
    # uPVC (Altus branded)
    # =========================================================================
    {
        "url": f"{ALTUS_BASE}/Uploads/Documents/AWS-Upvc-brochure-BPIR.pdf",
        "folder": "Altus_Window_Systems/uPVC",
        "filename": "Altus - uPVC - Product Brochure.pdf"
    },
]

# =============================================================================
# OMEGA WINDOWS & DOORS (Fairview)
# =============================================================================

OMEGA_BASE = "https://www.omegawindows.co.nz/uploads/pdfs/downloads"

OMEGA_PDFS = [
    # =========================================================================
    # 00_General_Resources - Brochures
    # =========================================================================
    {
        "url": f"{OMEGA_BASE}/Omega_Product_Suite_Brochure.pdf",
        "folder": "Omega_Windows/00_General_Resources",
        "filename": "Omega - 00 General - Product Suite Brochure.pdf",
        "is_monolith": True
    },
    {
        "url": f"{OMEGA_BASE}/Omega_Colour_Chart.pdf",
        "folder": "Omega_Windows/00_General_Resources",
        "filename": "Omega - 00 General - Colour Chart.pdf"
    },
    
    # =========================================================================
    # 800 Series - Thermal Residential (Full Installation Sets)
    # =========================================================================
    {
        "url": f"{OMEGA_BASE}/800%20Series%20Awning%20Window%20-%20Full%20Set.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Awning Window Full Installation Set.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/800%20Series%20Fixed%20Window%20-%20Full%20Set.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Fixed Window Full Installation Set.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/800%20Series%20Open%20In%20Door%20-%20Full%20Set.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Open In Door Full Installation Set.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/800%20Series%20Open%20Out%20Door%20-%20Full%20Set.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Open Out Door Full Installation Set.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/800%20Series%20-%20BiParting%20Slider%20-%20Full%20Set.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - BiParting Slider Full Installation Set.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/SINGLE%20SLIDER%20-%20FIXED%20SLIDING%20FIXED-Sheet%20Number-SINGLE%20SLIDER%20-%20FIXED%20SLIDING%20FIXED-.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Single Slider Fixed Sliding Fixed.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/SINGLE%20SLIDER%20-%20SLIDER%20AND%20AWNING-Sheet%20Number-SINGLE%20SLIDER%20-%20SLIDER%20AND%20AWNING-.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Single Slider and Awning.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/SLIDER%20-%204PJ%20%20(FOUR%20PANEL%20JOINTER)-Sheet%20Number-SLIDER%20-%204PJ%20%20(FOUR%20PANEL%20JOINTER)-.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Slider 4PJ Four Panel Jointer.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/STACKER%20SLIDER%20-%203%20PANEL%20STACKER%20(BASIC)-Sheet%20Number-STACKER%20SLIDER%20-%203%20PANEL%20STACKER%20(BASIC)-.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Stacker Slider 3 Panel Basic.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/STACKER%20SLIDER%20-%206%20PANEL%20STACKER-Sheet%20Number-STACKER%20SLIDER%20-%206%20PANEL%20STACKER-.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential",
        "filename": "Omega - 800 Series - Stacker Slider 6 Panel.pdf"
    },
    
    # =========================================================================
    # 800 Series - Cladding-Specific Installation Details
    # =========================================================================
    {
        "url": f"{OMEGA_BASE}/dfFCS-Direct-Fix-Construction-Fibre-Cement-Sheet-V3.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential/Direct_Fix_Details",
        "filename": "Omega - 800 Series - Direct Fix Fibre Cement Sheet V3.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/dfCBLK-Direct-Fix-Construction-Concrete-Block-V1.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential/Direct_Fix_Details",
        "filename": "Omega - 800 Series - Direct Fix Concrete Block V1.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/dfPCP-Direct-Fix-Construction-Precast-Concrete-V1.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential/Direct_Fix_Details",
        "filename": "Omega - 800 Series - Direct Fix Precast Concrete V1.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/dfVPM-Direct-Fix-Construction-Metal-File-Cladding-V1.pdf",
        "folder": "Omega_Windows/800_Series_Thermal_Residential/Direct_Fix_Details",
        "filename": "Omega - 800 Series - Direct Fix Vertical Metal Cladding V1.pdf"
    },
    
    # =========================================================================
    # 400 Series - Thermal Architectural
    # =========================================================================
    {
        "url": f"{OMEGA_BASE}/Declare-400.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural",
        "filename": "Omega - 400 Series - Declare Label Environmental.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/ccBBWBTRM-V3Cavity-Construction-Bevel-Back-Weatherboard%20(5).pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Cavity_Details",
        "filename": "Omega - 400 Series - Cavity Construction Bevel Back Weatherboard V3.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/ccBVTRM-V2Cavity-Construction-Brick-Veneer-Thermal-.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Cavity_Details",
        "filename": "Omega - 400 Series - Cavity Construction Brick Veneer Thermal V2.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/ccEIFTHRM-V2Cavity-Construction-Exterior-Insulation-Finishing-System.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Cavity_Details",
        "filename": "Omega - 400 Series - Cavity Construction EIFS V2.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/ccFCSTHRM-V2Cavity-Construction-Fibre-Cement-Sheet-Thermal.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Cavity_Details",
        "filename": "Omega - 400 Series - Cavity Construction Fibre Cement Sheet Thermal V2.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/ccHPM-V2Cavity-Construction-Horizontal-Profile-Metal-Cladding.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Cavity_Details",
        "filename": "Omega - 400 Series - Cavity Construction Horizontal Profile Metal V2.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/dfBANDBTHRM-Direct-Fix-Construction-Board-and-Batten-V4.pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Direct_Fix_Details",
        "filename": "Omega - 400 Series - Direct Fix Board and Batten Thermal V4.pdf"
    },
    {
        "url": f"{OMEGA_BASE}/dfBBWTHRM-Direct-Fix-Construction-System-Bevel-Backed-Weatherboard-V4%20(1).pdf",
        "folder": "Omega_Windows/400_Series_Thermal_Architectural/Direct_Fix_Details",
        "filename": "Omega - 400 Series - Direct Fix Bevel Backed Weatherboard Thermal V4.pdf"
    },
    
    # =========================================================================
    # 500 Series - Standard Architectural
    # =========================================================================
    {
        "url": f"{OMEGA_BASE}/Declare-Label.pdf",
        "folder": "Omega_Windows/500_Series_Standard_Architectural",
        "filename": "Omega - 500 Series - Declare Label Environmental.pdf"
    },
]

# =============================================================================
# APL / VANTAGE / ALTHERM (via BRANZ CloudFront)
# =============================================================================

APL_PDFS = [
    # =========================================================================
    # ThermalHEART Systems
    # =========================================================================
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1_1188_2023_a2.pdf",
        "folder": "APL_Window_Solutions/ThermalHEART",
        "filename": "APL - ThermalHEART - Metro Centrafix BRANZ Appraisal 1188.pdf",
        "h1_compliance": True
    },
    {
        "url": "https://d39d3mj7qio96p.cloudfront.net/media/documents/1259_2024_A1_.pdf",
        "folder": "APL_Window_Solutions/ThermalHEART",
        "filename": "APL - ThermalHEART Plus - Systems 2024 BRANZ Appraisal 1259.pdf",
        "h1_compliance": True
    },
]

# =============================================================================
# NK WINDOWS - HIGH PERFORMANCE uPVC
# =============================================================================

NK_BASE = "https://nkwindows.co.nz/wp-content/uploads"

NK_PDFS = [
    # =========================================================================
    # Core Compliance Documents
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/12/NKW-Buildiing-Product-Information-Sheet-Dec-24.pdf",
        "folder": "High_Performance_uPVC/NK_Windows",
        "filename": "NK Windows - BPIS Building Product Information Sheet Dec 2024.pdf",
        "is_upvc": True,
        "h1_compliance": True
    },
    {
        "url": "https://warmwindows.co.nz/wp-content/uploads/2024/02/WarmWindows-BRANZ.pdf",
        "folder": "High_Performance_uPVC/NK_Windows",
        "filename": "NK Windows - BRANZ Appraisal aluPlast uPVC.pdf",
        "is_upvc": True,
        "h1_compliance": True
    },
    
    # =========================================================================
    # BRANZ Approved Installation Details
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Board-Batten-Direct-Fix4.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Board Batten Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Board-Batten-on-Cavity4.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Board Batten on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-EIFS-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - EIFS on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Fibre-Cement-Sheet-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Fibre Cement Sheet Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Fibre-Cement-Sheet-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Fibre Cement Sheet on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Masonry-Veneer-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Masonry Veneer on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Horizontal-Profiled-Metal-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Horizontal Profiled Metal on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Vertical-Profiled-Metal-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Vertical Profiled Metal Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Bevel-Back-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Bevel Back Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Bevel-Back-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Bevel Back on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Fibre-Cement-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Fibre Cement Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Fibre-Cement-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Fibre Cement on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Rusticated-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Rusticated Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Rusticated-on-Cavity2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Rusticated on Cavity.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Weatherboard-Shiplap-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/BRANZ_Details",
        "filename": "NK Windows - BRANZ Detail - Weatherboard Shiplap Direct Fix.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Construction Drawings - Windows
    # =========================================================================
    {
        "url": f"{NK_BASE}/Windows/NK-Window-OO-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Window Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/Windows/NK-Window-IO-Direct-Fix2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/Windows/NK-Window-IO-Direct-Fix-Triple-Glazed2.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window Triple Glazed.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-OO-Direct-Fix-105-Sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Window 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-IO-Direct-Fix-105-Sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-IO-Reveal-Fix-Monobloc.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window Monobloc Reveal Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-IO-Direct-Fix-Monobloc.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window Monobloc Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-OO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Window Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Window-IO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Window Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Construction Drawings - Doors
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-OO-Direct-Fix.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Door Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-IO-Direct-Fix.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Door Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-OO-Direct-Fix-105-Sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Door 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-IO-Direct-Fix-105-Sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Door 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-IO-Direct-Fix-Monobloc.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Door Monobloc Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-OO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Outward Opening Door Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Door-IO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Inward Opening Door Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Construction Drawings - Multi-Slide
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Stacker-Direct-Fix-3-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide Stacker Direct Fix 3 Track.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Direct-Fix-2-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide Direct Fix 2 Track.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Stacker-Direct-Fix-105-Sill-3-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide Stacker 105mm Sill 3 Track.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Direct-Fix-105-Sill-2-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide 105mm Sill 2 Track.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Stacker-Reveal-Fix-Flange-3-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide Stacker Reveal Fix 3 Track.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Multi-Slide-Reveal-Fix-Flange-2-track.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Multi-Slide Reveal Fix 2 Track.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Construction Drawings - Tilt & Slide, Smart Slide, Lift & Slide
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Tilt-Slide-Reveal-Fix-Flange-1.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Tilt Slide Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Tilt-Slide-Direct-Fix-1.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Tilt Slide Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Tilt-Slide-Direct-Fix-105.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Tilt Slide 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-SmartSlider-Reveal-Fix-No-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Smart Slider Reveal Fix No Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-SmartSlider-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Smart Slider Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-SmartSlider-Direct-Fix.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Smart Slider Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-SmartSlider-Direct-Fix-105-sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Smart Slider 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-LiftSlide.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Lift Slide Premium.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Construction Drawings - Bifold
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-OO-Direct-Fix.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Outward Opening Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-IO-Direct-Fix.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Inward Opening Direct Fix.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-OO-Direct-Fix-105-Sill.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Outward Opening 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-IO-Direct-Fix-105.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Inward Opening 105mm Sill.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-OO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Outward Opening Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-OO-Reveal-Fix-No-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Outward Opening Reveal Fix No Flange.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Bifold-IO-Reveal-Fix-Flange.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Construction_Drawings",
        "filename": "NK Windows - Drawing - Bifold Inward Opening Reveal Fix Flange.pdf",
        "is_upvc": True
    },
    
    # =========================================================================
    # Instructions & Maintenance
    # =========================================================================
    {
        "url": f"{NK_BASE}/2024/08/NK-Windows-Glazing-Instructions-v01.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Instructions",
        "filename": "NK Windows - Glazing Instructions.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Windows-M-tech-Hinge-Adjustment-Instructions-v01.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Instructions",
        "filename": "NK Windows - M-tec II Hinge Adjustment Instructions.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Windows-Maco-Tech-100-Restrictor-Instructions.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Instructions",
        "filename": "NK Windows - Maco Tech 100 Brake Stay Restrictor Instructions.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Windows-Tilt-Slide-Adjustment-and-Maintenance-v01.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Instructions",
        "filename": "NK Windows - Tilt Slide Adjustment and Maintenance.pdf",
        "is_upvc": True
    },
    {
        "url": f"{NK_BASE}/2024/08/NK-Windows-Glazing-Instructions-v01-1.pdf",
        "folder": "High_Performance_uPVC/NK_Windows/Instructions",
        "filename": "NK Windows - Glazing Packer Location Instructions.pdf",
        "is_upvc": True
    },
]

# =============================================================================
# STARKE / AMBIANCE uPVC
# =============================================================================

STARKE_PDFS = [
    {
        "url": "https://ambiance.co.nz/wp-content/uploads/2024/04/Product-Technical-Statement.pdf",
        "folder": "High_Performance_uPVC/Starke_Joinery",
        "filename": "Starke Ambiance - Product Technical Statement.pdf",
        "is_upvc": True,
        "h1_compliance": True
    },
    {
        "url": "https://ambiance.co.nz/wp-content/uploads/2024/04/4211-Report-Summary.pdf",
        "folder": "High_Performance_uPVC/Starke_Joinery",
        "filename": "Starke Ambiance - NZS 4211 Report Summary.pdf",
        "is_upvc": True,
        "h1_compliance": True
    },
    {
        "url": "https://ambiance.co.nz/wp-content/uploads/2024/04/Care-Maintenance-Guide.pdf",
        "folder": "High_Performance_uPVC/Starke_Joinery",
        "filename": "Starke Ambiance - Care and Maintenance Guide.pdf",
        "is_upvc": True
    },
]

# =============================================================================
# COMBINE ALL PDFs
# =============================================================================

ALL_PDFS = ALTUS_PDFS + OMEGA_PDFS + APL_PDFS + NK_PDFS + STARKE_PDFS


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
            if pdf_info.get("is_smartfit"):
                stats["smartfit"] += 1
            if pdf_info.get("is_pacific"):
                stats["pacific"] += 1
            if pdf_info.get("h1_compliance"):
                stats["h1_compliance"] += 1
            if pdf_info.get("is_upvc"):
                stats["upvc"] += 1
            
            return True, len(content)
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def print_summary():
    """Print final summary."""
    print("\n" + "="*70)
    print("📊 WINDOW JOINERY SCRAPE SUMMARY")
    print("="*70)
    print(f"   Total PDFs Found: {stats['pdfs_found']}")
    print(f"   PDFs Uploaded: {stats['pdfs_uploaded']}")
    print(f"   PDFs Skipped (Duplicate): {stats['pdfs_skipped']}")
    print(f"   Errors: {stats['errors']}")
    print("="*70)
    
    print("\n🛡️ PROTOCOL v2.0 COMPLIANCE")
    print("-"*70)
    print(f"✅ Rule 8 Monoliths: {stats['monoliths']}")
    print(f"✅ Rule 1 Smartfit (Separated): {stats['smartfit']}")
    print(f"✅ Rule 1 Pacific Series: {stats['pacific']}")
    print(f"✅ Rule 6 H1 Compliance Docs: {stats['h1_compliance']}")
    print(f"✅ uPVC Documents: {stats['upvc']}")
    print("-"*70)


def verify_folder_structure():
    """Verify the critical folder separations exist."""
    print("\n🔍 FOLDER STRUCTURE VERIFICATION")
    print("-"*70)
    
    critical_folders = [
        "Altus_Window_Systems/Smartfit_Windows",
        "Altus_Window_Systems/Pacific_Series",
        "High_Performance_uPVC/NK_Windows",
        "High_Performance_uPVC/Starke_Joinery",
    ]
    
    for folder in critical_folders:
        full_path = f"{STORAGE_PREFIX}/{folder}"
        try:
            result = supabase.storage.from_(BUCKET).list(full_path, {"limit": 100})
            count = len([f for f in result if f.get('name', '').endswith('.pdf')])
            if count > 0:
                print(f"✅ {folder}: {count} PDFs")
            else:
                print(f"⚠️ {folder}: EMPTY")
        except Exception as e:
            print(f"❌ {folder}: Error - {str(e)[:30]}")
    
    print("-"*70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🪟 STRYDA Window Joinery Scraper")
    print("="*70)
    print(f"Target: /{STORAGE_PREFIX}/")
    print("Manufacturers: Altus (Big 3), Omega, APL, NK Windows, Starke")
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
            tags = []
            if pdf.get("is_monolith"):
                tags.append("MONOLITH")
            if pdf.get("is_smartfit"):
                tags.append("SMARTFIT")
            if pdf.get("is_pacific"):
                tags.append("PACIFIC")
            if pdf.get("h1_compliance"):
                tags.append("H1")
            if pdf.get("is_upvc"):
                tags.append("uPVC")
            
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"   ✅ Uploaded ({info:,} bytes){tag_str}")
            stats["pdfs_uploaded"] += 1
        else:
            print(f"   ❌ Failed: {info}")
            stats["errors"] += 1
        
        time.sleep(0.3)  # Slightly longer delay for varied sources
    
    print_summary()
    verify_folder_structure()
    print("\n✅ Window Joinery Scrape Complete!")
