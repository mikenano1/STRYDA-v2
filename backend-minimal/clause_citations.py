"""
STRYDA Clause-Level Citation System v2
Enhanced citations with clause/table/figure specificity
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

class LocatorType(str, Enum):
    CLAUSE = "clause"
    TABLE = "table" 
    FIGURE = "figure"
    SECTION = "section"
    PAGE = "page"

class ClauseCitation:
    """Enhanced citation with clause-level metadata"""
    
    def __init__(self, doc: Dict[str, Any], query: str = ""):
        self.id = f"cite_{doc.get('id', '')[:8]}"
        self.source = doc.get('source', 'Unknown')
        self.page = doc.get('page', 0)
        self.content = doc.get('content', '')
        self.snippet = doc.get('snippet', '')
        self.score = doc.get('score', 0.0)
        self.query = query
        
        # Extract clause-level metadata
        self.clause_id, self.clause_title, self.locator_type = self._extract_clause_info()
        self.anchor = self._build_anchor()
        self.confidence = self._calculate_confidence()
    
    def _extract_clause_info(self) -> Tuple[Optional[str], Optional[str], LocatorType]:
        """Enhanced clause extraction with table/figure priority"""
        content = self.content or self.snippet or ""
        query_lower = self.query.lower()
        
        # FORCE TABLE MODE for table-related queries
        force_table_mode = any(term in query_lower for term in ['table', 'span', 'schedule', 'joist span', 'maximum span'])
        
        # ENHANCED TABLE detection (HIGHEST PRIORITY)
        table_patterns = [
            r'(?:^|\s)Table\s+(\d+(?:\.\d+)*)\b.*?[:\-—]?\s*(.{1,80})?',
            r'(?:^|\s)TABLE\s+(\d+(?:\.\d+)*)\b.*?[:\-—]?\s*(.{1,80})?',
        ]
        
        table_matches = []
        for pattern in table_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                table_id = match.group(1)
                table_title = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
                
                # Enhanced table title extraction
                table_title = re.sub(r'^[:\-—\s]*', '', table_title)
                table_title = table_title.split('\n')[0].strip()
                
                # Score based on query relevance
                score = 0.7
                if force_table_mode:
                    score += 0.2  # Boost when table explicitly requested
                if any(term in table_title.lower() for term in ['joist', 'span', 'spacing', 'beam']):
                    score += 0.1  # Boost for structural terms
                
                table_matches.append((table_id, table_title or f"Table {table_id}", score))
        
        # Return highest scoring table if found
        if table_matches:
            best_table = max(table_matches, key=lambda x: x[2])
            return best_table[0], best_table[1], LocatorType.TABLE
        
        # FIGURE detection (SECOND PRIORITY) - only if no tables or figure explicitly mentioned
        if not force_table_mode or 'figure' in query_lower:
            figure_patterns = [
                r'(?:^|\s)Figure\s+(\d+(?:\.\d+)*)\b.*?[:\-—]?\s*(.{1,80})?',
                r'(?:^|\s)FIGURE\s+(\d+(?:\.\d+)*)\b.*?[:\-—]?\s*(.{1,80})?',
            ]
            
            for pattern in figure_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    figure_id = match.group(1)
                    figure_title = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
                    
                    figure_title = re.sub(r'^[:\-—\s]*', '', figure_title)
                    figure_title = figure_title.split('\n')[0].strip()[:45]
                    
                    return figure_id, figure_title or f"Figure {figure_id}", LocatorType.FIGURE
        
        # CLAUSE detection (THIRD PRIORITY) - enhanced with negative lookbehind
        clause_patterns = [
            r'(?<!Table\s)(?<!Figure\s)(?<!table\s)(?<!figure\s)(\d+(?:\.\d+){1,3})\s*[:\-—]?\s*(.{1,60})?',
            r'([A-H]\d+(?:/[A-Z]+\d+)?)\s*[:\-—]?\s*(.{1,60})?',  # B1/AS1, E2/AS1
        ]
        
        for pattern in clause_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                clause_id = match.group(1)
                clause_title = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
                
                clause_title = re.sub(r'^[:\-—\s]*', '', clause_title)
                clause_title = clause_title.split('\n')[0].strip()[:45]
                
                return clause_id, clause_title or f"Clause {clause_id}", LocatorType.CLAUSE
        
        # SECTION heading detection (FOURTH PRIORITY)
        section_patterns = [
            r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{5,50})',  # "7.1 FLOOR JOISTS"
        ]
        
        lines = content.split('\n')[:15]
        for line in lines:
            line = line.strip()
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    section_id = match.group(1)
                    section_title = match.group(2)[:45]
                    return section_id, section_title, LocatorType.SECTION
        
        # PAGE-level fallback (lowest priority)
        return None, None, LocatorType.PAGE
    
    def _build_anchor(self) -> Optional[str]:
        """Build stable anchor for deep linking"""
        if not self.clause_id:
            return None
        
        # Normalize source for anchor
        source_slug = re.sub(r'[^a-zA-Z0-9]', '_', self.source.lower())
        
        # Normalize clause_id for anchor
        clause_slug = re.sub(r'[^a-zA-Z0-9]', '_', str(self.clause_id))
        
        return f"#{source_slug}-p{self.page}-{self.locator_type.value}-{clause_slug}"
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence based on text similarity and heading proximity"""
        base_confidence = float(self.score)
        
        # Boost for clause-level detection
        clause_boost = 0.0
        if self.locator_type in [LocatorType.TABLE, LocatorType.FIGURE]:
            clause_boost = 0.15
        elif self.locator_type == LocatorType.CLAUSE:
            clause_boost = 0.10
        elif self.locator_type == LocatorType.SECTION:
            clause_boost = 0.05
        
        # Query term matching boost
        query_terms = self.query.lower().split()
        content_lower = (self.content or self.snippet or "").lower()
        
        term_matches = sum(1 for term in query_terms if term in content_lower)
        term_boost = min(0.1, term_matches * 0.02)
        
        final_confidence = min(1.0, base_confidence + clause_boost + term_boost)
        
        return final_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "id": self.id,
            "source": self.source,
            "page": self.page,
            "clause_id": self.clause_id,
            "clause_title": self.clause_title,
            "locator_type": self.locator_type.value,
            "snippet": self.snippet[:180],  # Limit to 180 chars
            "anchor": self.anchor,
            "confidence": round(self.confidence, 3)
        }
    
    def get_pill_text(self) -> str:
        """Generate professional pill text with source abbreviations"""
        # Professional source shortnames
        source_mapping = {
            "NZS 3604:2011": "NZS 3604",
            "B1 Amendment 13": "B1 Amd 13", 
            "E2/AS1": "E2/AS1",
            "B1/AS1": "B1/AS1",
            "NZS 4229:2013": "NZS 4229",
            "NZ Building Code": "NZBC"
        }
        
        source_short = source_mapping.get(self.source, self.source)
        
        # Build clause identifier part
        if self.clause_id and self.locator_type == LocatorType.TABLE:
            clause_part = f"Table {self.clause_id}"
        elif self.clause_id and self.locator_type == LocatorType.FIGURE:
            clause_part = f"Figure {self.clause_id}"
        elif self.clause_id and self.locator_type == LocatorType.CLAUSE:
            clause_part = self.clause_id
        elif self.clause_id and self.locator_type == LocatorType.SECTION:
            clause_part = f"§{self.clause_id}"
        else:
            # Page-level fallback
            clause_part = f"p.{self.page}"
            return f"[{source_short}] {clause_part}"
        
        # Add title if available
        title_part = ""
        if self.clause_title:
            clean_title = self.clause_title
            if len(clean_title) > 35:
                clean_title = clean_title[:32] + "..."
            title_part = f" — {clean_title}"
        
        return f"[{source_short}] {clause_part}{title_part} (p.{self.page})"

def build_clause_citations(docs: List[Dict], query: str, max_citations: int = 3) -> List[Dict]:
    """Build clause-level citations from retrieval results"""
    clause_citations = []
    
    for doc in docs:
        try:
            citation = ClauseCitation(doc, query)
            clause_citations.append(citation)
        except Exception as e:
            print(f"⚠️ Clause citation building failed: {e}")
            # Fallback to basic citation
            basic_citation = ClauseCitation({
                'id': doc.get('id', ''),
                'source': doc.get('source', 'Unknown'),
                'page': doc.get('page', 0),
                'content': '',
                'snippet': doc.get('snippet', ''),
                'score': doc.get('score', 0.0)
            }, query)
            clause_citations.append(basic_citation)
    
    # Sort by confidence and deduplicate
    sorted_citations = sorted(clause_citations, key=lambda x: x.confidence, reverse=True)
    
    # Deduplicate by source+page+clause_id
    seen = set()
    deduped_citations = []
    
    for citation in sorted_citations:
        key = f"{citation.source}_{citation.page}_{citation.clause_id or 'page'}"
        if key not in seen:
            seen.add(key)
            deduped_citations.append(citation)
            
            if len(deduped_citations) >= max_citations:
                break
    
    # Convert to dictionary format
    return [citation.to_dict() for citation in deduped_citations]

# Export for main app
def get_clause_citations(docs: List[Dict], query: str) -> List[Dict]:
    return build_clause_citations(docs, query)