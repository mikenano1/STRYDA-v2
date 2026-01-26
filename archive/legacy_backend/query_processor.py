"""
STRYDA.ai Advanced Query Processor
Implements Gemini's day-one question patterns with smart field extraction
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    CARPENTRY_FRAMING = "carpentry_framing"
    CLADDING_WEATHERPROOFING = "cladding_weatherproofing"
    WET_AREAS_PLUMBING = "wet_areas_plumbing"
    FIRE_SAFETY = "fire_safety"
    INSULATION_THERMAL = "insulation_thermal"
    STRUCTURAL_DESIGN = "structural_design"
    GENERAL = "general"

@dataclass
class ExtractedFields:
    """Structured fields extracted from query"""
    dimensions: Dict[str, float] = None
    materials: List[str] = None
    location_zone: str = None
    brand_model: str = None
    building_type: str = None
    specific_code: str = None
    
@dataclass
class ProcessedQuery:
    """Processed query with extracted information"""
    original_query: str
    query_type: QueryType
    extracted_fields: ExtractedFields
    enhanced_query: str
    search_keywords: List[str]
    required_documents: List[str]

class AdvancedQueryProcessor:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.query_patterns = self._load_query_patterns()
        
    def _load_query_patterns(self) -> Dict[str, Any]:
        """Load Gemini's day-one query patterns with field extraction"""
        
        return {
            QueryType.CARPENTRY_FRAMING: {
                "patterns": [
                    r"(lintel|beam).*size.*window.*opening",
                    r"dwang|nog.*wall.*spacing",
                    r"stud.*spacing.*height.*bracing",
                    r"timber.*frame.*requirements",
                    r"joist.*span.*spacing"
                ],
                "field_extractors": {
                    "span": r"(\d+(?:\.\d+)?)\s*(?:m|mm|metre|meter)",
                    "load": r"(residential|commercial|heavy|light|dead|live)\s*load",
                    "wood_type": r"(pine|hardwood|lvl|glulam|timber)",
                    "stud_height": r"(\d+(?:\.\d+)?)\s*(?:m|mm)\s*(?:high|height|stud)",
                    "spacing": r"(\d+)\s*(?:mm|m)\s*(?:centres|centers|spacing|oc|o\.c\.)"
                },
                "required_docs": ["nzs_3604", "nzbc_b1"],
                "enhanced_keywords": ["NZS 3604", "span tables", "timber framing", "structural", "dwangs", "nogs"]
            },
            
            QueryType.CLADDING_WEATHERPROOFING: {
                "patterns": [
                    r"cladding.*wind.*zone",
                    r"weathertight.*requirements", 
                    r"flashing.*window.*penetration",
                    r"cavity.*system.*installation",
                    r"e2.*weathertightness"
                ],
                "field_extractors": {
                    "cladding_type": r"(hardiplank|weatherboard|brick|block|stucco|fibre.*cement)",
                    "wind_zone": r"(low|medium|high|very.*high)\s*wind|wind.*zone.*([1-4])",
                    "window_size": r"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:m|mm)",
                    "exposure": r"(sheltered|normal|exposed|severe)\s*exposure"
                },
                "required_docs": ["nzbc_e2", "e2_as1"],
                "enhanced_keywords": ["E2/AS1", "weathertightness", "cladding", "flashing", "cavity"]
            },
            
            QueryType.WET_AREAS_PLUMBING: {
                "patterns": [
                    r"shower.*timber.*floor.*tray",
                    r"wet.*area.*waterproofing",
                    r"bathroom.*tanking.*requirements",
                    r"e3.*plumbing.*compliance"
                ],
                "field_extractors": {
                    "subfloor_type": r"(timber|concrete|suspended|slab)\s*(?:floor|subfloor)",
                    "room_type": r"(bathroom|shower|laundry|kitchen|toilet)",
                    "room_size": r"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:m|mm)",
                    "material": r"(tile|vinyl|timber|concrete)\s*(?:floor|flooring)"
                },
                "required_docs": ["nzbc_e3", "nzbc_g12"],
                "enhanced_keywords": ["E3/AS1", "wet areas", "waterproofing", "tanking", "plumbing"]
            },
            
            QueryType.FIRE_SAFETY: {
                "patterns": [
                    r"fireplace.*clearance.*timber.*gib",
                    r"fire.*rating.*party.*wall",
                    r"solid.*fuel.*appliance.*installation",
                    r"hearth.*requirements.*construction"
                ],
                "field_extractors": {
                    "brand": r"(metrofires|jayline|nectre|woods|yunca|pyroclassic)",
                    "model": r"model\s*:?\s*([a-zA-Z0-9\-\s]+)",
                    "material": r"(timber|gib|concrete|brick|stone)\s*(?:wall|floor|hearth)",
                    "building_type": r"(residential|commercial|industrial)"
                },
                "required_docs": ["nzbc_g5", "nzs_4513"],
                "enhanced_keywords": ["G5 interior environment", "fireplace", "clearances", "hearth", "solid fuel"]
            },
            
            QueryType.INSULATION_THERMAL: {
                "patterns": [
                    r"insulation.*r.*value.*climate.*zone",
                    r"h1.*energy.*efficiency.*requirements",
                    r"thermal.*performance.*compliance",
                    r"pink.*batts.*installation"
                ],
                "field_extractors": {
                    "climate_zone": r"(?:climate\s*)?zone\s*([1-3])|([1-3])\s*zone",
                    "location": r"(auckland|wellington|christchurch|tauranga|hamilton|northland|canterbury|otago|southland)",
                    "r_value": r"r[-\s]*(\d+(?:\.\d+)?)",
                    "insulation_type": r"(bulk|reflective|continuous)\s*insulation"
                },
                "required_docs": ["nzbc_h1", "h1_as1"],
                "enhanced_keywords": ["H1 energy efficiency", "insulation", "R-values", "thermal", "climate zones"]
            },
            
            QueryType.STRUCTURAL_DESIGN: {
                "patterns": [
                    r"foundation.*bearing.*capacity",
                    r"seismic.*design.*requirements",
                    r"beam.*column.*design.*loads",
                    r"retaining.*wall.*height.*limits"
                ],
                "field_extractors": {
                    "load_type": r"(dead|live|wind|seismic|snow)\s*load",
                    "building_height": r"(\d+(?:\.\d+)?)\s*(?:m|storey|story|level)\s*(?:high|height)",
                    "soil_type": r"(clay|sand|rock|silt|gravel)\s*(?:soil|ground)",
                    "seismic_zone": r"seismic.*zone.*([a-d])|zone.*([a-d]).*seismic"
                },
                "required_docs": ["nzbc_b1", "nzs_1170", "nzs_3604"],
                "enhanced_keywords": ["B1 structure", "structural design", "loads", "seismic", "foundations"]
            }
        }
    
    async def process_query(self, query: str) -> ProcessedQuery:
        """Process query and extract structured information"""
        
        # Identify query type
        query_type = self._classify_query(query)
        
        # Extract fields based on query type
        extracted_fields = self._extract_fields(query, query_type)
        
        # Generate enhanced query with context
        enhanced_query = self._enhance_query(query, query_type, extracted_fields)
        
        # Generate search keywords
        search_keywords = self._generate_search_keywords(query, query_type)
        
        # Determine required documents
        required_documents = self._get_required_documents(query_type)
        
        processed = ProcessedQuery(
            original_query=query,
            query_type=query_type,
            extracted_fields=extracted_fields,
            enhanced_query=enhanced_query,
            search_keywords=search_keywords,
            required_documents=required_documents
        )
        
        logger.info(f"Processed query type: {query_type.value}, extracted {len(extracted_fields.__dict__)} fields")
        
        return processed
    
    def _classify_query(self, query: str) -> QueryType:
        """Classify query type based on patterns"""
        
        query_lower = query.lower()
        
        for query_type, config in self.query_patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return query_type
        
        return QueryType.GENERAL
    
    def _extract_fields(self, query: str, query_type: QueryType) -> ExtractedFields:
        """Extract structured fields from query"""
        
        fields = ExtractedFields()
        
        if query_type == QueryType.GENERAL:
            return fields
        
        config = self.query_patterns[query_type]
        extractors = config.get("field_extractors", {})
        
        extracted = {}
        
        for field_name, pattern in extractors.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    extracted[field_name] = match.group(1).strip()
                else:
                    # Multiple groups, take first non-None
                    for group in match.groups():
                        if group:
                            extracted[field_name] = group.strip()
                            break
        
        # Map extracted values to structured fields
        self._map_to_structured_fields(extracted, fields)
        
        return fields
    
    def _map_to_structured_fields(self, extracted: Dict[str, str], fields: ExtractedFields):
        """Map raw extracted values to structured fields"""
        
        # Handle dimensions
        dimensions = {}
        for key, value in extracted.items():
            if key in ['span', 'window_size', 'room_size', 'stud_height', 'spacing']:
                try:
                    if 'x' in value or 'by' in value:
                        # Handle dimensions like "3.0 x 2.4"
                        parts = re.split(r'\s*[x×by]\s*', value, re.IGNORECASE)
                        if len(parts) == 2:
                            dimensions['width'] = float(re.findall(r'\d+(?:\.\d+)?', parts[0])[0])
                            dimensions['height'] = float(re.findall(r'\d+(?:\.\d+)?', parts[1])[0])
                    else:
                        # Single dimension
                        num = re.findall(r'\d+(?:\.\d+)?', value)
                        if num:
                            dimensions[key] = float(num[0])
                except (ValueError, IndexError):
                    pass
        
        if dimensions:
            fields.dimensions = dimensions
        
        # Handle materials
        materials = []
        for key, value in extracted.items():
            if key in ['wood_type', 'cladding_type', 'material', 'subfloor_type']:
                materials.append(value.lower())
        
        if materials:
            fields.materials = materials
        
        # Handle other fields
        if 'climate_zone' in extracted:
            fields.location_zone = f"Zone {extracted['climate_zone']}"
        elif 'wind_zone' in extracted:
            fields.location_zone = f"Wind {extracted['wind_zone']}"
        
        if 'brand' in extracted and 'model' in extracted:
            fields.brand_model = f"{extracted['brand']} {extracted['model']}"
        elif 'brand' in extracted:
            fields.brand_model = extracted['brand']
        
        if 'building_type' in extracted:
            fields.building_type = extracted['building_type']
        
        # Extract building code references
        code_patterns = [
            r'([A-Z]\d+(?:\.\d+)*)',  # G5, H1, E2.3.1
            r'(NZS\s*\d+(?::\d+)?)',  # NZS 3604:2011
            r'(AS/NZS\s*\d+(?:\.\d+)?)'  # AS/NZS 1170.1
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, extracted.get('query', ''), re.IGNORECASE)
            if matches:
                fields.specific_code = matches[0]
                break
    
    def _enhance_query(self, query: str, query_type: QueryType, fields: ExtractedFields) -> str:
        """Enhance query with context and specific requirements"""
        
        if query_type == QueryType.GENERAL:
            return query
        
        enhancements = []
        
        # Add context based on query type
        context_map = {
            QueryType.CARPENTRY_FRAMING: "For timber framing and structural carpentry work in New Zealand",
            QueryType.CLADDING_WEATHERPROOFING: "For external cladding and weathertightness in New Zealand conditions",
            QueryType.WET_AREAS_PLUMBING: "For wet area waterproofing and plumbing compliance in New Zealand",
            QueryType.FIRE_SAFETY: "For solid fuel appliance and fire safety compliance in New Zealand",
            QueryType.INSULATION_THERMAL: "For thermal insulation and energy efficiency in New Zealand climate zones",
            QueryType.STRUCTURAL_DESIGN: "For structural design and building loads in New Zealand seismic conditions"
        }
        
        if query_type in context_map:
            enhancements.append(context_map[query_type])
        
        # Add field-specific context
        if fields.dimensions:
            dim_text = ", ".join([f"{k}: {v}" for k, v in fields.dimensions.items()])
            enhancements.append(f"with dimensions {dim_text}")
        
        if fields.materials:
            materials_text = ", ".join(fields.materials)
            enhancements.append(f"using materials: {materials_text}")
        
        if fields.location_zone:
            enhancements.append(f"in {fields.location_zone}")
        
        if fields.brand_model:
            enhancements.append(f"for {fields.brand_model}")
        
        if fields.building_type:
            enhancements.append(f"for {fields.building_type} construction")
        
        # Combine original query with enhancements
        if enhancements:
            enhanced = f"{query} ({', '.join(enhancements)})"
        else:
            enhanced = query
        
        return enhanced
    
    def _generate_search_keywords(self, query: str, query_type: QueryType) -> List[str]:
        """Generate enhanced search keywords"""
        
        keywords = []
        
        # Base keywords from query
        query_words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        keywords.extend(query_words[:5])  # Limit to top 5 words
        
        # Add query type specific keywords
        if query_type in self.query_patterns:
            enhanced_keywords = self.query_patterns[query_type].get("enhanced_keywords", [])
            keywords.extend(enhanced_keywords)
        
        # Remove duplicates and common words
        stop_words = {"the", "and", "for", "with", "what", "how", "can", "need", "have", "this", "that"}
        keywords = [kw for kw in keywords if kw.lower() not in stop_words]
        
        return list(set(keywords))  # Remove duplicates
    
    def _get_required_documents(self, query_type: QueryType) -> List[str]:
        """Get required document types for query"""
        
        if query_type in self.query_patterns:
            return self.query_patterns[query_type].get("required_docs", [])
        
        return []
    
    async def get_contextual_response(self, processed_query: ProcessedQuery) -> Dict[str, Any]:
        """Get contextual response based on processed query"""
        
        # Search for relevant documents with query type filtering
        doc_types = self._map_doc_types_to_search_filter(processed_query.required_documents)
        
        relevant_docs = await self.document_processor.search_documents(
            query=processed_query.enhanced_query,
            document_types=doc_types,
            limit=7
        )
        
        # Build contextual information
        context_info = {
            "query_analysis": {
                "type": processed_query.query_type.value,
                "extracted_fields": processed_query.extracted_fields.__dict__,
                "search_keywords": processed_query.search_keywords,
                "enhanced_query": processed_query.enhanced_query
            },
            "relevant_documents": len(relevant_docs),
            "document_sources": [doc["metadata"].get("title", "Unknown") for doc in relevant_docs],
            "confidence_indicators": []
        }
        
        # Add confidence indicators based on field extraction
        if processed_query.extracted_fields.dimensions:
            context_info["confidence_indicators"].append("Specific dimensions identified")
        
        if processed_query.extracted_fields.materials:
            context_info["confidence_indicators"].append("Materials specified")
        
        if processed_query.extracted_fields.brand_model:
            context_info["confidence_indicators"].append("Brand/model identified")
        
        if processed_query.extracted_fields.location_zone:
            context_info["confidence_indicators"].append("Location/zone context")
        
        # Build enhanced context for AI
        knowledge_sections = []
        if relevant_docs:
            knowledge_sections.append("=== RELEVANT NZ BUILDING CODE INFORMATION ===")
            
            for i, doc in enumerate(relevant_docs):
                if doc["similarity_score"] > 0.3:  # Only high relevance
                    knowledge_sections.append(f"\n--- Source {i+1}: {doc['metadata'].get('title')} ---")
                    knowledge_sections.append(doc["content"])
        
        context_info["knowledge_context"] = "\n".join(knowledge_sections)
        
        return context_info
    
    def _map_doc_types_to_search_filter(self, required_docs: List[str]) -> List[str]:
        """Map required document codes to search filter types"""
        
        doc_type_map = {
            "nzbc_b1": "nzbc",
            "nzbc_e2": "nzbc", 
            "nzbc_e3": "nzbc",
            "nzbc_g5": "nzbc",
            "nzbc_h1": "nzbc",
            "nzs_3604": "nzs",
            "nzs_1170": "nzs",
            "nzs_4513": "nzs",
            "h1_as1": "nzbc",
            "e2_as1": "nzbc"
        }
        
        doc_types = []
        for doc in required_docs:
            if doc in doc_type_map:
                doc_types.append(doc_type_map[doc])
        
        # Remove duplicates
        return list(set(doc_types)) if doc_types else None