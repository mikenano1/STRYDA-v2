"""
STRYDA V3.0 GOD TIER RETRIEVAL SERVICE
=======================================
Protocol: BRAIN TRANSPLANT V1 + PROTOCOL SYNONYM
Engine: Weighted Hybrid Search (70% Vector + 30% Keyword)

Features:
- GOD TIER LAWS: Technical synonym expansion (M16 -> 16)
- Hybrid Search: Vector + Keyword boosting
- Smart source filtering by product and material
- Value boosting for chunks with actual data
- Smart snippet extraction (no mid-word cutoffs)

Status: PRODUCTION - Platinum Certified
"""
import os
import re
import psycopg2
import openai
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Config
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# ==============================================================================
# GOD TIER LAWS: TECHNICAL SYNONYM EXPANSION (IMMUTABLE)
# ==============================================================================

def apply_god_tier_laws(query: str) -> str:
    """
    Mandatory pre-processing that expands technical terms.
    Fixes disconnects like "M16" vs "16" in different table chunks.
    """
    expanded_terms = []
    
    # LAW 1: Metric Thread Law (M16 -> 16, size 16)
    metric_matches = re.findall(r'\bM(\d{1,3})\b', query, re.IGNORECASE)
    for val in metric_matches:
        expanded_terms.extend([val, f"size {val}", f"Size: {val}"])
    
    # LAW 2: Rebar/Diameter Law (D12 -> 12mm, 12)
    diameter_matches = re.findall(r'\bD(\d{1,3})\b', query, re.IGNORECASE)
    for val in diameter_matches:
        expanded_terms.extend([f"{val}mm", val, f"Ø{val}"])
    
    # LAW 3: Grade Law (G450 -> 450, Grade 450)
    grade_matches = re.findall(r'\bG(\d{3})\b', query, re.IGNORECASE)
    for val in grade_matches:
        expanded_terms.extend([val, f"Grade {val}"])
    
    # LAW 4: Imperial Fraction Law
    fraction_map = {
        '1/4': '0.25', '3/8': '0.375', '1/2': '0.5', 
        '5/8': '0.625', '3/4': '0.75', '7/8': '0.875',
        '1/8': '0.125', '5/16': '0.3125', '7/16': '0.4375',
        '9/16': '0.5625', '11/16': '0.6875', '13/16': '0.8125'
    }
    for frac, decimal in fraction_map.items():
        if frac in query.lower():
            expanded_terms.extend([decimal, f"{frac} inch"])
    
    # LAW 5: Screw Gauge Law (10-24 -> #10)
    gauge_matches = re.findall(r'\b(\d{1,2})-(\d{2})\b', query)
    for gauge, tpi in gauge_matches:
        expanded_terms.extend([f"#{gauge}", f"{gauge} gauge"])
    
    # LAW 6: Class/Grade Law (Class 8.8 -> 8.8)
    class_matches = re.findall(r'\bclass\s*([\d.]+)\b', query, re.IGNORECASE)
    for val in class_matches:
        expanded_terms.append(val)
        if '.' in val:
            expanded_terms.append(f"Grade {val.split('.')[0]}")
    
    if expanded_terms:
        seen = set()
        unique = [t for t in expanded_terms if t.lower() not in seen and not seen.add(t.lower())]
        return f"{query} {' '.join(unique)}"
    
    return query


# ==============================================================================
# LAW 7: PRODUCT SYNONYM EXPANSION (GRANULARITY BOOST)
# ==============================================================================
# Maps abbreviated/common terms to their technical equivalents

PRODUCT_SYNONYMS = {
    'wtc': ['wind tie', 'wind tie connector', 'wind restraint'],
    'wind tie': ['wtc', 'wind tie connector', 'wind restraint'],
    'pilot hole': ['pre-drill', 'pre drill', 'predrill', 'predrilled'],
    'pre-drill': ['pilot hole', 'pre drill', 'predrill'],
    'pre drill': ['pilot hole', 'pre-drill', 'predrill'],
    'hct': ['heavy connector tie', 'heavy tie'],
    'ltt': ['light twist tie', 'twist tie'],
    'fpc': ['framing anchor', 'post cap'],
    'jh': ['joist hanger'],
    'hs': ['hanger strap', 'hurricane strap'],
    'dynabolt': ['sleeve anchor', 'expansion anchor'],
    'trubolts': ['wedge anchor', 'through bolt'],
    'hilti hit': ['chemical anchor', 'adhesive anchor', 'injection anchor'],
    'hit-hy': ['hybrid anchor', 'chemical anchor'],
    'hit-re': ['epoxy anchor', 'chemical anchor'],
}


def expand_product_synonyms(query: str) -> str:
    """Expand product abbreviations to technical terms"""
    query_lower = query.lower()
    expanded = []
    
    for abbrev, synonyms in PRODUCT_SYNONYMS.items():
        if abbrev in query_lower:
            expanded.extend(synonyms)
    
    if expanded:
        seen = set()
        unique = [t for t in expanded if t.lower() not in seen and not seen.add(t.lower())]
        return f"{query} {' '.join(unique)}"
    
    return query


# ==============================================================================
# KEYWORD EXTRACTION
# ==============================================================================

def extract_keywords(query: str) -> List[str]:
    """Extract technical keywords for boosting."""
    query_lower = query.lower()
    found = []
    
    # Priority terms
    priority_terms = [
        "proof load", "tensile strength", "shear strength", "yield strength",
        "single shear", "double shear", "pull out", "pullout",
        "hardness", "torque", "span", "wind zone", "axial tensile",
        "edge distance", "embedment", "installation torque"
    ]
    for term in priority_terms:
        if term in query_lower:
            found.append(term)
    
    # Size patterns
    found.extend(re.findall(r'\d+-\d+', query_lower))  # 10-24
    found.extend(re.findall(r'\d+/\d+(?:\s*inch)?', query_lower))  # 1/2 inch
    found.extend(re.findall(r'm\d+', query_lower))  # M12
    found.extend(re.findall(r'\d+x\d+', query_lower))  # 140x45
    found.extend(re.findall(r'grade\s*\d+|class\s*[\d.]+|sg\d+|msg\d+', query_lower))
    
    # Product types
    product_types = [
        "hex nut", "hex bolt", "set screw", "lock nut", "anchor",
        "washer", "rafter", "joist", "bearer", "purlin",
        "wafer head", "wafer", "sdm", "deep driller",
        "through bolt", "throughbolt", "sleeve anchor"
    ]
    for pt in product_types:
        if pt in query_lower:
            found.append(pt)
    
    return list(set(found))


# ==============================================================================
# SMART SNIPPET EXTRACTION
# ==============================================================================

def find_boundary_left(content: str, pos: int) -> int:
    """Walk left to clean boundary (newline, pipe, or start)."""
    while pos > 0:
        char = content[pos - 1]
        if char in '\n|':
            break
        pos -= 1
    return pos


def find_boundary_right(content: str, pos: int) -> int:
    """Walk right to clean boundary (newline, period, pipe, or end)."""
    length = len(content)
    while pos < length:
        char = content[pos]
        if char == '\n':
            pos += 1
            break
        if char == '.' and (pos + 1 >= length or content[pos + 1] in ' \n'):
            pos += 1
            break
        if char == '|':
            remaining = content[pos:].split('\n')[0]
            if remaining.count('|') <= 1:
                pos += 1
                break
        pos += 1
    return pos


def extract_smart_snippet(content: str, match_pos: int, min_length: int = 80) -> str:
    """Extract grammatically complete snippet around match position."""
    left = find_boundary_left(content, match_pos)
    right = find_boundary_right(content, match_pos)
    snippet = content[left:right].strip()
    
    if len(snippet) < min_length:
        if left > 0:
            prev_left = find_boundary_left(content, left - 1)
            snippet = content[prev_left:right].strip()
        if len(snippet) < min_length and right < len(content):
            next_right = find_boundary_right(content, right)
            snippet = content[left:next_right].strip()
    
    return snippet


def highlight_snippet(content: str, keywords: List[str]) -> str:
    """Find relevant snippet around keywords with complete boundaries."""
    content_lower = content.lower()
    best_snippet = None
    best_score = 0
    best_pos = 0
    
    value_patterns = [
        r'value[:\s]*[\d,]+', r'\d+\.?\d*\s*mm', r'\d+\.?\d*\s*kn',
        r'\d+\.?\d*\s*lbf', r'\|\s*[\d,]+\.?\d*\s*\|',
        r':\s*[\d,]+\.?\d*\s*(?:mm|kn|lbf|psi|mpa)',
        r'shear[:\s]*[\d,]+', r'tension[:\s]*[\d,]+'
    ]
    
    for pattern in value_patterns:
        for match in re.finditer(pattern, content_lower):
            pos = match.start()
            nearby = content_lower[max(0, pos-150):min(len(content), pos+150)]
            
            score = sum(2 for kw in keywords if kw.lower() in nearby)
            if any(s in nearby for s in ['size', '1/2', 'm12', 'm16', '10-24']):
                score += 1
            if 'shear' in nearby or 'tension' in nearby or 'torque' in nearby:
                score += 2
            
            if score > best_score:
                best_score = score
                best_pos = pos
    
    if best_score > 0:
        best_snippet = extract_smart_snippet(content, best_pos)
    
    if not best_snippet:
        for kw in keywords:
            pos = content_lower.find(kw.lower())
            if pos != -1:
                best_snippet = extract_smart_snippet(content, pos)
                break
    
    if not best_snippet:
        first_newline = content.find('\n')
        if first_newline > 0 and first_newline < 300:
            best_snippet = content[:first_newline].strip()
        else:
            best_snippet = content[:300].strip()
    
    # Add ellipsis for truncation
    if len(best_snippet) < len(content):
        snippet_start = content.find(best_snippet[:30]) if len(best_snippet) >= 30 else 0
        if snippet_start > 5:
            best_snippet = "..." + best_snippet
        if not content.strip().endswith(best_snippet.strip()[-30:]):
            best_snippet = best_snippet + "..."
    
    return best_snippet


# ==============================================================================
# EMBEDDING GENERATION
# ==============================================================================

def get_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI."""
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
        dimensions=1536
    )
    return r.data[0].embedding


# ==============================================================================
# DIRECTIVE 4: BRAND SYNONYM MAP (MITEK REFINERY PROTOCOL)
# ==============================================================================
# Rule: If user asks for "Lumberlok", search "Lumberlok" AND "MiTek"
# This ensures sub-brand queries always include the parent brand

BRAND_SYNONYM_MAP = {
    # MiTek Sub-brands -> Parent
    'lumberlok': ['MiTek', 'Lumberlok'],
    'bowmac': ['MiTek', 'Bowmac'],
    'gang-nail': ['MiTek', 'Gang-Nail'],
    'gangnail': ['MiTek', 'Gang-Nail'],
    'gib-handibrac': ['MiTek', 'GIB', 'Winstone'],  # Cross-brand product
    'gib handibrac': ['MiTek', 'GIB', 'Winstone'],
    'handibrac': ['MiTek', 'GIB', 'Winstone'],
    'posistrut': ['MiTek', 'PosiStrut'],
    'stud-lok': ['MiTek', 'Stud-Lok'],
    'studlok': ['MiTek', 'Stud-Lok'],
    'plate-lok': ['MiTek', 'Plate-Lok'],
    'platelok': ['MiTek', 'Plate-Lok'],
    'multi-brace': ['MiTek', 'Multi-Brace'],
    'multibrace': ['MiTek', 'Multi-Brace'],
    'gib quiet tie': ['MiTek', 'GIB', 'Winstone'],
    'gib-quiet-tie': ['MiTek', 'GIB', 'Winstone'],
    # Reverse mappings (MiTek -> include all sub-brands)
    'mitek': ['MiTek', 'Lumberlok', 'Bowmac', 'Gang-Nail', 'PosiStrut', 'Stud-Lok'],
    # Pryda brands
    'pryda': ['Pryda'],
    # Bremick brands
    'bremick': ['Bremick'],
}

# ==============================================================================
# LAW 1: BRAND SUPREMACY - PROTECTED BRANDS (HARD-WIRED)
# ==============================================================================
# If query contains ANY of these brands, apply -100% penalty to NZS 3604 chunks
# The Brand's "Structural Bible" is the ONLY source of truth for that query

PROTECTED_BRANDS = [
    'mitek', 'lumberlok', 'bowmac', 'gang-nail', 'gangnail', 'posistrut',
    'stud-lok', 'studlok', 'plate-lok', 'platelok', 'handibrac', 'gib-handibrac',
    'pryda', 'bremick', 'multinail', 'simpson', 'hilti', 'ramset', 'buildex',
    # Hilti product lines (Law 1 Brand Supremacy for concrete/chemical anchors)
    'hit-hy', 'hit-re', 'hit-mm', 'hvu', 'hst', 'hsl', 'hus', 'kwik bolt',
    'kwikbolt', 'trubolts', 'kb-tz', 'hda', 'hce', 'hcl', 'hrd',
    # DELFAST - Protected Brand (Hard-Wire Law 1)
    'delfast', 'jdn', 'd-head', 'batten staple', 'rx40a', 'cn series', 
    't-nail', 'c-nail', 'framing nail', 'cladding nail', 'fencing staple'
]

# ==============================================================================
# LAW 3: SUPREME AUTHORITY DOCUMENTS (HARD-WIRED)
# ==============================================================================
# These documents override ALL other sources for their respective brands

SUPREME_AUTHORITY_DOCS = {
    'MiTek': 'Residential-Manual',
    'Pryda': 'Pryda-Manual',
    'Bremick': 'Technical-Data-Sheet',
}

# Structural connector terms for MiTek products
STRUCTURAL_TERMS = [
    'pile fixing', '6kn', '12kn', 'joist hanger', 'purlin cleat',
    'top plate', 'bottom plate', 'stud fixing', 'bearer bracket',
    'angle bracket', 'post bracket', 'timber connector', 'floor joist',
    'deck joist', 'bracing', 'stiffener', 'lintel', 'stringer',
    'characteristic load', 'characteristic strength', 'flitch beam'
]


def detect_protected_brand(query: str) -> Optional[str]:
    """
    LAW 1: BRAND SUPREMACY - Detect if query targets a protected brand.
    Returns the brand name if found, None otherwise.
    """
    query_lower = query.lower()
    for brand in PROTECTED_BRANDS:
        if brand in query_lower:
            # Return the canonical brand name
            if brand in ['mitek', 'lumberlok', 'bowmac', 'gang-nail', 'gangnail', 
                         'posistrut', 'stud-lok', 'studlok', 'plate-lok', 'handibrac']:
                return 'MiTek'
            elif brand == 'pryda':
                return 'Pryda'
            elif brand == 'bremick':
                return 'Bremick'
            elif brand in ['hilti', 'hit-hy', 'hit-re', 'hit-mm', 'hvu', 'hst', 'hsl', 
                          'hus', 'kwik bolt', 'kwikbolt', 'trubolts', 'kb-tz', 'hda', 
                          'hce', 'hcl', 'hrd']:
                return 'Hilti'
            elif brand == 'ramset':
                return 'Ramset'
            elif brand == 'simpson':
                return 'Simpson'
            else:
                return brand.title()
    return None


def apply_brand_supremacy_penalty(chunks: List[Dict], protected_brand: str) -> List[Dict]:
    """
    LAW 1: BRAND SUPREMACY - Apply -100% penalty to NZS 3604 chunks.
    When a protected brand is detected, NZS 3604 generic content is FORBIDDEN.
    Only the brand's own documentation is allowed.
    
    REFINED RULE:
    - If chunk SOURCE is from the protected brand → KEEP (even if mentions NZS 3604)
    - If chunk SOURCE is NZS 3604 or generic standards → EXCLUDE
    """
    if not protected_brand:
        return chunks
    
    filtered_chunks = []
    for chunk in chunks:
        source_lower = chunk.get('source', '').lower()
        
        # Check if chunk is from the protected brand (by source name)
        is_brand_source = protected_brand.lower() in source_lower
        
        # Check if chunk is from a GENERIC standard (not the brand)
        is_generic_standard = any(term in source_lower for term in [
            'nzs 3604', '3604', 'nzs3604', 'standards nz', 'standard new zealand',
            'building code', 'b1/as1', 'e2/as1', 'acceptable solution'
        ])
        
        # KEEP if from brand source, EXCLUDE if from generic standards
        if is_brand_source:
            # Always keep brand's own documentation
            filtered_chunks.append(chunk)
        elif is_generic_standard:
            # Exclude generic standards when brand is specified
            continue
        else:
            # Keep other sources (might be related products)
            filtered_chunks.append(chunk)
    
    return filtered_chunks


def expand_brand_synonyms(query: str) -> str:
    """
    DIRECTIVE 4: Brand Synonym Injection
    Expands sub-brand queries to include parent brand for better retrieval.
    """
    query_lower = query.lower()
    expanded_brands = []
    
    for brand_key, brand_variants in BRAND_SYNONYM_MAP.items():
        if brand_key in query_lower:
            expanded_brands.extend(brand_variants)
    
    if expanded_brands:
        # Remove duplicates while preserving order
        seen = set()
        unique_brands = [b for b in expanded_brands if b.lower() not in seen and not seen.add(b.lower())]
        brand_suffix = ' ' + ' '.join(unique_brands)
        return query + brand_suffix
    
    return query


# ==============================================================================
# FASTENER TERMS FOR SOURCE DETECTION
# ==============================================================================

FASTENER_TERMS = [
    'hex nut', 'hex bolt', 'proof load', 'tensile', 'lock nut',
    'set screw', 'coach screw', 'anchor', 'washer', 'fastener',
    'unc', 'unf', 'metric', 'grade 5', 'grade 8', 'class 4', 'class 8',
    'm6', 'm8', 'm10', 'm12', 'm14', 'm16', 'm20', 'm24',
    '1/4', '5/16', '3/8', '7/16', '1/2', '9/16', '5/8', '3/4', '7/8',
    'bremick', 'dynabolt', 'edge distance', 'embedment', 'concrete anchor',
    'masonry anchor', 'through bolt', 'throughbolt', 'sleeve anchor',
    'torque', 'installation torque'
]


# ==============================================================================
# HYBRID SEARCH ENGINE (GOD TIER V3)
# ==============================================================================

def semantic_search(
    query: str,
    top_k: int = 20,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> List[Dict]:
    """
    God Tier V3 Hybrid Search Engine.
    
    Features:
    - Technical synonym expansion (GOD TIER LAWS)
    - Product synonym expansion (LAW 7 - WTC, Pilot Hole, etc.)
    - Brand synonym expansion (MITEK REFINERY PROTOCOL)
    - 70% Vector + 30% Keyword weighting
    - Smart source filtering for fasteners/structural
    - Value boosting for chunks with actual data
    - Smart snippet extraction
    
    Returns:
        List of dicts with: content, source, page, snippet, score, keyword_matches
    """
    # Step 1: Apply GOD TIER LAWS
    expanded_query = apply_god_tier_laws(query)
    
    # Step 1b: Apply Product Synonym Expansion (LAW 7 - WTC, Pilot Hole, etc.)
    expanded_query = expand_product_synonyms(expanded_query)
    
    # Step 1c: Apply Brand Synonym Expansion (DIRECTIVE 4)
    expanded_query = expand_brand_synonyms(expanded_query)
    
    # Step 2: Get embedding
    emb = get_embedding(expanded_query)
    
    # Step 3: Extract keywords
    keywords = extract_keywords(expanded_query)
    
    # Step 4: Database search
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    query_lower = query.lower()
    is_fastener_query = any(term in query_lower for term in FASTENER_TERMS)
    is_structural_query = any(term in query_lower for term in STRUCTURAL_TERMS)
    
    # Detect protected brand for increased granularity
    protected_brand = detect_protected_brand(query)
    
    # GRANULARITY BOOST: Increase top_k for brand queries
    effective_top_k = top_k
    if protected_brand:
        effective_top_k = max(top_k, 30)  # Ensure at least 30 for brand queries
    
    # Detect specific protected brand
    protected_brand = detect_protected_brand(query)
    
    # BRAND-SPECIFIC QUERY HANDLING
    if protected_brand:
        # Search ONLY the protected brand's documents
        brand_pattern = f'%{protected_brand}%'
        cur.execute("""
            SELECT id, content, source, page, 
                   1 - (embedding <=> %s::vector) as vector_score
            FROM documents
            WHERE source ILIKE %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (emb, brand_pattern, emb, top_k * 3))
        candidates = cur.fetchall()
        
        # If brand is MiTek, also search sub-brands
        if protected_brand == 'MiTek' and len(candidates) < 10:
            cur.execute("""
                SELECT id, content, source, page, 
                       1 - (embedding <=> %s::vector) as vector_score
                FROM documents
                WHERE source ILIKE '%%Lumberlok%%' 
                   OR source ILIKE '%%Bowmac%%'
                   OR source ILIKE '%%PosiStrut%%'
                   OR source ILIKE '%%Gang%%Nail%%'
                   OR source ILIKE '%%MiTek%%'
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (emb, emb, top_k * 3))
            extra = cur.fetchall()
            # Merge and dedupe
            seen_ids = {c[0] for c in candidates}
            candidates.extend([c for c in extra if c[0] not in seen_ids])
    
    elif is_fastener_query:
        # Detect specific product and material
        specific_product = None
        specific_material = None
        
        if 'through bolt' in query_lower or 'throughbolt' in query_lower:
            specific_product = '%Throughbolt%'
        elif 'sleeve anchor' in query_lower or 'sleeveanchor' in query_lower:
            specific_product = '%Sleeveanchor%'
        elif 'screw anchor' in query_lower or 'screwanchor' in query_lower:
            specific_product = '%Screwanchor%'
        
        if 'stainless' in query_lower:
            specific_material = '%Stainless%'
        elif 'galvanised' in query_lower or 'galvanized' in query_lower:
            specific_material = '%Galvanised%'
        elif 'zinc' in query_lower:
            specific_material = '%Zinc%'
        
        if specific_product and specific_material:
            cur.execute("""
                SELECT id, content, source, page, 
                       1 - (embedding <=> %s::vector) as vector_score
                FROM documents
                WHERE source LIKE %s AND source LIKE %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (emb, specific_product, specific_material, emb, top_k * 2))
            candidates = cur.fetchall()
        elif specific_product:
            cur.execute("""
                SELECT id, content, source, page, 
                       1 - (embedding <=> %s::vector) as vector_score
                FROM documents
                WHERE source LIKE %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (emb, specific_product, emb, top_k * 2))
            candidates = cur.fetchall()
            
            if len(candidates) < 5:
                cur.execute("""
                    SELECT id, content, source, page, 
                           1 - (embedding <=> %s::vector) as vector_score
                    FROM documents
                    WHERE source LIKE 'Bremick%%'
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (emb, emb, top_k * 3))
                candidates = cur.fetchall()
        else:
            cur.execute("""
                SELECT id, content, source, page, 
                       1 - (embedding <=> %s::vector) as vector_score
                FROM documents
                WHERE source LIKE 'Bremick%%'
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (emb, emb, top_k * 3))
            candidates = cur.fetchall()
    else:
        cur.execute("""
            SELECT id, content, source, page, 
                   1 - (embedding <=> %s::vector) as vector_score
            FROM documents
            WHERE is_active = true
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (emb, emb, top_k * 3))
        candidates = cur.fetchall()
    
    conn.close()
    
    # Step 5: Keyword boosting and scoring
    results = []
    
    for row in candidates:
        doc_id, content, source, page, vector_score = row
        content_lower = content.lower()
        
        # Keyword score
        keyword_matches = sum(1 for kw in keywords if kw.lower() in content_lower)
        keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0) if keywords else 0
        
        # Hybrid score
        hybrid_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
        
        # Perfect keyword match bonus
        if keywords and all(kw.lower() in content_lower for kw in keywords):
            hybrid_score += 0.15
        
        # Value boost for chunks with actual data
        if 'torque' in query_lower and 'installation torque' in content_lower:
            if re.search(r'torque.*\|\s*\d+', content_lower) or re.search(r'value:\s*\d+', content_lower):
                hybrid_score += 0.20
        
        for size_match in re.findall(r'\bm?(\d{1,2})\b', query_lower):
            if f'size: {size_match}' in content_lower or f'| {size_match} |' in content_lower:
                if re.search(r'value:\s*\d+', content_lower):
                    hybrid_score += 0.10
        
        # Extract snippet
        snippet = highlight_snippet(content, keywords)
        
        results.append({
            'content': content,
            'source': source,
            'page': page,
            'snippet': snippet,
            'score': hybrid_score,
            'vector_score': vector_score,
            'keyword_matches': keyword_matches
        })
    
    # ==============================================================================
    # LAW 1: BRAND SUPREMACY - Apply -100% penalty to NZS 3604 chunks
    # ==============================================================================
    protected_brand = detect_protected_brand(query)
    if protected_brand:
        results = apply_brand_supremacy_penalty(results, protected_brand)
    
    # Sort by hybrid score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results[:top_k]


# ==============================================================================
# LEGACY COMPATIBILITY WRAPPER
# ==============================================================================

def godtier_retrieval(
    query: str,
    top_k: int = 20,
    intent: str = None,
    agent_mode: str = None
) -> List[Dict]:
    """
    Wrapper for compatibility with existing tier1_retrieval interface.
    Maps to semantic_search with appropriate formatting.
    """
    results = semantic_search(query, top_k=top_k)
    
    # Format for compatibility
    formatted = []
    for r in results:
        formatted.append({
            'content': r['content'],
            'source': r['source'],
            'page': r['page'],
            'snippet': r['snippet'],
            'final_score': r['score'],
            'base_score': r['vector_score'],
            'doc_type': 'Technical_Data_Sheet',
            'trade': 'fasteners',
            'priority': 95
        })
    
    return formatted
