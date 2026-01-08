#!/usr/bin/env python3
"""
STRYDA Librarian v3.0 - Enhanced PDF Ingestion Pipeline
========================================================

Quality Control Features:
1. Garbage Cleaning - Removes OCR noise, headers/footers, fixes hyphenation
2. Smart Chunking - RecursiveCharacterTextSplitter with sentence boundaries
3. Auto-Tagging - Automatic compliance/product classification from filename

Usage:
    from librarian_v3 import STRYDALibrarian
    
    librarian = STRYDALibrarian()
    chunks = librarian.process_pdf("path/to/document.pdf", brand_name="Expol")
    # Chunks are cleaned, smartly split, and auto-tagged
"""

import os
import sys
import re
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

# Add backend to path for env vars
sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# =============================================================================
# AUTO-TAGGING RULES (Agent Classification)
# =============================================================================

# Filename patterns that indicate COMPLIANCE documents (Inspector domain)
COMPLIANCE_FILENAME_PATTERNS = [
    # Standards
    r'nzs[\s_-]?\d+',           # NZS 3604, NZS-4229, etc.
    r'as/nzs',                   # AS/NZS standards
    r'acceptable[\s_-]?solution', # Acceptable Solution
    r'verification[\s_-]?method', # Verification Method
    r'as1|as2|as3|vm1|vm2',      # AS1, VM1, etc.
    # Building Code
    r'nzbc',                     # New Zealand Building Code
    r'building[\s_-]?code',
    r'building[\s_-]?act',
    r'clause[\s_-]?\d+',         # Clause references
    # Regulatory
    r'amendment',
    r'legislation',
    r'mbie',
    r'council[\s_-]?guide',
    r'compliance',
    r'code[\s_-]?of[\s_-]?practice',
]

# Filename patterns that indicate PRODUCT documents (Product Rep domain)
PRODUCT_FILENAME_PATTERNS = [
    # Data Sheets
    r'data[\s_-]?sheet',
    r'tds',                      # Technical Data Sheet
    r'spec[\s_-]?sheet',
    # Guides
    r'installation[\s_-]?guide',
    r'design[\s_-]?guide',
    r'user[\s_-]?guide',
    r'manual',
    # Product Documentation
    r'appraisal',
    r'branz',
    r'codemark',
    r'certificate',
    r'certification',
    r'product[\s_-]?info',
    r'warranty',
    r'brochure',
    r'catalogue',
    r'catalog',
]

# Doc type mappings for auto-tagging
COMPLIANCE_DOC_TYPES = [
    'Building_Code', 'Building_Code_Compliance', 'Compliance_Document',
    'standard', 'NZS_Standard', 'acceptable_solution', 'verification_method',
    'legislation', 'MBIE_Guidance', 'council_guide'
]

PRODUCT_DOC_TYPES = [
    'Technical_Data_Sheet', 'Installation_Guide', 'Product_Manual',
    'Appraisal', 'BRANZ_Appraisal', 'Certification', 'Spec_Sheet', 'Warranty'
]

# =============================================================================
# GARBAGE CLEANING FUNCTIONS
# =============================================================================

def clean_ocr_garbage(text: str) -> str:
    """
    Remove OCR noise and artifacts from extracted text.
    
    Handles:
    - Lines with >50% non-alphanumeric characters
    - Isolated single characters and fragments
    - Excessive whitespace and control characters
    - Inline OCR garbage sequences (e.g., "c 6 o x4 n m tin m u o...")
    """
    # First pass: Clean inline garbage sequences
    # Pattern: 5+ consecutive short tokens (1-3 chars each) - typical OCR garbage
    # Matches sequences like: 'c 6 o x4 n m tin m u o b u u s t r y u l n se s a o l f a nt'
    text = re.sub(r'(?:(?<![a-zA-Z])[a-zA-Z0-9]{1,3}\s+){5,}[a-zA-Z0-9]{1,3}(?![a-zA-Z])', '', text)
    
    # Clean up double spaces left behind
    text = re.sub(r'\s{2,}', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip empty lines (but preserve paragraph breaks)
        if not line.strip():
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            continue
        
        # Calculate alphanumeric ratio
        stripped = line.strip()
        if len(stripped) < 3:
            continue  # Skip very short fragments
            
        alphanumeric_chars = sum(1 for c in stripped if c.isalnum() or c.isspace())
        ratio = alphanumeric_chars / len(stripped) if stripped else 0
        
        # Filter out garbage lines (>50% non-alphanumeric)
        if ratio < 0.5:
            continue
            
        # Skip lines that look like OCR artifacts (random character sequences)
        if is_ocr_artifact(stripped):
            continue
            
        cleaned_lines.append(stripped)
    
    return '\n'.join(cleaned_lines)


def is_ocr_artifact(line: str) -> bool:
    """
    Detect if a line is likely OCR garbage.
    
    Patterns detected:
    - Random letters/numbers: "c 6 o x4 0H z"
    - Excessive spacing between characters: "C l i c k h e r e"
    - Unicode junk
    - Very short words repeated
    """
    words = line.split()
    
    # Check for excessive spaces between single characters
    single_char_count = sum(1 for w in words if len(w) == 1)
    if len(words) > 3 and single_char_count / len(words) > 0.4:
        return True
    
    # Check for too many very short words (1-2 chars)
    short_word_count = sum(1 for w in words if len(w) <= 2)
    if len(words) > 4 and short_word_count / len(words) > 0.5:
        return True
    
    # Check for lines with mostly uppercase single letters and numbers
    if len(words) > 3:
        gibberish_pattern = sum(1 for w in words if len(w) <= 2 and (w.isupper() or w.isdigit()))
        if gibberish_pattern / len(words) > 0.4:
            return True
    
    # Check for common OCR garbage patterns
    garbage_patterns = [
        r'^[\s\d\W]+$',                    # Only whitespace, digits, special chars
        r'^[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]',  # Spaced single letters at start
        r'[^\x00-\x7F]{3,}',               # Too many non-ASCII chars in sequence
        r'^[!@#$%^&*()]+',                 # Starts with special chars
        r'[!@#$%^&*]{3,}',                 # Multiple special chars in sequence
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, line):
            return True
    
    # Check average word length - OCR garbage tends to have very short avg word length
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 2.5 and len(words) > 3:
            return True
    
    return False


def remove_headers_footers(text: str, threshold: int = 3) -> str:
    """
    Remove repeated headers and footers that appear on multiple pages.
    
    Args:
        text: Full document text
        threshold: Minimum occurrences to consider as header/footer
    """
    lines = text.split('\n')
    
    # Count occurrences of each line (normalized)
    line_counts = Counter()
    for line in lines:
        normalized = line.strip().lower()
        if 10 < len(normalized) < 150:  # Typical header/footer length
            line_counts[normalized] += 1
    
    # Find lines that appear multiple times (likely headers/footers)
    repeated_lines = {line for line, count in line_counts.items() if count >= threshold}
    
    # Filter out repeated headers/footers
    cleaned_lines = []
    for line in lines:
        normalized = line.strip().lower()
        if normalized not in repeated_lines:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def fix_hyphenation(text: str) -> str:
    """
    Fix hyphenated line breaks common in PDF extraction.
    
    Converts:
    - "in-\nstallation" → "installation"
    - "com-\npliance" → "compliance"
    """
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    
    # Also handle with spaces after newline
    text = re.sub(r'(\w)-\n\s*(\w)', r'\1\2', text)
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize excessive whitespace while preserving paragraph structure.
    """
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Collapse multiple spaces into one
    text = re.sub(r' +', ' ', text)
    
    # Collapse multiple newlines (more than 2) into double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from each line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
    return text.strip()


def full_text_cleaning(text: str) -> str:
    """
    Apply all garbage cleaning steps in sequence.
    """
    # Step 1: Fix hyphenation first (before other processing)
    text = fix_hyphenation(text)
    
    # Step 2: Remove headers/footers
    text = remove_headers_footers(text)
    
    # Step 3: Clean OCR garbage
    text = clean_ocr_garbage(text)
    
    # Step 4: Normalize whitespace
    text = normalize_whitespace(text)
    
    return text


# =============================================================================
# SMART CHUNKING (Sentence-Boundary Aware)
# =============================================================================

class RecursiveTextSplitter:
    """
    Recursive Character Text Splitter with sentence boundary awareness.
    
    Features:
    - Tries to split at paragraph breaks first, then sentences, then words
    - Configurable chunk size and overlap
    - Never cuts mid-sentence if possible
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Priority order of separators (try each in sequence)
        self.separators = separators or [
            "\n\n",      # Paragraph breaks (highest priority)
            "\n",        # Line breaks
            ". ",        # Sentence endings
            ".\n",       # Sentence + newline
            "? ",        # Questions
            "! ",        # Exclamations
            "; ",        # Semicolons
            ", ",        # Commas
            " ",         # Words (last resort)
        ]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting sentence boundaries.
        """
        return self._split_text_recursive(text, self.separators)
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separator hierarchy."""
        final_chunks = []
        
        # Try each separator in order
        separator = separators[0] if separators else ""
        remaining_separators = separators[1:] if len(separators) > 1 else []
        
        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)  # Character-level split as last resort
        
        # Process splits
        current_chunk = ""
        
        for split in splits:
            # Add separator back (except for whitespace-only separators at end)
            split_with_sep = split + separator if separator and separator.strip() else split
            
            # Check if adding this split exceeds chunk size
            test_chunk = current_chunk + split_with_sep
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is complete
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                
                # Start new chunk
                # If this single split is too large, recursively split it
                if len(split_with_sep) > self.chunk_size and remaining_separators:
                    sub_chunks = self._split_text_recursive(split_with_sep, remaining_separators)
                    final_chunks.extend(sub_chunks[:-1] if sub_chunks else [])
                    current_chunk = sub_chunks[-1] if sub_chunks else split_with_sep
                else:
                    current_chunk = split_with_sep
        
        # Don't forget the last chunk
        if current_chunk.strip():
            final_chunks.append(current_chunk.strip())
        
        # Apply overlap
        if self.chunk_overlap > 0:
            final_chunks = self._add_overlap(final_chunks)
        
        return final_chunks
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between chunks for context continuity."""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Get the last N characters from previous chunk for overlap
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # Find a clean break point in the overlap (sentence/word boundary)
            clean_break = self._find_clean_break(overlap_text)
            if clean_break > 0:
                overlap_text = overlap_text[clean_break:]
            
            # Prepend overlap to current chunk
            overlapped_chunk = overlap_text + " " + curr_chunk if overlap_text else curr_chunk
            overlapped_chunks.append(overlapped_chunk.strip())
        
        return overlapped_chunks
    
    def _find_clean_break(self, text: str) -> int:
        """Find a clean break point (sentence/word boundary) in text."""
        # Look for sentence boundaries
        for pattern in ['. ', '.\n', '? ', '! ']:
            idx = text.find(pattern)
            if idx > 0:
                return idx + len(pattern)
        
        # Fall back to word boundary
        idx = text.find(' ')
        return idx + 1 if idx > 0 else 0


# =============================================================================
# AUTO-TAGGING (Agent Classification)
# =============================================================================

def auto_tag_document(filename: str, content_sample: str = "") -> Dict[str, str]:
    """
    Automatically classify document as compliance or product based on filename and content.
    
    Returns:
        {
            'agent_domain': 'inspector' | 'product_rep' | 'general',
            'doc_type': Suggested doc_type based on patterns,
            'confidence': 'high' | 'medium' | 'low'
        }
    """
    filename_lower = filename.lower()
    content_lower = content_sample.lower() if content_sample else ""
    
    # Check for compliance patterns
    compliance_score = 0
    for pattern in COMPLIANCE_FILENAME_PATTERNS:
        if re.search(pattern, filename_lower):
            compliance_score += 2
        if content_sample and re.search(pattern, content_lower):
            compliance_score += 1
    
    # Check for product patterns
    product_score = 0
    for pattern in PRODUCT_FILENAME_PATTERNS:
        if re.search(pattern, filename_lower):
            product_score += 2
        if content_sample and re.search(pattern, content_lower):
            product_score += 1
    
    # Determine domain and doc_type
    if compliance_score > product_score and compliance_score >= 2:
        domain = 'inspector'
        doc_type = detect_compliance_doc_type(filename_lower)
        confidence = 'high' if compliance_score >= 4 else 'medium'
    elif product_score > compliance_score and product_score >= 2:
        domain = 'product_rep'
        doc_type = detect_product_doc_type(filename_lower)
        confidence = 'high' if product_score >= 4 else 'medium'
    else:
        domain = 'general'
        doc_type = 'General_Document'
        confidence = 'low'
    
    return {
        'agent_domain': domain,
        'doc_type': doc_type,
        'confidence': confidence,
        'compliance_score': compliance_score,
        'product_score': product_score
    }


def detect_compliance_doc_type(filename: str) -> str:
    """Detect specific compliance doc_type from filename."""
    if re.search(r'nzs[\s_-]?\d+', filename):
        return 'NZS_Standard'
    if re.search(r'acceptable[\s_-]?solution|as[1-9]', filename):
        return 'acceptable_solution'
    if re.search(r'verification[\s_-]?method|vm[1-9]', filename):
        return 'verification_method'
    if re.search(r'nzbc|building[\s_-]?code', filename):
        return 'Building_Code'
    if re.search(r'amendment', filename):
        return 'Compliance_Document'
    if re.search(r'mbie', filename):
        return 'MBIE_Guidance'
    if re.search(r'council', filename):
        return 'council_guide'
    return 'Compliance_Document'


def detect_product_doc_type(filename: str) -> str:
    """Detect specific product doc_type from filename."""
    if re.search(r'data[\s_-]?sheet|tds', filename):
        return 'Technical_Data_Sheet'
    if re.search(r'installation', filename):
        return 'Installation_Guide'
    if re.search(r'appraisal|branz', filename):
        return 'BRANZ_Appraisal'
    if re.search(r'manual|guide', filename):
        return 'Product_Manual'
    if re.search(r'certificate|certification|codemark', filename):
        return 'Certification'
    if re.search(r'warranty', filename):
        return 'Warranty'
    if re.search(r'spec[\s_-]?sheet', filename):
        return 'Spec_Sheet'
    return 'Technical_Data_Sheet'


# =============================================================================
# MAIN LIBRARIAN CLASS
# =============================================================================

@dataclass
class IngestionConfig:
    """Configuration for PDF ingestion."""
    brand_name: str = "Unknown"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    clean_ocr: bool = True
    remove_headers: bool = True
    fix_hyphenation: bool = True
    auto_tag: bool = True
    # Override auto-tagging
    force_doc_type: Optional[str] = None
    force_agent_domain: Optional[str] = None


class STRYDALibrarian:
    """
    The STRYDA Librarian - Quality-controlled PDF ingestion pipeline.
    
    Features:
    1. Garbage Cleaning - OCR noise removal
    2. Smart Chunking - Sentence-boundary aware splitting
    3. Auto-Tagging - Automatic agent domain classification
    """
    
    def __init__(self):
        self.splitter = RecursiveTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.stats = {
            'pages_processed': 0,
            'chunks_created': 0,
            'chars_cleaned': 0,
            'documents_tagged': {'inspector': 0, 'product_rep': 0, 'general': 0}
        }
    
    def process_pdf(
        self, 
        pdf_path: str, 
        config: IngestionConfig = None
    ) -> List[Dict]:
        """
        Process a PDF file through the full pipeline.
        
        Returns:
            List of chunk dictionaries ready for embedding and insertion
        """
        if config is None:
            config = IngestionConfig()
        
        # Update splitter settings
        self.splitter.chunk_size = config.chunk_size
        self.splitter.chunk_overlap = config.chunk_overlap
        
        filename = os.path.basename(pdf_path)
        print(f"\n📚 LIBRARIAN: Processing '{filename}'")
        
        # Step 1: Extract text from PDF
        print(f"   📄 Extracting text...")
        pages = self._extract_pdf_text(pdf_path)
        
        if not pages:
            print(f"   ❌ No text extracted from PDF")
            return []
        
        print(f"   ✅ Extracted {len(pages)} pages")
        self.stats['pages_processed'] += len(pages)
        
        # Step 2: Auto-tag document
        first_page_text = pages[0]['text'][:2000] if pages else ""
        tags = auto_tag_document(filename, first_page_text)
        
        # Allow config overrides
        if config.force_doc_type:
            tags['doc_type'] = config.force_doc_type
        if config.force_agent_domain:
            tags['agent_domain'] = config.force_agent_domain
        
        print(f"   🏷️ Auto-tagged: {tags['agent_domain']} / {tags['doc_type']} ({tags['confidence']})")
        self.stats['documents_tagged'][tags['agent_domain']] += 1
        
        # Step 3: Process each page
        all_chunks = []
        
        for page in pages:
            page_num = page['page']
            raw_text = page['text']
            
            original_len = len(raw_text)
            
            # Apply garbage cleaning
            if config.clean_ocr or config.remove_headers or config.fix_hyphenation:
                cleaned_text = raw_text
                
                if config.fix_hyphenation:
                    cleaned_text = fix_hyphenation(cleaned_text)
                
                if config.clean_ocr:
                    cleaned_text = clean_ocr_garbage(cleaned_text)
                
                cleaned_text = normalize_whitespace(cleaned_text)
                
                self.stats['chars_cleaned'] += original_len - len(cleaned_text)
            else:
                cleaned_text = raw_text
            
            # Skip pages with minimal content
            if len(cleaned_text.strip()) < 50:
                continue
            
            # Step 4: Smart chunking
            page_chunks = self.splitter.split_text(cleaned_text)
            
            # Build chunk metadata
            for i, chunk_text in enumerate(page_chunks):
                chunk = {
                    'content': chunk_text,
                    'source': filename.replace('.pdf', ''),
                    'source_file': filename,
                    'page': page_num,
                    'chunk_index': i,
                    'brand_name': config.brand_name,
                    'doc_type': tags['doc_type'],
                    'agent_domain': tags['agent_domain'],
                    'snippet': chunk_text[:200],
                    'section': None,  # Can be enhanced with section detection
                    'clause': None,   # Can be enhanced with clause detection
                }
                all_chunks.append(chunk)
        
        self.stats['chunks_created'] += len(all_chunks)
        print(f"   ✅ Created {len(all_chunks)} chunks (avg {config.chunk_size} chars)")
        print(f"   🧹 Cleaned {self.stats['chars_cleaned']} chars of garbage")
        
        return all_chunks
    
    def _extract_pdf_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF using available library.
        Returns list of {'page': int, 'text': str}
        """
        pages = []
        
        # Try pdfplumber first (best for tables)
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append({'page': i + 1, 'text': text})
            return pages
        except ImportError:
            pass
        except Exception as e:
            print(f"   ⚠️ pdfplumber error: {e}")
        
        # Try PyMuPDF (fitz) as fallback
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                text = page.get_text()
                pages.append({'page': i + 1, 'text': text})
            doc.close()
            return pages
        except ImportError:
            pass
        except Exception as e:
            print(f"   ⚠️ PyMuPDF error: {e}")
        
        # Try pypdf as last resort
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({'page': i + 1, 'text': text})
            return pages
        except ImportError:
            pass
        except Exception as e:
            print(f"   ⚠️ pypdf error: {e}")
        
        print("   ❌ No PDF library available (install pdfplumber, PyMuPDF, or pypdf)")
        return []
    
    def process_text(
        self,
        text: str,
        source_name: str,
        page_num: int = 1,
        config: IngestionConfig = None
    ) -> List[Dict]:
        """
        Process raw text (non-PDF) through the pipeline.
        Useful for JSON imports or text files.
        """
        if config is None:
            config = IngestionConfig()
        
        # Clean the text
        cleaned_text = full_text_cleaning(text) if config.clean_ocr else text
        
        # Auto-tag
        tags = auto_tag_document(source_name, cleaned_text[:2000])
        
        # Chunk
        chunks = self.splitter.split_text(cleaned_text)
        
        # Build chunk metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk = {
                'content': chunk_text,
                'source': source_name,
                'page': page_num,
                'chunk_index': i,
                'brand_name': config.brand_name,
                'doc_type': tags['doc_type'],
                'agent_domain': tags['agent_domain'],
                'snippet': chunk_text[:200],
            }
            result.append(chunk)
        
        return result
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return self.stats.copy()


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Command-line interface for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='STRYDA Librarian - PDF Ingestion Pipeline')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--brand', default='Unknown', help='Brand name')
    parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size')
    parser.add_argument('--overlap', type=int, default=200, help='Chunk overlap')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    # Process PDF
    librarian = STRYDALibrarian()
    config = IngestionConfig(
        brand_name=args.brand,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap
    )
    
    chunks = librarian.process_pdf(args.pdf_path, config)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(chunks, f, indent=2)
        print(f"\n💾 Saved {len(chunks)} chunks to {args.output}")
    else:
        print(f"\n📊 Summary:")
        print(f"   Pages: {librarian.stats['pages_processed']}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Chars cleaned: {librarian.stats['chars_cleaned']}")
        
        if chunks:
            print(f"\n📝 Sample chunk:")
            print(f"   Source: {chunks[0]['source']}")
            print(f"   Doc Type: {chunks[0]['doc_type']}")
            print(f"   Agent Domain: {chunks[0]['agent_domain']}")
            print(f"   Content: {chunks[0]['content'][:200]}...")


if __name__ == '__main__':
    main()
