"""
STRYDA.ai NZ Building Language Intelligence Engine
Combines curated terminology with targeted scraping for authentic Kiwi building communication
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

@dataclass
class NZTerminology:
    term: str
    definition: str
    context: str  # residential, commercial, both
    formality: str  # formal, informal, slang
    source: str
    confidence: float
    usage_examples: List[str]

class NZBuildingLanguageEngine:
    def __init__(self):
        self.terminology_db: Dict[str, NZTerminology] = {}
        self.regional_variations: Dict[str, List[str]] = {}
        self.context_patterns: Dict[str, List[str]] = {}
        self.last_update = None
        
        # Initialize with curated core terminology
        self._load_core_terminology()
        
        # Professional NZ building sources for targeted scraping
        self.professional_sources = [
            {
                "name": "MBIE Building Performance",
                "base_url": "https://www.building.govt.nz",
                "sections": ["/building-code-compliance/", "/managing-buildings/", "/building-officials/"],
                "priority": "high",
                "scrape_patterns": ["terminology", "definitions", "glossary"]
            },
            {
                "name": "Licensed Building Practitioners",
                "base_url": "https://www.lbp.govt.nz",
                "sections": ["/resources/", "/guidance/"],
                "priority": "high", 
                "scrape_patterns": ["common-terms", "building-terms"]
            },
            {
                "name": "PlaceMakers Trade Resources",
                "base_url": "https://www.placemakers.co.nz",
                "sections": ["/trade-resources/", "/technical-support/"],
                "priority": "medium",
                "scrape_patterns": ["product-terminology", "installation-guides"]
            },
            {
                "name": "ITM Building Supplies",
                "base_url": "https://www.itm.co.nz",
                "sections": ["/technical/", "/building-guide/"],
                "priority": "medium",
                "scrape_patterns": ["building-terminology", "trade-guides"]
            },
            {
                "name": "BRANZ Build Right",
                "base_url": "https://www.buildright.co.nz",
                "sections": ["/glossary/", "/building-basics/"],
                "priority": "high",
                "scrape_patterns": ["terminology", "building-terms", "definitions"]
            }
        ]
    
    def _load_core_terminology(self):
        """Load curated core NZ building terminology"""
        core_terms = {
            # Structural Terms
            "dwangs": NZTerminology(
                term="dwangs",
                definition="horizontal timber pieces between wall studs (also called noggins or blocking)",
                context="both",
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Need to put dwangs in for the towel rail",
                    "The dwangs are spaced at 450mm centres",
                    "Missing dwangs between these studs"
                ]
            ),
            "nogs": NZTerminology(
                term="nogs",
                definition="short form of noggins - horizontal blocking between studs",
                context="both", 
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Put some nogs in there",
                    "The nogs need to line up with the benchtop",
                    "Standard 90x45 nogs between studs"
                ]
            ),
            
            # Materials
            "gib": NZTerminology(
                term="gib",
                definition="plasterboard/drywall (from GIB brand name, now generic term)",
                context="both",
                formality="informal",
                source="curated_core", 
                confidence=1.0,
                usage_examples=[
                    "Standard 10mm gib on the walls",
                    "Need to gib up the ceiling",
                    "Wet area gib in the bathroom"
                ]
            ),
            "sarking": NZTerminology(
                term="sarking",
                definition="building wrap/house wrap installed under cladding for weatherproofing",
                context="residential",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Install sarking before cladding",
                    "The sarking is torn near the window",
                    "Building wrap/sarking requirements under E2"
                ]
            ),
            
            # Fasteners & Hardware
            "fixings": NZTerminology(
                term="fixings", 
                definition="fasteners including screws, nails, bolts, and anchors",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "What fixings do I need for this bracket?",
                    "Concrete fixings for the ledger board",
                    "Stainless steel fixings in wet areas"
                ]
            ),
            "tek screws": NZTerminology(
                term="tek screws",
                definition="self-drilling metal screws (from Tek brand, now generic)",
                context="both",
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Use tek screws for the steel frame",
                    "12-14 teks into the purlin",
                    "Stainless tek screws for coastal areas"
                ]
            ),
            
            # Building Performance & Compliance
            "weathertightness": NZTerminology(
                term="weathertightness",
                definition="building's ability to prevent water ingress (key NZ building term)",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "E2 weathertightness requirements",
                    "Weathertightness issues around windows", 
                    "Need a weathertightness report"
                ]
            ),
            "leaky building": NZTerminology(
                term="leaky building",
                definition="building with weathertightness failures (major NZ issue 1990s-2000s)",
                context="residential",
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Is this a leaky building?",
                    "Leaky building repairs needed",
                    "Checking for leaky building signs"
                ]
            ),
            
            # Climate Zones & Standards
            "H1 zone": NZTerminology(
                term="H1 zone",
                definition="NZ climate zone 1 (warmest) - includes Auckland, Tauranga, etc.",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "R1.9 insulation required in H1 zone",
                    "Auckland is in H1 climate zone",
                    "H1 zone thermal requirements"
                ]
            ),
            "H3 zone": NZTerminology(
                term="H3 zone", 
                definition="NZ climate zone 3 (coldest) - includes Central Otago, Canterbury high country",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "R2.9 ceiling insulation in H3 zone",
                    "Queenstown is H3 climate zone",
                    "Higher thermal performance needed in H3"
                ]
            ),
            
            # Brands & Products
            "metrofires": NZTerminology(
                term="metrofires",
                definition="popular NZ fireplace manufacturer (often used generically)",
                context="residential",
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Installing a metrofires unit",
                    "Metrofires clearance requirements",
                    "What size metrofires for this room?"
                ]
            ),
            "colorsteel": NZTerminology(
                term="colorsteel",
                definition="pre-painted steel roofing/cladding (from ColorSteel brand)",
                context="both",
                formality="informal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Colorsteel roofing installation",
                    "What profile colorsteel should I use?",
                    "Colorsteel vs longrun roofing"
                ]
            ),
            
            # Construction Methods
            "scribe": NZTerminology(
                term="scribe",
                definition="to cut/fit building materials to irregular surfaces",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Scribe the gib to the ceiling",
                    "Need to scribe around the pipe",
                    "Scribing weatherboards to fit"
                ]
            ),
            "flashings": NZTerminology(
                term="flashings",
                definition="weatherproofing strips around windows, doors, roof penetrations",
                context="both",
                formality="formal",
                source="curated_core",
                confidence=1.0,
                usage_examples=[
                    "Install head flashings above windows",
                    "The roof flashings are leaking",
                    "Proper flashing details are critical"
                ]
            )
        }
        
        for term_key, terminology in core_terms.items():
            self.terminology_db[term_key.lower()] = terminology
    
    async def enhance_query_understanding(self, user_query: str) -> Dict[str, any]:
        """Enhance understanding of user queries with NZ building context"""
        
        # Detect NZ building terms in query
        detected_terms = []
        normalized_query = user_query.lower()
        
        for term, term_data in self.terminology_db.items():
            if term in normalized_query:
                detected_terms.append({
                    "term": term,
                    "definition": term_data.definition,
                    "formality": term_data.formality,
                    "context": term_data.context
                })
        
        # Extract regional context
        regional_indicators = self._detect_regional_context(user_query)
        
        # Determine query formality level
        formality_level = self._assess_query_formality(user_query, detected_terms)
        
        return {
            "detected_nz_terms": detected_terms,
            "regional_context": regional_indicators,
            "formality_level": formality_level,
            "enhanced_understanding": self._generate_enhanced_understanding(
                user_query, detected_terms, regional_indicators
            )
        }
    
    def adapt_response_tone(self, response: str, user_context: Dict[str, any]) -> str:
        """Adapt AI response tone to match appropriate NZ building communication style"""
        
        formality_level = user_context.get("formality_level", "professional")
        detected_terms = user_context.get("detected_nz_terms", [])
        
        # Add appropriate NZ building terminology to response
        enhanced_response = response
        
        # Replace generic terms with NZ equivalents where appropriate
        replacements = {
            "plasterboard": "gib board",
            "drywall": "gib",
            "house wrap": "building wrap/sarking", 
            "noggins": "dwangs",
            "fasteners": "fixings",
            "self-drilling screws": "tek screws"
        }
        
        for generic, nz_term in replacements.items():
            if generic.lower() in enhanced_response.lower():
                enhanced_response = re.sub(
                    generic, nz_term, enhanced_response, flags=re.IGNORECASE
                )
        
        # Add regional context if detected
        regional_context = user_context.get("regional_context", {})
        if regional_context.get("climate_zone"):
            zone = regional_context["climate_zone"]
            enhanced_response += f"\n\nNote: Given you're in {zone}, specific thermal requirements may apply."
        
        return enhanced_response
    
    def _detect_regional_context(self, query: str) -> Dict[str, str]:
        """Detect regional context from query"""
        
        regional_patterns = {
            # Major cities and climate zones
            "auckland": {"climate_zone": "H1 zone", "region": "Auckland"},
            "wellington": {"climate_zone": "H2 zone", "region": "Wellington"},
            "christchurch": {"climate_zone": "H2 zone", "region": "Canterbury"},
            "queenstown": {"climate_zone": "H3 zone", "region": "Central Otago"},
            "dunedin": {"climate_zone": "H2 zone", "region": "Otago"},
            "hamilton": {"climate_zone": "H1 zone", "region": "Waikato"},
            "tauranga": {"climate_zone": "H1 zone", "region": "Bay of Plenty"},
            
            # Climate zone mentions
            "h1": {"climate_zone": "H1 zone"},
            "h2": {"climate_zone": "H2 zone"}, 
            "h3": {"climate_zone": "H3 zone"},
            
            # Regional building considerations
            "coastal": {"considerations": ["salt spray", "wind exposure", "moisture"]},
            "alpine": {"considerations": ["snow loads", "thermal performance", "freeze-thaw"]},
            "seismic": {"considerations": ["earthquake strengthening", "base isolation"]}
        }
        
        detected_context = {}
        query_lower = query.lower()
        
        for pattern, context in regional_patterns.items():
            if pattern in query_lower:
                detected_context.update(context)
        
        return detected_context
    
    def _assess_query_formality(self, query: str, detected_terms: List[Dict]) -> str:
        """Assess appropriate formality level for response"""
        
        # Formal indicators
        formal_indicators = [
            "building code", "compliance", "nzbc", "standards", "regulations",
            "consent", "inspection", "certification", "engineer", "specification"
        ]
        
        # Informal indicators  
        informal_indicators = [
            "gib", "dwangs", "nogs", "fixings", "teks", "quick question",
            "what's the deal", "how do i", "can i just"
        ]
        
        query_lower = query.lower()
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in query_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in query_lower)
        
        # Check detected terms formality
        term_formality = [term["formality"] for term in detected_terms]
        informal_terms = sum(1 for f in term_formality if f == "informal")
        
        if formal_count > informal_count + informal_terms:
            return "formal"
        elif informal_count + informal_terms > formal_count:
            return "casual_professional"
        else:
            return "professional"
    
    def _generate_enhanced_understanding(self, query: str, terms: List[Dict], 
                                       regional: Dict[str, str]) -> str:
        """Generate enhanced understanding summary"""
        
        understanding_parts = []
        
        if terms:
            nz_terms = [t["term"] for t in terms]
            understanding_parts.append(f"Query uses NZ building terminology: {', '.join(nz_terms)}")
        
        if regional.get("climate_zone"):
            understanding_parts.append(f"Regional context: {regional['climate_zone']}")
        
        if regional.get("region"):
            understanding_parts.append(f"Location context: {regional['region']}")
        
        return " | ".join(understanding_parts) if understanding_parts else "Standard building query"
    
    async def scrape_professional_sources(self, max_concurrent: int = 3) -> Dict[str, int]:
        """Scrape professional NZ building sources for terminology updates"""
        
        logger.info("Starting targeted scraping of professional NZ building sources...")
        
        results = {"sources_scraped": 0, "terms_found": 0, "errors": 0}
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "STRYDA.ai NZ Building Language Engine (Educational Use)"}
        ) as session:
            
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = []
            
            for source in self.professional_sources:
                if source["priority"] == "high":  # Start with high priority sources
                    for section in source["sections"]:
                        task = self._scrape_source_section(
                            session, semaphore, source, section
                        )
                        tasks.append(task)
            
            # Execute scraping tasks
            scrape_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in scrape_results:
                if isinstance(result, Exception):
                    results["errors"] += 1
                    logger.error(f"Scraping error: {result}")
                elif result:
                    results["sources_scraped"] += 1
                    results["terms_found"] += result.get("terms_found", 0)
        
        self.last_update = datetime.now()
        logger.info(f"Professional source scraping completed: {results}")
        
        return results
    
    async def _scrape_source_section(self, session: aiohttp.ClientSession, 
                                   semaphore: asyncio.Semaphore,
                                   source: Dict, section: str) -> Optional[Dict]:
        """Scrape a specific section of a professional source"""
        
        async with semaphore:
            try:
                url = urljoin(source["base_url"], section)
                
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_terminology_from_html(html, source["name"], url)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                return None
    
    def _extract_terminology_from_html(self, html: str, source_name: str, url: str) -> Dict:
        """Extract building terminology from HTML content"""
        
        soup = BeautifulSoup(html, 'html.parser')
        terms_found = 0
        
        # Look for definition lists, glossaries, and term explanations
        definition_patterns = [
            {'tag': 'dl', 'term_tag': 'dt', 'def_tag': 'dd'},  # Definition lists
            {'tag': 'div', 'class': 'glossary-item'},           # Glossary items
            {'tag': 'div', 'class': 'term-definition'},         # Term definitions
        ]
        
        for pattern in definition_patterns:
            elements = soup.find_all(pattern['tag'], class_=pattern.get('class'))
            
            for element in elements:
                term_text = None
                definition_text = None
                
                if 'term_tag' in pattern and 'def_tag' in pattern:
                    term_elem = element.find(pattern['term_tag'])
                    def_elem = element.find(pattern['def_tag'])
                    
                    if term_elem and def_elem:
                        term_text = term_elem.get_text().strip().lower()
                        definition_text = def_elem.get_text().strip()
                
                if term_text and definition_text and len(term_text) > 2:
                    # Check if it's a relevant building term
                    if self._is_relevant_building_term(term_text, definition_text):
                        self._add_scraped_terminology(
                            term_text, definition_text, source_name, url
                        )
                        terms_found += 1
        
        return {"terms_found": terms_found, "source": source_name}
    
    def _is_relevant_building_term(self, term: str, definition: str) -> bool:
        """Check if a scraped term is relevant to NZ building"""
        
        building_keywords = [
            "building", "construction", "structural", "thermal", "insulation",
            "weatherproof", "compliance", "code", "standard", "material",
            "installation", "foundation", "roof", "wall", "cladding", "timber",
            "concrete", "steel", "frame", "dwelling", "commercial", "seismic"
        ]
        
        text_to_check = (term + " " + definition).lower()
        
        # Must contain at least one building keyword
        has_building_context = any(keyword in text_to_check for keyword in building_keywords)
        
        # Filter out overly generic terms
        too_generic = len(term) < 3 or term in ["the", "and", "or", "with", "for"]
        
        return has_building_context and not too_generic
    
    def _add_scraped_terminology(self, term: str, definition: str, 
                               source: str, url: str) -> None:
        """Add scraped terminology to database"""
        
        # Don't override curated core terms
        if term in self.terminology_db and self.terminology_db[term].source == "curated_core":
            return
        
        terminology = NZTerminology(
            term=term,
            definition=definition,
            context="both",  # Default, could be enhanced with ML classification
            formality="formal",  # Professional sources tend to be formal
            source=f"scraped_{source}",
            confidence=0.7,  # Lower confidence for scraped content
            usage_examples=[]  # Could be enhanced by finding usage examples
        )
        
        self.terminology_db[term] = terminology
    
    def get_terminology_stats(self) -> Dict[str, any]:
        """Get statistics about the terminology database"""
        
        total_terms = len(self.terminology_db)
        by_source = {}
        by_formality = {}
        by_context = {}
        
        for term_data in self.terminology_db.values():
            # Count by source
            source = term_data.source
            by_source[source] = by_source.get(source, 0) + 1
            
            # Count by formality
            formality = term_data.formality
            by_formality[formality] = by_formality.get(formality, 0) + 1
            
            # Count by context
            context = term_data.context
            by_context[context] = by_context.get(context, 0) + 1
        
        return {
            "total_terms": total_terms,
            "by_source": by_source,
            "by_formality": by_formality,
            "by_context": by_context,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "core_nz_terms_loaded": sum(1 for t in self.terminology_db.values() 
                                      if t.source == "curated_core")
        }
    
    def search_terminology(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search the terminology database"""
        
        search_lower = search_term.lower()
        matches = []
        
        for term, term_data in self.terminology_db.items():
            if search_lower in term or search_lower in term_data.definition.lower():
                matches.append({
                    "term": term_data.term,
                    "definition": term_data.definition,
                    "context": term_data.context,
                    "formality": term_data.formality,
                    "source": term_data.source,
                    "confidence": term_data.confidence,
                    "usage_examples": term_data.usage_examples[:3]  # Limit examples
                })
        
        # Sort by confidence and relevance
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return matches[:limit]


# Global instance
nz_language_engine = NZBuildingLanguageEngine()