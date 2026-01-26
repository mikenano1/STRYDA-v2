"""
STRYDA LAW 5: DELFAST ZERO-HIT CONSULTATIVE TRIGGER
====================================================
Protocol: /protocols/BRAND_SHIELD_DELFAST.md

When a Delfast query returns insufficient data, this module:
1. NEVER says "Data not found" or "consult the manual"
2. Asks for: Timber Grade, Application (Structural/Non-structural), Environment
3. Suggests nearest standard equivalent from available data

Triggers:
- JDN, D-Head, Batten Staple, RX40A, CN Series, T-Nail, C-Nail
- Framing Nail, Cladding Nail, Fencing Staple
- Any Delfast capacity/specification query
"""

import re
from typing import Dict, List, Optional, Tuple

# ============================================================================
# DELFAST PRODUCT TRIGGERS
# ============================================================================

DELFAST_TRIGGERS = [
    # Product codes
    'jdn', 'd-head', 'd head', 'batten staple', 'rx40a', 'cn series',
    't-nail', 't nail', 'c-nail', 'c nail',
    # Generic terms mapped to Delfast
    'framing nail', 'cladding nail', 'fencing staple', 'coil nail',
    '34 degree', 'paper collated', 'wire collated',
    # Brand
    'delfast',
]

# Standard alternatives for fallback suggestions
DELFAST_ALTERNATIVES = {
    # JDN variants
    'jd5': ['jd4', 'jd3', 'jdn-65', 'jdn-50'],
    'jd4': ['jd5', 'jd3', 'jdn-65'],
    'jd3': ['jd4', 'jdn-50'],
    'jdn-75': ['jdn-65', 'jdn-90'],
    'jdn-65': ['jdn-50', 'jdn-75'],
    'jdn-50': ['jdn-65', 'jdn-40'],
    # D-Head variants
    'd-head 90': ['d-head 75', 'd-head 100', '90mm framing'],
    'd-head 75': ['d-head 65', 'd-head 90', '75mm framing'],
    'd-head 65': ['d-head 75', 'd-head 50'],
    # Staple variants
    '4.0mm staple': ['3.5mm staple', '4.5mm staple', 'barbed staple'],
    'barbed staple': ['4.0mm staple', 'batten staple'],
    # Generic mappings
    'framing nail': ['d-head', '90mm nail', '75mm nail'],
    'cladding nail': ['jdn', 'hardwood nail', '316 stainless nail'],
    'fencing staple': ['batten staple', 'barbed staple'],
}

# Zone-based consultative triggers
ZONE_KEYWORDS = ['zone b', 'zone c', 'zone d', 'sea spray', 'marine', 'coastal']
TIMBER_KEYWORDS = ['sg8', 'sg10', 'sg6', 'msg6', 'msg8', 'msg10', 'pine', 'hardwood', 'radiata']
STRUCTURAL_KEYWORDS = ['structural', 'load bearing', 'load-bearing', 'capacity', 'shear', 'withdrawal', 'pull-out', 'pullout']

# ============================================================================
# DETECTION FUNCTIONS
# ============================================================================

def is_delfast_query(query: str) -> bool:
    """Check if query is targeting Delfast products."""
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in DELFAST_TRIGGERS)


def extract_delfast_context(query: str) -> Dict:
    """Extract context from a Delfast query."""
    query_lower = query.lower()
    
    context = {
        'has_zone': any(z in query_lower for z in ZONE_KEYWORDS),
        'has_timber': any(t in query_lower for t in TIMBER_KEYWORDS),
        'is_structural': any(s in query_lower for s in STRUCTURAL_KEYWORDS),
        'detected_zone': None,
        'detected_timber': None,
        'detected_product': None,
    }
    
    # Detect specific zone
    for zone in ['zone d', 'zone c', 'zone b', 'sea spray']:
        if zone in query_lower:
            context['detected_zone'] = zone.title()
            break
    
    # Detect timber grade
    timber_pattern = r'\b(sg\d+|msg\d+)\b'
    timber_match = re.search(timber_pattern, query_lower)
    if timber_match:
        context['detected_timber'] = timber_match.group(1).upper()
    
    # Detect product
    for product in ['jdn', 'd-head', 'batten staple', 'coil nail', 'framing nail', 'cladding nail']:
        if product in query_lower:
            context['detected_product'] = product.title()
            break
    
    return context


def find_nearest_alternative(product: str, available_products: List[str]) -> Optional[str]:
    """Find the nearest alternative product from available data."""
    product_lower = product.lower().strip()
    
    # Check if product has alternatives defined
    if product_lower in DELFAST_ALTERNATIVES:
        alternatives = DELFAST_ALTERNATIVES[product_lower]
        for alt in alternatives:
            alt_lower = alt.lower()
            for avail in available_products:
                if alt_lower in avail.lower():
                    return avail
    
    # Fuzzy match - look for similar sizes
    size_match = re.search(r'(\d+)', product)
    if size_match:
        target_size = int(size_match.group(1))
        closest = None
        min_diff = float('inf')
        
        for avail in available_products:
            avail_match = re.search(r'(\d+)', avail)
            if avail_match:
                avail_size = int(avail_match.group(1))
                diff = abs(target_size - avail_size)
                if diff < min_diff:
                    min_diff = diff
                    closest = avail
        
        if closest and min_diff <= 15:  # Within 15mm
            return closest
    
    return None


# ============================================================================
# ZERO-HIT CONSULTATIVE RESPONSE GENERATOR
# ============================================================================

def generate_delfast_consultative_response(
    query: str,
    retrieved_docs: List[Dict],
    context: Dict
) -> Tuple[bool, Optional[str]]:
    """
    LAW 5: Generate consultative response for Delfast queries with insufficient data.
    
    Returns:
        (should_intervene, consultative_message)
        - should_intervene=True means replace the normal response
        - consultative_message contains the asking/suggestion text
    """
    if not is_delfast_query(query):
        return False, None
    
    query_context = extract_delfast_context(query)
    
    # Check if we have sufficient data in retrieved docs
    delfast_docs = [d for d in retrieved_docs if 'delfast' in d.get('source', '').lower() or 'delfast' in d.get('content', '').lower()]
    
    # If we have good Delfast data, no intervention needed
    if len(delfast_docs) >= 3:
        # But check for zone ambiguity on durability queries
        if any(kw in query.lower() for kw in ['durability', 'corrosion', 'zone', 'galv', 'stainless']):
            if not query_context['has_zone']:
                return True, _generate_zone_clarification(query, query_context)
        return False, None
    
    # LOW DATA SCENARIO - Generate consultative response
    
    # Scenario 1: Structural capacity query without timber grade
    if query_context['is_structural'] and not query_context['has_timber']:
        return True, _generate_structural_clarification(query, query_context)
    
    # Scenario 2: Durability query without zone
    if any(kw in query.lower() for kw in ['durability', 'corrosion', 'zone', 'galv', 'stainless', 'marine']):
        if not query_context['has_zone']:
            return True, _generate_zone_clarification(query, query_context)
    
    # Scenario 3: Generic application clarification
    if not query_context['is_structural'] and query_context['detected_product']:
        return True, _generate_application_clarification(query, query_context, delfast_docs)
    
    # Scenario 4: Product not found - suggest alternative
    if len(delfast_docs) == 0:
        # Extract available products from retrieved docs
        available = [d.get('source', '') for d in retrieved_docs if d.get('source')]
        alternative = find_nearest_alternative(query_context.get('detected_product', ''), available)
        
        if alternative:
            return True, _generate_alternative_suggestion(query, query_context, alternative)
    
    return False, None


def _generate_zone_clarification(query: str, context: Dict) -> str:
    """Generate zone clarification question."""
    product = context.get('detected_product', 'nail')
    
    return f"""I can help with the durability rating for {product}s, but I need one key detail:

**What durability zone is this for?**
- **Zone B** (most of NZ, >100m from coast)
- **Zone C** (within 100-500m of coast)
- **Zone D** (within 100m of coast, direct salt exposure)
- **Sea Spray Zone** (severe marine environment)

💡 **Why this matters:** The required finish changes dramatically:
- Zone B/C: Hot-dip galvanised is typically suitable
- Zone D: Mechanical galvanising may be insufficient - 304 Stainless often required
- Sea Spray: Grade 316 Stainless Steel is mandatory per BRANZ Appraisal 1154

Just reply with your zone (e.g., "Zone C") and I'll give you the exact specification."""


def _generate_structural_clarification(query: str, context: Dict) -> str:
    """Generate structural application clarification."""
    product = context.get('detected_product', 'nail')
    
    return f"""I can look up the capacity data for {product}, but I need a few details to give you the correct value:

**1. Timber Grade:**
- SG8, SG10, SG12 (structural softwood)
- MSG6, MSG8, MSG10 (machine stress graded)
- H3.2, H4, H5 (treated timber grades)

**2. Application Type:**
- Structural connection (e.g., framing, joist-to-bearer)
- Non-structural/Decorative (e.g., cladding, trim)

**3. Load Direction:**
- Shear (parallel to nail)
- Withdrawal (pulling out)
- Lateral (perpendicular)

💡 The capacity can vary by **200-300%** depending on these factors.

Just reply with the details (e.g., "SG8, structural, shear load") and I'll pull the exact value from the BRANZ Appraisal."""


def _generate_application_clarification(query: str, context: Dict, available_docs: List[Dict]) -> str:
    """Generate application type clarification."""
    product = context.get('detected_product', 'nail')
    
    return f"""I found some data on {product}, but to give you the most relevant specification:

**Is this for a structural connection or decorative application?**

- **Structural** (e.g., JDN into SG8 framing, load-bearing connections)
  → I'll reference BRANZ Appraisal 1154 capacity tables
  
- **Decorative/Cladding** (e.g., exterior weatherboard, trim)
  → I'll focus on durability/corrosion resistance requirements

This helps me pull the right data - structural needs capacity values, cladding needs durability ratings."""


def _generate_alternative_suggestion(query: str, context: Dict, alternative: str) -> str:
    """Generate alternative product suggestion."""
    requested = context.get('detected_product', 'product')
    
    return f"""I don't have specific data for **{requested}** in my Delfast documentation, but I found a close alternative:

📋 **Available Alternative:** {alternative}

This is from the BRANZ Appraisal 1154 data. The specifications are typically similar for adjacent sizes.

Would you like me to:
1. **Show the {alternative} data** (likely close to what you need)
2. **Check if your specific size is mentioned elsewhere** in the PlaceMakers Nail Guide

Just reply with "1" or "2" and I'll proceed."""


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def apply_delfast_zero_hit_trigger(
    query: str,
    retrieved_docs: List[Dict],
    generated_answer: str
) -> Tuple[str, bool]:
    """
    Post-process check: If the generated answer is weak/generic for a Delfast query,
    replace it with consultative response.
    
    Returns:
        (final_answer, was_modified)
    """
    if not is_delfast_query(query):
        return generated_answer, False
    
    # Check for weak/generic responses
    weak_indicators = [
        'data not found',
        'not available',
        'consult the manual',
        'refer to the manufacturer',
        'i don\'t have specific',
        'unable to find',
        'no specific data',
        'couldn\'t find',
    ]
    
    answer_lower = generated_answer.lower()
    is_weak = any(indicator in answer_lower for indicator in weak_indicators)
    
    if is_weak:
        context = extract_delfast_context(query)
        
        # Generate consultative response based on query type
        if any(kw in query.lower() for kw in ['durability', 'zone', 'corrosion', 'galv']):
            return _generate_zone_clarification(query, context), True
        elif any(kw in query.lower() for kw in ['capacity', 'load', 'strength', 'shear']):
            return _generate_structural_clarification(query, context), True
        else:
            return _generate_application_clarification(query, context, []), True
    
    return generated_answer, False
