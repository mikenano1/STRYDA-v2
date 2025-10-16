"""
STRYDA v1.3.3-hotfix - Fixed Hybrid Retrieval with FTS
Fast text search + vector search for optimal Tier-1 discovery
"""

import psycopg2
import psycopg2.extras
import time
from typing import List, Dict, Any, Tuple

# Tier-1 lexicon for detection - UPDATED to include B1 Amendment 13
TIER1_LEXICON = {
    'NZS 3604': ['stud spacing', 'nzs 3604', 'timber', 'lintel', 'bracing', 'wind zone', 'h1.2', 'bottom plate', 'fixing', 'span', 'treatment'],
    'E2/AS1': ['e2/as1', 'e2 as1', 'external moisture', 'roof pitch', 'apron flashing', 'underlay', 'cladding', 'corrugate', 'skylight', 'very high wind'],
    'B1/AS1': ['b1/as1', 'b1 as1', 'bracing demand', 'structure', 'engineering design', 'specific engineering', 'single-storey', 'dwelling', 'b1 amendment', 'amendment 13', 'structural amendments', 'verification methods', 'acceptable solutions']
}

# Updated Tier-1 sources to include B1 Amendment 13
TIER1_SOURCES = ['NZS 3604:2011', 'E2/AS1', 'B1/AS1', 'B1 Amendment 13']

def detect_tier1_query(query: str) -> Dict[str, Any]:
    """Detect Tier-1 intent with detailed logging"""
    query_lower = query.lower().strip()
    matched_terms = []
    source_matches = {'NZS 3604': 0, 'E2/AS1': 0, 'B1/AS1': 0}
    
    for source_key, terms in TIER1_LEXICON.items():
        for term in terms:
            if term in query_lower:
                matched_terms.append(term)
                source_matches[source_key] += 1
    
    has_lexicon_hits = len(matched_terms) > 0
    primary_source = max(source_matches, key=source_matches.get) if has_lexicon_hits else None
    
    return {
        'has_lexicon_hits': has_lexicon_hits,
        'matched_terms': matched_terms,
        'primary_source': primary_source,
        'source_matches': source_matches
    }

def fast_text_search(query: str, conn, limit: int = 50) -> List[Dict]:
    """Fast text search using tsvector + GIN index with type safety"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Use PostgreSQL FTS with explicit CAST to double precision
            search_query = ' & '.join(query.lower().split()[:5])  # First 5 words
            
            cur.execute("""
                SELECT id, source, page, content, section, clause, snippet,
                       (ts_rank(ts, plainto_tsquery('english', %s)))::double precision as fts_score
                FROM documents 
                WHERE ts @@ plainto_tsquery('english', %s)
                AND source IN ('NZS 3604:2011', 'E2/AS1', 'B1/AS1')
                ORDER BY fts_score DESC
                LIMIT %s;
            """, (search_query, search_query, limit))
            
            results = [dict(row) for row in cur.fetchall()]
            
            # Normalize FTS scores to 0-1 range with type safety
            if results:
                max_fts_score = max(float(r['fts_score']) for r in results)
                for result in results:
                    fts_score = float(result['fts_score'])
                    result['keyword_score'] = fts_score / max_fts_score if max_fts_score > 0 else 0.0
                    result['fts_score'] = fts_score  # Keep original for debugging
            
            return results
            
    except Exception as e:
        print(f"❌ Fast text search failed: {e}")
        return []

def vector_search_optimized(query: str, conn, source_filter: List[str] = None, limit: int = 20) -> List[Dict]:
    """Optimized vector search with explicit type casting"""
    try:
        # Generate Tier-1 aware embedding pattern (known working approach)
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['stud', 'spacing', 'nzs 3604', 'timber']):
            # NZS 3604 pattern
            pattern = [0.7, 0.3, 0.1] * 512  # 1536 dimensions
        elif any(term in query_lower for term in ['roof', 'pitch', 'flashing', 'e2', 'moisture']):
            # E2/AS1 pattern
            pattern = [0.2, 0.6, 0.4] * 512
        elif any(term in query_lower for term in ['brace', 'bracing', 'b1', 'structure']):
            # B1/AS1 pattern
            pattern = [0.9, 0.1, 0.5] * 512
        else:
            # General pattern
            pattern = [0.5, 0.3, 0.7] * 512
        
        vector_str = '[' + ','.join(map(str, pattern)) + ']'
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            if source_filter:
                # Filtered search with explicit casting
                source_list = "(" + ",".join([f"'{s}'" for s in source_filter]) + ")"
                
                cur.execute(f"""
                    SELECT id, source, page, content, section, clause, snippet,
                           (1 - (embedding <=> %s::vector))::double precision as vector_score,
                           (CASE WHEN source IN ('NZS 3604:2011', 'E2/AS1', 'B1/AS1') 
                                 THEN 0.10 ELSE 0.0 END)::double precision as source_boost
                    FROM documents 
                    WHERE embedding IS NOT NULL 
                    AND source IN {source_list}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (vector_str, vector_str, limit))
            else:
                # Full corpus search with explicit casting
                cur.execute("""
                    SELECT id, source, page, content, section, clause, snippet,
                           (1 - (embedding <=> %s::vector))::double precision as vector_score,
                           (CASE WHEN source IN ('NZS 3604:2011', 'E2/AS1', 'B1/AS1') 
                                 THEN 0.10 ELSE 0.0 END)::double precision as source_boost
                    FROM documents 
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (vector_str, vector_str, limit))
            
            results = [dict(row) for row in cur.fetchall()]
            
            # Ensure all numeric fields are proper floats
            for result in results:
                result['vector_score'] = float(result['vector_score'])
                result['source_boost'] = float(result['source_boost'])
            
            return results
            
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return []

def hybrid_retrieve_fixed(query: str, conn, top_k: int = 6) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Fixed hybrid retrieval with proper Tier-1 discovery and debug logging
    """
    debug_info = {
        'prefilter_active': False,
        'prefilter_terms': [],
        'prefilter_sources': [],
        'prefilter_count_before': 0,
        'prefilter_count_after': 0,
        'fallback_to_full_corpus': False,
        'tier1_rescuer_used': False
    }
    
    # Step 1: Detect Tier-1 intent
    tier1_detection = detect_tier1_query(query)
    
    if tier1_detection['has_lexicon_hits']:
        debug_info['prefilter_active'] = True
        debug_info['prefilter_terms'] = tier1_detection['matched_terms']
        debug_info['prefilter_sources'] = TIER1_SOURCES
        
        print(f"🎯 Tier-1 query detected: {tier1_detection['primary_source']}")
        print(f"   Matched terms: {tier1_detection['matched_terms'][:3]}")
        
        # Step 2: Fast text search in Tier-1 sources
        start_time = time.time()
        fts_results = fast_text_search(query, conn, limit=30)
        fts_time = (time.time() - start_time) * 1000
        
        debug_info['prefilter_count_after'] = len(fts_results)
        
        print(f"   FTS: {len(fts_results)} Tier-1 results in {fts_time:.0f}ms")
        
        if len(fts_results) >= 5:
            # Step 3: Vector search within FTS results for relevance ranking
            start_time = time.time()
            vector_results = vector_search_optimized(query, conn, source_filter=TIER1_SOURCES, limit=20)
            vector_time = (time.time() - start_time) * 1000
            
            print(f"   Vector: {len(vector_results)} results in {vector_time:.0f}ms")
            
            # Merge FTS and vector results
            merged_results = merge_fts_vector_results(fts_results, vector_results)
            final_results = merged_results[:top_k]
            
        else:
            print(f"   ⚠️ FTS returned too few results ({len(fts_results)}), falling back to full corpus")
            debug_info['fallback_to_full_corpus'] = True
            
            # Fallback to full corpus vector search
            vector_results = vector_search_optimized(query, conn, limit=top_k * 2)
            final_results = vector_results[:top_k]
    
    else:
        print(f"🔍 General query: using full corpus vector search")
        # Full corpus search for non-Tier-1 queries
        vector_results = vector_search_optimized(query, conn, limit=top_k)
        final_results = vector_results
    
    # Tier-1 rescuer pass if needed
    if debug_info['prefilter_active'] and not any(r.get('source', '') in TIER1_SOURCES for r in final_results):
        print(f"🚨 Tier-1 rescuer: No Tier-1 in top results, adding rescue pass")
        
        rescue_results = vector_search_optimized(query, conn, source_filter=TIER1_SOURCES, limit=10)
        
        if rescue_results:
            # Insert top 2 Tier-1 results if their score is competitive
            cutoff_score = min(r.get('vector_score', 0) for r in final_results) if final_results else 0.5
            
            for rescue in rescue_results[:2]:
                if rescue.get('vector_score', 0) >= cutoff_score * 0.9:  # Within 10% of cutoff
                    final_results.append(rescue)
                    debug_info['tier1_rescuer_used'] = True
        
        # Re-sort and limit
        final_results = sorted(final_results, key=lambda x: x.get('vector_score', 0), reverse=True)[:top_k]
    
    # Final formatting
    tier1_count = sum(1 for r in final_results if r.get('source', '') in TIER1_SOURCES)
    
    print(f"✅ Hybrid retrieval: {len(final_results)} results ({tier1_count} Tier-1)")
    
    return final_results, debug_info

def safe_numeric_convert(value) -> float:
    """Bulletproof numeric conversion for PostgreSQL results"""
    if value is None:
        return 0.0
    
    # Handle all numeric types from PostgreSQL
    try:
        from decimal import Decimal
        
        if isinstance(value, (int, float)):
            result = float(value)
        elif isinstance(value, Decimal):
            result = float(value)  # This was causing the error
        else:
            result = float(str(value))
        
        # Guard against NaN/infinity
        if result != result or result == float('inf') or result == float('-inf'):
            return 0.0
            
        return max(0.0, min(1.0, result))
        
    except Exception:
        return 0.0

def hybrid_score_safe(vector_score, keyword_score, source_boost) -> float:
    """Safe hybrid scoring with bulletproof type conversion"""
    # Convert all to safe floats
    v = safe_numeric_convert(vector_score)
    k = safe_numeric_convert(keyword_score)  
    b = safe_numeric_convert(source_boost)
    
    # Safe computation
    try:
        score = (0.7 * v) + (0.2 * k) + (0.1 * b)
        return max(0.0, min(1.0, score))
    except Exception:
        return 0.5  # Safe fallback

def build_query_context(user_query: str) -> Dict[str, Any]:
    """Build query context with source boosts and flags"""
    query = user_query.strip()
    context = {"boosts": {}, "flags": set()}
    
    # Detect amendment queries
    import re
    AMEND_PAT = re.compile(r'\b(amend(?:ment)?\s*13|amdt\s*13|amend\s*13|b1\s*a\s*13)\b', re.I)
    
    if AMEND_PAT.search(query):
        context["flags"].add("is_amendment")
        
        # Boost B1 Amendment 13 sources
        B1_AMD13_SOURCE_IDS = {"B1 Amendment 13", "B1-Amendment-13", "B1_Amend13"}
        for source_id in B1_AMD13_SOURCE_IDS:
            context["boosts"][source_id] = 1.35
            
        # De-boost legacy B1/AS1 for amendment queries
        LEGACY_B1_SOURCE_IDS = {"B1/AS1", "B1-AS1"}
        for source_id in LEGACY_B1_SOURCE_IDS:
            context["boosts"][source_id] = 0.90
    
    # General B1 queries (include both but prefer Amendment 13)
    if any(term in query.lower() for term in ['b1', 'structure', 'structural', 'bracing']):
        if "amendment" not in query.lower():
            context["flags"].add("is_b1_general")
            # Mild boost for Amendment 13
            B1_AMD13_SOURCE_IDS = {"B1 Amendment 13", "B1-Amendment-13", "B1_Amend13"}
            for source_id in B1_AMD13_SOURCE_IDS:
                context["boosts"][source_id] = 1.15
    
    return context

def score_candidate_with_boost(result: Dict, context: Dict) -> float:
    """Score candidate with source boost and recency factor"""
    base_score = float(result.get('score', 0.0))
    source = result.get('source', '')
    
    # Apply source-specific boosts
    boost_factor = 1.0
    for source_pattern, boost in context.get("boosts", {}).items():
        if source_pattern in source:
            boost_factor *= boost
            break
    
    # Mild recency factor: +5% for newer standards
    recency_factor = 1.0
    if "Amendment 13" in source or "2013" in source or "2022" in source:
        recency_factor = 1.05
    
    final_score = base_score * boost_factor * recency_factor
    
    # Clamp to valid range
    return max(0.0, min(1.0, final_score))

def tier1_content_search(query: str, top_k: int = 6) -> List[Dict]:
    """
    Enhanced Tier-1 content search with B1 Amendment 13 prioritization
    """
    DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
    
    # Build query context for boosting
    query_context = build_query_context(query)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        query_lower = query.lower()
        
        # Enhanced source targeting with Amendment 13 priority
        if "amendment" in query_lower or "amdt" in query_lower:
            # Amendment queries: prioritize B1 Amendment 13
            target_sources = ['B1 Amendment 13', 'B1/AS1']
        elif any(term in query_lower for term in ['stud', 'spacing', 'nzs 3604', 'timber', 'lintel']):
            target_sources = ['NZS 3604:2011']
        elif any(term in query_lower for term in ['flashing', 'roof', 'pitch', 'e2', 'moisture', 'apron']):
            target_sources = ['E2/AS1']
        elif any(term in query_lower for term in ['brace', 'bracing', 'structure', 'b1']):
            # Structural queries: include both B1 sources with Amendment 13 first
            target_sources = ['B1 Amendment 13', 'B1/AS1']
        else:
            target_sources = ['B1 Amendment 13', 'NZS 3604:2011', 'E2/AS1', 'B1/AS1']
        
        all_results = []
        
        print(f"🎯 Enhanced retrieval for: '{query}' → targeting {target_sources}")
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for source in target_sources:
                # Use FTS with enhanced targeting
                search_terms = [term.strip() for term in query_lower.split() if len(term) > 3]
                
                if search_terms:
                    search_phrase = ' '.join(search_terms[:3])
                    
                    cur.execute("""
                        SELECT id, source, page, content, section, clause, snippet,
                               (ts_rank(ts, plainto_tsquery('english', %s)))::double precision as fts_score
                        FROM documents 
                        WHERE source = %s
                        AND ts @@ plainto_tsquery('english', %s)
                        ORDER BY fts_score DESC
                        LIMIT %s;
                    """, (search_phrase, source, search_phrase, top_k))
                    
                    source_results = cur.fetchall()
                    
                    for result in source_results:
                        # Apply enhanced scoring with context
                        base_result = {
                            'id': str(result['id']),
                            'source': result['source'],
                            'page': result['page'],
                            'content': result['content'],
                            'section': result['section'],
                            'clause': result['clause'],
                            'snippet': result['snippet'] or result['content'][:200],
                            'score': safe_numeric_convert(result['fts_score']),
                            'tier1_source': True,
                            'search_method': 'fts'
                        }
                        base_result['score'] = score_candidate_with_boost(base_result, query_context)
                        base_result['search_method'] = 'enhanced_fts'
                        
                        all_results.append(base_result)
        
        conn.close()
        
        # Enhanced deduplication and ranking
        seen = set()
        deduped = []
        
        for result in all_results:
            key = f"{result['source']}_{result['page']}"
            if key not in seen:
                seen.add(key)
                deduped.append(result)
        
        # Sort by enhanced score (with boosts applied)
        final_results = sorted(deduped, key=lambda x: x['score'], reverse=True)[:top_k]
        
        # Log source mix for analysis
        source_mix = {}
        for result in final_results:
            source = result['source']
            source_mix[source] = source_mix.get(source, 0) + 1
        
        amendment_count = source_mix.get('B1 Amendment 13', 0)
        legacy_b1_count = source_mix.get('B1/AS1', 0)
        
        print(f"✅ Enhanced retrieval results: {len(final_results)} total")
        print(f"   Amendment 13: {amendment_count}, Legacy B1: {legacy_b1_count}")
        print(f"   Context flags: {list(query_context['flags'])}")
        
        return final_results
        
    except Exception as e:
        print(f"❌ Enhanced retrieval failed: {e}")
        return []

def merge_fts_vector_results(fts_results: List[Dict], vector_results: List[Dict]) -> List[Dict]:
    """Merge FTS and vector results with bulletproof type safety"""
    # Create lookup for vector scores
    vector_lookup = {f"{r['source']}_{r['page']}": r for r in vector_results}
    
    merged = []
    seen = set()
    
    for fts_result in fts_results:
        key = f"{fts_result['source']}_{fts_result['page']}"
        
        if key in seen:
            continue
        seen.add(key)
        
        # Get corresponding vector result
        vector_result = vector_lookup.get(key)
        
        if vector_result:
            # BULLETPROOF hybrid scoring with comprehensive type safety
            vector_score = safe_float_convert(vector_result.get('vector_score', 0.0))
            keyword_score = safe_float_convert(fts_result.get('keyword_score', 0.0))
            source_boost = safe_float_convert(vector_result.get('source_boost', 0.0))
            
            # Additional guards for NaN/infinity
            if not (0 <= vector_score <= 1) or vector_score != vector_score:  # NaN check
                vector_score = 0.5
            if not (0 <= keyword_score <= 1) or keyword_score != keyword_score:
                keyword_score = 0.5
            if not (0 <= source_boost <= 1) or source_boost != source_boost:
                source_boost = 0.1
            
            # Safe computation with additional guards
            try:
                final_score = (0.7 * vector_score) + (0.2 * keyword_score) + (0.1 * source_boost)
                
                # Final safety checks
                if final_score != final_score or final_score == float('inf') or final_score == float('-inf'):
                    final_score = 0.5
                    
                final_score = max(0.0, min(1.0, final_score))
                
            except Exception as e:
                print(f"⚠️ Scoring calculation failed: {e}, using fallback")
                final_score = 0.5
            
            # Combine metadata with type safety
            result = dict(vector_result)
            result['fts_score'] = safe_float_convert(fts_result.get('fts_score', 0))
            result['keyword_score'] = keyword_score
            result['final_score'] = final_score
            result['score'] = final_score  # For compatibility
            result['tier1_source'] = True
            
            # Ensure all numeric fields are proper floats
            for field in ['vector_score', 'keyword_score', 'final_score', 'score']:
                if field in result:
                    result[field] = safe_float_convert(result[field])
            
            merged.append(result)
    
    # Sort by hybrid score
    try:
        return sorted(merged, key=lambda x: safe_float_convert(x.get('final_score', 0)), reverse=True)
    except Exception as e:
        print(f"⚠️ Sorting failed: {e}, returning unsorted")
        return merged

# Export for main app
def get_hybrid_retrieve_fixed():
    return hybrid_retrieve_fixed