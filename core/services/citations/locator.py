"""
Citation Locator - Extracts precise page, clause, table, and figure references
Fixes page-number truncation bug (e.g., p.184 should not become p.18)
"""

import re
from typing import Dict, Optional, List, Tuple

# Page reference patterns - captures 1-4 digit page numbers
PAGE_PATTERN = re.compile(
    r'(?:page|p\.?)\s*(\d{1,4})\b',
    re.IGNORECASE
)

# Clause patterns (e.g., "5.3.2", "G5.3.2", "B1.3.3.1")
CLAUSE_PATTERN = re.compile(
    r'\b([A-Z]?\d{1,2}(?:\.\d{1,2}){1,4})\b',
    re.IGNORECASE
)

# Table patterns (e.g., "Table 5.1", "Table 1A")
TABLE_PATTERN = re.compile(
    r'\bTable\s+(\d+\.?\d*[A-Z]?)\b',
    re.IGNORECASE
)

# Figure patterns (e.g., "Figure 3.4", "Fig. 5A")
FIGURE_PATTERN = re.compile(
    r'\b(?:Figure|Fig\.?)\s+(\d+\.?\d*[A-Z]?)\b',
    re.IGNORECASE
)


def extract_page_number(text: str) -> Optional[int]:
    """
    Extract page number from text, ensuring full numbers are captured.
    
    Args:
        text: Input text (e.g., "p.184", "page 45", "See page 7")
    
    Returns:
        Page number as integer, or None if not found
    
    Examples:
        >>> extract_page_number("p.184")
        184
        >>> extract_page_number("page 45")
        45
        >>> extract_page_number("See p. 1234")
        1234
        >>> extract_page_number("no page here")
        None
    """
    match = PAGE_PATTERN.search(text)
    if match:
        try:
            page_num = int(match.group(1))
            # Validate reasonable page range (1-9999)
            if 1 <= page_num <= 9999:
                return page_num
        except ValueError:
            pass
    return None


def extract_all_page_numbers(text: str) -> List[int]:
    """
    Extract all page numbers from text.
    
    Args:
        text: Input text with multiple page references
    
    Returns:
        List of page numbers as integers
    
    Examples:
        >>> extract_all_page_numbers("See p.184, p.185, and page 190")
        [184, 185, 190]
    """
    matches = PAGE_PATTERN.finditer(text)
    pages = []
    for match in matches:
        try:
            page_num = int(match.group(1))
            if 1 <= page_num <= 9999:
                pages.append(page_num)
        except ValueError:
            continue
    return pages


def extract_clause(text: str) -> Optional[str]:
    """
    Extract clause reference from text.
    
    Args:
        text: Input text (e.g., "Clause 5.3.2", "G5.3.2 requirements")
    
    Returns:
        Clause reference string, or None if not found
    
    Examples:
        >>> extract_clause("Clause 5.3.2")
        "5.3.2"
        >>> extract_clause("G5.3.2 requirements")
        "G5.3.2"
    """
    match = CLAUSE_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_table(text: str) -> Optional[str]:
    """
    Extract table reference from text.
    
    Args:
        text: Input text (e.g., "Table 5.1", "see Table 1A")
    
    Returns:
        Table reference string, or None if not found
    """
    match = TABLE_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def extract_figure(text: str) -> Optional[str]:
    """
    Extract figure reference from text.
    
    Args:
        text: Input text (e.g., "Figure 3.4", "Fig. 5A")
    
    Returns:
        Figure reference string, or None if not found
    """
    match = FIGURE_PATTERN.search(text)
    if match:
        return match.group(1)
    return None


def normalize_page_reference(page: int) -> str:
    """
    Normalize page number to standard format.
    
    Args:
        page: Page number as integer
    
    Returns:
        Formatted page reference (e.g., "p.184")
    
    Examples:
        >>> normalize_page_reference(184)
        "p.184"
        >>> normalize_page_reference(7)
        "p.7"
    """
    return f"p.{page}"


def build_citation_locator(
    doc: Dict,
    locator_type: str = "page"
) -> Dict[str, any]:
    """
    Build a citation locator dictionary from a document.
    
    Args:
        doc: Document dict with keys: source, page, content, snippet
        locator_type: Type of locator (page, clause, table, figure)
    
    Returns:
        Citation locator dictionary
    """
    source = doc.get("source", "Unknown")
    page = doc.get("page", 0)
    content = doc.get("content", "")
    snippet = doc.get("snippet", content[:200])
    
    # Ensure page is stored as integer (not truncated)
    if isinstance(page, str):
        try:
            page = int(page)
        except ValueError:
            page = 0
    
    locator = {
        "source": source,
        "page": page,
        "locator_type": locator_type,
        "snippet": snippet,
        "page_ref": normalize_page_reference(page)
    }
    
    # Extract additional locators from content if available
    if locator_type == "clause":
        clause = extract_clause(content)
        if clause:
            locator["clause_id"] = clause
            locator["locator_text"] = f"{source} clause {clause} (p.{page})"
        else:
            # Fallback to page-level
            locator["locator_type"] = "page"
            locator["locator_text"] = f"{source} {normalize_page_reference(page)}"
    
    elif locator_type == "table":
        table = extract_table(content)
        if table:
            locator["table_id"] = table
            locator["locator_text"] = f"{source} Table {table} (p.{page})"
        else:
            locator["locator_type"] = "page"
            locator["locator_text"] = f"{source} {normalize_page_reference(page)}"
    
    elif locator_type == "figure":
        figure = extract_figure(content)
        if figure:
            locator["figure_id"] = figure
            locator["locator_text"] = f"{source} Figure {figure} (p.{page})"
        else:
            locator["locator_type"] = "page"
            locator["locator_text"] = f"{source} {normalize_page_reference(page)}"
    
    else:
        # Default page-level locator
        locator["locator_text"] = f"{source} {normalize_page_reference(page)}"
    
    return locator


def validate_page_extraction(test_cases: List[Tuple[str, int]]) -> bool:
    """
    Validate page extraction against test cases.
    
    Args:
        test_cases: List of (input_text, expected_page) tuples
    
    Returns:
        True if all tests pass
    """
    all_passed = True
    for text, expected in test_cases:
        actual = extract_page_number(text)
        if actual != expected:
            print(f"❌ FAIL: '{text}' → {actual} (expected {expected})")
            all_passed = False
        else:
            print(f"✅ PASS: '{text}' → {actual}")
    return all_passed


if __name__ == "__main__":
    # Test page number extraction with the truncation bug scenarios
    print("Testing page number extraction (fixes truncation bug)...\n")
    
    test_cases = [
        ("E2/AS1 p.184", 184),
        ("See page 184", 184),
        ("p. 184", 184),
        ("p.7", 7),
        ("page 11", 11),
        ("p.18", 18),
        ("NZS 3604 p.45", 45),
        ("B1/AS1 p.8", 8),
        ("page 1234", 1234),
        ("no page here", None),
    ]
    
    if validate_page_extraction(test_cases):
        print("\n✅ All page extraction tests passed!")
    else:
        print("\n❌ Some tests failed!")
