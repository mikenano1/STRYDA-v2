"""
STRYDA LAW 5: DELFAST ZERO-HIT CONSULTATIVE TRIGGER (HARDENED)
===============================================================
Protocol: /protocols/BRAND_SHIELD_DELFAST.md

HARDWIRED RULES:
1. NEVER say "Data not found", "consult the manual", or "I don't have"
2. For CAPACITY queries: MUST have timber type + thickness OR ask
3. For DURABILITY queries: MUST have zone specified OR ask
4. For STAPLE queries: Search ALL Delfast sources (Catalogue + BRANZ)
5. Suggest alternatives from available data

MANDATORY CONTEXT FOR CAPACITY QUERIES:
- Timber thickness (19mm, 32mm, 45mm, etc.)
- Timber species/grade (SG8, radiata, vitex, etc.)  
- Application type (structural, cladding, fencing)
"""

import re
from typing import Dict, List, Optional, Tuple

# ============================================================================
# DELFAST PRODUCT TRIGGERS (EXPANDED)
# ============================================================================

DELFAST_TRIGGERS = [
    # Product codes
    'jdn', 'd-head', 'd head', 'batten staple', 'rx40a', 'cn series',
    't-nail', 't nail', 'c-nail', 'c nail', 'smartnail',
    # Generic terms mapped to Delfast
    'framing nail', 'cladding nail', 'fencing staple', 'coil nail',
    '34 degree', 'paper collated', 'wire collated',
    # Brand
    'delfast',
    # Additional triggers
    'stainless staple', 'galvanised staple', 'fence staple',
    'ring shank', 'bright nail', 'galv nail',
]

# ============================================================================
# CAPACITY QUERY DETECTION (HARDENED)
# ============================================================================

CAPACITY_KEYWORDS = [
    'capacity', 'load', 'strength', 'withdrawal', 'pull-out', 'pullout',
    'shear', 'lateral', 'holding', 'kn', 'newton', 'force',
    'how strong', 'how much load', 'can it hold', 'will it hold'
]

TIMBER_THICKNESS_PATTERNS = [
    r'\b(\d{2,3})\s*mm\b',  # "32mm", "45mm"
    r'\b(\d{2,3})mm\b',
]

TIMBER_SPECIES = [
    'pine', 'radiata', 'vitex', 'cedar', 'macrocarpa', 'rimu', 'kwila',
    'hardwood', 'softwood', 'treated', 'h3', 'h4', 'h5',
    'sg6', 'sg8', 'sg10', 'sg12', 'msg6', 'msg8', 'msg10'
]

# ============================================================================
# DETECTION FUNCTIONS
# ============================================================================

def is_delfast_query(query: str) -> bool:
    """Check if query is targeting Delfast products."""
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in DELFAST_TRIGGERS)


def is_capacity_query(query: str) -> bool:
    """Check if this is a capacity/load/strength query - MUST enforce clarification."""
    query_lower = query.lower()
    return any(kw in query_lower for kw in CAPACITY_KEYWORDS)


def has_timber_thickness(query: str) -> Tuple[bool, Optional[str]]:
    """Check if timber thickness is specified."""
    for pattern in TIMBER_THICKNESS_PATTERNS:
        match = re.search(pattern, query.lower())
        if match:
            return True, match.group(1) + "mm"
    return False, None


def has_timber_species(query: str) -> Tuple[bool, Optional[str]]:
    """Check if timber species/grade is specified."""
    query_lower = query.lower()
    for species in TIMBER_SPECIES:
        if species in query_lower:
            return True, species.upper()
    return False, None


def extract_delfast_context(query: str) -> Dict:
    """Extract ALL context from a Delfast query."""
    query_lower = query.lower()
    
    has_thickness, thickness = has_timber_thickness(query)
    has_species, species = has_timber_species(query)
    
    # Zone detection
    zone_keywords = ['zone b', 'zone c', 'zone d', 'sea spray', 'marine', 'coastal']
    detected_zone = None
    for zone in ['zone d', 'zone c', 'zone b', 'sea spray']:
        if zone in query_lower:
            detected_zone = zone.title()
            break
    
    # Product detection
    detected_product = None
    for product in ['jdn', 'd-head', 'batten staple', 'coil nail', 'framing nail', 
                    'cladding nail', 'stainless staple', 'fencing staple']:
        if product in query_lower:
            detected_product = product.title()
            break
    
    context = {
        'has_zone': any(z in query_lower for z in zone_keywords),
        'has_timber_thickness': has_thickness,
        'has_timber_species': has_species,
        'is_capacity_query': is_capacity_query(query),
        'detected_zone': detected_zone,
        'detected_thickness': thickness,
        'detected_species': species,
        'detected_product': detected_product,
    }
    
    return context


# ============================================================================
# HARDENED LAW 5: MANDATORY CLARIFICATION GENERATORS
# ============================================================================

def _generate_capacity_clarification(query: str, context: Dict) -> str:
    """MANDATORY: Generate clarification for capacity queries missing timber details."""
    product = context.get('detected_product', 'nail')
    has_thickness = context.get('has_timber_thickness', False)
    has_species = context.get('has_timber_species', False)
    thickness = context.get('detected_thickness')
    species = context.get('detected_species')
    
    missing = []
    if not has_thickness:
        missing.append("timber thickness")
    if not has_species:
        missing.append("timber type/grade")
    
    if not missing:
        return None  # All info provided
    
    clarification = f"""I have the capacity data for {product} in the Delfast BRANZ Appraisal, but I need these details to give you the correct value:

"""
    
    if not has_thickness:
        clarification += """**1. Timber Thickness:**
- 19mm (weatherboard, sarking)
- 32mm (standard framing)
- 45mm (heavy framing, bearers)
- Other: ___mm

"""
    
    if not has_species:
        clarification += """**2. Timber Type/Grade:**
- Radiata Pine (SG8)
- Treated Pine (H3.2, H4, H5)
- MSG8/MSG10 (machine stress graded)
- Hardwood (Vitex, Cedar, etc.)
- Other: ___

"""
    
    if has_thickness and thickness:
        clarification += f"✓ You mentioned: {thickness}\n"
    if has_species and species:
        clarification += f"✓ You mentioned: {species}\n"
    
    clarification += """
💡 **Why this matters:** Withdrawal capacity varies by **50-200%** depending on timber thickness and species. A 90mm D-Head in 19mm pine has very different holding power than in 45mm hardwood.

Just reply with the details (e.g., "32mm radiata" or "45mm H3.2 treated") and I'll pull the exact capacity from BRANZ Appraisal 1154."""
    
    return clarification


def _generate_zone_clarification(query: str, context: Dict) -> str:
    """Generate zone clarification for durability queries."""
    product = context.get('detected_product', 'nail')
    
    return f"""I have the durability ratings for {product}s from BRANZ Appraisal 1154, but I need one key detail:

**What durability zone is this for?**
- **Zone B** (most of NZ, >100m from coast)
- **Zone C** (within 100-500m of coast)
- **Zone D** (within 100m of coast, direct salt exposure)
- **Sea Spray Zone** (severe marine environment)

💡 **Why this matters:** The required finish changes dramatically:
- Zone B/C: Hot-dip galvanised is typically suitable
- Zone D: Mechanical galvanising may be insufficient - 304 Stainless often required
- Sea Spray: **Grade 316 Stainless Steel is mandatory** per BRANZ Appraisal 1154

Just reply with your zone (e.g., "Zone C") and I'll give you the exact specification."""


def _generate_staple_clarification(query: str, context: Dict) -> str:
    """Generate clarification for staple queries."""
    return """I have Delfast staple data in both the BRANZ Appraisal and Product Catalogue. To find the right product:

**What type of staple application?**
- **Fencing/Rural** (batten staples, barbed staples for wire)
- **Building/Construction** (flooring staples, sarking staples)
- **Stainless Steel** (for coastal/marine zones)

**What size range?**
- 3.15mm series (cordless stapler compatible)
- 4.0mm series (pneumatic)
- Other: ___mm

Just reply with application type and I'll pull the matching products with SKU codes from the PlaceMakers Catalogue."""


# ============================================================================
# MAIN CONSULTATIVE LOGIC (HARDENED)
# ============================================================================

def generate_delfast_consultative_response(
    query: str,
    retrieved_docs: List[Dict],
    context: Dict
) -> Tuple[bool, Optional[str]]:
    """
    LAW 5 HARDENED: Generate consultative response for Delfast queries.
    
    MANDATORY TRIGGERS:
    1. Capacity query without timber thickness/species -> MUST clarify
    2. Durability query without zone -> MUST clarify
    3. Staple query -> Confirm application type
    
    Returns:
        (should_intervene, consultative_message)
    """
    if not is_delfast_query(query):
        return False, None
    
    query_lower = query.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # RULE 3: STAPLE QUERIES - CONFIRM APPLICATION (CHECK FIRST!)
    # ═══════════════════════════════════════════════════════════════════════
    if 'staple' in query_lower:
        # Check if application type is specified
        application_keywords = ['fencing', 'rural', 'fence', 'building', 'floor', 'sarking', 'marine']
        has_application = any(kw in query_lower for kw in application_keywords)
        
        if not has_application:
            return True, _generate_staple_clarification(query, context)
    
    # ═══════════════════════════════════════════════════════════════════════
    # RULE 1: CAPACITY QUERIES - MANDATORY TIMBER DETAILS
    # ═══════════════════════════════════════════════════════════════════════
    if context.get('is_capacity_query') or is_capacity_query(query):
        has_thickness = context.get('has_timber_thickness', False)
        has_species = context.get('has_timber_species', False)
        
        # HARDENED: If EITHER is missing, MUST ask
        if not has_thickness or not has_species:
            clarification = _generate_capacity_clarification(query, context)
            if clarification:
                return True, clarification
    
    # ═══════════════════════════════════════════════════════════════════════
    # RULE 2: DURABILITY QUERIES - MANDATORY ZONE
    # ═══════════════════════════════════════════════════════════════════════
    durability_keywords = ['durability', 'corrosion', 'zone', 'galv', 'stainless', 'marine', 'coastal', 'rust']
    if any(kw in query_lower for kw in durability_keywords):
        if not context.get('has_zone', False):
            return True, _generate_zone_clarification(query, context)
    
    # ═══════════════════════════════════════════════════════════════════════
    # RULE 3: STAPLE QUERIES - CONFIRM APPLICATION
    # ═══════════════════════════════════════════════════════════════════════
    if 'staple' in query_lower:
        # Check if application type is specified
        application_keywords = ['fencing', 'rural', 'fence', 'building', 'floor', 'sarking', 'marine']
        has_application = any(kw in query_lower for kw in application_keywords)
        
        if not has_application:
            return True, _generate_staple_clarification(query, context)
    
    # ═══════════════════════════════════════════════════════════════════════
    # NO INTERVENTION NEEDED - Let retrieval proceed
    # ═══════════════════════════════════════════════════════════════════════
    return False, None


def apply_delfast_zero_hit_trigger(
    query: str,
    retrieved_docs: List[Dict],
    generated_answer: str
) -> Tuple[str, bool]:
    """
    Post-process check: If the generated answer is weak/generic for a Delfast query,
    replace it with consultative response.
    
    HARDENED: Also catches "I don't have specific data" type responses.
    """
    if not is_delfast_query(query):
        return generated_answer, False
    
    # Check for weak/generic responses that should NEVER happen
    weak_indicators = [
        'data not found',
        'not available',
        'consult the manual',
        'refer to the manufacturer',
        'i don\'t have specific',
        'unable to find',
        'no specific data',
        'couldn\'t find',
        'not in my data',
        'don\'t have that information',
        'cannot find',
        'no data for',
        'doesn\'t have',
        'does not have',
        'information not available',
    ]
    
    answer_lower = generated_answer.lower()
    is_weak = any(indicator in answer_lower for indicator in weak_indicators)
    
    if is_weak:
        context = extract_delfast_context(query)
        
        # Generate appropriate consultative response
        if is_capacity_query(query):
            return _generate_capacity_clarification(query, context), True
        elif any(kw in query.lower() for kw in ['durability', 'zone', 'corrosion', 'galv', 'stainless']):
            return _generate_zone_clarification(query, context), True
        elif 'staple' in query.lower():
            return _generate_staple_clarification(query, context), True
        else:
            # Generic fallback
            return _generate_capacity_clarification(query, context) or _generate_zone_clarification(query, context), True
    
    return generated_answer, False


# ============================================================================
# QUERY EXPANSION FOR BETTER RETRIEVAL
# ============================================================================

def expand_delfast_query(query: str) -> str:
    """
    Expand Delfast queries to search ALL relevant sources.
    Called before retrieval to ensure we search Catalogue + BRANZ.
    """
    expansions = []
    query_lower = query.lower()
    
    # Add source expansions
    if 'staple' in query_lower:
        expansions.extend(['PlaceMakers', 'Catalogue', 'Rural Range', 'fencing'])
    
    if 'jdn' in query_lower:
        expansions.extend(['withdrawal', 'capacity', 'cladding', 'BRANZ 1154'])
    
    if 'd-head' in query_lower or 'framing' in query_lower:
        expansions.extend(['withdrawal', 'capacity', 'framing', 'BRANZ 1154'])
    
    if 'stainless' in query_lower:
        expansions.extend(['316', '304', 'marine', 'coastal', 'sea spray'])
    
    if expansions:
        return query + " " + " ".join(expansions)
    
    return query
