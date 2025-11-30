"""
STRYDA Source Preference Helper
Selects the preferred document when multiple versions exist for a code family
"""

from typing import List, Dict, Optional

def get_preferred_document_for_code(code_prefix: str, candidate_docs: List[Dict]) -> Optional[Dict]:
    """
    Select the preferred document for a code family
    
    Priority order:
    1. acceptable_solution_current (priority ~90)
    2. verification_method_current (priority ~85)
    3. acceptable_solution_legacy (priority ~70)
    4. Highest priority remaining
    
    Args:
        code_prefix: Code family (e.g., "E2", "H1", "C/AS", "NZS 3604")
        candidate_docs: List of documents with metadata
    
    Returns:
        Preferred document or None
    """
    
    # Filter to code family matches
    matches = []
    code_lower = code_prefix.lower()
    
    for doc in candidate_docs:
        source = doc.get('source', '').lower()
        doc_type = doc.get('doc_type', '')
        
        # Match on source name or doc_type
        if code_lower in source or (code_prefix.upper() in doc.get('source', '')):
            matches.append(doc)
        elif code_prefix == "C/AS" and (source.startswith('c-as') or source.startswith('c/as')):
            matches.append(doc)
        elif code_prefix == "NZS 3604" and '3604' in source:
            matches.append(doc)
    
    if not matches:
        return None
    
    # Sort by preference
    def preference_key(doc):
        doc_type = doc.get('doc_type', '')
        priority = doc.get('priority', 0)
        
        # Primary ordering by doc_type
        type_order = {
            'acceptable_solution_current': 1,
            'verification_method_current': 2,
            'industry_code_of_practice': 3,
            'acceptable_solution_legacy': 4,
            'nz_standard': 5,
            'handbook_guide': 6,
            'unclassified': 7
        }
        
        type_rank = type_order.get(doc_type, 8)
        
        # Secondary ordering by priority (higher is better, so negate)
        return (type_rank, -priority)
    
    sorted_matches = sorted(matches, key=preference_key)
    return sorted_matches[0]

def select_preferred_sources(all_docs: List[Dict], intent: str) -> List[Dict]:
    """
    Given all retrieved docs, select preferred sources per code family
    
    For compliance intents: strongly prefer current over legacy
    For product/general intents: allow guides and manufacturer docs to surface
    """
    
    # Group by code family
    code_families = {
        'E2': [],
        'E1': [],
        'E3': [],
        'H1': [],
        'C/AS': [],
        'F4': [],
        'F6': [],
        'F7': [],
        'G12': [],
        'G13': [],
        'NZS 3604': [],
        'NZS 4229': [],
        'B1': []
    }
    
    ungrouped = []
    
    for doc in all_docs:
        source = doc.get('source', '')
        matched = False
        
        for code in code_families.keys():
            if code.lower() in source.lower() or code.replace('/', '-').lower() in source.lower():
                code_families[code].append(doc)
                matched = True
                break
        
        if not matched:
            ungrouped.append(doc)
    
    # Select preferred from each family
    preferred_docs = []
    
    for code, docs in code_families.items():
        if docs:
            preferred = get_preferred_document_for_code(code, docs)
            if preferred:
                preferred_docs.append(preferred)
                
                # Log selection
                print(f"[source_select] code={code} intent={intent} preferred={preferred['source']} "
                      f"(doc_type={preferred.get('doc_type')}, priority={preferred.get('priority')})")
    
    # Add ungrouped docs
    preferred_docs.extend(ungrouped)
    
    return preferred_docs
