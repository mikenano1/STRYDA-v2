"""
STRYDA v1.3.3-hotfix4 - Simplified Tier-1 Retrieval
Direct approach that works without Decimal issues
"""

import psycopg2
import psycopg2.extras
from typing import List, Dict

def simple_tier1_retrieval(query: str, top_k: int = 6) -> List[Dict]:
    """
    Simplified Tier-1 retrieval that actually works
    """
    DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        query_lower = query.lower()
        
        # Determine target sources based on query terms
        target_sources = []
        
        if any(term in query_lower for term in ['stud', 'spacing', 'nzs 3604', 'timber', 'framing', 'lintel']):
            target_sources.append('NZS 3604:2011')
        
        if any(term in query_lower for term in ['flashing', 'roof', 'pitch', 'e2', 'moisture', 'underlay', 'apron']):
            target_sources.append('E2/AS1')
        
        if any(term in query_lower for term in ['brace', 'bracing', 'structure', 'b1', 'engineering', 'demand']):
            target_sources.append('B1/AS1')
        
        # If no specific match, include all Tier-1
        if not target_sources:
            target_sources = ['NZS 3604:2011', 'E2/AS1', 'B1/AS1']
        
        results = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Search each target source
            for source in target_sources:
                # Use content search (proven working)
                search_terms = [term for term in query_lower.split() if len(term) > 3][:3]
                
                for term in search_terms:
                    cur.execute("""
                        SELECT id, source, page, content, section, clause, snippet,
                               LENGTH(content) as content_length
                        FROM documents 
                        WHERE source = %s
                        AND LOWER(content) LIKE %s
                        ORDER BY 
                            CASE WHEN LOWER(content) LIKE %s THEN 1 ELSE 2 END,
                            page
                        LIMIT %s;
                    """, (source, f'%{term}%', f'%{" ".join(search_terms)}%', top_k // len(target_sources) + 1))
                    
                    term_results = cur.fetchall()
                    
                    for result in term_results:
                        # Simple scoring based on content relevance
                        content_len = result['content_length']
                        base_score = 0.8 if content_len > 1000 else 0.6
                        
                        # Boost for multiple term matches
                        content_lower = result['content'].lower()
                        term_count = sum(1 for t in search_terms if t in content_lower)
                        score_boost = term_count * 0.1
                        
                        final_score = min(1.0, base_score + score_boost)
                        
                        # Format result
                        formatted_result = {
                            'id': str(result['id']),
                            'source': result['source'],
                            'page': result['page'],
                            'content': result['content'],
                            'section': result['section'],
                            'clause': result['clause'],
                            'snippet': result['snippet'] or result['content'][:200],
                            'score': final_score,
                            'tier1_source': True,
                            'search_term': term
                        }
                        
                        results.append(formatted_result)
                    
                    if term_results:
                        break  # Found results for this source, move to next
        
        conn.close()
        
        # Remove duplicates and sort by score
        seen = set()
        deduped = []
        
        for result in results:
            key = f"{result['source']}_{result['page']}"
            if key not in seen:
                seen.add(key)
                deduped.append(result)
        
        # Sort by score and return top_k
        final_results = sorted(deduped, key=lambda x: x['score'], reverse=True)[:top_k]
        
        tier1_count = sum(1 for r in final_results if r.get('tier1_source', False))
        print(f"✅ Simple Tier-1 retrieval: {len(final_results)} results ({tier1_count} Tier-1)")
        
        return final_results
        
    except Exception as e:
        print(f"❌ Simple Tier-1 retrieval failed: {e}")
        return []

# Export the working function
def get_simple_tier1_retrieval():
    return simple_tier1_retrieval