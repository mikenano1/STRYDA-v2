"""
STRYDA.ai Visual Content Engine
Intelligent retrieval and display of diagrams, charts, and technical visuals from knowledge base
"""

import os
import logging
import base64
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import re
from datetime import datetime
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class VisualContent(BaseModel):
    """Represents visual content with metadata"""
    id: str
    title: str
    description: str
    content_type: str  # 'diagram', 'chart', 'installation_guide', 'compliance_chart'
    source_document: str
    image_base64: str
    keywords: List[str]
    nz_building_codes: List[str]  # Related NZBC clauses
    trade_categories: List[str]  # 'electrical', 'plumbing', 'structural', etc.
    difficulty_level: str  # 'basic', 'intermediate', 'advanced'
    created_at: datetime

class VisualContentEngine:
    """Engine for intelligent visual content retrieval"""
    
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.db = document_processor.db
        self.collection = self.db.visual_content
        self.visual_mappings = self._initialize_visual_mappings()
    
    def _initialize_visual_mappings(self) -> Dict[str, Dict]:
        """Initialize mappings of common queries to visual content"""
        return {
            # Hearth and Fireplace
            "hearth": {
                "keywords": ["hearth", "fireplace", "solid fuel", "combustion", "clearance"],
                "nz_codes": ["G5.3.2", "G5.3.3"],
                "content_type": "installation_guide",
                "description": "Hearth clearance requirements and installation diagrams"
            },
            "fireplace_clearance": {
                "keywords": ["fireplace clearance", "combustible materials", "hearth pad"],
                "nz_codes": ["G5.3.2"],
                "content_type": "diagram", 
                "description": "Required clearances for fireplaces from combustible materials"
            },
            
            # Insulation
            "insulation": {
                "keywords": ["insulation", "thermal", "R-value", "H1"],
                "nz_codes": ["H1.2", "H1.3"],
                "content_type": "chart",
                "description": "NZ insulation requirements by climate zone"
            },
            "r_value": {
                "keywords": ["R-value", "thermal resistance", "insulation thickness"],
                "nz_codes": ["H1.2"],
                "content_type": "chart",
                "description": "R-value requirements chart for different building elements"
            },
            
            # Weathertightness
            "weathertightness": {
                "keywords": ["weathertightness", "moisture", "E2", "cladding"],
                "nz_codes": ["E2.1.1", "E2.3.2"],
                "content_type": "installation_guide",
                "description": "E2 weathertightness installation details and junction diagrams"
            },
            "flashing": {
                "keywords": ["flashing", "window", "door", "penetration"],
                "nz_codes": ["E2.3.2"],
                "content_type": "diagram",
                "description": "Proper flashing installation diagrams for openings"
            },
            
            # Structural
            "framing": {
                "keywords": ["framing", "timber", "NZS3604", "structural"],
                "nz_codes": ["B1.3.1"],
                "content_type": "diagram",
                "description": "Timber framing connection details and spacing requirements"
            },
            "foundation": {
                "keywords": ["foundation", "concrete", "slab", "footing"],
                "nz_codes": ["B1.3.3"],
                "content_type": "diagram",
                "description": "Foundation construction details and reinforcement diagrams"
            },
            
            # Electrical
            "switchboard": {
                "keywords": ["switchboard", "electrical", "RCD", "main switch"],
                "nz_codes": ["G9.2"],
                "content_type": "diagram",
                "description": "Electrical switchboard layout and safety requirements"
            },
            "wiring": {
                "keywords": ["electrical wiring", "cable", "conduit", "AS/NZS3000"],
                "nz_codes": ["G9.3"],
                "content_type": "installation_guide",
                "description": "Electrical wiring installation methods and protection"
            }
        }
    
    async def find_relevant_visuals(self, query: str, max_results: int = 3) -> List[VisualContent]:
        """Find visual content relevant to user query"""
        try:
            # First, try to match with predefined visual mappings
            query_lower = query.lower()
            matched_visuals = []
            
            for keyword, mapping in self.visual_mappings.items():
                if any(kw in query_lower for kw in mapping["keywords"]):
                    # Create visual content based on mapping
                    visual = await self._generate_visual_content(keyword, mapping)
                    if visual:
                        matched_visuals.append(visual)
            
            # If we have predefined visuals, return them
            if matched_visuals:
                return matched_visuals[:max_results]
            
            # Otherwise, search in processed documents for visual references
            document_visuals = await self._search_document_visuals(query)
            return document_visuals[:max_results]
            
        except Exception as e:
            logger.error(f"Error finding relevant visuals: {e}")
            return []
    
    async def _generate_visual_content(self, keyword: str, mapping: Dict) -> Optional[VisualContent]:
        """Generate visual content based on mapping"""
        try:
            # For MVP, we'll create placeholder diagrams with descriptions
            # In production, these would be actual diagrams from the knowledge base
            
            visual_id = f"visual_{keyword}_{int(datetime.now().timestamp())}"
            
            # Create a text-based diagram description for now
            # TODO: Replace with actual image generation or retrieval
            diagram_description = self._create_text_diagram(keyword, mapping)
            
            return VisualContent(
                id=visual_id,
                title=mapping["description"],
                description=f"Technical diagram showing: {mapping['description']}",
                content_type=mapping["content_type"],
                source_document=f"NZBC {', '.join(mapping['nz_codes'])}",
                image_base64="",  # Placeholder - would contain actual image data
                keywords=mapping["keywords"],
                nz_building_codes=mapping["nz_codes"],
                trade_categories=self._determine_trade_category(keyword),
                difficulty_level="intermediate",
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error generating visual content for {keyword}: {e}")
            return None
    
    def _create_text_diagram(self, keyword: str, mapping: Dict) -> str:
        """Create ASCII-style text diagrams for visual representation"""
        diagrams = {
            "hearth": """
HEARTH CLEARANCE REQUIREMENTS (NZBC G5.3.2)
════════════════════════════════════════════

           [COMBUSTIBLE WALL]
                   │
     ┌─────────────┼─────────────┐  ← 300mm min clearance
     │             │             │
     │    ┌─────────────────┐    │
     │    │                 │    │
     │    │    FIREPLACE    │    │  ← Fire opening
     │    │                 │    │
     │    └─────────────────┘    │
     │                           │
     └───────────────────────────┘
              HEARTH PAD
        ← 300mm → ← 300mm →
        
Key Requirements:
• Hearth extends 300mm beyond fireplace opening
• Non-combustible materials only
• Minimum thickness: 12mm
            """,
            
            "insulation": """
NZ CLIMATE ZONES - INSULATION R-VALUES (H1.2)
════════════════════════════════════════════

Zone 1 (Auckland): R1.9 walls, R2.9 ceiling
Zone 2 (Wellington): R2.0 walls, R3.3 ceiling  
Zone 3 (Christchurch): R2.2 walls, R3.3 ceiling
Zone 4 (Queenstown): R2.5 walls, R3.3 ceiling
Zone 5 (Central Otago): R2.6 walls, R4.0 ceiling
Zone 6 (Fiordland): R2.8 walls, R4.6 ceiling

     [CEILING R3.3-R4.6]
    ═══════════════════════
    ║                     ║ [WALL R1.9-R2.8]
    ║     LIVING SPACE    ║
    ║                     ║
    ═══════════════════════
         [FLOOR R1.3-R2.2]
            """,
            
            "weathertightness": """
WINDOW FLASHING DETAIL (E2.3.2)
══════════════════════════════

    [CLADDING]
         │
    ┌────▼────┐  ← Head flashing
    │ WINDOW  │
    │ HEAD    │  ← Seal with sealant
    ├─────────┤
    │         │  ← Window opening
    │ WINDOW  │
    │ SILL    │  ← Sill flashing
    └─┬─────┬─┘
      │     │    ← Drainage gaps
      ▼     ▼
   [CAVITY] [CAVITY]
   
Critical Points:
• Head flashing laps behind cladding
• Sill flashing projects 5mm minimum
• Continuous seal at frame-to-opening junction
            """
        }
        
        return diagrams.get(keyword, f"Technical diagram for {keyword} - {mapping['description']}")
    
    def _determine_trade_category(self, keyword: str) -> List[str]:
        """Determine trade categories based on keyword"""
        trade_mappings = {
            "hearth": ["general_building", "fire_safety"],
            "fireplace_clearance": ["general_building", "fire_safety"],
            "insulation": ["insulation", "general_building"],
            "weathertightness": ["cladding", "general_building"],
            "flashing": ["cladding", "roofing"],
            "framing": ["structural", "carpentry"],
            "foundation": ["structural", "concrete"],
            "switchboard": ["electrical"],
            "wiring": ["electrical"]
        }
        return trade_mappings.get(keyword, ["general_building"])
    
    async def _search_document_visuals(self, query: str) -> List[VisualContent]:
        """Search for visual content references in processed documents"""
        try:
            # This would search through document metadata for visual references
            # For now, return empty list as we don't have visual content indexed yet
            return []
            
        except Exception as e:
            logger.error(f"Error searching document visuals: {e}")
            return []
    
    async def get_visual_by_id(self, visual_id: str) -> Optional[VisualContent]:
        """Retrieve specific visual content by ID"""
        try:
            visual_doc = await self.collection.find_one({"id": visual_id})
            if visual_doc:
                return VisualContent(**visual_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving visual {visual_id}: {e}")
            return None
    
    async def store_visual_content(self, visual: VisualContent) -> bool:
        """Store visual content in database"""
        try:
            await self.collection.insert_one(visual.dict())
            logger.info(f"Stored visual content: {visual.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing visual content: {e}")
            return False