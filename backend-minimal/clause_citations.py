"""
Clause-level citation builder for STRYDA.ai
Builds enhanced citation pills with clause/table/figure locators
Uses services/citations/locator.py for page number extraction
"""

import re
from typing import List, Dict, Any, Optional
from services.citations.locator import (
    extract_page_number,
    extract_clause,
    extract_table,
    extract_figure,
    normalize_page_reference,
    build_citation_locator
)


def detect_locator_type(doc: Dict[str, Any]) -> str:
    """
    Detect the most specific locator type for a document.
    Priority: TABLE > FIGURE > CLAUSE > SECTION > PAGE
    
    Args:
        doc: Document dictionary with content
    
    Returns:
        Locator type: "table", "figure", "clause", "section", or "page"
    """
    content = doc.get("content", "")
    snippet = doc.get("snippet", "")
    
    # Combine content and snippet for detection
    text = f"{snippet} {content[:500]}"
    
    # Check for table references (highest priority)
    if extract_table(text):
        return "table"
    
    # Check for figure references
    if extract_figure(text):
        return "figure"
    
    # Check for clause references
    if extract_clause(text):
        return "clause"
    
    # Check if section metadata exists
    if doc.get("section"):
        return "section"
    
    # Default to page-level
    return "page"


def build_clause_citations(
    docs: List[Dict[str, Any]],
    query: str,
    max_citations: int = 3
) -> List[Dict[str, Any]]:
    """
    Build clause-level citations from retrieved documents.
    
    Args:
        docs: List of retrieved documents
        query: User query (for context)
        max_citations: Maximum number of citations to return
    
    Returns:
        List of citation dictionaries with enhanced locators
    """
    citations = []
    
    for idx, doc in enumerate(docs[:max_citations]):
        source = doc.get("source", "Unknown")
        page = doc.get("page", 0)
        content = doc.get("content", "")
        snippet = doc.get("snippet", content[:200])
        
        # Ensure page is integer (fixes truncation bug)
        if isinstance(page, str):
            try:
                page = int(page)
            except ValueError:
                # Try to extract from content as fallback
                extracted_page = extract_page_number(content)
                page = extracted_page if extracted_page else 0
        
        # Detect locator type
        locator_type = detect_locator_type(doc)
        
        # Build base citation
        citation = {
            "id": f"{source}_{page}_{idx}",
            "source": source,
            "page": page,  # Full page number preserved
            "snippet": snippet,
            "locator_type": locator_type,
            "confidence": 1.0,
            "anchor": None
        }
        
        # Extract specific locator details
        text = f"{snippet} {content[:500]}"
        
        if locator_type == "table":
            table_id = extract_table(text)
            citation["clause_id"] = table_id
            citation["clause_title"] = f"Table {table_id}"
            citation["pill_text"] = f"[{source}] Table {table_id} (p.{page})"
        
        elif locator_type == "figure":
            figure_id = extract_figure(text)
            citation["clause_id"] = figure_id
            citation["clause_title"] = f"Figure {figure_id}"
            citation["pill_text"] = f"[{source}] Figure {figure_id} (p.{page})"
        
        elif locator_type == "clause":
            clause_id = extract_clause(text)
            citation["clause_id"] = clause_id
            citation["clause_title"] = f"Clause {clause_id}"
            citation["pill_text"] = f"[{source}] Clause {clause_id} (p.{page})"
        
        elif locator_type == "section":
            section = doc.get("section", "")
            citation["clause_id"] = None
            citation["clause_title"] = section
            citation["pill_text"] = f"[{source}] {section} (p.{page})"
        
        else:
            # Page-level fallback
            citation["clause_id"] = None
            citation["clause_title"] = None
            # Use normalize_page_reference to ensure full page number
            citation["pill_text"] = f"[{source.replace('NZS 3604:2011', 'NZS 3604')}] {normalize_page_reference(page)}"
        
        citations.append(citation)
    
    return citations


def test_clause_citations():
    """
    Test clause citation building with sample documents
    """
    print("Testing clause citation building...\n")
    
    # Test documents
    test_docs = [
        {
            "source": "E2/AS1",
            "page": 184,  # Test 3-digit page number
            "content": "Table C.1.1.1B: Compatibility of materials in contact. Aluminium, steel, copper...",
            "snippet": "Material compatibility requirements for flashing materials"
        },
        {
            "source": "NZS 3604:2011",
            "page": 45,
            "content": "Clause 5.3.2: Wall framing requirements. Studs shall be spaced at maximum 600mm centres...",
            "snippet": "Wall framing stud spacing requirements"
        },
        {
            "source": "B1/AS1",
            "page": 8,
            "content": "Figure 3.2: Bracing layout example showing portal frame connections...",
            "snippet": "Bracing configuration for residential structures"
        }
    ]
    
    # Build citations
    citations = build_clause_citations(test_docs, "test query", max_citations=3)
    
    # Print results
    for cite in citations:
        print(f"Source: {cite['source']}")
        print(f"Page: {cite['page']}")
        print(f"Locator Type: {cite['locator_type']}")
        print(f"Pill Text: {cite['pill_text']}")
        print(f"Clause ID: {cite.get('clause_id')}")
        print(f"Clause Title: {cite.get('clause_title')}")
        print()
    
    # Verify page 184 is not truncated
    page_184_citation = [c for c in citations if c['page'] == 184][0]
    assert page_184_citation['page'] == 184, "Page 184 was truncated!"
    assert "p.184" in page_184_citation['pill_text'], "Pill text doesn't show full page number!"
    
    print("✅ All tests passed! Page numbers preserved correctly.")


if __name__ == "__main__":
    test_clause_citations()
