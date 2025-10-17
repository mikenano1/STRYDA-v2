"""
STRYDA v1.3.3-hotfix4 - Simplified Tier-1 Retrieval
Direct approach that works without Decimal issues
"""

import psycopg2
import psycopg2.extras
import re
from typing import List, Dict

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
        
        # Check for B1 Amendment 13 queries
        if any(term in query_lower for term in ['amendment 13', 'b1 amendment', 'verification methods']):
            target_sources.append('B1 Amendment 13')
        
        # If no specific match, include all Tier-1
        if not target_sources:
            target_sources = ['NZS 3604:2011', 'E2/AS1', 'B1/AS1', 'B1 Amendment 13']
        
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
        
        # Apply ranking bias based on query patterns
        bias_weights = detect_b1_amendment_bias(query)
        bias_applied = False
        if bias_weights:
            print(f"🎯 Applying ranking bias: {bias_weights}")
            deduped = apply_ranking_bias(deduped, bias_weights)
            bias_applied = True
            
            # Log telemetry for bias application
            bias_count = sum(1 for r in deduped if r.get('bias_applied', False))
            print(f"[telemetry] ranking_bias applied={bias_applied} weights={bias_weights} affected_results={bias_count}/{len(deduped)}")
        
        # Sort by score and return top_k
        final_results = sorted(deduped, key=lambda x: x['score'], reverse=True)[:top_k]
        
        tier1_count = sum(1 for r in final_results if r.get('tier1_source', False))
        
        # Log source distribution after bias
        source_mix = {}
        for result in final_results:
            source = result['source']
            source_mix[source] = source_mix.get(source, 0) + 1
        
        print(f"✅ Simple Tier-1 retrieval: {len(final_results)} results ({tier1_count} Tier-1)")
        print(f"📊 Retrieval source mix for '{query[:50]}...': {source_mix}")
        
        # Log B1 Amendment 13 vs Legacy B1 distribution
        amendment_count = source_mix.get('B1 Amendment 13', 0)
        legacy_count = source_mix.get('B1/AS1', 0)
        print(f"   B1 Amendment 13: {amendment_count}, Legacy B1: {legacy_count}")
        
        return final_results
        
    except Exception as e:
        print(f"❌ Simple Tier-1 retrieval failed: {e}")
        return []

# Export the working function
def get_simple_tier1_retrieval():
    return simple_tier1_retrieval