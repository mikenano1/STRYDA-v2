"""
STRYDA.ai Enhanced Knowledge Base - Comprehensive NZ Building Intelligence
Expands knowledge base with comprehensive manufacturers, building codes, and standards
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class EnhancedKnowledgeBase:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.comprehensive_documents = self._load_comprehensive_documents()
    
    def _load_comprehensive_documents(self) -> List[Dict[str, Any]]:
        """Load comprehensive NZ building knowledge base"""
        
        documents = []
        
        # === EXPANDED NZ BUILDING CODE DOCUMENTS ===
        
        # Building Code Clause B1 - Structure
        documents.append({
            "title": "NZBC Clause B1 - Structure (Structural Requirements)",
            "content": """
            B1.1 General structural requirements
            
            B1.1.1 Structural design
            Buildings must be designed to withstand all loads likely to occur during construction and use.
            
            B1.1.2 Dead loads
            Permanent loads including:
            - Building materials and fixed equipment
            - Minimum design weights as per AS/NZS 1170.1
            
            B1.1.3 Live loads
            Variable loads including:
            - Occupancy loads (residential: 1.5 kPa, commercial varies)
            - Snow loads (varies by location and altitude)
            - Wind loads (AS/NZS 1170.2)
            
            B1.1.4 Seismic design
            All buildings must be designed for earthquake loads:
            - Site class determination required
            - Hazard factor Z varies by location (0.13-0.60)
            - Structural ductility factor μ determines detailing requirements
            
            B1.1.5 Foundation design
            Foundations must:
            - Transfer all loads safely to ground
            - Account for ground conditions and bearing capacity
            - Provide adequate protection against ground moisture
            
            B1.1.6 Timber frame design
            Refer to NZS 3604:2011 for light timber construction up to 10m height
            For structures outside NZS 3604 scope, use NZS 3603 or alternative solution
            
            Reference: Building Code Clause B1, Building Regulations 1992
            """,
            "source_url": "https://www.building.govt.nz/building-code-compliance/b-stability/b1-structure/",
            "document_type": "nzbc",
            "metadata": {
                "clause": "B1",
                "section": "Structure",
                "category": "structural",
                "tags": ["structure", "foundations", "seismic", "loads", "timber", "design"]
            }
        })
        
        # Building Code Clause F2 - Hazardous Building Materials
        documents.append({
            "title": "NZBC Clause F2 - Hazardous Building Materials (Asbestos)",
            "content": """
            F2.1 Hazardous building materials requirements
            
            F2.1.1 Asbestos prohibition
            The manufacture, import, supply, and use of materials containing asbestos is prohibited.
            
            F2.1.2 Existing asbestos materials
            Where asbestos materials exist in buildings:
            - Must be identified during any building work
            - Removal must comply with Health and Safety at Work (Asbestos) Regulations 2016
            - Licensed asbestos removalists required for friable asbestos
            
            F2.1.3 Asbestos identification
            Common locations of asbestos in pre-1980s buildings:
            - Fibrolite sheets (walls and eaves)
            - Asbestos cement pipes
            - Vinyl floor tiles and backing
            - Textured ceiling coatings
            - Thermal insulation around pipes and boilers
            
            F2.1.4 Safe work practices
            When asbestos is suspected:
            - Stop work immediately
            - Engage licensed asbestos assessor for identification
            - Follow WorkSafe NZ guidelines for asbestos management
            - Notify all workers and occupants
            
            F2.1.5 Disposal requirements
            Asbestos waste must be:
            - Double-wrapped in 200-micron plastic
            - Clearly labeled as asbestos waste
            - Disposed of at approved landfills only
            - Accompanied by waste tracking documentation
            
            Reference: Building Code Clause F2, Health and Safety at Work Act 2015
            """,
            "source_url": "https://www.building.govt.nz/building-code-compliance/f-safety-of-users/f2-hazardous-building-materials/",
            "document_type": "nzbc",
            "metadata": {
                "clause": "F2",
                "section": "Hazardous Materials",
                "category": "safety",
                "tags": ["asbestos", "hazardous", "safety", "removal", "worksafe", "health"]
            }
        })
        
        # === COMPREHENSIVE MANUFACTURER DOCUMENTS ===
        
        # Gib - Plasterboard Systems
        documents.append({
            "title": "GIB Plasterboard Installation Guide",
            "content": """
            GIB Plasterboard Installation Requirements
            
            Installation Standards:
            All GIB plasterboard installation must comply with NZS 4251 and manufacturer specifications.
            
            Stud Spacing Requirements:
            - Standard GIB: 600mm maximum stud centres
            - 13mm GIB: 450mm maximum for ceilings, 600mm for walls
            - Wet area applications: 450mm maximum in all directions
            
            Fixing Requirements:
            Standard Wall Installation:
            - GIB screws at 300mm centres to perimeter
            - GIB screws at 400mm centres to intermediate supports
            - Minimum 13mm penetration into timber studs
            - Screws must be 6mm minimum from cut edges
            
            Wet Area Installation:
            - Must use wet area rated GIB boards
            - Tanking system required behind showers/baths
            - Seal all penetrations with appropriate sealants
            - Minimum 200mm above bath rim, full height in showers
            
            Fire Rated Systems:
            - Fire rated GIB systems must follow tested configurations exactly
            - No substitution of materials without re-testing
            - All penetrations must maintain fire rating
            - Installation certificates required for commercial applications
            
            Jointing and Finishing:
            - All joints must be reinforced with GIB tape
            - Three coat system: base coat, fill coat, finish coat
            - Sand lightly between coats when dry
            - Prime before painting with appropriate sealer
            
            Common Installation Errors to Avoid:
            - Over-driving screws (paper face damaged)
            - Inadequate support at board edges
            - Incorrect screw spacing
            - Mixing different GIB systems in same area
            
            Contact: GIB Technical Support 0800 422 842
            """,
            "source_url": "https://www.gib.co.nz/technical-support/installation-guides",
            "document_type": "manufacturer",
            "metadata": {
                "manufacturer": "GIB",
                "product_type": "plasterboard",
                "category": "interior_lining",
                "tags": ["gib", "plasterboard", "installation", "fixing", "wet_area", "fire_rating"]
            }
        })
        
        # James Hardie - Cladding Systems  
        documents.append({
            "title": "James Hardie Cladding Installation Manual",
            "content": """
            James Hardie Fibre Cement Cladding Installation
            
            Product Range:
            - HardiePanel (vertical cladding)
            - HardiePlank (weatherboard style)
            - HardieGroove (grooved panel system)
            - Axon Panel (textured cladding)
            
            General Installation Requirements:
            All installations must comply with E2/AS1 and manufacturer specifications.
            
            Structural Support:
            - Minimum 90x45mm timber framing at 600mm centres
            - Dwangs required at 1200mm maximum vertical spacing
            - Additional dwangs at panel joints
            - Steel framing requires specific fixing schedule
            
            Cavity System Requirements:
            - 20mm minimum cavity behind cladding
            - Building wrap over frame, under cavity battens
            - Cavity battens minimum 45x20mm treated timber
            - Ventilation gaps at top and bottom of cavity
            
            Fixing Schedule:
            HardiePanel 9mm:
            - Hot-dip galvanized flat head nails minimum 2.8x65mm
            - 300mm centres to all supports
            - Minimum 12mm from edges
            - Pre-drill within 50mm of corners
            
            HardiePlank 18mm:
            - Stainless steel or hot-dip galvanized nails 2.8x75mm
            - Fix through overlap zone only (top 40mm of lower board)
            - 600mm maximum centres horizontally
            
            Jointing and Sealing:
            - Horizontal joints require flashing
            - Vertical joints require backing rod and sealant
            - Use polyurethane sealant compatible with fibre cement
            - All penetrations must be properly flashed and sealed
            
            Cutting and Handling:
            - Use carbide-tipped saw blades or shears
            - Wear appropriate PPE (dust mask, safety glasses)
            - Support boards properly during cutting
            - Clean cut edges before installation
            
            Painting and Finishing:
            - Prime all cut edges before installation
            - Use high-quality acrylic paint systems
            - Two-coat system minimum over primer
            - Re-coat intervals as per paint manufacturer
            
            Wind Zone Considerations:
            - High wind zones may require closer fixing centres
            - Additional structural support may be needed
            - Refer to E2/AS1 wind pressure tables
            
            Contact: James Hardie Technical 0800 808 868
            """,
            "source_url": "https://www.jameshardie.co.nz/technical-support/installation-guides",
            "document_type": "manufacturer",
            "metadata": {
                "manufacturer": "James Hardie",
                "product_type": "fibre_cement_cladding",
                "category": "cladding",
                "tags": ["james_hardie", "cladding", "fibre_cement", "installation", "cavity", "fixing"]
            }
        })
        
        # Resene - Paint Systems and Specifications
        documents.append({
            "title": "Resene Paint Systems - Exterior Applications",
            "content": """
            Resene Paint Systems for New Zealand Conditions
            
            System Selection:
            Choose paint systems based on substrate and exposure conditions.
            
            Timber Substrates:
            New Timber Preparation:
            - Sand to 120-150 grit finish
            - Remove all dust and contamination
            - Prime within 48 hours of preparation
            - Use Resene Quick Dry Primer Undercoat
            
            Previously Painted Timber:
            - Check for lead paint (pre-1980s buildings)
            - Remove loose and flaking paint
            - Sand glossy surfaces for adhesion
            - Clean with sugar soap solution
            
            Fibre Cement Substrates:
            - New fibre cement must be primed within 6 months
            - Use Resene 3 in 1 Primer Sealer Undercoat
            - Pay special attention to cut edges
            - Two topcoats minimum for durability
            
            System Recommendations by Exposure:
            
            Severe Exposure (coastal, high UV):
            - Prime: Resene 3 in 1 Primer Sealer Undercoat
            - Intermediate: Resene Lumbersider (first topcoat)  
            - Finish: Resene Lumbersider (second topcoat)
            - Expected life: 12-15 years
            
            Moderate Exposure (suburban):
            - Prime: Resene Quick Dry Primer Undercoat
            - Finish: 2 coats Resene Lumbersider
            - Expected life: 10-12 years
            
            Protected Areas (eaves, protected walls):
            - Prime: Resene Primer Undercoat
            - Finish: 2 coats Resene SpaceCote
            - Expected life: 8-10 years
            
            Application Conditions:
            - Temperature: 10-30°C during application and cure
            - Humidity: Below 85% relative humidity
            - Wind: Avoid application in strong winds
            - Rain: No rain forecast for 4 hours after application
            
            Coverage Rates:
            - Primer/Undercoat: 10-12 m²/litre
            - Topcoat on primed surface: 12-14 m²/litre
            - Topcoat on previously painted: 14-16 m²/litre
            
            Quality Control:
            - Use quality brushes and rollers
            - Maintain wet edge during application
            - Back-roll spray applications
            - Allow full recoat time between coats
            
            Common Issues:
            - Flaking: Usually due to poor surface preparation
            - Fading: Inadequate UV protection or wrong system choice
            - Chalking: Normal weathering, increase system specification
            
            Environmental Considerations:
            - Use low-VOC formulations where possible
            - Dispose of paint waste at approved facilities
            - Clean equipment with appropriate solvents
            
            Contact: Resene ColorShop for technical advice
            """,
            "source_url": "https://www.resene.co.nz/technical-advice/paint-systems",
            "document_type": "manufacturer",
            "metadata": {
                "manufacturer": "Resene",
                "product_type": "paint_systems",
                "category": "finishing",
                "tags": ["resene", "paint", "exterior", "systems", "preparation", "application"]
            }
        })
        
        # Pink Batts - Insulation Systems
        documents.append({
            "title": "Pink Batts Insulation Installation Guide",
            "content": """
            Pink Batts Glasswool Insulation Installation
            
            Product Range and R-Values:
            
            Ceiling Insulation:
            - R1.8 (145mm) - Zone 1 minimum
            - R2.6 (200mm) - Zone 2 minimum  
            - R3.2 (260mm) - Zone 3 minimum
            - R4.0 (330mm) - High performance option
            
            Wall Insulation:
            - R1.5 (90mm) - Standard wall cavity
            - R1.8 (94mm) - Enhanced performance
            - R2.2 (140mm) - Thick wall construction
            
            Underfloor Insulation:
            - R1.3 (segments) - Minimum requirement all zones
            - R1.5 (segments) - Enhanced performance
            - R1.8 (segments) - High performance option
            
            Installation Requirements:
            
            Ceiling Installation:
            - Install between ceiling joists, not over them
            - Maintain 75mm clearance to recessed lights
            - Do not compress insulation
            - Cover with building paper in roof spaces
            - Ventilation gaps maintained at eaves
            
            Wall Installation:
            - Cut batts 10-15mm oversize for friction fit
            - Fill entire cavity without gaps or compression  
            - Electrical cables can pass through batts
            - Vapor barrier on warm side in cold climates
            - Do not install behind wet area linings
            
            Underfloor Installation:
            - Support with building wire or battens
            - Paper face towards heated space (up)
            - Overlap segments by 25mm minimum
            - Seal gaps with tape or additional segments
            - Protect from moisture and vermin
            
            Health and Safety:
            Personal Protective Equipment:
            - Long sleeves and long pants
            - Dust mask (P2 rating minimum)
            - Safety glasses or goggles
            - Gloves (disposable recommended)
            
            Safe Handling:
            - Minimize skin contact with glasswool
            - Work in well-ventilated areas
            - Shower after installation work
            - Wash work clothes separately
            
            Common Installation Errors:
            - Compressing insulation reduces R-value significantly
            - Leaving gaps allows thermal bridging
            - Installing wrong way up (underfloor)
            - Blocking ventilation pathways
            - Insufficient clearance to heat sources
            
            Building Code Compliance:
            - Installation must achieve minimum R-values for climate zone
            - Thermal bridging must be addressed
            - Condensation control may require vapor barriers
            - Fire separation requirements in roof spaces
            
            Performance Factors:
            - Moisture reduces insulation effectiveness
            - Air gaps significantly reduce performance
            - Thermal bridging through framing
            - Installation quality affects long-term performance
            
            Contact: Pink Batts Technical Support 0800 BATTS1
            """,
            "source_url": "https://www.pinkbatts.co.nz/technical-support/installation-guides",
            "document_type": "manufacturer",
            "metadata": {
                "manufacturer": "Pink Batts",
                "product_type": "glasswool_insulation", 
                "category": "insulation",
                "tags": ["pink_batts", "insulation", "glasswool", "r_values", "installation", "thermal"]
            }
        })
        
        # === ADVANCED NZS STANDARDS ===
        
        # NZS 4230 - Concrete Masonry Design  
        documents.append({
            "title": "NZS 4230:2004 - Design of Reinforced Concrete Masonry",
            "content": """
            NZS 4230:2004 Reinforced Concrete Masonry Design
            
            Scope and Application:
            Covers design of reinforced concrete masonry structures including:
            - Residential and commercial buildings
            - Retaining walls and boundary walls
            - Seismic design requirements
            - Material specifications
            
            Material Requirements:
            
            Concrete Masonry Units:
            - Minimum compressive strength: 15 MPa (residential)
            - Higher strengths required for commercial: 20-30 MPa
            - Units must comply with AS/NZS 4455.1
            - Shrinkage movement considerations
            
            Mortar Specifications:
            - Type M mortar: General purpose (10 MPa minimum)
            - Type S mortar: High strength (15 MPa minimum) 
            - Type N mortar: Medium strength (5 MPa minimum)
            - Plasticizer use affects bond strength
            
            Reinforcing Steel:
            - Grade 300E deformed bars (residential)
            - Grade 500E for higher loads
            - Minimum cover: 15mm internal, 25mm external
            - Lap lengths vary with bar diameter and grade
            
            Structural Design Requirements:
            
            Wall Design:
            - Slenderness limits for unreinforced masonry
            - Reinforcement requirements for height/thickness ratios
            - Control joint spacing: 6m maximum
            - Openings require lintels sized for loads
            
            Seismic Design:
            - Masonry structures must be designed for earthquake loads
            - Ductile detailing required in high seismic zones
            - Special reinforcement at wall intersections
            - Ties between masonry and other materials
            
            Foundation Requirements:
            - Starter bars from foundation must lap with wall reinforcement
            - Minimum foundation width: wall thickness plus 100mm
            - Damp-proof course required between foundation and masonry
            - Expansion joints aligned through foundation
            
            Construction Requirements:
            
            Workmanship Standards:
            - Full bedding of mortar joints required
            - Head joints must be filled completely
            - No partial grouting permitted in reinforced masonry
            - Weather protection during construction
            
            Grouting Requirements:
            - Grout must be fluid consistency for placement
            - Lift heights limited to 1.2m maximum
            - Consolidation required to eliminate voids
            - Grout strength minimum 15 MPa at 28 days
            
            Quality Control:
            - Mortar cube testing required
            - Grout cylinder testing required  
            - Reinforcement placement inspection
            - Prism testing for masonry strength verification
            
            Common Design Issues:
            - Inadequate connection to other structural elements
            - Insufficient reinforcement for seismic loads
            - Thermal movement not accommodated
            - Moisture penetration through mortar joints
            
            Reference: NZS 4230:2004 Design of reinforced concrete masonry structures
            """,
            "source_url": "https://www.standards.govt.nz/shop/nzs-42302004",
            "document_type": "nzs",
            "metadata": {
                "standard": "NZS 4230:2004",
                "section": "Concrete Masonry Design",
                "category": "structural_masonry",
                "tags": ["concrete_masonry", "reinforced", "design", "seismic", "mortar", "grout"]
            }
        })
        
        return documents
    
    async def load_all_comprehensive_documents(self):
        """Load all comprehensive documents into the knowledge base"""
        logger.info("Loading comprehensive NZ building knowledge base...")
        
        total_processed = 0
        for doc in self.comprehensive_documents:
            try:
                doc_id = await self.document_processor.process_and_store_document(
                    title=doc["title"],
                    content=doc["content"],
                    source_url=doc["source_url"],
                    document_type=doc["document_type"],
                    metadata=doc["metadata"]
                )
                total_processed += 1
                logger.info(f"Processed: {doc['title']}")
                
            except Exception as e:
                logger.error(f"Error processing {doc['title']}: {e}")
        
        logger.info(f"Comprehensive knowledge base loaded: {total_processed} documents")
        return total_processed