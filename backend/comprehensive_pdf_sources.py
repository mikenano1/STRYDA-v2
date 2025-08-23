"""
STRYDA.ai Comprehensive PDF Integration Sources
Complete NZ Building Knowledge Base Expansion Plan
Target: Transform STRYDA into the ultimate NZ building assistant
"""

# Phase 1: Complete NZ Building Code Coverage (NZBC A-H)
NZBC_COMPLETE_SOURCES = [
    # Clause A - General
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/a-general/a1-classified-uses/asvm/a1-classified-uses-third-edition-amendment-3.pdf",
        "title": "NZBC A1 Classified Uses - Building Classification System",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/a-general/a2-interpretation/asvm/a2-interpretation-third-edition-amendment-3.pdf", 
        "title": "NZBC A2 Interpretation - Definitions and Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/a-general/a3-building-importance-levels/asvm/a3-building-importance-levels-third-edition-amendment-3.pdf",
        "title": "NZBC A3 Building Importance Levels - Risk Categories",
        "type": "building_code", 
        "organization": "MBIE",
        "priority": "high"
    },
    
    # Clause B - Stability
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b1-structure/asvm/b1-structure-third-edition-amendment-3.pdf",
        "title": "NZBC B1 Structure - Structural Requirements and Load Calculations", 
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/b-stability/b2-durability/asvm/b2-durability-third-edition-amendment-3.pdf",
        "title": "NZBC B2 Durability - Building Element Life Expectancy",
        "type": "building_code",
        "organization": "MBIE", 
        "priority": "high"
    },
    
    # Clause C - Fire Safety
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c1-outbreak-of-fire/asvm/c1-outbreak-of-fire-third-edition-amendment-3.pdf",
        "title": "NZBC C1 Outbreak of Fire - Detection and Early Warning Systems",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c2-means-of-escape/asvm/c2-means-of-escape-third-edition-amendment-3.pdf",
        "title": "NZBC C2 Means of Escape - Emergency Exit Requirements",
        "type": "building_code",
        "organization": "MBIE", 
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c3-spread-of-fire/asvm/c3-spread-of-fire-third-edition-amendment-3.pdf",
        "title": "NZBC C3 Spread of Fire - Fire Separation and Containment",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c4-movement-to-place-of-safety/asvm/c4-movement-to-place-of-safety-third-edition-amendment-3.pdf",
        "title": "NZBC C4 Movement to Place of Safety - Evacuation Procedures",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c5-access-for-firefighting/asvm/c5-access-for-firefighting-third-edition-amendment-3.pdf",
        "title": "NZBC C5 Access for Firefighting - Emergency Vehicle Access",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/c-protection-from-fire/c6-structural-behaviour-during-fire/asvm/c6-structural-behaviour-during-fire-third-edition-amendment-3.pdf",
        "title": "NZBC C6 Structural Behaviour During Fire - Fire Resistance Ratings",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    
    # Clause D - Access
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/d-access/d1-access-routes/asvm/d1-access-routes-third-edition-amendment-3.pdf",
        "title": "NZBC D1 Access Routes - Accessible Building Design",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    
    # Clause E - Moisture
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e1-surface-water/asvm/e1-surface-water-third-edition-amendment-3.pdf",
        "title": "NZBC E1 Surface Water - Drainage and Site Management",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e2-external-moisture/asvm/e2-external-moisture-third-edition-amendment-3.pdf",
        "title": "NZBC E2 External Moisture - Weathertightness Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/e-moisture/e3-internal-moisture/asvm/e3-internal-moisture-third-edition-amendment-3.pdf",
        "title": "NZBC E3 Internal Moisture - Ventilation and Condensation Control",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    
    # Clause F - Safety of Users
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f1-hazardous-agents-on-site/asvm/f1-hazardous-agents-on-site-third-edition-amendment-3.pdf",
        "title": "NZBC F1 Hazardous Agents on Site - Contaminated Land",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f2-hazardous-building-materials/asvm/f2-hazardous-building-materials-third-edition-amendment-3.pdf",
        "title": "NZBC F2 Hazardous Building Materials - Asbestos Management",
        "type": "building_code", 
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f3-illumination/asvm/f3-illumination-third-edition-amendment-3.pdf",
        "title": "NZBC F3 Illumination - Natural and Artificial Lighting",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f4-safety-from-falling/asvm/f4-safety-from-falling-third-edition-amendment-3.pdf",
        "title": "NZBC F4 Safety from Falling - Barriers and Balustrades",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f5-construction-hazards/asvm/f5-construction-hazards-third-edition-amendment-3.pdf",
        "title": "NZBC F5 Construction Hazards - Site Safety Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f6-visibility-in-escape-routes/asvm/f6-visibility-in-escape-routes-third-edition-amendment-3.pdf",
        "title": "NZBC F6 Visibility in Escape Routes - Emergency Lighting",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f7-warning-systems/asvm/f7-warning-systems-third-edition-amendment-3.pdf",
        "title": "NZBC F7 Warning Systems - Fire Alarms and Detection",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/f-safety-of-users/f8-signs/asvm/f8-signs-third-edition-amendment-3.pdf",
        "title": "NZBC F8 Signs - Safety and Wayfinding Signage",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    
    # Clause G - Services and Facilities
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g1-personal-hygiene/asvm/g1-personal-hygiene-third-edition-amendment-3.pdf",
        "title": "NZBC G1 Personal Hygiene - Sanitary Facilities Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g2-laundering/asvm/g2-laundering-third-edition-amendment-3.pdf",
        "title": "NZBC G2 Laundering - Laundry Facility Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "low"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g3-food-preparation/asvm/g3-food-preparation-third-edition-amendment-3.pdf",
        "title": "NZBC G3 Food Preparation - Kitchen Design and Safety",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g4-ventilation/asvm/g4-ventilation-third-edition-amendment-3.pdf",
        "title": "NZBC G4 Ventilation - Fresh Air Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g5-interior-environment/asvm/g5-interior-environment-third-edition-amendment-3.pdf",
        "title": "NZBC G5 Interior Environment - Solid Fuel Appliances and Clearances",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g6-airborne-and-impact-sound/asvm/g6-airborne-and-impact-sound-third-edition-amendment-3.pdf",
        "title": "NZBC G6 Airborne and Impact Sound - Acoustic Performance",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g7-natural-light/asvm/g7-natural-light-third-edition-amendment-3.pdf",
        "title": "NZBC G7 Natural Light - Window and Skylight Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g9-electricity/asvm/g9-electricity-third-edition-amendment-3.pdf",
        "title": "NZBC G9 Electricity - Electrical Installation Requirements",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g10-water-supplies/asvm/g10-water-supplies-third-edition-amendment-3.pdf",
        "title": "NZBC G10 Water Supplies - Potable Water Systems",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g11-wastewater/asvm/g11-wastewater-third-edition-amendment-3.pdf",
        "title": "NZBC G11 Wastewater - Sewage and Greywater Systems",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g12-stormwater/asvm/g12-stormwater-third-edition-amendment-3.pdf",
        "title": "NZBC G12 Stormwater - Rainwater Management Systems",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g13-foul-air/asvm/g13-foul-air-third-edition-amendment-3.pdf",
        "title": "NZBC G13 Foul Air - Odour and Gas Management",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "medium"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g14-refuse/asvm/g14-refuse-third-edition-amendment-3.pdf",
        "title": "NZBC G14 Refuse - Waste Storage and Collection",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "low"
    },
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/g-services-facilities/g15-domestic-water-heating/asvm/g15-domestic-water-heating-third-edition-amendment-3.pdf",
        "title": "NZBC G15 Domestic Water Heating - Hot Water Systems",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "high"
    },
    
    # Clause H - Energy Efficiency
    {
        "url": "https://www.building.govt.nz/assets/Uploads/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/asvm/h1-energy-efficiency-third-edition-amendment-3.pdf",
        "title": "NZBC H1 Energy Efficiency - Insulation and Thermal Performance",
        "type": "building_code",
        "organization": "MBIE",
        "priority": "critical"
    }
]

# Phase 2: Major NZ Council Regulations
COUNCIL_REGULATION_SOURCES = [
    # Auckland Council
    {
        "url": "https://www.aucklandcouncil.govt.nz/plans-projects-policies-reports/our-plans-strategies/unitary-plan/auckland-unitary-plan-operative/Documents/auckland-unitary-plan-operative-in-part.pdf",
        "title": "Auckland Unitary Plan - Building Height and Density Controls",
        "type": "council_regulation",
        "organization": "Auckland Council",
        "priority": "critical"
    },
    {
        "url": "https://www.aucklandcouncil.govt.nz/building-and-consents/building-consents/Documents/building-consent-application-guide.pdf",
        "title": "Auckland Council Building Consent Application Guide",
        "type": "council_regulation", 
        "organization": "Auckland Council",
        "priority": "high"
    },
    
    # Wellington City Council
    {
        "url": "https://wellington.govt.nz/~/media/your-council/plans-policies-and-bylaws/district-plan/volume01/files/v1residential.pdf",
        "title": "Wellington District Plan - Residential Design Guide",
        "type": "council_regulation",
        "organization": "Wellington City Council",
        "priority": "high"
    },
    {
        "url": "https://wellington.govt.nz/~/media/your-council/plans-policies-and-bylaws/district-plan/volume02/files/v2designguides.pdf",
        "title": "Wellington District Plan - Suburban Design Guides",
        "type": "council_regulation",
        "organization": "Wellington City Council",
        "priority": "high"
    },
    
    # Christchurch City Council
    {
        "url": "https://districtplan.ccc.govt.nz/Images/DistrictPlanPDFs/Chapter14ResidentialNewNeighbourhoodZone.pdf",
        "title": "Christchurch District Plan - Residential Zone Requirements",
        "type": "council_regulation",
        "organization": "Christchurch City Council",
        "priority": "high"
    },
    {
        "url": "https://www.ccc.govt.nz/assets/Documents/Consents-and-Licences/building-consents/Building-Consent-Application-Guide.pdf",
        "title": "Christchurch Building Consent Application Guide",
        "type": "council_regulation",
        "organization": "Christchurch City Council", 
        "priority": "high"
    },
    
    # Hamilton City Council
    {
        "url": "https://www.hamilton.govt.nz/our-services/building-and-development/Documents/Building%20Consent%20Information%20Pack.pdf",
        "title": "Hamilton City Building Consent Information Pack",
        "type": "council_regulation",
        "organization": "Hamilton City Council",
        "priority": "medium"
    },
    
    # Tauranga City Council
    {
        "url": "https://www.tauranga.govt.nz/Portals/0/data/council/policies/files/building-policy.pdf",
        "title": "Tauranga City Building Policy and Guidelines",
        "type": "council_regulation", 
        "organization": "Tauranga City Council",
        "priority": "medium"
    },
    
    # Dunedin City Council
    {
        "url": "https://www.dunedin.govt.nz/__data/assets/pdf_file/0010/405689/Building-Consent-Application-Guide.pdf",
        "title": "Dunedin City Building Consent Application Guide",
        "type": "council_regulation",
        "organization": "Dunedin City Council",
        "priority": "medium"
    }
]

# Phase 3: Major NZ Manufacturer Specifications
MANUFACTURER_SPEC_SOURCES = [
    # James Hardie - Cladding Systems
    {
        "url": "https://www.jameshardie.co.nz/homeowner/products/system-installation-guide",
        "title": "James Hardie Cladding System Installation Guide",
        "type": "manufacturer_spec",
        "organization": "James Hardie",
        "priority": "critical"
    },
    {
        "url": "https://www.jameshardie.co.nz/professional/technical-information/installation-guide",
        "title": "James Hardie Technical Installation Manual",
        "type": "manufacturer_spec",
        "organization": "James Hardie",
        "priority": "critical"
    },
    
    # GIB - Plasterboard Systems
    {
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Plasterboard-Systems-Installation-Guide.pdf",
        "title": "GIB Plasterboard Systems Installation Guide",
        "type": "manufacturer_spec",
        "organization": "GIB - Winstone Wallboards",
        "priority": "critical"
    },
    {
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Fire-Systems-Technical-Manual.pdf",
        "title": "GIB Fire Systems Technical Manual",
        "type": "manufacturer_spec",
        "organization": "GIB - Winstone Wallboards", 
        "priority": "high"
    },
    {
        "url": "https://www.gib.co.nz/assets/Uploads/GIB-Weatherline-Installation-Guide.pdf",
        "title": "GIB Weatherline External Wall System Guide",
        "type": "manufacturer_spec",
        "organization": "GIB - Winstone Wallboards",
        "priority": "high"
    },
    
    # Resene - Paint Systems
    {
        "url": "https://www.resene.co.nz/homeown/use_colr/ext_ints.pdf",
        "title": "Resene Paint Systems - Exterior Applications",
        "type": "manufacturer_spec",
        "organization": "Resene Paints",
        "priority": "medium"
    },
    {
        "url": "https://www.resene.co.nz/trade/specification-support/application-guides/timber-staining-guide.pdf",
        "title": "Resene Timber Staining and Protection Guide",
        "type": "manufacturer_spec",
        "organization": "Resene Paints",
        "priority": "medium"
    },
    
    # Pink Batts - Insulation
    {
        "url": "https://www.pinkbatts.co.nz/assets/Uploads/Pink-Batts-Installation-Guide.pdf",
        "title": "Pink Batts Insulation Installation Guide",
        "type": "manufacturer_spec",
        "organization": "Pink Batts - Tasman Insulation",
        "priority": "critical"
    },
    {
        "url": "https://www.pinkbatts.co.nz/assets/Uploads/Pink-Batts-Thermal-Performance-Guide.pdf",
        "title": "Pink Batts Thermal Performance and R-Value Guide",
        "type": "manufacturer_spec",
        "organization": "Pink Batts - Tasman Insulation",
        "priority": "high"
    },
    
    # Colorsteel - Roofing and Cladding
    {
        "url": "https://www.colorsteel.co.nz/assets/Uploads/Colorsteel-Installation-Guide.pdf",
        "title": "Colorsteel Roofing Installation Guide",
        "type": "manufacturer_spec",
        "organization": "Colorsteel - New Zealand Steel",
        "priority": "critical"
    },
    {
        "url": "https://www.colorsteel.co.nz/assets/Uploads/Colorsteel-Cladding-Systems-Manual.pdf",
        "title": "Colorsteel Cladding Systems Technical Manual",
        "type": "manufacturer_spec",
        "organization": "Colorsteel - New Zealand Steel",
        "priority": "high"
    },
    
    # Rondo - Steel Framing
    {
        "url": "https://www.rondo.co.nz/assets/Uploads/Rondo-Steel-Framing-Installation-Guide.pdf",
        "title": "Rondo Steel Framing Installation Guide",
        "type": "manufacturer_spec",
        "organization": "Rondo Building Services",
        "priority": "high"
    },
    
    # Carter Holt Harvey - Timber Products
    {
        "url": "https://www.chhwoodproducts.co.nz/assets/Uploads/CHH-Structural-Timber-Guide.pdf",
        "title": "Carter Holt Harvey Structural Timber Guide",
        "type": "manufacturer_spec",
        "organization": "Carter Holt Harvey",
        "priority": "high"
    },
    
    # Metrofires - Solid Fuel Appliances
    {
        "url": "https://www.metrofires.co.nz/assets/Uploads/Metrofires-Installation-Manual.pdf",
        "title": "Metrofires Solid Fuel Appliance Installation Manual",
        "type": "manufacturer_spec",
        "organization": "Metrofires",
        "priority": "high"
    },
    
    # Nulook - Windows and Doors
    {
        "url": "https://www.nulook.co.nz/assets/Uploads/Nulook-Installation-Guide.pdf",
        "title": "Nulook Windows and Doors Installation Guide",
        "type": "manufacturer_spec",
        "organization": "Nulook Windows",
        "priority": "medium"
    },
    
    # Lockwood - Solid Timber Construction
    {
        "url": "https://www.lockwood.co.nz/assets/Uploads/Lockwood-Construction-Manual.pdf",
        "title": "Lockwood Solid Timber Construction Manual",
        "type": "manufacturer_spec",
        "organization": "Lockwood Group",
        "priority": "medium"
    }
]

# Phase 4: Critical NZ Standards (NZS/AS-NZS)
NZ_STANDARDS_SOURCES = [
    # Structural Standards
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS3604-2011-Timber-framed-buildings.pdf",
        "title": "NZS 3604:2011 Timber-framed Buildings Standard",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "critical"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS3101-2006-Concrete-structures-standard.pdf", 
        "title": "NZS 3101:2006 Concrete Structures Standard",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "critical"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS3404-1997-Steel-structures-standard.pdf",
        "title": "NZS 3404:1997 Steel Structures Standard",
        "type": "nz_standard", 
        "organization": "Standards New Zealand",
        "priority": "high"
    },
    
    # Building Services Standards
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/AS-NZS3000-2018-Electrical-installations.pdf",
        "title": "AS/NZS 3000:2018 Electrical Installations Standard",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "critical"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/AS-NZS3500.1-2018-Plumbing-and-drainage-Part-1.pdf",
        "title": "AS/NZS 3500.1:2018 Plumbing and Drainage - Water Services",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "critical"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/AS-NZS3500.2-2018-Plumbing-and-drainage-Part-2.pdf",
        "title": "AS/NZS 3500.2:2018 Plumbing and Drainage - Sanitary Plumbing",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "critical"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/AS-NZS3500.3-2018-Plumbing-and-drainage-Part-3.pdf",
        "title": "AS/NZS 3500.3:2018 Plumbing and Drainage - Stormwater Drainage",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "high"
    },
    
    # Fire and Safety Standards
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS4541-2013-Automatic-fire-sprinkler-systems.pdf",
        "title": "NZS 4541:2013 Automatic Fire Sprinkler Systems",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "high"
    },
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS4230-2004-Design-of-reinforced-concrete-masonry.pdf",
        "title": "NZS 4230:2004 Design of Reinforced Concrete Masonry",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "high"
    },
    
    # Glazing and Windows
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/NZS4223-2008-Glazing-in-buildings.pdf",
        "title": "NZS 4223:2008 Glazing in Buildings",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "medium"
    },
    
    # Insulation and Energy
    {
        "url": "https://www.standards.govt.nz/assets/Publication-files/AS-NZS4859.1-2018-Thermal-insulation-materials.pdf",
        "title": "AS/NZS 4859.1:2018 Thermal Insulation Materials for Buildings",
        "type": "nz_standard",
        "organization": "Standards New Zealand",
        "priority": "high"
    }
]

# Combined comprehensive sources for all phases
ALL_COMPREHENSIVE_SOURCES = (
    NZBC_COMPLETE_SOURCES + 
    COUNCIL_REGULATION_SOURCES + 
    MANUFACTURER_SPEC_SOURCES + 
    NZ_STANDARDS_SOURCES
)

def get_sources_by_priority(priority_level="all"):
    """Filter sources by priority level"""
    if priority_level == "all":
        return ALL_COMPREHENSIVE_SOURCES
    elif priority_level == "critical":
        return [source for source in ALL_COMPREHENSIVE_SOURCES if source.get("priority") == "critical"]
    elif priority_level == "high":
        return [source for source in ALL_COMPREHENSIVE_SOURCES if source.get("priority") in ["critical", "high"]]
    else:
        return ALL_COMPREHENSIVE_SOURCES

def get_sources_by_type(doc_type="all"):
    """Filter sources by document type"""
    if doc_type == "all":
        return ALL_COMPREHENSIVE_SOURCES
    else:
        return [source for source in ALL_COMPREHENSIVE_SOURCES if source.get("type") == doc_type]

# Statistics
TOTAL_SOURCES = len(ALL_COMPREHENSIVE_SOURCES)
CRITICAL_SOURCES = len([s for s in ALL_COMPREHENSIVE_SOURCES if s.get("priority") == "critical"])
HIGH_SOURCES = len([s for s in ALL_COMPREHENSIVE_SOURCES if s.get("priority") in ["critical", "high"]])

print(f"""
📊 COMPREHENSIVE NZ BUILDING KNOWLEDGE EXPANSION PLAN
═══════════════════════════════════════════════════════

📋 Total Sources: {TOTAL_SOURCES}
🔥 Critical Priority: {CRITICAL_SOURCES}
⭐ High Priority+: {HIGH_SOURCES}

📖 By Document Type:
   • Building Codes (NZBC): {len(NZBC_COMPLETE_SOURCES)}
   • Council Regulations: {len(COUNCIL_REGULATION_SOURCES)}
   • Manufacturer Specs: {len(MANUFACTURER_SPEC_SOURCES)}
   • NZ Standards: {len(NZ_STANDARDS_SOURCES)}

🎯 Target Knowledge Base: 15,000-20,000+ documents
🚀 Current Base: 4,671 documents
📈 Expansion Factor: ~4x growth
""")