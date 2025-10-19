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
        """Extract clause/table/figure information from content"""
        content = self.content or self.snippet or ""
        
        # Table detection patterns
        table_patterns = [
            r'(Table\s+(\d+(?:\.\d+)*))\s*[:\-—]?\s*([^\n]{1,80})',
            r'(TABLE\s+(\d+(?:\.\d+)*))\s*[:\-—]?\s*([^\n]{1,80})',
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                table_ref = match.group(1)  # "Table 7.1"
                table_id = match.group(2)   # "7.1"
                table_title = match.group(3).strip() if len(match.groups()) > 2 else ""
                
                # Clean title
                table_title = re.sub(r'^[:\-—\s]*', '', table_title)
                table_title = table_title[:60] + "..." if len(table_title) > 60 else table_title
                
                return table_id, table_title or table_ref, LocatorType.TABLE
        
        # Figure detection patterns
        figure_patterns = [
            r'(Figure\s+(\d+(?:\.\d+)*))\s*[:\-—]?\s*([^\n]{1,80})',
            r'(FIGURE\s+(\d+(?:\.\d+)*))\s*[:\-—]?\s*([^\n]{1,80})',
        ]
        
        for pattern in figure_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                figure_ref = match.group(1)  # "Figure 4.2"
                figure_id = match.group(2)   # "4.2"
                figure_title = match.group(3).strip() if len(match.groups()) > 2 else ""
                
                figure_title = re.sub(r'^[:\-—\s]*', '', figure_title)
                figure_title = figure_title[:60] + "..." if len(figure_title) > 60 else figure_title
                
                return figure_id, figure_title or figure_ref, LocatorType.FIGURE
        
        # Clause detection patterns
        clause_patterns = [
            r'(?:Clause\s*)?(\d+(?:\.\d+){1,3})\s*[:\-—]?\s*([^\n]{1,80})',
            r'([A-H]\d+(?:/[A-Z]+\d+)?)\s*[:\-—]?\s*([^\n]{1,80})',  # B1/AS1, E2/AS1
        ]
        
        for pattern in clause_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                clause_id = match.group(1)
                clause_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                clause_title = re.sub(r'^[:\-—\s]*', '', clause_title)
                clause_title = clause_title[:60] + "..." if len(clause_title) > 60 else clause_title
                
                return clause_id, clause_title, LocatorType.CLAUSE
        
        # Section heading detection
        section_patterns = [
            r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{5,80})',  # "7.1 FLOOR JOISTS"
        ]
        
        lines = content.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            for pattern in section_patterns:
                match = re.match(pattern, line.strip())
                if match:
                    section_id = match.group(1)
                    section_title = match.group(2)
                    
                    return section_id, section_title[:60], LocatorType.SECTION
        
        # Fallback to page-level
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
        """Generate text for citation pill display"""
        # Source shortname
        source_short = self.source.replace("NZS 3604:2011", "NZS 3604").replace("B1 Amendment 13", "B1 Amd 13")
        
        # Clause/table identifier
        if self.clause_id and self.locator_type == LocatorType.TABLE:
            clause_part = f"Table {self.clause_id}"
        elif self.clause_id and self.locator_type == LocatorType.FIGURE:
            clause_part = f"Figure {self.clause_id}"
        elif self.clause_id and self.locator_type == LocatorType.CLAUSE:
            clause_part = f"Clause {self.clause_id}"
        elif self.clause_id and self.locator_type == LocatorType.SECTION:
            clause_part = f"§{self.clause_id}"
        else:
            clause_part = ""
        
        # Title (shortened)
        title_part = ""
        if self.clause_title:
            title = self.clause_title
            if len(title) > 40:
                title = title[:37] + "..."
            title_part = f" — {title}"
        
        # Combine parts
        if clause_part:
            return f"[{source_short}] {clause_part}{title_part} (p.{self.page})"
        else:
            return f"[{source_short}] p.{self.page}"

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