#!/usr/bin/env python3
"""
STRYDA V3.0 RAG ENGINE WITH HYBRID SEARCH
==========================================
Protocol: BRAIN TRANSPLANT V1 + PROTOCOL SYNONYM
Engine: Weighted Hybrid Search (70% Vector + 30% Keyword)

Features:
- Semantic vector search for conceptual understanding
- Keyword boosting for technical terms
- Clarification loop for ambiguous queries
- Mandatory citation format
- GOD TIER LAWS: Technical synonym expansion
"""
import os
import sys
import re
import asyncio
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import core prompts
sys.path.insert(0, '/app/backend-minimal')
from core_prompts import STRYDA_SYSTEM_PROMPT, TECHNICAL_KEYWORDS, AMBIGUOUS_PATTERNS, CLARIFICATION_TEMPLATES

# Config
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# ==============================================================================
# GOD TIER LAWS: TECHNICAL SYNONYM EXPANSION (PERMANENT - DO NOT MODIFY)
# ==============================================================================
# Protocol: PROTOCOL SYNONYM V1
# Purpose: Translate technical shorthand into searchable variants
# Status: IMMUTABLE - These laws apply to ALL searches across ALL files
# ==============================================================================

def apply_god_tier_laws(query):
    """
    Mandatory pre-processing step that expands technical terms.
    This fixes disconnects like "M16" vs "16" in different table chunks.
    """
    expanded_terms = []
    original_query = query
    
    # LAW 1: The "Metric Thread" Law (M16 -> 16, size 16)
    # Handles: M6, M8, M10, M12, M14, M16, M20, M24, M30 etc.
    metric_matches = re.findall(r'\bM(\d{1,3})\b', query, re.IGNORECASE)
    for val in metric_matches:
        expanded_terms.append(val)              # "16"
        expanded_terms.append(f"size {val}")    # "size 16"
        expanded_terms.append(f"Size: {val}")   # "Size: 16" (table format)
    
    # LAW 2: The "Rebar/Diameter" Law (D12 -> 12mm, 12)
    # Handles: D10, D12, D16, D20, D25, D32 etc.
    diameter_matches = re.findall(r'\bD(\d{1,3})\b', query, re.IGNORECASE)
    for val in diameter_matches:
        expanded_terms.append(f"{val}mm")       # "12mm"
        expanded_terms.append(val)              # "12"
        expanded_terms.append(f"Ø{val}")        # "Ø12"
    
    # LAW 3: The "Grade" Law (G450 -> 450, Grade 450)
    # Handles: G300, G450, G500 etc.
    grade_matches = re.findall(r'\bG(\d{3})\b', query, re.IGNORECASE)
    for val in grade_matches:
        expanded_terms.append(val)              # "450"
        expanded_terms.append(f"Grade {val}")   # "Grade 450"
    
    # LAW 4: The "Imperial Fraction" Law (1/2" -> 0.5, 1/2 inch)
    # Handles: 1/4, 3/8, 1/2, 5/8, 3/4, 7/8 etc.
    fraction_map = {
        '1/4': '0.25', '3/8': '0.375', '1/2': '0.5', 
        '5/8': '0.625', '3/4': '0.75', '7/8': '0.875',
        '1/8': '0.125', '5/16': '0.3125', '7/16': '0.4375',
        '9/16': '0.5625', '11/16': '0.6875', '13/16': '0.8125'
    }
    for frac, decimal in fraction_map.items():
        if frac in query.lower():
            expanded_terms.append(decimal)
            expanded_terms.append(f"{frac} inch")
    
    # LAW 5: The "Screw Gauge" Law (10-24 -> #10, 10 gauge)
    # Handles: 6-32, 8-32, 10-24, 10-32, 12-24 etc.
    gauge_matches = re.findall(r'\b(\d{1,2})-(\d{2})\b', query)
    for gauge, tpi in gauge_matches:
        expanded_terms.append(f"#{gauge}")      # "#10"
        expanded_terms.append(f"{gauge} gauge") # "10 gauge"
    
    # LAW 6: The "Class/Grade" Law (Class 8.8 -> 8.8, Grade 8)
    class_matches = re.findall(r'\bclass\s*([\d.]+)\b', query, re.IGNORECASE)
    for val in class_matches:
        expanded_terms.append(val)              # "8.8"
        if '.' in val:
            expanded_terms.append(f"Grade {val.split('.')[0]}")  # "Grade 8"
    
    # Combine: "M16 torque" becomes "M16 torque 16 size 16 Size: 16"
    if expanded_terms:
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                unique_terms.append(term)
        
        new_query = f"{query} {' '.join(unique_terms)}"
        print(f"⚡ GOD TIER LAW APPLIED: '{original_query}'")
        print(f"   → Expanded to: '{new_query}'")
        return new_query
    
    return query

# ==============================================================================
# SMART SNIPPET BOUNDARIES - Complete sentences/rows only
# ==============================================================================

def find_boundary_left(content, pos):
    """Walk left until we hit a clean boundary (newline, pipe, or start)"""
    while pos > 0:
        char = content[pos - 1]
        # Stop at newline (new line/row)
        if char == '\n':
            break
        # Stop at pipe if we're in a table (start of cell)
        if char == '|':
            break
        pos -= 1
    return pos


def find_boundary_right(content, pos):
    """Walk right until we hit a clean boundary (newline, period, pipe, or end)"""
    length = len(content)
    while pos < length:
        char = content[pos]
        # Stop after newline
        if char == '\n':
            pos += 1  # Include the newline
            break
        # Stop after period followed by space or end (sentence boundary)
        if char == '.' and (pos + 1 >= length or content[pos + 1] in ' \n'):
            pos += 1  # Include the period
            break
        # Stop at pipe if we're in a table (end of cell) - but grab the full row
        if char == '|':
            # Look ahead to see if there's more row content
            remaining = content[pos:].split('\n')[0]
            if remaining.count('|') <= 1:  # End of row
                pos += 1
                break
        pos += 1
    return pos


def extract_smart_snippet(content, match_pos, min_length=80):
    """
    Extract a grammatically complete snippet around a match position.
    Expands to complete sentences or table rows.
    """
    # Find boundaries
    left = find_boundary_left(content, match_pos)
    right = find_boundary_right(content, match_pos)
    
    snippet = content[left:right].strip()
    
    # Safety buffer: if too short, grab more context
    if len(snippet) < min_length:
        # Try to get the previous line too
        if left > 0:
            prev_left = find_boundary_left(content, left - 1)
            snippet = content[prev_left:right].strip()
        
        # Still too short? Get the next line too
        if len(snippet) < min_length and right < len(content):
            next_right = find_boundary_right(content, right)
            snippet = content[left:next_right].strip()
    
    return snippet


def highlight_snippet(content, keywords, context_chars=75):
    """
    Find and highlight the actual answer data around keywords.
    Returns a grammatically complete snippet (full sentences/table rows).
    """
    content_lower = content.lower()
    best_snippet = None
    best_score = 0
    best_pos = 0
    
    # Priority 1: Find numeric values near keywords (the actual answer)
    value_patterns = [
        r'value[:\s]*[\d,]+',             # Value: 17000
        r'\d+\.?\d*\s*mm',                # 130mm, 12.5mm
        r'\d+\.?\d*\s*kn',                # 45kN
        r'\d+\.?\d*\s*lbf',               # 17000 lbf
        r'\|\s*[\d,]+\.?\d*\s*\|',        # | 130 |
        r':\s*[\d,]+\.?\d*\s*(?:mm|kn|lbf|psi|mpa)',  # : 130mm
        r'shear[:\s]*[\d,]+',             # Shear: 1234
        r'tension[:\s]*[\d,]+',           # Tension: 5678
    ]
    
    for pattern in value_patterns:
        matches = list(re.finditer(pattern, content_lower))
        for match in matches:
            pos = match.start()
            # Check if any keyword is nearby (within 200 chars)
            snippet_start = max(0, pos - 150)
            snippet_end = min(len(content), pos + 150)
            nearby_text = content_lower[snippet_start:snippet_end]
            
            # Score based on keyword proximity
            score = 0
            for kw in keywords:
                if kw.lower() in nearby_text:
                    score += 2
            
            # Bonus for specific patterns
            if 'size' in nearby_text:
                score += 1
            if any(s in nearby_text for s in ['1/2', 'm12', 'm10', '10-24', 'wafer']):
                score += 1
            if 'shear' in nearby_text or 'tension' in nearby_text:
                score += 2
            
            if score > best_score:
                best_score = score
                best_pos = pos
    
    # Extract smart snippet at best position
    if best_score > 0:
        best_snippet = extract_smart_snippet(content, best_pos)
    
    # Priority 2: If no value pattern found, look for keyword matches
    if not best_snippet:
        for kw in keywords:
            kw_lower = kw.lower()
            pos = content_lower.find(kw_lower)
            if pos != -1:
                # Use smart snippet extraction for keyword matches too
                best_snippet = extract_smart_snippet(content, pos)
                break
    
    # Fallback: Return first complete sentence/row if nothing found
    if not best_snippet:
        # Try to get first complete line or sentence
        first_newline = content.find('\n')
        first_period = content.find('. ')
        
        if first_newline > 0 and first_newline < 300:
            best_snippet = content[:first_newline].strip()
        elif first_period > 0 and first_period < 300:
            best_snippet = content[:first_period + 1].strip()
        else:
            best_snippet = content[:300].strip()
    
    # Clean up: Add ellipsis only at real truncation points
    if len(best_snippet) < len(content):
        # Check if we're at the start
        snippet_start_in_content = content.find(best_snippet[:30]) if len(best_snippet) >= 30 else 0
        if snippet_start_in_content > 5:
            best_snippet = "..." + best_snippet
        
        # Check if we're at the end
        if not content.strip().endswith(best_snippet.strip()[-30:]):
            best_snippet = best_snippet + "..."
    
    return best_snippet


# ==============================================================================
# HYBRID SEARCH ENGINE
# ==============================================================================

def get_embedding(text):
    """Get embedding for query"""
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
        dimensions=1536
    )
    return r.data[0].embedding


def extract_keywords(query):
    """Extract technical keywords from query for boosting"""
    query_lower = query.lower()
    found_keywords = []
    
    # Priority keywords - exact technical terms
    priority_terms = [
        "proof load", "tensile strength", "shear strength", "yield strength",
        "single shear", "double shear", "pull out", "pullout",
        "hardness", "torque", "span", "wind zone", "axial tensile"
    ]
    
    for term in priority_terms:
        if term in query_lower:
            found_keywords.append(term)
    
    # Size patterns - look for specific formats
    # Screw sizes: 10-24, 12-14, 8-18, etc.
    screw_sizes = re.findall(r'\d+-\d+', query_lower)
    found_keywords.extend(screw_sizes)
    
    # Imperial: 1/4, 1/2, 3/8, etc.
    imperial_sizes = re.findall(r'\d+/\d+(?:\s*inch)?', query_lower)
    found_keywords.extend(imperial_sizes)
    
    # Metric: M6, M8, M10, etc.
    metric_sizes = re.findall(r'm\d+', query_lower)
    found_keywords.extend(metric_sizes)
    
    # Timber sizes: 140x45, 90x45, etc.
    timber_sizes = re.findall(r'\d+x\d+', query_lower)
    found_keywords.extend(timber_sizes)
    
    # Grade patterns
    grades = re.findall(r'grade\s*\d+|class\s*[\d.]+|sg\d+|msg\d+', query_lower)
    found_keywords.extend(grades)
    
    # Product types
    product_types = ["hex nut", "hex bolt", "set screw", "lock nut", "anchor", 
                     "washer", "rafter", "joist", "bearer", "purlin",
                     "wafer head", "wafer", "sdm", "deep driller"]
    for pt in product_types:
        if pt in query_lower:
            found_keywords.append(pt)
    
    return list(set(found_keywords))  # Remove duplicates


def detect_ambiguity(query):
    """Detect if query is ambiguous and needs clarification"""
    query_lower = query.lower()
    
    # Skip clarification for very specific product queries
    # If query mentions specific product codes, sizes, or asks "what is the X"
    if re.search(r'\d+-\d+', query_lower):  # Size like 10-24
        return None
    if re.search(r'bf\d+', query_lower):  # Product code like BF1068
        return None
    if 'what is the' in query_lower or 'what are the' in query_lower:
        return None  # Direct lookup questions don't need clarification
    
    # Check for span queries without wind zone
    if re.search(r'span|rafter|joist|bearer|purlin', query_lower):
        if not re.search(r'wind zone|high wind|very high|low wind|medium wind|extra high', query_lower):
            return "wind_zone"
    
    # Check for timber size without grade
    if re.search(r'\d+x\d+', query_lower):
        if not re.search(r'sg\d+|msg\d+|timber grade', query_lower):
            if 'span' in query_lower:
                return "wind_zone"  # For span queries, wind zone is most critical
    
    return None


def hybrid_retrieve(query, top_k=20, vector_weight=0.7, keyword_weight=0.3):
    """
    Weighted Hybrid Search:
    - 70% Vector similarity (semantic understanding)
    - 30% Keyword matching (technical precision)
    - Smart source filtering based on query intent
    - GOD TIER LAWS: Technical synonym expansion
    """
    # ⚡ APPLY GOD TIER LAWS FIRST (before embedding)
    expanded_query = apply_god_tier_laws(query)
    
    # Get query embedding (using expanded query)
    emb = get_embedding(expanded_query)
    
    # Extract keywords for boosting (from BOTH original and expanded)
    keywords = extract_keywords(expanded_query)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    # Detect if query is about fasteners/Bremick products (use original query)
    query_lower = query.lower()
    fastener_terms = [
        'hex nut', 'hex bolt', 'proof load', 'tensile', 'lock nut', 
        'set screw', 'coach screw', 'anchor', 'washer', 'fastener',
        'unc', 'unf', 'metric', 'grade 5', 'grade 8', 'class 4', 'class 8',
        'm6', 'm8', 'm10', 'm12', 'm14', 'm16', 'm20', 'm24',
        '1/4', '5/16', '3/8', '7/16', '1/2', '9/16', '5/8', '3/4', '7/8', 'bremick',
        'dynabolt', 'edge distance', 'embedment', 'concrete anchor', 'masonry anchor',
        'through bolt', 'throughbolt', 'sleeve anchor', 'torque', 'installation torque'
    ]
    fastener_query = any(term in query_lower for term in fastener_terms)
    
    if fastener_query:
        # Check for specific product mentions to narrow search
        specific_product = None
        specific_material = None
        
        # Detect product type
        if 'through bolt' in query_lower or 'throughbolt' in query_lower:
            specific_product = '%Throughbolt%'
        elif 'sleeve anchor' in query_lower or 'sleeveanchor' in query_lower:
            specific_product = '%Sleeveanchor%'
        elif 'screw anchor' in query_lower or 'screwanchor' in query_lower:
            specific_product = '%Screwanchor%'
        
        # Detect material type
        if 'stainless' in query_lower:
            specific_material = '%Stainless%'
        elif 'galvanised' in query_lower or 'galvanized' in query_lower:
            specific_material = '%Galvanised%'
        elif 'zinc' in query_lower:
            specific_material = '%Zinc%'
        
        if specific_product and specific_material:
            # Search SPECIFIC product AND material first
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
            # Search SPECIFIC product source first
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
                # Fallback to all Bremick
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
            # Search all Bremick sources for general fastener queries
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
        # General query - search all documents
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
    
    # Step 2: Keyword boosting with ENHANCED torque/value matching
    scored_results = []
    
    for row in candidates:
        doc_id, content, source, page, vector_score = row
        content_lower = content.lower()
        
        # Calculate keyword score
        keyword_matches = 0
        for kw in keywords:
            if kw.lower() in content_lower:
                keyword_matches += 1
        
        # Normalize keyword score (0-1)
        keyword_score = min(keyword_matches / max(len(keywords), 1), 1.0) if keywords else 0
        
        # Weighted hybrid score
        hybrid_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
        
        # Extra boost if ALL query keywords are present
        if keywords and all(kw.lower() in content_lower for kw in keywords):
            hybrid_score += 0.15  # 15% bonus for perfect keyword match
        
        # ⚡ GOD TIER BOOST: Chunks with ACTUAL VALUES get priority
        # If looking for torque and chunk has "Installation torque (Nm)" with numbers
        if 'torque' in query_lower and 'installation torque' in content_lower:
            if re.search(r'torque.*\|\s*\d+', content_lower) or re.search(r'value:\s*\d+', content_lower):
                hybrid_score += 0.20  # 20% bonus for actual torque values
        
        # If looking for specific size and chunk has that size with values
        for size_match in re.findall(r'\bm?(\d{1,2})\b', query_lower):
            if f'size: {size_match}' in content_lower or f'| {size_match} |' in content_lower:
                if re.search(r'value:\s*\d+', content_lower):
                    hybrid_score += 0.10  # 10% bonus for size-specific values
        
        scored_results.append({
            'content': content,
            'source': source,
            'page': page,
            'vector_score': vector_score,
            'keyword_score': keyword_score,
            'hybrid_score': hybrid_score,
            'keyword_matches': keyword_matches
        })
    
    # Sort by hybrid score
    scored_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    return scored_results[:top_k], keywords


async def generate_answer(query, context_chunks, keywords, needs_clarification=None):
    """Generate answer using Gemini with STRYDA personality"""
    
    # If clarification needed, ask for it
    if needs_clarification:
        clarification = CLARIFICATION_TEMPLATES.get(needs_clarification, 
            f"I need more information to answer accurately. Please specify the {needs_clarification}.")
        return f"🔍 **Clarification Needed**\n\n{clarification}"
    
    # Build context string with scores
    context_parts = []
    for i, chunk in enumerate(context_chunks[:10], 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']} | Page {chunk['page']} | "
            f"Relevance: {chunk['hybrid_score']:.0%} (Vector: {chunk['vector_score']:.0%}, "
            f"Keywords: {chunk['keyword_matches']})]\\n{chunk['content']}"
        )
    
    context = "\n\n---\n\n".join(context_parts)
    
    user_prompt = f"""QUERY: {query}

DETECTED KEYWORDS: {', '.join(keywords) if keywords else 'None'}

RETRIEVED CONTEXT (Hybrid Search Results):
{context}

INSTRUCTIONS:
1. If the answer is in the context, provide it with EXACT citations
2. Format: "Value: [X] (Source: [filename], Page [Y])"
3. If data is not found, say "Not found in knowledge base"
4. If the query is ambiguous, ask for clarification"""

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id="stryda-rag",
        system_message=STRYDA_SYSTEM_PROMPT
    ).with_model("gemini", "gemini-2.5-flash")
    
    response = await chat.send_message(UserMessage(text=user_prompt))
    return response


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_rag_v3.py \"your query\"")
        sys.exit(1)
    
    query = sys.argv[1]
    
    print("="*80)
    print("⚡ STRYDA V3.0 RAG - HYBRID SEARCH ENGINE")
    print("   Protocol: BRAIN TRANSPLANT V1")
    print("   Search: 70% Vector + 30% Keyword Boosting")
    print("="*80)
    print(f"\n📝 QUERY: {query}\n")
    
    # Step 1: Check for ambiguity
    ambiguity = detect_ambiguity(query)
    if ambiguity:
        print(f"⚠️  AMBIGUITY DETECTED: Missing '{ambiguity}'")
        print(f"    Triggering Clarification Loop...\n")
    
    # Step 2: Extract keywords
    keywords = extract_keywords(query)
    print(f"🔑 DETECTED KEYWORDS: {keywords if keywords else 'None'}\n")
    
    # Step 3: Hybrid search
    print("="*80)
    print("📚 HYBRID SEARCH RESULTS (Top 10)")
    print("="*80)
    
    chunks, _ = hybrid_retrieve(query, top_k=15)
    
    for i, chunk in enumerate(chunks[:10], 1):
        # Use snippet highlighting instead of first 400 chars
        snippet = highlight_snippet(chunk['content'], keywords)
        print(f"\n[{i}] Source: {chunk['source']}")
        print(f"    Page: {chunk['page']}")
        print(f"    Hybrid Score: {chunk['hybrid_score']:.2%} "
              f"(Vector: {chunk['vector_score']:.2%}, Keywords: {chunk['keyword_matches']})")
        print(f"    📌 SNIPPET: {snippet}")
        print("-"*60)
    
    # Step 4: Generate answer
    print("\n" + "="*80)
    print("🤖 STRYDA ANSWER")
    print("="*80 + "\n")
    
    answer = asyncio.run(generate_answer(query, chunks, keywords, ambiguity))
    print(answer)
    
    print("\n" + "="*80)
    print("✅ RAG TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
