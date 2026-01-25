#!/usr/bin/env python3
"""
STRYDA V2.5 GOD-TIER INGESTION ENGINE
Cell-Level Context Injection for Technical Data Sheets

Protocol: /protocols/PARSING_STANDARD_V2_5.md
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================================
# GOD-TIER CONTEXT INJECTION - THE CORE LOGIC
# ============================================================================

def parse_table_with_context(table_data, product_context):
    """
    GOD-TIER PARSING: Glues Row/Col headers to every cell.
    Every data point is self-contained and independently retrievable.
    """
    structured_chunks = []
    
    if not table_data or len(table_data) < 2:
        return structured_chunks
    
    # Extract headers from first row
    headers = [str(h).strip() if h else f"Col_{i}" for i, h in enumerate(table_data[0])]
    
    # Process each data row
    for row_idx, row in enumerate(table_data[1:], 1):
        # First cell is typically the row identifier (e.g., "1/2 inch")
        row_header = str(row[0]).strip() if row and row[0] else f"Row_{row_idx}"
        
        # Process each cell in the row
        for col_idx, cell_value in enumerate(row):
            if col_idx == 0:
                continue  # Skip row header column
            
            col_header = headers[col_idx] if col_idx < len(headers) else f"Property_{col_idx}"
            value = str(cell_value).strip() if cell_value else ""
            
            if value and value not in ['', '-', 'N/A', 'n/a']:
                # THE GLUE: Create self-contained context chunk
                chunk = f"Context: {{Product: {product_context} | Size/Type: {row_header} | Property: {col_header}}} -> Value: {value}"
                structured_chunks.append(chunk)
    
    return structured_chunks


def extract_tables_god_tier(pdf_bytes, product_name):
    """
    Vision-First table extraction with God-Tier context injection.
    """
    import fitz
    
    all_chunks = []
    text_content = []
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text_content.append(page_text)
            
            # Try PyMuPDF table extraction
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for table_idx, table in enumerate(tables.tables):
                        table_data = table.extract()
                        
                        # Apply God-Tier Context Injection
                        context_chunks = parse_table_with_context(table_data, product_name)
                        all_chunks.extend(context_chunks)
                        
                        # Also create markdown version for full table context
                        md_table = table_to_markdown_with_context(table_data, product_name, page_num + 1)
                        if md_table:
                            all_chunks.append(md_table)
            except:
                # Fallback: detect tables from text patterns
                detected_tables = detect_tables_from_text_patterns(page_text)
                for table_data in detected_tables:
                    context_chunks = parse_table_with_context(table_data, product_name)
                    all_chunks.extend(context_chunks)
        
        doc.close()
        
        # Also chunk the regular text content
        full_text = '\n\n'.join(text_content).replace('\x00', '')
        text_chunks = smart_chunk_text(full_text, product_name)
        all_chunks.extend(text_chunks)
        
        return all_chunks
        
    except Exception as e:
        print(f"      ⚠️ Extraction error: {str(e)[:50]}")
        return []


def table_to_markdown_with_context(table_data, product_name, page_num):
    """
    Create markdown table with full product context header.
    """
    if not table_data or len(table_data) < 2:
        return None
    
    try:
        lines = [f"[TECHNICAL TABLE: {product_name} - Page {page_num}]"]
        
        # Header row
        header = [str(c).strip() if c else '' for c in table_data[0]]
        lines.append('| ' + ' | '.join(header) + ' |')
        lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
        
        # Data rows
        for row in table_data[1:]:
            cells = [str(c).strip() if c else '' for c in row]
            while len(cells) < len(header):
                cells.append('')
            lines.append('| ' + ' | '.join(cells[:len(header)]) + ' |')
        
        return '\n'.join(lines)
    except:
        return None


def detect_tables_from_text_patterns(text):
    """
    Detect table structures from text when PyMuPDF table detection fails.
    Returns list of table_data arrays.
    """
    tables = []
    lines = text.split('\n')
    
    # Look for consecutive lines with numeric data
    current_table = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if len(current_table) >= 3:
                tables.append(current_table)
            current_table = []
            continue
        
        # Check if line looks like table data (has numbers and multiple parts)
        parts = re.split(r'\s{2,}|\t', line)
        has_numbers = bool(re.search(r'\d+', line))
        
        if len(parts) >= 2 and (has_numbers or len(current_table) == 0):
            current_table.append(parts)
        else:
            if len(current_table) >= 3:
                tables.append(current_table)
            current_table = []
    
    if len(current_table) >= 3:
        tables.append(current_table)
    
    return tables


def smart_chunk_text(text, product_name, chunk_size=1000, overlap=150):
    """
    Smart text chunking with product context prefix.
    """
    chunks = []
    
    # Add product context to each chunk
    context_prefix = f"[Document: {product_name}]\n"
    effective_chunk_size = chunk_size - len(context_prefix)
    
    start = 0
    while start < len(text):
        end = start + effective_chunk_size
        chunk = text[start:end].strip()
        
        if chunk:
            # Prepend context to every chunk
            contextualized_chunk = context_prefix + chunk
            chunks.append(contextualized_chunk)
        
        start = end - overlap
    
    return chunks


# ============================================================================
# V2 RULES (Existing - Enhanced)
# ============================================================================

FORBIDDEN_PATTERNS = [r"\((\d+)\)", r"Download", r"Brochure", r"%20"]
TARGET_FOLDERS = {
    "WARRANTY": "/app/storage/00_General_Resources/",
    "CARE": "/app/storage/00_General_Resources/",
    "COLORSTEEL": "/app/storage/00_Material_Suppliers/NZ_Steel/",
    "COLORCOTE": "/app/storage/00_Material_Suppliers/Pacific_Coil/"
}

def sanitize_filename(filename):
    """
    Rule 2: Strip garbage, hashes, and trademarks.
    """
    clean = filename.replace("™", "").replace("®", "").replace("%20", "_")
    clean = re.sub(r"[a-f0-9]{8,}", "", clean)
    return clean.strip()

def enforce_naming_convention(brand, product, doc_type, extension=".pdf"):
    """
    Rule 1: [Manufacturer] - [Product] - [Type].pdf
    """
    safe_brand = sanitize_filename(brand)
    safe_product = sanitize_filename(product)
    safe_type = sanitize_filename(doc_type)
    return f"{safe_brand} - {safe_product} - {safe_type}{extension}"

def route_file(filepath, filename):
    """
    Rule 3: Sorting based on keywords.
    """
    upper_name = filename.upper()
    
    for key, dest in TARGET_FOLDERS.items():
        if key in upper_name:
            return dest
    
    if "ACCESSORIES" in upper_name:
        pass
    
    return "/app/storage/01_Unsorted/"


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("   STRYDA V2.5 GOD-TIER ENGINE - Context Injection Test")
    print("=" * 70)
    
    # Test table data
    test_table = [
        ["DIAMETER (inches)", "PROOF LOAD (lbf)", "HARDNESS"],
        ["1/4", "5460", "24-32"],
        ["5/16", "8700", "24-32"],
        ["3/8", "13150", "26-34"],
        ["1/2", "24000", "26-34"],
        ["5/8", "38400", "26-36"],
    ]
    
    product = "Hex Nut Grade 8 UNF Zinc"
    
    print(f"\n📊 Testing Context Injection on: {product}")
    print("-" * 70)
    
    chunks = parse_table_with_context(test_table, product)
    
    print(f"\n🎯 Generated {len(chunks)} context-injected chunks:\n")
    for chunk in chunks:
        print(f"   {chunk}")
    
    print("\n" + "-" * 70)
    print("✅ God-Tier Context Injection: ACTIVE")
    print("=" * 70)
