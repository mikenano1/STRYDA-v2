#!/usr/bin/env python3
"""
STRYDA V5 VISION-FIRST INGESTION ENGINE
Enhanced PDF parsing with intelligent table detection and markdown conversion

Features:
- Table detection via gridlines and structure analysis
- Markdown table conversion (preserving rows/columns)
- Structured data extraction for technical specs
- Vision-First approach for TDS documents
"""

import os
import re
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================================
# VISION-FIRST TABLE PARSER
# ============================================================================

class VisionFirstParser:
    """
    Enhanced PDF parser that detects and preserves table structures.
    Converts tables to Markdown format for better RAG retrieval.
    """
    
    def __init__(self):
        self.table_patterns = [
            # Common table header patterns for fastener TDS
            r'DIAMETER.*PROOF\s*LOAD',
            r'SIZE.*TENSILE.*STRENGTH',
            r'THREAD.*PITCH.*LOAD',
            r'MECHANICAL\s*PROPERTIES',
            r'CHEMICAL\s*COMPOSITION',
            r'DIMENSIONS',
            r'TORQUE.*VALUES',
        ]
    
    def extract_with_tables(self, pdf_bytes):
        """
        Extract text from PDF with intelligent table detection.
        Returns structured content with tables converted to Markdown.
        """
        import fitz  # PyMuPDF
        
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages_content = []
            
            for page_num, page in enumerate(doc):
                page_data = {
                    'page': page_num + 1,
                    'text': '',
                    'tables': [],
                    'has_tables': False
                }
                
                # Method 1: Try to extract tables using PyMuPDF's table detection
                try:
                    tables = page.find_tables()
                    if tables and len(tables.tables) > 0:
                        page_data['has_tables'] = True
                        for table in tables.tables:
                            # Convert table to markdown
                            md_table = self._table_to_markdown(table.extract())
                            if md_table:
                                page_data['tables'].append(md_table)
                except Exception as e:
                    # Table extraction not available or failed
                    pass
                
                # Method 2: Get raw text
                raw_text = page.get_text()
                
                # Method 3: If no tables found via method 1, try pattern detection
                if not page_data['has_tables']:
                    detected_tables = self._detect_tables_from_text(raw_text)
                    if detected_tables:
                        page_data['has_tables'] = True
                        page_data['tables'].extend(detected_tables)
                
                # Combine text with table markers
                if page_data['tables']:
                    # Insert tables into text at appropriate positions
                    page_data['text'] = self._merge_text_and_tables(raw_text, page_data['tables'])
                else:
                    page_data['text'] = raw_text
                
                # Clean text
                page_data['text'] = page_data['text'].replace('\x00', '')
                pages_content.append(page_data)
            
            doc.close()
            return pages_content
            
        except Exception as e:
            print(f"      ⚠️ Vision parser error: {str(e)[:50]}")
            return None
    
    def _table_to_markdown(self, table_data):
        """Convert extracted table data to Markdown format."""
        if not table_data or len(table_data) < 2:
            return None
        
        try:
            md_lines = []
            
            # Header row
            header = table_data[0]
            header_cells = [str(cell).strip() if cell else '' for cell in header]
            md_lines.append('| ' + ' | '.join(header_cells) + ' |')
            
            # Separator
            md_lines.append('| ' + ' | '.join(['---'] * len(header_cells)) + ' |')
            
            # Data rows
            for row in table_data[1:]:
                cells = [str(cell).strip() if cell else '' for cell in row]
                # Pad if necessary
                while len(cells) < len(header_cells):
                    cells.append('')
                md_lines.append('| ' + ' | '.join(cells[:len(header_cells)]) + ' |')
            
            return '\n'.join(md_lines)
        except:
            return None
    
    def _detect_tables_from_text(self, text):
        """
        Detect table-like structures from raw text using pattern matching.
        Returns list of markdown tables.
        """
        tables = []
        lines = text.split('\n')
        
        # Look for consecutive lines with similar structure (multiple columns)
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this looks like a table header
            if self._is_table_header(line):
                table_lines = [line]
                j = i + 1
                
                # Collect subsequent table rows
                while j < len(lines):
                    next_line = lines[j].strip()
                    if self._is_table_row(next_line, line):
                        table_lines.append(next_line)
                        j += 1
                    elif next_line == '':
                        j += 1  # Skip empty lines within table
                    else:
                        break
                
                if len(table_lines) >= 2:
                    md_table = self._text_lines_to_markdown(table_lines)
                    if md_table:
                        tables.append(md_table)
                
                i = j
            else:
                i += 1
        
        return tables
    
    def _is_table_header(self, line):
        """Check if line looks like a table header."""
        # Multiple capitalized words or known header patterns
        if not line:
            return False
        
        # Check for known table headers
        header_keywords = ['DIAMETER', 'SIZE', 'GRADE', 'CLASS', 'TYPE', 'LOAD', 
                          'STRENGTH', 'HARDNESS', 'TORQUE', 'THREAD', 'PITCH',
                          'MIN', 'MAX', 'RANGE', 'MATERIAL']
        
        upper_count = sum(1 for word in line.split() if word.isupper() and len(word) > 2)
        keyword_count = sum(1 for kw in header_keywords if kw in line.upper())
        
        return upper_count >= 2 or keyword_count >= 2
    
    def _is_table_row(self, line, header_line):
        """Check if line looks like a table data row."""
        if not line:
            return False
        
        # Contains numbers (typical for data rows)
        has_numbers = bool(re.search(r'\d+', line))
        
        # Similar structure to header (whitespace-separated values)
        header_parts = len(header_line.split())
        line_parts = len(line.split())
        
        return has_numbers and abs(header_parts - line_parts) <= 2
    
    def _text_lines_to_markdown(self, lines):
        """Convert text lines that look like a table to markdown."""
        if len(lines) < 2:
            return None
        
        try:
            # Split each line by multiple spaces or tabs
            rows = []
            for line in lines:
                # Split by 2+ spaces or tabs
                cells = re.split(r'\s{2,}|\t', line.strip())
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    rows.append(cells)
            
            if len(rows) < 2:
                return None
            
            # Normalize column count
            max_cols = max(len(row) for row in rows)
            
            md_lines = []
            
            # Header
            header = rows[0]
            while len(header) < max_cols:
                header.append('')
            md_lines.append('| ' + ' | '.join(header) + ' |')
            md_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
            
            # Data rows
            for row in rows[1:]:
                while len(row) < max_cols:
                    row.append('')
                md_lines.append('| ' + ' | '.join(row[:max_cols]) + ' |')
            
            return '\n'.join(md_lines)
        except:
            return None
    
    def _merge_text_and_tables(self, raw_text, tables):
        """Merge raw text with extracted markdown tables."""
        if not tables:
            return raw_text
        
        # Add tables section at the end with clear markers
        result = raw_text.strip()
        result += '\n\n--- EXTRACTED TABLES ---\n\n'
        
        for i, table in enumerate(tables, 1):
            result += f'**Table {i}:**\n{table}\n\n'
        
        return result


# ============================================================================
# ENHANCED CHUNKING WITH TABLE AWARENESS
# ============================================================================

def smart_chunk(text, chunk_size=1000, overlap=150):
    """
    Smart chunking that keeps tables intact.
    """
    chunks = []
    
    # Check if text contains tables (markdown format)
    if '--- EXTRACTED TABLES ---' in text:
        # Split into text and tables sections
        parts = text.split('--- EXTRACTED TABLES ---')
        main_text = parts[0].strip()
        tables_section = parts[1].strip() if len(parts) > 1 else ''
        
        # Chunk main text normally
        if main_text:
            text_chunks = _basic_chunk(main_text, chunk_size, overlap)
            chunks.extend(text_chunks)
        
        # Keep each table as a separate chunk (don't split tables)
        if tables_section:
            table_blocks = re.split(r'\*\*Table \d+:\*\*', tables_section)
            for block in table_blocks:
                block = block.strip()
                if block and '|' in block:  # Has table content
                    # Add context header
                    table_chunk = f"[TECHNICAL TABLE DATA]\n{block}"
                    chunks.append(table_chunk)
    else:
        # No tables detected, chunk normally
        chunks = _basic_chunk(text, chunk_size, overlap)
    
    return chunks


def _basic_chunk(text, chunk_size, overlap):
    """Basic text chunking with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


# ============================================================================
# MAIN INGESTION ENGINE
# ============================================================================

if __name__ == "__main__":
    # Test the parser
    print("=" * 60)
    print("   STRYDA V5 VISION-FIRST ENGINE")
    print("   Testing table detection...")
    print("=" * 60)
    
    # Sample table text
    sample = """
MECHANICAL PROPERTIES

DIAMETER (inches)    PROOF LOAD (lbf)    HARDNESS
1/4                  5460                24-32
5/16                 8700                24-32
3/8                  13150               26-34
1/2                  24000               26-34
5/8                  38400               26-36
"""
    
    parser = VisionFirstParser()
    tables = parser._detect_tables_from_text(sample)
    
    print("\n📊 Detected Tables:")
    for t in tables:
        print(t)
    
    print("\n✅ Vision-First Engine Ready")
