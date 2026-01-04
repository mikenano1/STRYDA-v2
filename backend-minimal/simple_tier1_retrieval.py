"""
STRYDA v1.3.3-hotfix4 - Simplified Tier-1 Retrieval
Direct approach that works without Decimal issues
"""

import psycopg2
import psycopg2.extras
import re
from typing import List, Dict, Optional

# Enhanced amendment detection patterns
AMEND_PAT = re.compile(r'\b(amend(?:ment)?\s*13|amdt\s*13|amend\s*13|b1\s*a\s*13)\b', re.I)
B1_LATEST_PAT = re.compile(r'\b(latest\s+b1|current\s+b1|new\s+b1|updated\s+b1)\b', re.I)
VERIFICATION_PAT = re.compile(r'\b(verification\s+method|verification\s+requirement)\b', re.I)

def detect_b1_amendment_bias(query: str) -> Dict[str, float]:
    """
    Detect if query should have B1 Amendment 13 ranking bias
    Returns bias weights for different sources
    """
    query_lower = query.lower()
    bias_weights = {}
    
    # Strong bias for explicit amendment queries
    if AMEND_PAT.search(query):
        bias_weights.update({
            'B1 Amendment 13': 1.5,  # Strong boost for amendment
            'B1/AS1': 0.85           # Slight de-bias for legacy
        })
        
    # Moderate bias for latest B1 queries  
    elif B1_LATEST_PAT.search(query):
        bias_weights.update({
            'B1 Amendment 13': 1.3,  # Moderate boost for latest
            'B1/AS1': 0.90           # Mild de-bias for legacy
        })
        
    # Mild bias for verification method queries
    elif VERIFICATION_PAT.search(query) and 'b1' in query_lower:
        bias_weights.update({
            'B1 Amendment 13': 1.2,  # Mild boost for verification
            'B1/AS1': 0.95           # Very mild de-bias
        })
        
    # General B1 queries with mild Amendment 13 preference
    elif any(term in query_lower for term in ['b1', 'structure', 'structural']):
        bias_weights.update({
            'B1 Amendment 13': 1.1,  # Slight boost for general B1
            'B1/AS1': 0.98           # Minimal de-bias
        })
    
    return bias_weights

# =============================================================================
# GLOBAL MERCHANT-TO-BRAND MAPPING (ALL CATEGORIES A-F)
# =============================================================================
# MANY-TO-MANY MATRIX: Reflects REAL availability across NZ merchants.
# Many brands (GIB, James Hardie, Thermakraft) are widely available.
# Only truly exclusive brands are restricted.

# =============================================================================
# BRAND -> RETAILERS (Many-to-Many "Store Locator" Matrix)
# =============================================================================
# This is the SOURCE OF TRUTH for availability.
# If a brand is in a retailer's list, it's available there.

BRAND_RETAILER_MAP = {
    # =========================================================================
    # CATEGORY F: FASTENERS
    # =========================================================================
    # Widely Available (Most Merchants)
    'Paslode': ['PlaceMakers', 'Carters', 'ITM', 'Mitre 10'],  # NOT Bunnings
    'Delfast': ['PlaceMakers', 'ITM', 'Bunnings Trade', 'Mitre 10'],
    'SPAX': ['PlaceMakers', 'ITM', 'Mitre 10', 'Carters'],
    
    # PlaceMakers/ITM Focus
    'Ecko': ['PlaceMakers', 'ITM'],
    'NZ Nails': ['ITM', 'PlaceMakers'],
    'Titan': ['Bunnings', 'ITM', 'Mitre 10'],
    
    # Bunnings/Mitre 10 Focus
    'Zenith': ['Bunnings', 'Mitre 10'],
    'Pryda': ['Bunnings', 'Mitre 10', 'Carters', 'ITM'],
    'Bremick': ['Bunnings', 'Mitre 10', 'Trade Suppliers'],
    'MacSim': ['Bunnings', 'Mitre 10', 'PlaceMakers'],
    
    # Carters/Trade Focus
    'Lumberlok': ['Carters', 'ITM', 'Trade Suppliers'],
    'MiTek': ['Carters', 'ITM', 'PlaceMakers'],
    'Simpson Strong-Tie': ['Carters', 'PlaceMakers', 'ITM', 'Trade Suppliers'],
    
    # =========================================================================
    # CATEGORY C: INTERIORS / LININGS
    # =========================================================================
    # Universal Availability
    'GIB': ['PlaceMakers', 'Carters', 'ITM', 'Mitre 10', 'Bunnings'],  # ALL MERCHANTS
    
    # Bunnings Exclusives
    'Elephant Board': ['Bunnings'],
    'Gyprock': ['Bunnings', 'Mitre 10'],
    
    # Widely Available Insulation
    'Pink Batts': ['PlaceMakers', 'ITM', 'Mitre 10', 'Bunnings'],
    'Earthwool': ['Bunnings', 'Mitre 10', 'PlaceMakers'],
    'Bradford Gold': ['Carters', 'Mitre 10', 'ITM'],
    'Knauf': ['Carters', 'Mitre 10', 'ITM', 'PlaceMakers'],
    'Expol': ['PlaceMakers', 'ITM', 'Bunnings', 'Mitre 10'],
    
    # Specialty
    'Autex': ['PlaceMakers', 'Carters', 'Specialty Acoustic'],
    
    # =========================================================================
    # CATEGORY B: ENCLOSURE / CLADDING / UNDERLAY
    # =========================================================================
    # Universal Availability
    'James Hardie': ['PlaceMakers', 'Carters', 'ITM', 'Mitre 10', 'Bunnings'],  # ALL MERCHANTS
    'Thermakraft': ['PlaceMakers', 'ITM', 'Bunnings', 'Carters', 'Mitre 10'],  # WIDELY AVAILABLE
    'Marley': ['PlaceMakers', 'Bunnings', 'Mitre 10', 'ITM'],
    
    # More Limited
    'Tekton': ['Carters', 'ITM'],
    'Mammoth': ['Bunnings', 'Mitre 10'],
    'Sika': ['PlaceMakers', 'Carters', 'ITM', 'Bunnings', 'Mitre 10'],  # ALL MERCHANTS
    
    # =========================================================================
    # CATEGORY A: STRUCTURE
    # =========================================================================
    'Firth': ['PlaceMakers', 'ITM', 'Mitre 10', 'Allied Concrete'],
    'Hume': ['PlaceMakers', 'Specialist'],
    'CHH Woodproducts': ['PlaceMakers', 'ITM', 'Carters'],
}

# =============================================================================
# RETAILER -> BRANDS (Derived from above - for quick lookup)
# =============================================================================
# Auto-generated reverse mapping

def _build_retailer_brand_map():
    """Build retailer->brands map from brand->retailers map"""
    retailer_map = {}
    for brand, retailers in BRAND_RETAILER_MAP.items():
        for retailer in retailers:
            retailer_key = retailer.lower().replace(' ', '')
            if retailer_key not in retailer_map:
                retailer_map[retailer_key] = []
            if brand not in retailer_map[retailer_key]:
                retailer_map[retailer_key].append(brand)
    return retailer_map

RETAILER_BRAND_MAP = _build_retailer_brand_map()

# Also add common variations
RETAILER_BRAND_MAP['mitre10'] = RETAILER_BRAND_MAP.get('mitre10', [])
RETAILER_BRAND_MAP['bunnings'] = RETAILER_BRAND_MAP.get('bunnings', [])
RETAILER_BRAND_MAP['placemakers'] = RETAILER_BRAND_MAP.get('placemakers', [])
RETAILER_BRAND_MAP['carters'] = RETAILER_BRAND_MAP.get('carters', [])
RETAILER_BRAND_MAP['itm'] = RETAILER_BRAND_MAP.get('itm', [])

# All known brands (for universal access)
ALL_KNOWN_BRANDS = list(BRAND_RETAILER_MAP.keys())

# =============================================================================
# ATTRIBUTE FILTER PROTOCOL - MATERIAL CLASSIFICATION
# =============================================================================
# Defines product categories by differentiating attributes (e.g., material type)
# Used for "Pre-Answer Triage" to narrow options before listing products

INSULATION_MATERIAL_GROUPS = {
    'glass_wool': {
        'display_name': 'Glass Wool',
        'brands': ['Pink Batts', 'Earthwool', 'Bradford', 'Knauf'],
        'description': 'Traditional glass fibre insulation - lightweight, cost-effective',
        'keywords': ['glass wool', 'glass fibre', 'pink batts', 'earthwool', 'bradford', 'knauf'],
    },
    'polyester': {
        'display_name': 'Polyester', 
        'brands': ['Mammoth', 'GreenStuf', 'Autex'],
        'description': 'Polyester fibre insulation - no itch, allergy-friendly, moisture resistant',
        'keywords': ['polyester', 'mammoth', 'greenstuf', 'autex', 'no itch', 'allergy'],
    },
    'polystyrene': {
        'display_name': 'Polystyrene/EPS',
        'brands': ['Expol'],
        'description': 'Rigid foam boards - high R-value per thickness, moisture resistant',
        'keywords': ['polystyrene', 'eps', 'expol', 'foam board', 'rigid'],
    },
}

# Reverse lookup: Brand -> Material Group
BRAND_TO_MATERIAL = {}
for material, info in INSULATION_MATERIAL_GROUPS.items():
    for brand in info['brands']:
        BRAND_TO_MATERIAL[brand.lower()] = material

def detect_material_preference(query: str) -> str:
    """Detect if user has specified a material preference in their query"""
    query_lower = query.lower()
    
    for material, info in INSULATION_MATERIAL_GROUPS.items():
        # Check for material keywords
        if any(kw in query_lower for kw in info['keywords']):
            return material
        # Check for brand names (implies material preference)
        for brand in info['brands']:
            if brand.lower() in query_lower:
                return material
    
    return None  # No preference detected

def get_available_material_groups(brands_in_db: list) -> list:
    """Get which material groups have brands available in the database"""
    available_groups = set()
    for brand in brands_in_db:
        brand_lower = brand.lower()
        if brand_lower in BRAND_TO_MATERIAL:
            available_groups.add(BRAND_TO_MATERIAL[brand_lower])
    return list(available_groups)

def build_material_triage_question(available_groups: list, query_context: str = '') -> dict:
    """Build the triage question for material selection"""
    if len(available_groups) < 2:
        return None  # No triage needed if only one material type
    
    options = []
    for group in available_groups:
        info = INSULATION_MATERIAL_GROUPS.get(group, {})
        brands = info.get('brands', [])
        # Filter to only brands we actually have
        options.append({
            'material': group,
            'display_name': info.get('display_name', group),
            'brands': brands[:3],  # Max 3 example brands
            'description': info.get('description', ''),
        })
    
    return {
        'type': 'material_triage',
        'category': 'insulation',
        'question': "I have compliant insulation options in multiple material types. Do you have a material preference?",
        'options': options,
        'allow_skip': True,
        'skip_text': "No preference - show me what's available at my merchant",
    }

def check_insulation_triage_needed(query: str, brands_in_results: list) -> dict:
    """
    Check if material triage is needed for an insulation query.
    Returns triage info dict or None if not needed.
    """
    query_lower = query.lower()
    
    # Skip triage if user already specified material or brand
    material_pref = detect_material_preference(query)
    if material_pref:
        return None  # User already has a preference
    
    # Skip if user mentioned a merchant (they'll get filtered results)
    merchant_keywords = ['placemakers', 'bunnings', 'carters', 'itm', 'mitre 10', 'mitre10']
    if any(m in query_lower for m in merchant_keywords):
        return None
    
    # Check what materials are represented in the results
    materials_found = set()
    for brand in brands_in_results:
        brand_lower = brand.lower() if brand else ''
        for material, info in INSULATION_MATERIAL_GROUPS.items():
            for b in info['brands']:
                if b.lower() in brand_lower or brand_lower in b.lower():
                    materials_found.add(material)
    
    # If multiple materials found, triage is needed
    if len(materials_found) >= 2:
        return {
            'triage_needed': True,
            'type': 'material_triage',
            'materials_available': list(materials_found),
            'triage_question': build_material_triage_question(list(materials_found)),
        }
    
    return None

# =============================================================================
# PRODUCT FUNCTION / TRADE DETECTION FOR RETRIEVAL
# =============================================================================
# Detects product-specific keywords to filter by trade

TRADE_DETECTION_KEYWORDS = {
    'foundations': [
        'foundation', 'slab', 'ribraft', 'rib raft', 'x-pod', 'xpod', 
        'footing', 'pile', 'tc3', 'canterbury', 'ground beam'
    ],
    'paving': [
        'paving', 'paver', 'pavers', 'holland', 'ecopave', 'driveway', 
        'pathway', 'permeable paving', 'cobble'
    ],
    'masonry': [
        'masonry', 'block wall', 'blockwork', 'concrete block', '20 series', 
        '25 series', 'bond beam', 'grout', 'mortar', 'blocklayer'
    ],
    'cladding': [
        'cladding', 'weatherboard', 'linea', 'axon', 'stria', 'facade',
        'underlay', 'building wrap', 'wall wrap', 'exterior wall'
    ],
    'roofing': [
        'roof', 'roofing', 'purlin', 'ridge', 'hip', 'valley', 
        'roof underlay', 'sarking', 'roofing screw', 'cladding screw'
    ],
    'interior_linings': [
        'plasterboard', 'gib', 'lining', 'drywall', 'ceiling', 'stopping',
        'cornice', 'fyreline', 'aqualine', 'braceline', 'noiseline'
    ],
    'insulation': [
        'insulation', 'batts', 'pink batts', 'earthwool', 'r-value',
        'thermal insulation', 'acoustic insulation', 'bradford'
    ],
    'retaining': [
        'retaining wall', 'keystone', 'garden wall', 'landscape wall'
    ],
    # =========================================================================
    # FASTENER SUB-CATEGORIES (New granular trades from multi-brand re-tag)
    # =========================================================================
    'framing': [
        'joist hanger', 'hanger', 'connector', 'framing bracket',
        'post support', 'rafter connector', 'purlin clip', 'stringer'
    ],
    'bracing': [
        'brace', 'bracing', 'hold down', 'hold-down', 'speed brace',
        'wall brace', 'strap', 'tie-down', 'tension tie', 'lateral'
    ],
    'anchoring': [
        'anchor', 'dynabolt', 'chemical anchor', 'wedge anchor', 'drop-in',
        'sleeve anchor', 'post base', 'post anchor', 'concrete anchor',
        'masonry anchor', 'chemset', 'epoxy anchor', 'bremfix'
    ],
    'nailplates': [
        'nail plate', 'nailplate', 'gang nail', 'truss plate', 'mending plate'
    ],
    'screws': [
        'timber screw', 'self drill', 'self-drill', 'bugle screw', 
        'countersunk screw', 'tek screw', 'decking screw'
    ],
    'nails': [
        'framing nail', 'gun nail', 'collated nail', 'coil nail', 
        'brad nail', 'finishing nail', 'clout nail'
    ],
    'bolts': [
        'coach bolt', 'hex bolt', 'carriage bolt', 'cup head', 
        'structural bolt', 'high tensile bolt'
    ],
    'decking': [
        'deck screw', 'decking fastener', 't-rex', 'outdoor screw',
        'exterior screw', 'stainless deck'
    ],
    'hardware': [
        'hinge', 'latch', 'hasp', 'lock', 'handle', 'hook', 'shelf bracket'
    ],
    # Generic fasteners fallback (lowest priority)
    'fasteners': [
        'fastener', 'fixing', 'nail', 'screw', 'bolt', 'anchor'
    ],
    # =========================================================================
    # INSULATION TRADES (Pink Batts Deep Dive)
    # =========================================================================
    'wall_insulation': [
        'wall insulation', 'wall batts', 'r2.2', 'r2.4', 'r2.6', 'r2.8',
        'stud insulation', 'wall r-value'
    ],
    'ceiling_insulation': [
        'ceiling insulation', 'ceiling batts', 'r3.2', 'r3.6', 'r4.0', 
        'r4.3', 'r5.0', 'r6.0', 'r7.0', 'attic insulation'
    ],
    'underfloor_insulation': [
        'underfloor insulation', 'floor insulation', 'snug floor',
        'suspended floor insulation', 'subfloor'
    ],
    'roof_insulation': [
        'roof insulation', 'skillion insulation', 'rafter insulation',
        'pitched roof insulation'
    ],
    'acoustic_insulation': [
        'acoustic insulation', 'soundproofing', 'sound insulation',
        'noise control', 'silencer', 'acoustic batts'
    ],
    'general_insulation': [
        'insulation', 'pink batts', 'batts', 'r-value', 'thermal',
        'glass wool'
    ],
    # AUTEX ACOUSTIC TRADES (Autex Deep Dive)
    'acoustic_ceiling': [
        'acoustic ceiling', 'ceiling tiles', 'ceiling panel', 'acoustic tile',
        '3d ceiling', 'accent ceiling', 'grid ceiling', 'cove ceiling',
        'horizon ceiling', 'lattice ceiling'
    ],
    'acoustic_wall': [
        'acoustic wall', 'wall panel', 'acoustic panel', 'sound panel',
        'quietspace', 'composition', 'cube panel', 'embrace wall',
        'groove panel', 'lanes', 'mirage panel', 'reform', 'vertiface',
        'pinboard', 'noticeboard'
    ],
    'acoustic_screens': [
        'acoustic screen', 'workstation screen', 'desk screen', 'partition',
        'cascade screen', 'frontier screen', 'vicinity screen',
        'office divider', 'desk divider'
    ],
    'acoustic_timber': [
        'acoustic timber', 'timber acoustic', 'wood acoustic', 'timber panel',
        'slat panel', 'timber slat'
    ],
    'acoustic_general': [
        'autex colour', 'autex color', 'nrc rating', 'sound absorption',
        'acoustic performance', 'care and maintenance'
    ],
}

def detect_trade_from_query(query: str) -> Optional[str]:
    """
    Detect the specific trade/product function from a query.
    Returns the trade name if detected, None otherwise.
    """
    query_lower = query.lower()
    
    # Score each trade by keyword matches
    trade_scores = {}
    for trade, keywords in TRADE_DETECTION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            trade_scores[trade] = score
    
    if trade_scores:
        # Return the trade with highest score
        best_trade = max(trade_scores, key=trade_scores.get)
        return best_trade
    
    return None

CATEGORY_KEYWORDS = {
    'fasteners': [
        'nail', 'screw', 'fastener', 'anchor', 'bolt', 'bracket', 'hanger',
        'connector', 'strap', 'tie-down', 'bracing', 'collated', 'framing nail',
        'joist hanger', 'post anchor', 'masonry anchor', 'dynabolt', 'chemset'
    ],
    'interiors': [
        'plasterboard', 'gib', 'lining', 'drywall', 'ceiling', 'cornice',
        'stopping', 'fibrous plaster', 'acoustic', 'fire rating', 'wall lining',
        'interior wall', 'internal wall', 'gypsum'
    ],
    'enclosure': [
        'cladding', 'weatherboard', 'underlay', 'wrap', 'membrane', 'flashing',
        'roofing', 'soffit', 'fascia', 'james hardie', 'hardie', 'linea',
        'axon', 'stria', 'titan board', 'exterior', 'weather tight'
    ],
    'insulation': [
        'insulation', 'batts', 'pink batts', 'earthwool', 'polyester', 'r-value',
        'thermal', 'acoustic insulation', 'underfloor', 'ceiling insulation',
        'wall insulation', 'bradford', 'mammoth', 'expol'
    ],
    'structure': [
        'concrete', 'steel', 'timber', 'foundation', 'pile', 'bearer', 'joist',
        'rafter', 'truss', 'lintel', 'beam', 'post', 'stud', 'framing',
        'structural', 'load bearing', 'firth', 'hume'
    ],
}

def detect_product_category(query: str) -> Optional[str]:
    """Detect which product category the query relates to."""
    query_lower = query.lower()
    
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        return max(category_scores, key=category_scores.get)
    return None

def detect_retailer_context(query: str) -> Optional[str]:
    """
    Detect if user has specified a merchant/retailer context.
    Returns the retailer name if found, None otherwise.
    """
    query_lower = query.lower()
    
    retailer_keywords = {
        'placemakers': 'PlaceMakers',
        'place makers': 'PlaceMakers',
        'bunnings': 'Bunnings',
        'mitre 10': 'Mitre 10',
        'mitre10': 'Mitre 10',
        'carters': 'Carters',
        'itm': 'ITM',
    }
    
    for keyword, retailer in retailer_keywords.items():
        if keyword in query_lower:
            return retailer
    
    return None

def get_brands_for_retailer(retailer: str) -> List[str]:
    """Get the list of brands available at a specific retailer."""
    retailer_key = retailer.lower().replace(' ', '')
    
    for key, brands in RETAILER_BRAND_MAP.items():
        if key.replace(' ', '') == retailer_key:
            return brands
    
    return ALL_FASTENER_BRANDS  # Fallback to all brands

def detect_retailer_bias(query: str) -> Dict[str, float]:
    """
    Detect if user mentions a retailer and bias towards brands they stock.
    e.g., "I'm at Bunnings looking for anchors" → boost Zenith, Pryda, Bremick
    """
    query_lower = query.lower()
    bias_weights = {}
    
    for retailer, brands in RETAILER_BRAND_MAP.items():
        if retailer in query_lower:
            # Boost all brands that retailer carries
            for brand in brands:
                bias_weights[brand] = 1.3  # 30% boost for retailer-stocked brands
            break
    
    return bias_weights

def apply_ranking_bias(results: List[Dict], bias_weights: Dict[str, float]) -> List[Dict]:
    """
    Apply ranking bias to search results based on source
    """
    biased_results = []
    
    for result in results:
        source = result.get('source', '')
        original_score = result.get('score', 0.0)
        
        # Apply bias if source matches
        bias_factor = 1.0
        for source_pattern, weight in bias_weights.items():
            if source_pattern in source:
                bias_factor = weight
                break
        
        # Create biased result
        biased_result = dict(result)
        biased_result['score'] = min(1.0, original_score * bias_factor)
        biased_result['original_score'] = original_score
        biased_result['bias_factor'] = bias_factor
        biased_result['bias_applied'] = bias_factor != 1.0
        
        biased_results.append(biased_result)
    
    return biased_results

def canonical_source_map(query: str) -> List[str]:
    """
    Map query terms to canonical source names in database
    Returns prioritized list of sources to search
    """
    query_lower = query.lower()
    sources = []
    
    # NZS 3604 - Timber framing standard
    if any(term in query_lower for term in [
        'nzs 3604', 'nzs3604', '3604',
        'stud', 'spacing', 'timber', 'framing', 'lintel',
        'bearer', 'joist', 'nog', 'dwang', 'plate',
        'table 7.1', 'table 5.', 'span', 'member'
    ]):
        sources.append('NZS 3604:2011')
    
    # E2/AS1 - External moisture
    if any(term in query_lower for term in [
        'e2', 'e2/as1', 'as1', 'external moisture',
        'flashing', 'apron', 'weathertight', 'weather',
        'cladding', 'cavity', 'membrane', 'underlay',
        'roof pitch', 'deck', 'balcony', 'risk score'
    ]):
        sources.append('E2/AS1')
    
    # E1/AS1 - Internal drainage (Task 3.4)
    if any(term in query_lower for term in [
        'e1', 'e1/as1', 'internal gutter', 'gutter fall',
        'box gutter', 'valley gutter', 'internal drainage'
    ]):
        sources.append('E1/AS1')
    
    # B1 Amendment 13 - Latest structural standard (prioritize over B1/AS1)
    if any(term in query_lower for term in [
        'amendment 13', 'amdt 13', 'b1 amendment', 'b1 amend',
        'verification method', 'vm1', 'vm4', 'vm8',
        'latest b1', 'current b1', 'new b1', 'updated b1'
    ]):
        sources.append('B1 Amendment 13')
    
    # B1/AS1 - Legacy structural standard (only if Amendment 13 not mentioned)
    elif any(term in query_lower for term in [
        'b1', 'b1/as1', 'structure', 'structural',
        'brace', 'bracing', 'foundation', 'footing',
        'demand', 'capacity', 'engineering'
    ]):
        # Prioritize Amendment 13 over legacy B1/AS1
        if 'B1 Amendment 13' not in sources:
            sources.append('B1 Amendment 13')  # Default to latest
        sources.append('B1/AS1')  # Also include legacy for completeness
    
    # NZ Building Code - General building code sections
    if any(term in query_lower for term in [
        'h1', 'energy', 'insulation', 'r-value', 'thermal',
        'f4', 'f4/as1', 'barrier', 'balustrade', 'handrail', 'guardrail',
        'deck fall', '1m fall', '1 metre fall', 'fall protection',
        'escape', 'means of escape', 'safety barriers', 'minimum barrier height',
        'g5', 'g5.3.2', 'hearth', 'solid fuel', 'fireplace',
        'c1', 'c2', 'c3', 'c4', 'fire', 'fire rating', 'fire stopping',
        'g12', 'g13', 'water', 'sanitary', 'plumbing', 'hot water',
        'building code', 'nzbc'
    ]):
        sources.append('NZ Building Code')
    
    # NZS 4229 - Concrete masonry
    if any(term in query_lower for term in [
        'nzs 4229', 'nzs4229', '4229',
        'concrete', 'masonry', 'block', 'blockwork',
        'reinforcement', 'steel', 'mesh', 'rebar'
    ]):
        sources.append('NZS 4229:2013')
    
    # Firth - Concrete & Masonry Products (Brand Deep Dive)
    if any(term in query_lower for term in [
        'firth', 'ribraft', 'rib raft', 'x-pod', 'xpod',
        'concrete block', '20 series', '25 series',
        'masonry block', 'hollow block', 'bond beam',
        'ecopave', 'paving', 'paver', 'holland paver',
        'keystone', 'retaining wall', 'masonry veneer',
        'foundation slab', 'tc3', 'canterbury foundation',
        'dricon', 'mortar', 'grout'
    ]):
        sources.append('Firth Deep Dive (Universal)')
    
    # NZ Metal Roofing
    if any(term in query_lower for term in [
        'metal roof', 'corrugated', 'profiled', 'longrun',
        'fixing screw', 'roofing screw', 'purlin'
    ]):
        sources.append('NZ Metal Roofing')
    
    # GIB / Winstone Wallboards - Interior linings (Big Brain Integration)
    if any(term in query_lower for term in [
        'gib', 'plasterboard', 'gib board', 'gypsum',
        'braceline', 'ezybrace', 'fyreline', 'aqualine',
        'gib stopping', 'gib fixing', 'gib fastener',
        'interior lining', 'wall lining', 'ceiling lining',
        'fire rating', 'frl', 'fire resistance', 'frr'
    ]):
        sources.append('GIB Site Guide 2024')
    
    # Pink Batts - Insulation (Brand Deep Dive)
    if any(term in query_lower for term in [
        'pink batts', 'pink batt', 'insulation', 'batts',
        'r-value', 'r2.6', 'r2.8', 'r3.2', 'r4.0', 'r5.0', 'r6.0', 'r7.0',
        'ceiling insulation', 'wall insulation', 'underfloor insulation',
        'roof insulation', 'skillion', 'acoustic insulation',
        'glass wool', 'thermal insulation', 'snug floor', 'superbatts',
        'silencer', 'comfortech', 'tasman insulation'
    ]):
        sources.append('Pink Batts Deep Dive')
    
    # Earthwool - Glass Wool Insulation (Brand Deep Dive)
    # NOTE: Also triggers on generic insulation keywords for multi-brand comparison
    if any(term in query_lower for term in [
        'earthwool', 'earth wool', 'knauf', 'floorshield',
        # Generic insulation keywords (for multi-brand search)
        'insulation', 'r-value', 'wall insulation', 'ceiling insulation',
        'underfloor insulation', 'roof insulation', 'glass wool'
    ]):
        sources.append('Earthwool Deep Dive')
    
    # Bradford - Glass Wool Insulation & Ventilation (Brand Deep Dive)
    # NOTE: Also triggers on generic insulation keywords for multi-brand comparison
    if any(term in query_lower for term in [
        'bradford', 'gold batts', 'polymax', 'optimo', 'anticon', 'thermoseal',
        'soundscreen', 'fireseal', 'ashgrid', 'quietel',
        # Generic insulation keywords
        'insulation', 'r-value', 'wall insulation', 'ceiling insulation',
        'underfloor insulation', 'roof insulation', 'glass wool',
        # Ventilation keywords
        'ventilation', 'whirlybird', 'windmaster', 'hurricane', 'ecopower',
        'solarxvent', 'roof vent', 'subfloor vent'
    ]):
        sources.append('Bradford Deep Dive')
    
    # Mammoth - Polyester Insulation (Brand Deep Dive)
    # NOTE: Also triggers on generic insulation keywords for multi-brand comparison
    if any(term in query_lower for term in [
        'mammoth', 'polyester insulation', 'acoustic baffle', 'bafflestack',
        'acoustic blanket', 'acoustic panel', 'deco flex', 'martini',
        'duct liner', 'carpark insulation', 'inzone',
        # Generic insulation keywords (for multi-brand search)
        'insulation', 'r-value', 'wall insulation', 'ceiling insulation',
        'underfloor insulation', 'roof insulation', 'acoustic insulation'
    ]):
        sources.append('Mammoth Deep Dive')
    
    # GreenStuf - Polyester Insulation (Brand Deep Dive)
    # NOTE: Also triggers on generic insulation keywords for multi-brand comparison
    if any(term in query_lower for term in [
        'greenstuf', 'green stuf', 'duct wrap', 'duct liner',
        'masonry wall blanket', 'garage door insulation',
        # Generic insulation keywords (for multi-brand search)
        'insulation', 'r-value', 'wall insulation', 'ceiling insulation',
        'underfloor insulation', 'roof insulation', 'acoustic insulation'
    ]):
        sources.append('GreenStuf Deep Dive')
    
    # Autex - Acoustic Products (Brand Deep Dive)
    # NOTE: Also triggers on generic acoustic keywords for multi-brand comparison
    if any(term in query_lower for term in [
        'autex', 'quietspace', 'composition', 'vertiface', 'frontier',
        'cascade', 'vicinity', 'acoustic panel', 'acoustic ceiling',
        'acoustic wall', 'acoustic screen', 'acoustic timber',
        'workstation screen', 'desk screen', 'ceiling tile', 'wall tile',
        '3d tile', 'acoustic tile', 'pinboard', 'noticeboard',
        'embrace', 'cube panel', 'groove', 'lattice', 'horizon', 'cove',
        'lanes', 'mirage', 'reform', 'accent ceiling', 'grid ceiling',
        # Generic acoustic keywords (for multi-brand search)
        'soundproofing', 'sound absorption', 'nrc', 'acoustic'
    ]):
        sources.append('Autex Deep Dive')
    
    # James Hardie - Cladding/Exterior (Big Brain Integration)
    if any(term in query_lower for term in [
        'james hardie', 'hardie', 'linea', 'weatherboard',
        'axon', 'stria', 'hardieflex', 'fibre cement',
        'cladding', 'head flashing', 'apron flashing',
        'cavity batten', 'direct fix', 'wall cladding',
        'rab board', 'homerab', 'rigid air barrier',
        'villaboard', 'secura', 'oblique'
    ]):
        sources.append('James Hardie Full Suite')
    
    # Fasteners - Category F (Big Brain Integration - Full Suite + Final Sweep)
    # Detect specific brands and add their Final Sweep sources
    fastener_brands = {
        'pryda': 'Final Sweep - Pryda',
        'zenith': 'Final Sweep - Zenith',
        'macsim': 'Final Sweep - MacSim',
        'bremick': 'Final Sweep - Bremick',
        'spax': 'Final Sweep - SPAX',
        'delfast': 'Final Sweep - Delfast',
        'ecko': 'Ecko Master Library (PlaceMakers)',
        't-rex': 'Ecko Master Library (PlaceMakers)',
        'titan': 'Final Sweep - Titan',
        'simpson': 'Final Sweep - Simpson_Strong_Tie',
        'strong-tie': 'Final Sweep - Simpson_Strong_Tie',
        'paslode': 'Final Sweep - Paslode',
        'buildex': 'Final Sweep - Buildex',
        'ramset': 'Final Sweep - Ramset',
        'mitek': 'Final Sweep - MiTek',
        'mainland': 'Final Sweep - Mainland_Fasteners',
        'nz nails': 'Final Sweep - NZ_Nails',
    }
    
    # Check for specific brand mentions first
    brand_matched = False
    for brand_key, source_name in fastener_brands.items():
        if brand_key in query_lower:
            sources.append(source_name)
            brand_matched = True
    
    # Also add generic fastener detection
    if any(term in query_lower for term in [
        'nail', 'screw', 'fastener', 'anchor', 'bolt',
        'framing nail', 'purlin nail', 'collated', 'coil nail',
        'chemset', 'dynabolt', 'ankascrew', 'connector',
        'joist hanger', 'post anchor', 'load capacity',
        'bracing', 'bracket', 'tie-down', 'nailplate',
        'decking screw', 'timber screw', 'stainless fastener',
        'masonry anchor', 'drop-in anchor', 'socket screw',
        'packer', 'window packer', 'lumberlok', 'bowmac'
    ]) or brand_matched:
        sources.append('Fasteners Full Suite')
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sources = []
    for src in sources:
        if src not in seen:
            seen.add(src)
            unique_sources.append(src)
    
    return unique_sources

def score_with_metadata(base_similarity: float, doc_type: str, priority: int, intent: str) -> float:
    """
    Metadata-aware scoring that combines similarity + doc_type + priority
    
    Scoring formula:
    - final_score = base_similarity + (priority/1000) + intent_bonus
    
    Where:
    - base_similarity: 0.0-1.0 (from cosine similarity, 1.0 = best match)
    - priority: 0-100 → contributes 0.0-0.1 to final score
    - intent_bonus: -0.10 to +0.10 based on doc_type alignment with intent
    
    Intent-based bonuses:
    - compliance_strict/implicit_compliance → favor current standards
    - general_help/product_info → favor guides and manufacturer docs
    """
    score = base_similarity
    
    # Priority influence (0-100 → 0.00-0.10)
    if priority:
        score += priority / 1000.0
    
    # Intent-based bonuses/penalties
    if intent in ("compliance_strict", "implicit_compliance"):
        # Compliance queries: favor current official standards
        if doc_type == "acceptable_solution_current":
            score += 0.10  # Strong bonus for current AS
        elif doc_type == "verification_method_current":
            score += 0.08  # Strong bonus for current VM
        elif doc_type == "industry_code_of_practice":
            score += 0.05  # Medium bonus for industry codes
        elif doc_type == "acceptable_solution_legacy":
            score += 0.03  # Small bonus for legacy (still official)
        elif doc_type and doc_type.startswith("manufacturer_manual"):
            score -= 0.02  # Slight penalty for manufacturer docs
        elif doc_type == "handbook_guide":
            score -= 0.01  # Very slight penalty for guides
            
    elif intent in ("general_help", "product_info"):
        # Practical queries: strongly favor guides and manufacturer docs
        if doc_type and doc_type.startswith("manufacturer_manual"):
            score += 0.08  # INCREASED: Strong bonus for manufacturer docs
        elif doc_type == "handbook_guide":
            score += 0.06  # INCREASED: Strong bonus for guides
        elif doc_type in ("acceptable_solution_current", "verification_method_current"):
            score += 0.02  # Keep standards as useful context
    
    return score



def simple_tier1_retrieval(query: str, top_k: int = 20, intent: str = "compliance_strict") -> List[Dict]:
    """
    Optimized Tier-1 retrieval using pgvector similarity search with caching
    PERFORMANCE: Reduced top_k to 4 for faster context assembly and lower token usage
    IMPROVEMENTS: Canonical source mapping + fallback logic + metadata-aware ranking
    
    Args:
        query: User question
        top_k: Number of results to return
        intent: Intent from classifier (compliance_strict, general_help, product_info, etc.)
    """
    DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
    
    try:
        import time
        from openai import OpenAI
        import os
        from cache_manager import embedding_cache, cache_key
        
        start_time = time.time()
        
        # Check embedding cache
        embed_cache_key = cache_key(query)
        cached_embedding = embedding_cache.get(embed_cache_key)
        
        if cached_embedding:
            query_embedding = cached_embedding
            print(f"🎯 Embedding cache HIT for query")
            embed_time = 0
        else:
            # Generate query embedding using OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️ No OpenAI API key, falling back to keyword search")
                return _fallback_keyword_search(query, top_k, DATABASE_URL)
            
            embed_start = time.time()
            client = OpenAI(api_key=api_key)
            embedding_response = client.embeddings.create(
                model="text-embedding-3-small",  # CHANGED: Match regenerated embeddings model
                input=query
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Cache for future use
            embedding_cache.set(embed_cache_key, query_embedding)
            
            embed_time = (time.time() - embed_start) * 1000
            print(f"⚡ Query embedding generated in {embed_time:.0f}ms (cached for 1h)")
        
        # Connect to database using connection pool
        from db_pool import get_db_connection, return_db_connection
        
        conn = get_db_connection()
        
        # Use canonical source mapping for better source detection
        target_sources = canonical_source_map(query)
        
        # NEW: Detect specific trade/product function from query
        detected_trade = detect_trade_from_query(query)
        
        # Debug logging
        print(f"🔍 Source detection for query: '{query[:60]}...'")
        print(f"   Detected sources: {target_sources if target_sources else 'None (will search all docs)'}")
        if detected_trade:
            print(f"   🏷️ Detected trade/product function: {detected_trade}")
        
        results = []
        search_time = 0
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            search_start = time.time()
            
            # STRATEGY: Try filtered search first, fallback to global if no results
            if target_sources and len(target_sources) > 0:
                # Check if we have any Final Sweep sources or fastener-related sources
                has_final_sweep = any('Final Sweep' in s for s in target_sources)
                has_fasteners_suite = 'Fasteners Full Suite' in target_sources
                has_firth = any('Firth' in s for s in target_sources)
                has_brand_deep_dive = any('Deep Dive' in s for s in target_sources)
                
                # NEW: Brand Deep Dive with trade filter (e.g., Firth paving vs Firth foundations)
                if has_brand_deep_dive and detected_trade:
                    brand_sources = [s for s in target_sources if 'Deep Dive' in s]
                    other_sources = [s for s in target_sources if 'Deep Dive' not in s]
                    
                    # IMPORTANT: Detect which brand is mentioned in the query
                    # This ensures we search the correct brand when multiple Deep Dives are detected
                    brand_name = None
                    query_lower = query.lower()
                    
                    # Check for specific brand mentions in query
                    brand_priority = [
                        ('autex', 'Autex'),
                        ('quietspace', 'Autex'),
                        ('vertiface', 'Autex'),
                        ('composition', 'Autex'),
                        ('mammoth', 'Mammoth'),
                        ('greenstuf', 'GreenStuf'),
                        ('green stuf', 'GreenStuf'),
                        ('pink batts', 'Pink Batts'),
                        ('pink batt', 'Pink Batts'),
                        ('earthwool', 'Earthwool'),
                        ('earth wool', 'Earthwool'),
                        ('knauf', 'Earthwool'),
                        ('bradford', 'Bradford'),
                        ('gold batts', 'Bradford'),
                        ('windmaster', 'Bradford'),
                        ('hurricane', 'Bradford'),
                        ('firth', 'Firth'),
                    ]
                    
                    for keyword, brand in brand_priority:
                        if keyword in query_lower:
                            brand_name = brand
                            break
                    
                    # NEW: If NO brand is mentioned in query, search ALL insulation brands
                    # This provides a comparison across brands for generic queries
                    if not brand_name and len(brand_sources) > 1:
                        # Multiple Deep Dive sources but no specific brand mentioned
                        # Search ALL brands with the trade filter
                        print(f"   🔎 Multi-brand search (no specific brand in query): trade={detected_trade}")
                        
                        # Extract all brand names from Deep Dive sources
                        all_brands = []
                        for src in brand_sources:
                            b = src.replace(' Deep Dive', '').replace(' (Universal)', '')
                            all_brands.append(b)
                        
                        use_like_trade = 'insulation' in detected_trade or detected_trade == 'general_insulation'
                        
                        # Build SQL to search ALL brands
                        brand_conditions = ' OR '.join(['brand_name ILIKE %s'] * len(all_brands))
                        trade_condition = "trade LIKE %s" if use_like_trade else "trade = %s"
                        trade_value = f"%{detected_trade.replace('general_', '')}%" if use_like_trade else detected_trade
                        
                        # BRAND FAIRNESS: Get top results from EACH brand separately
                        # then merge them to ensure representation from all brands
                        all_results = []
                        min_per_brand = max(3, top_k // len(all_brands))  # At least 3 from each brand
                        
                        for brand in all_brands:
                            brand_sql = f"""
                                SELECT id, source, page, content, section, clause, snippet,
                                       doc_type, trade, status, priority, phase, brand_name, product_family,
                                       (embedding <=> %s::vector) as similarity
                                FROM documents 
                                WHERE embedding IS NOT NULL
                                  AND brand_name ILIKE %s
                                  AND {trade_condition}
                                ORDER BY similarity ASC
                                LIMIT %s;
                            """
                            brand_params = [query_embedding, f"%{brand}%", trade_value, min_per_brand]
                            cur.execute(brand_sql, brand_params)
                            brand_results = cur.fetchall()
                            all_results.extend(brand_results)
                            print(f"      • {brand}: {len(brand_results)} results")
                        
                        # Sort combined results by similarity and take top_k * 2
                        results = sorted(all_results, key=lambda x: x[-1])[:top_k * 2]
                        
                        # If we got results from multiple brands, great!
                        if results:
                            search_time = (time.time() - search_start) * 1000
                            print(f"⚡ Vector search completed in {search_time:.0f}ms, found {len(results)} chunks from {len(all_brands)} brands")
                        else:
                            print(f"   ⚠️ No results with multi-brand search, falling back to broader search")
                            brand_name = None
                            results = None
                    
                    # Single brand search (when brand IS mentioned in query)
                    elif brand_name:
                        # For insulation, use LIKE to match wall_insulation, ceiling_insulation, etc.
                        trade_filter = detected_trade
                        use_like_trade = 'insulation' in detected_trade or detected_trade == 'general_insulation'
                        
                        if use_like_trade:
                            sql = """
                                SELECT id, source, page, content, section, clause, snippet,
                                       doc_type, trade, status, priority, phase, brand_name, product_family,
                                       (embedding <=> %s::vector) as similarity
                                FROM documents 
                                WHERE embedding IS NOT NULL
                                  AND (
                                    (brand_name ILIKE %s AND trade LIKE %s)
                            """
                            params = [query_embedding, f"%{brand_name}%", f"%{detected_trade.replace('general_', '')}%"]
                        else:
                            sql = """
                                SELECT id, source, page, content, section, clause, snippet,
                                       doc_type, trade, status, priority, phase, brand_name, product_family,
                                       (embedding <=> %s::vector) as similarity
                                FROM documents 
                                WHERE embedding IS NOT NULL
                                  AND (
                                    (brand_name ILIKE %s AND trade = %s)
                            """
                            params = [query_embedding, f"%{brand_name}%", detected_trade]
                        
                        if other_sources:
                            other_placeholders = ', '.join(['%s'] * len(other_sources))
                            sql += f" OR source IN ({other_placeholders})"
                            params.extend(other_sources)
                        
                        sql += """
                              )
                            ORDER BY similarity ASC
                            LIMIT %s;
                        """
                        params.append(top_k * 2)
                        
                        print(f"   🔎 Brand Deep Dive + Trade filter: brand={brand_name}, trade={detected_trade}")
                        cur.execute(sql, params)
                        results = cur.fetchall()
                    
                    # Fallback for single Deep Dive source with no brand in query
                    else:
                        source_name = brand_sources[0] if brand_sources else None
                        brand_name = source_name.replace(' Deep Dive', '').replace(' (Universal)', '') if source_name else None
                        
                        use_like_trade = 'insulation' in detected_trade or detected_trade == 'general_insulation'
                        
                        if use_like_trade:
                            sql = """
                                SELECT id, source, page, content, section, clause, snippet,
                                       doc_type, trade, status, priority, phase, brand_name, product_family,
                                       (embedding <=> %s::vector) as similarity
                                FROM documents 
                                WHERE embedding IS NOT NULL
                                  AND (
                                    (brand_name ILIKE %s AND trade LIKE %s)
                            """
                            params = [query_embedding, f"%{brand_name}%" if brand_name else "%", f"%{detected_trade.replace('general_', '')}%"]
                        else:
                            sql = """
                                SELECT id, source, page, content, section, clause, snippet,
                                       doc_type, trade, status, priority, phase, brand_name, product_family,
                                       (embedding <=> %s::vector) as similarity
                                FROM documents 
                                WHERE embedding IS NOT NULL
                                  AND (
                                    (brand_name ILIKE %s AND trade = %s)
                            """
                            params = [query_embedding, f"%{brand_name}%" if brand_name else "%", detected_trade]
                        
                        if other_sources:
                            other_placeholders = ', '.join(['%s'] * len(other_sources))
                            sql += f" OR source IN ({other_placeholders})"
                            params.extend(other_sources)
                        
                        sql += """
                              )
                            ORDER BY similarity ASC
                            LIMIT %s;
                        """
                        params.append(top_k * 2)
                        
                        print(f"   🔎 Brand Deep Dive + Trade filter: brand={brand_name}, trade={detected_trade}")
                        cur.execute(sql, params)
                        results = cur.fetchall()
                    
                    # Fallback if trade filter returned no results
                    if not results:
                        print(f"   ⚠️ No results with trade filter '{detected_trade}', falling back to brand-only search")
                        # Try brand-only search without trade filter
                        sql_brand_only = """
                            SELECT id, source, page, content, section, clause, snippet,
                                   doc_type, trade, status, priority, phase, brand_name, product_family,
                                   (embedding <=> %s::vector) as similarity
                            FROM documents 
                            WHERE embedding IS NOT NULL
                              AND brand_name ILIKE %s
                            ORDER BY similarity ASC
                            LIMIT %s;
                        """
                        cur.execute(sql_brand_only, [query_embedding, f"%{brand_name}%", top_k * 2])
                        results = cur.fetchall()
                        detected_trade = None  # Reset for logging
                
                elif has_final_sweep or has_fasteners_suite:
                    # Use special query that searches Final Sweep sources and brand names
                    # Extract brand names from Final Sweep sources
                    final_sweep_sources = [s for s in target_sources if 'Final Sweep' in s]
                    other_sources = [s for s in target_sources if 'Final Sweep' not in s and s != 'Fasteners Full Suite']
                    
                    # Build flexible query for fastener content
                    sql = """
                        SELECT id, source, page, content, section, clause, snippet,
                               doc_type, trade, status, priority, phase, brand_name,
                               (embedding <=> %s::vector) as similarity
                        FROM documents 
                        WHERE embedding IS NOT NULL
                          AND (
                            source LIKE 'Final Sweep%%'
                            OR trade = 'fasteners'
                            OR category_code = 'F_Manufacturers'
                    """
                    params = [query_embedding]
                    
                    # Add any specific brand name filters extracted from the query
                    if final_sweep_sources:
                        brand_placeholders = ', '.join(['%s'] * len(final_sweep_sources))
                        sql += f" OR source IN ({brand_placeholders})"
                        params.extend(final_sweep_sources)
                    
                    if other_sources:
                        other_placeholders = ', '.join(['%s'] * len(other_sources))
                        sql += f" OR source IN ({other_placeholders})"
                        params.extend(other_sources)
                    
                    sql += """
                          )
                        ORDER BY similarity ASC
                        LIMIT %s;
                    """
                    params.append(top_k * 2)
                    
                    print(f"   🔎 Fastener-optimized search: Final Sweep + fasteners trade")
                    cur.execute(sql, params)
                    results = cur.fetchall()
                else:
                    # Standard source-filtered search
                    # Generate placeholders for IN clause (%s, %s, %s, ...)
                    placeholders = ', '.join(['%s'] * len(target_sources))
                    
                    # Build SQL with expanded IN clause (psycopg2-safe) + metadata
                    sql = f"""
                        SELECT id, source, page, content, section, clause, snippet,
                               doc_type, trade, status, priority, phase, brand_name,
                               (embedding <=> %s::vector) as similarity
                        FROM documents 
                        WHERE source IN ({placeholders})
                          AND embedding IS NOT NULL
                        ORDER BY similarity ASC
                        LIMIT %s;
                    """
                    
                    # Bind parameters: embedding, then each source individually, then limit
                    params = [query_embedding] + target_sources + [top_k * 2]
                    
                    print(f"   🔎 Searching {len(target_sources)} sources: {target_sources}")
                    cur.execute(sql, params)
                    results = cur.fetchall()
                
                # FALLBACK LOGIC: If filtered search returns 0 results, retry with global search + metadata
                if len(results) == 0:
                    print(f"   ⚠️ Filtered search returned 0 results, retrying with GLOBAL search...")
                    cur.execute("""
                        SELECT id, source, page, content, section, clause, snippet,
                               doc_type, trade, status, priority, phase,
                               (embedding <=> %s::vector) as similarity
                        FROM documents 
                        WHERE embedding IS NOT NULL
                        ORDER BY similarity ASC
                        LIMIT %s;
                    """, (query_embedding, top_k * 2))
                    results = cur.fetchall()
                    print(f"   🌐 Global search fallback: found {len(results)} chunks")
            else:
                # Fallback global search also includes metadata
                print(f"   🌐 Searching ALL documents (no source filter)")
                cur.execute("""
                    SELECT id, source, page, content, section, clause, snippet,
                           doc_type, trade, status, priority, phase,
                           (embedding <=> %s::vector) as similarity
                    FROM documents 
                    WHERE embedding IS NOT NULL
                    ORDER BY similarity ASC
                    LIMIT %s;
                """, (query_embedding, top_k * 2))
                results = cur.fetchall()
            
            search_time = (time.time() - search_start) * 1000
            print(f"⚡ Vector search completed in {search_time:.0f}ms, found {len(results)} chunks")
        
        # Return connection to pool
        return_db_connection(conn)
        
        # Format results with metadata-aware scoring
        formatted_results = []
        for result in results:
            # Convert similarity to base score (lower similarity = higher score)
            # Similarity ranges from 0 (identical) to 2 (opposite)
            # Convert to 0-1 score where 1 is best match
            similarity = float(result['similarity'])
            base_score = max(0.0, 1.0 - (similarity / 2.0))
            
            # Extract metadata
            doc_type = result.get('doc_type')
            priority = result.get('priority', 50)
            trade_meta = result.get('trade')
            status_meta = result.get('status')
            
            # Apply metadata-aware scoring
            final_score = score_with_metadata(base_score, doc_type, priority, intent)
            
            formatted_result = {
                'id': str(result['id']),
                'source': result['source'],
                'page': result['page'],
                'content': result['content'],
                'section': result['section'],
                'clause': result['clause'],
                'snippet': result['snippet'] or result['content'][:200],
                'base_score': base_score,
                'final_score': final_score,
                'similarity': similarity,
                'doc_type': doc_type,
                'trade': trade_meta,
                'status': status_meta,
                'priority': priority,
                'tier1_source': True
            }
            
            formatted_results.append(formatted_result)
        
        # Apply ranking bias based on query patterns (keep existing B1 Amendment logic)
        bias_weights = detect_b1_amendment_bias(query)
        bias_applied = False
        if bias_weights:
            print(f"🎯 Applying ranking bias: {bias_weights}")
            formatted_results = apply_ranking_bias(formatted_results, bias_weights)
            bias_applied = True
        
        # Sort by final_score (metadata-aware) instead of base score
        final_results = sorted(formatted_results, key=lambda x: x['final_score'], reverse=True)[:top_k]
        
        # DEBUG LOGGING: Log top 5 unique documents with metadata
        unique_sources = {}
        for r in final_results:
            if r['source'] not in unique_sources:
                unique_sources[r['source']] = r
        
        top_docs_log = []
        for idx, (source, doc) in enumerate(list(unique_sources.items())[:5], 1):
            top_docs_log.append(
                f"{idx}) {source} (doc_type={doc.get('doc_type', 'N/A')}, trade={doc.get('trade', 'N/A')}, "
                f"priority={doc.get('priority', 0)}, base={doc['base_score']:.3f}, final={doc['final_score']:.3f})"
            )
        
        print(f"[retrieval] intent={intent} top_docs:")
        for log_line in top_docs_log:
            print(f"   {log_line}")
        
        tier1_count = sum(1 for r in final_results if r.get('tier1_source', False))
        
        # Log source distribution after bias
        source_mix = {}
        for result in final_results:
            source = result['source']
            source_mix[source] = source_mix.get(source, 0) + 1
        
        total_time = (time.time() - start_time) * 1000
        print(f"✅ Vector Tier-1 retrieval: {len(final_results)} results ({tier1_count} Tier-1) in {total_time:.0f}ms")
        print(f"📊 Retrieval source mix for '{query[:50]}...': {source_mix}")
        
        # Log B1 Amendment 13 vs Legacy B1 distribution
        amendment_count = source_mix.get('B1 Amendment 13', 0)
        legacy_count = source_mix.get('B1/AS1', 0)
        print(f"   B1 Amendment 13: {amendment_count}, Legacy B1: {legacy_count}")
        
        return final_results
        
    except Exception as e:
        print(f"❌ Vector retrieval failed: {e}, falling back to keyword search")
        return _fallback_keyword_search(query, top_k, DATABASE_URL)

def _fallback_keyword_search(query: str, top_k: int, DATABASE_URL: str) -> List[Dict]:
    """Old keyword-based search as fallback"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        query_lower = query.lower()
        
        # Simple keyword search
        search_terms = [term for term in query_lower.split() if len(term) > 3][:3]
        results = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for term in search_terms:
                cur.execute("""
                    SELECT id, source, page, content, section, clause, snippet
                    FROM documents 
                    WHERE LOWER(content) LIKE %s
                    ORDER BY page
                    LIMIT %s;
                """, (f'%{term}%', top_k))
                
                term_results = cur.fetchall()
                for result in term_results:
                    results.append({
                        'id': str(result['id']),
                        'source': result['source'],
                        'page': result['page'],
                        'content': result['content'],
                        'section': result['section'],
                        'clause': result['clause'],
                        'snippet': result['snippet'] or result['content'][:200],
                        'score': 0.7,
                        'tier1_source': True
                    })
        
        conn.close()
        
        # Remove duplicates
        seen = set()
        deduped = []
        for result in results:
            key = f"{result['source']}_{result['page']}"
            if key not in seen:
                seen.add(key)
                deduped.append(result)
        
        return deduped[:top_k]
        
    except Exception as e:
        print(f"❌ Fallback keyword search failed: {e}")
        return []

# Export the working function
def get_simple_tier1_retrieval():
    return simple_tier1_retrieval
