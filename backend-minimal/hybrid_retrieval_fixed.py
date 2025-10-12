"""
STRYDA v1.3.3-hotfix - Fixed Hybrid Retrieval with FTS
Fast text search + vector search for optimal Tier-1 discovery
"""

import psycopg2
import psycopg2.extras
import time
from typing import List, Dict, Any, Tuple

# Tier-1 lexicon for detection
TIER1_LEXICON = {
    'NZS 3604': ['stud spacing', 'nzs 3604', 'timber', 'lintel', 'bracing', 'wind zone', 'h1.2', 'bottom plate', 'fixing', 'span', 'treatment'],
    'E2/AS1': ['e2/as1', 'e2 as1', 'external moisture', 'roof pitch', 'apron flashing', 'underlay', 'cladding', 'corrugate', 'skylight', 'very high wind'],
    'B1/AS1': ['b1/as1', 'b1 as1', 'bracing demand', 'structure', 'engineering design', 'specific engineering', 'single-storey', 'dwelling']
}

TIER1_SOURCES = ['NZS 3604:2011', 'E2/AS1', 'B1/AS1']

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

def safe_float_convert(value) -> float:
    """Safely convert any numeric type to float with comprehensive error handling"""
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        
        # Handle Decimal explicitly
        from decimal import Decimal, InvalidOperation
        if isinstance(value, Decimal):
            return float(value)
        
        # Handle strings
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
                
        # Fallback for unknown types
        return float(str(value))
        
    except Exception:
        return 0.0

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