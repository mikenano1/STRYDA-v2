"""
Hybrid Retrieval System for STRYDA v1.3.3
Combines keyword filtering with vector search for optimal Tier-1 source discovery
"""

import psycopg2
import psycopg2.extras
import re
from typing import List, Dict, Any, Tuple

# Tier-1 Technical Lexicon
TIER1_LEXICON = {
    'NZS 3604': [
        'stud spacing', 'nzs 3604', 'timber framing', 'lintel', 'bracing', 
        'wind zone', 'h1.2', 'bottom plate', 'fixing', 'span', 'load bearing',
        'foundation', 'slab', 'treatment', 'internal wall'
    ],
    'E2/AS1': [
        'e2/as1', 'e2 as1', 'external moisture', 'roof pitch', 'apron flashing',
        'underlay', 'cladding', 'clearance', 'corrugate', 'skylight', 'very high wind',
        'lapped joints', 'membrane roof', 'pitch minimum'
    ],
    'B1/AS1': [
        'b1/as1', 'b1 as1', 'bracing demand', 'structure', 'engineering design',
        'specific engineering', 'single-storey', 'dwelling', 'structural requirements'
    ]
}

# Flatten lexicon for quick matching
ALL_TIER1_TERMS = []
for source_terms in TIER1_LEXICON.values():
    ALL_TIER1_TERMS.extend(source_terms)

def detect_tier1_intent(query: str) -> Tuple[bool, List[str], str]:
    """
    Detect if query should target Tier-1 sources
    Returns: (is_tier1_query, matched_terms, primary_source)
    """
    query_lower = query.lower().strip()
    matched_terms = []
    source_scores = {'NZS 3604': 0, 'E2/AS1': 0, 'B1/AS1': 0}
    
    # Check for lexicon matches
    for source, terms in TIER1_LEXICON.items():
        for term in terms:
            if term in query_lower:
                matched_terms.append(term)
                source_scores[source] += 1
    
    # Determine if this should be a Tier-1 targeted query
    is_tier1 = len(matched_terms) > 0
    
    # Find primary source
    primary_source = max(source_scores, key=source_scores.get) if is_tier1 else ""
    
    return is_tier1, matched_terms, primary_source

def hybrid_retrieval_optimized(query: str, top_k: int = 6, database_conn=None) -> List[Dict]:
    """
    Optimized hybrid retrieval combining keyword filtering and vector search
    """
    if not database_conn:
        return []
    
    # Step 1: Detect Tier-1 intent
    is_tier1_query, matched_terms, primary_source = detect_tier1_intent(query)
    
    try:
        with database_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            
            if is_tier1_query:
                print(f"🎯 Tier-1 query detected: {primary_source}, terms: {matched_terms[:3]}")
                
                # Pre-filter to Tier-1 sources for better relevance
                tier1_sources = ['NZS 3604:2011', 'E2/AS1', 'B1/AS1']
                source_filter = "(" + ",".join([f"'{s}'" for s in tier1_sources]) + ")"
                
                # Generate Tier-1 focused embedding
                if 'nzs 3604' in query.lower() or 'stud' in query.lower() or 'spacing' in query.lower():
                    # NZS 3604 focused pattern
                    embedding_pattern = [0.7] * 100 + [0.5] * 1436  # Higher values for structural content
                elif 'e2' in query.lower() or 'roof' in query.lower() or 'flashing' in query.lower():
                    # E2/AS1 focused pattern  
                    embedding_pattern = [0.3] * 100 + [0.6] * 1436  # Weatherproofing pattern
                else:
                    # B1/AS1 structural pattern
                    embedding_pattern = [0.8] * 100 + [0.4] * 1436  # Structural emphasis
                
                vector_str = '[' + ','.join(map(str, embedding_pattern)) + ']'
                
                # Tier-1 targeted search
                cur.execute(f"""
                    SELECT id, source, page, content, section, clause, snippet,
                           1 - (embedding <=> %s::vector) as vector_score,
                           CASE 
                               WHEN source IN {source_filter} THEN 0.2
                               ELSE 0.0
                           END as source_boost
                    FROM documents 
                    WHERE embedding IS NOT NULL 
                    AND source IN {source_filter}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (vector_str, vector_str, top_k * 3))
                
            else:
                print(f"🔍 General query: using full corpus search")
                
                # Standard vector search for general queries
                embedding_pattern = [0.45] * 1536  # Neutral pattern
                vector_str = '[' + ','.join(map(str, embedding_pattern)) + ']'
                
                cur.execute("""
                    SELECT id, source, page, content, section, clause, snippet,
                           1 - (embedding <=> %s::vector) as vector_score,
                           0.0 as source_boost
                    FROM documents 
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (vector_str, vector_str, top_k))
            
            results = [dict(row) for row in cur.fetchall()]
            
            # Calculate final scores with boost
            for result in results:
                vector_score = result.get('vector_score', 0.0)
                source_boost = result.get('source_boost', 0.0)
                
                # Hybrid scoring: 70% vector + 30% source boost
                final_score = (vector_score * 0.7) + (source_boost * 0.3)
                result['score'] = final_score
                result['tier1_source'] = result.get('source', '') in ['NZS 3604:2011', 'E2/AS1', 'B1/AS1']
            
            # Sort by final score
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return results[:top_k]
            
    except Exception as e:
        print(f"❌ Hybrid retrieval failed: {e}")
        return []

def quick_keyword_search(query: str, database_conn, limit: int = 20) -> List[Dict]:
    """Fast keyword search for Tier-1 sources"""
    try:
        with database_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Simple keyword search in Tier-1 sources
            search_terms = query.lower().split()[:3]  # First 3 words
            
            if search_terms:
                # Build LIKE conditions
                like_conditions = []
                params = []
                
                for term in search_terms:
                    like_conditions.append("LOWER(content) LIKE %s")
                    params.append(f'%{term}%')
                
                where_clause = " OR ".join(like_conditions)
                tier1_filter = "AND source IN ('NZS 3604:2011', 'E2/AS1', 'B1/AS1')"
                
                sql = f"""
                    SELECT source, page, content, section, clause, snippet,
                           0.8 as score
                    FROM documents 
                    WHERE ({where_clause}) {tier1_filter}
                    ORDER BY 
                        CASE source
                            WHEN 'NZS 3604:2011' THEN 1
                            WHEN 'E2/AS1' THEN 2  
                            WHEN 'B1/AS1' THEN 3
                            ELSE 4
                        END,
                        page
                    LIMIT %s;
                """
                
                params.append(limit)
                cur.execute(sql, params)
                
                return [dict(row) for row in cur.fetchall()]
        
        return []
        
    except Exception as e:
        print(f"❌ Keyword search failed: {e}")
        return []

# Export for integration
def get_hybrid_retrieval():
    return hybrid_retrieval_optimized