#!/usr/bin/env python3
"""
STRYDA INGESTION CONFIGURATION & RULES
======================================
Programmatic enforcement of the STRYDA Master Protocol.

This module provides constants, validators, and utilities for
enforcing data ingestion rules during PDF scraping operations.

Protocol Version: 2.0
Last Updated: January 2025
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

# =============================================================================
# PROTOCOL METADATA
# =============================================================================

PROTOCOL_VERSION = "2.0"
PROTOCOL_DATE = "2025-01"

# =============================================================================
# RULE 4: Extension Whitelist
# =============================================================================

ALLOWED_EXTENSIONS = [".pdf"]

FORBIDDEN_EXTENSIONS = [
    ".zip",   # Archive files
    ".exe",   # Executables
    ".dwg",   # AutoCAD
    ".dxf",   # CAD Exchange
    ".rvt",   # Revit
    ".jpg",   # Images
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".doc",   # Legacy Office
    ".xls",
    ".ppt",
]

# =============================================================================
# RULE 3: Universal Keywords (Move to 00_General_Resources)
# =============================================================================

UNIVERSAL_KEYWORDS = [
    "warranty",
    "terms of trade",
    "maintenance",
    "color chart",
    "colour chart",
    "environmental",
    "sustainability",
    "care guide",
    "company profile",
    "corporate brochure",
    "about us",
    "terms and conditions",
]

# =============================================================================
# RULE 7: Supply Chain Exclusion List
# Skip if found in Manufacturer folder - route to /00_Material_Suppliers/
# =============================================================================

SUPPLY_CHAIN_KEYWORDS = [
    # ColorSteel variants
    "colorsteel",
    "coloursteel",
    "color steel",
    "colour steel",
    
    # ColorCote variants
    "colorcote",
    "colourcote",
    "color cote",
    "colour cote",
    
    # Galvsteel / NZ Steel
    "galvsteel",
    "galv steel",
    "nz steel durability",
    
    # Zinc coatings
    "zincalume",
    "zinacore",
    "zinc coating",
    
    # Other suppliers
    "alumigard",
    "magnaflow",
    "dridex",
    "altimate",
    "maxam",
]

# Mapping of keywords to supplier folders
SUPPLIER_FOLDER_MAP = {
    "colorsteel": "ColorSteel",
    "coloursteel": "ColorSteel",
    "colorcote": "ColorCote",
    "colourcote": "ColorCote",
    "galvsteel": "NZ_Steel_Galv",
    "zincalume": "NZ_Steel_Galv",
    "nz steel": "NZ_Steel_Galv",
}

# =============================================================================
# RULE 8: Monolith Detection Thresholds
# =============================================================================

MONOLITH_SIZE_THRESHOLD_MB = 20
MONOLITH_PAGE_THRESHOLD = 50

# =============================================================================
# RULE 1 & 2: Filename Sanitization
# =============================================================================

# Characters to strip from filenames
SANITIZE_CHARS = [
    "™", "®", "©",  # Trademark symbols
    "<", ">", ":", '"', "/", "\\", "|", "?", "*",  # Invalid file chars
]

# Patterns for hash codes to remove
HASH_PATTERNS = [
    r"^[0-9a-fA-F]{16,}[\s_-]+",  # Leading hex hash
    r"[0-9a-fA-F]{32,}",           # MD5-like hash anywhere
    r"_[0-9a-fA-F]{8,}_",          # Embedded hash
]

# Generic filenames to reject (Rule 1)
FORBIDDEN_FILENAMES = [
    "download",
    "view",
    "brochure",
    "document",
    "file",
    "pdf",
    "click here",
    "untitled",
]

# =============================================================================
# RULE 6: Hidden Technical Data Keywords
# =============================================================================

TECHNICAL_CONTENT_KEYWORDS = [
    "span table",
    "span tables",
    "load capacity",
    "fixing pattern",
    "installation detail",
    "structural capacity",
    "design guide",
    "technical data",
    "specification",
]

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def is_allowed_extension(filename: str) -> bool:
    """Check if file extension is allowed (Rule 4)."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def is_forbidden_extension(filename: str) -> bool:
    """Check if file extension is forbidden (Rule 4)."""
    ext = Path(filename).suffix.lower()
    return ext in FORBIDDEN_EXTENSIONS


def is_universal_document(title: str) -> bool:
    """Check if document should go to 00_General_Resources (Rule 3)."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in UNIVERSAL_KEYWORDS)


def is_supply_chain_document(title: str) -> Tuple[bool, Optional[str]]:
    """
    Check if document is a supply chain document (Rule 7).
    Returns (is_supplier_doc, supplier_folder_name)
    """
    title_lower = title.lower()
    
    for keyword in SUPPLY_CHAIN_KEYWORDS:
        if keyword in title_lower:
            # Find the supplier folder
            for kw, folder in SUPPLIER_FOLDER_MAP.items():
                if kw in title_lower:
                    return (True, folder)
            return (True, None)  # Is supplier doc but no specific folder mapped
    
    return (False, None)


def is_generic_filename(filename: str) -> bool:
    """Check if filename is too generic and needs context (Rule 1)."""
    name_lower = Path(filename).stem.lower()
    return any(forbidden in name_lower for forbidden in FORBIDDEN_FILENAMES)


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Clean filename according to Rule 2.
    - Remove trademark symbols
    - Strip hash codes
    - Remove invalid characters
    - Normalize whitespace
    """
    # Remove trademark symbols
    for char in SANITIZE_CHARS:
        name = name.replace(char, "")
    
    # Remove hash codes
    for pattern in HASH_PATTERNS:
        name = re.sub(pattern, "", name)
    
    # Normalize whitespace
    name = re.sub(r"\s+", " ", name).strip()
    
    # Truncate if too long
    if len(name) > max_length:
        name = name[:max_length]
    
    return name


def format_filename(manufacturer: str, product: str, doc_title: str) -> str:
    """
    Format filename according to naming standard (Rule 2).
    Format: [Manufacturer] - [Product Name] - [Clean Document Title].pdf
    """
    clean_title = sanitize_filename(doc_title)
    return f"{manufacturer} - {product} - {clean_title}.pdf"


def is_potential_monolith(file_size_mb: float = 0, page_count: int = 0) -> bool:
    """
    Check if file should be flagged for Monolith review (Rule 8).
    """
    return (
        file_size_mb > MONOLITH_SIZE_THRESHOLD_MB or
        page_count > MONOLITH_PAGE_THRESHOLD
    )


def contains_technical_data(text_content: str) -> bool:
    """
    Check if document contains hidden technical data (Rule 6).
    Used to identify mislabeled "Accessories" files.
    """
    text_lower = text_content.lower()
    return any(kw in text_lower for kw in TECHNICAL_CONTENT_KEYWORDS)


# =============================================================================
# PROTOCOL LOADER
# =============================================================================

def get_protocol_path() -> Path:
    """Get the path to the Master Protocol document."""
    # Try relative to this file first
    src_dir = Path(__file__).parent
    protocol_path = src_dir.parent / "docs" / "STRYDA_MASTER_PROTOCOL.md"
    
    if protocol_path.exists():
        return protocol_path
    
    # Fallback to /app/docs
    return Path("/app/docs/STRYDA_MASTER_PROTOCOL.md")


def get_system_prompt() -> str:
    """
    Returns the Master Protocol for the LLM Agent.
    Use this when initializing scraping agents.
    """
    protocol_path = get_protocol_path()
    
    if protocol_path.exists():
        with open(protocol_path, "r", encoding="utf-8") as f:
            return f.read()
    
    return f"ERROR: Protocol file not found at {protocol_path}"


def print_protocol_summary():
    """Print a summary of active protocol rules."""
    print("=" * 60)
    print(f"STRYDA MASTER PROTOCOL v{PROTOCOL_VERSION}")
    print("=" * 60)
    print(f"\nRule 3 - Universal Keywords: {len(UNIVERSAL_KEYWORDS)}")
    print(f"Rule 4 - Allowed Extensions: {ALLOWED_EXTENSIONS}")
    print(f"Rule 7 - Supply Chain Keywords: {len(SUPPLY_CHAIN_KEYWORDS)}")
    print(f"Rule 8 - Monolith Threshold: {MONOLITH_SIZE_THRESHOLD_MB}MB / {MONOLITH_PAGE_THRESHOLD} pages")
    print("=" * 60)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    print_protocol_summary()
    
    # Test cases
    print("\n📋 Test Cases:")
    
    # Test Rule 1
    print(f"\n  is_generic_filename('Download.pdf'): {is_generic_filename('Download.pdf')}")
    print(f"  is_generic_filename('Espan 340 Loadspan.pdf'): {is_generic_filename('Espan 340 Loadspan.pdf')}")
    
    # Test Rule 3
    print(f"\n  is_universal_document('Warranty Guide'): {is_universal_document('Warranty Guide')}")
    print(f"  is_universal_document('Span Tables'): {is_universal_document('Span Tables')}")
    
    # Test Rule 7
    print(f"\n  is_supply_chain_document('ColorSteel Brochure'): {is_supply_chain_document('ColorSteel Brochure')}")
    print(f"  is_supply_chain_document('Loadspan Tables'): {is_supply_chain_document('Loadspan Tables')}")
    
    # Test sanitization
    print(f"\n  sanitize_filename('66e3abc™ Download®'): '{sanitize_filename('66e3abc™ Download®')}'")
