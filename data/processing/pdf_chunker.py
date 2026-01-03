#!/usr/bin/env python3
"""
STRYDA Big Brain - PDF Chunker with Table Extraction
Extracts text and tables from PDFs while preserving structure
Uses pdfplumber for layout-aware extraction
"""

import os
import sys
import json
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

import pdfplumber
from tabulate import tabulate

# Configuration
CHUNK_SIZE = 1500  # Target characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
TABLE_PRIORITY = True  # Prioritize table extraction

@dataclass
class DocumentChunk:
    """Represents a single chunk of extracted content"""
    chunk_id: str
    source: str
    page: int
    content: str
    chunk_type: str  # 'text', 'table', 'mixed'
    section: Optional[str] = None
    table_data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PDFChunker:
    """Extracts and chunks PDF content with table awareness"""
    
    def __init__(self, output_dir: str = "/app/data/processing"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def extract_tables_from_page(self, page) -> List[Dict]:
        """Extract tables from a single page"""
        tables = []
        try:
            # Extract tables with explicit settings
            page_tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3,
            })
            
            for idx, table in enumerate(page_tables):
                if table and len(table) > 1:  # At least header + 1 row
                    # Clean up table data
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [cell.strip() if cell else "" for cell in row]
                        if any(cleaned_row):  # Skip empty rows
                            cleaned_table.append(cleaned_row)
                    
                    if cleaned_table:
                        # Try to identify headers
                        headers = cleaned_table[0] if cleaned_table else []
                        data_rows = cleaned_table[1:] if len(cleaned_table) > 1 else []
                        
                        # Convert to markdown format for better LLM understanding
                        table_text = self._table_to_markdown(headers, data_rows)
                        
                        tables.append({
                            "index": idx,
                            "headers": headers,
                            "rows": data_rows,
                            "row_count": len(data_rows),
                            "col_count": len(headers),
                            "markdown": table_text
                        })
        except Exception as e:
            print(f"   ⚠️ Table extraction error: {e}")
        
        return tables
    
    def _table_to_markdown(self, headers: List[str], rows: List[List[str]]) -> str:
        """Convert table to markdown format"""
        if not headers or not rows:
            return ""
        
        try:
            return tabulate(rows, headers=headers, tablefmt="pipe")
        except:
            # Fallback to simple format
            lines = []
            lines.append(" | ".join(headers))
            lines.append(" | ".join(["---"] * len(headers)))
            for row in rows:
                lines.append(" | ".join(str(cell) for cell in row))
            return "\n".join(lines)
    
    def extract_text_from_page(self, page) -> str:
        """Extract text from a single page"""
        try:
            text = page.extract_text() or ""
            # Clean up text
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            return text
        except Exception as e:
            print(f"   ⚠️ Text extraction error: {e}")
            return ""
    
    def identify_section(self, text: str) -> Optional[str]:
        """Try to identify section headers in text"""
        # Common section patterns in GIB documents
        patterns = [
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)',  # "1. Section Name"
            r'^([A-Z]{2,}[A-Z\s]+)',  # "SECTION NAME"
            r'^(GIB\s+[A-Za-z]+\s+[A-Za-z]+)',  # "GIB Product Name"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[:200], re.MULTILINE)
            if match:
                return match.group(1).strip()[:100]
        
        return None
    
    def chunk_text(self, text: str, page_num: int, source: str) -> List[DocumentChunk]:
        """Split text into chunks with overlap"""
        chunks = []
        
        if not text or len(text) < 100:
            return chunks
        
        # Split into sentences/paragraphs
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < CHUNK_SIZE:
                current_chunk += " " + sentence
            else:
                if current_chunk.strip():
                    section = self.identify_section(current_chunk)
                    chunk_id = f"{source}_p{page_num}_c{chunk_idx}"
                    
                    chunks.append(DocumentChunk(
                        chunk_id=chunk_id,
                        source=source,
                        page=page_num,
                        content=current_chunk.strip(),
                        chunk_type="text",
                        section=section,
                        metadata={"char_count": len(current_chunk)}
                    ))
                    chunk_idx += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else ""
                current_chunk = overlap_text + " " + sentence
        
        # Don't forget the last chunk
        if current_chunk.strip() and len(current_chunk) > 100:
            section = self.identify_section(current_chunk)
            chunk_id = f"{source}_p{page_num}_c{chunk_idx}"
            
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                source=source,
                page=page_num,
                content=current_chunk.strip(),
                chunk_type="text",
                section=section,
                metadata={"char_count": len(current_chunk)}
            ))
        
        return chunks
    
    def process_pdf(self, pdf_path: str, doc_metadata: Dict = None) -> List[DocumentChunk]:
        """Process a single PDF file"""
        source_name = os.path.basename(pdf_path).replace('.pdf', '').replace('_', ' ')
        print(f"\n📄 Processing: {source_name}")
        
        all_chunks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   📖 Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Progress indicator
                    if page_num % 20 == 0 or page_num == 1:
                        print(f"   📃 Processing page {page_num}/{total_pages}...")
                    
                    # Extract tables first (priority)
                    tables = self.extract_tables_from_page(page)
                    
                    for table in tables:
                        if table['row_count'] > 0:
                            # Create table chunk with markdown representation
                            table_content = f"TABLE DATA:\n{table['markdown']}"
                            
                            chunk_id = f"{source_name}_p{page_num}_table{table['index']}"
                            
                            all_chunks.append(DocumentChunk(
                                chunk_id=chunk_id,
                                source=source_name,
                                page=page_num,
                                content=table_content,
                                chunk_type="table",
                                section=None,
                                table_data={
                                    "headers": table['headers'],
                                    "row_count": table['row_count'],
                                    "col_count": table['col_count']
                                },
                                metadata={"extraction_method": "pdfplumber_table"}
                            ))
                    
                    # Extract text
                    text = self.extract_text_from_page(page)
                    text_chunks = self.chunk_text(text, page_num, source_name)
                    all_chunks.extend(text_chunks)
                
                print(f"   ✅ Extracted {len(all_chunks)} chunks ({sum(1 for c in all_chunks if c.chunk_type == 'table')} tables)")
        
        except Exception as e:
            print(f"   ❌ Error processing {pdf_path}: {e}")
        
        return all_chunks
    
    def process_directory(self, input_dir: str, manifest: Dict = None) -> Dict:
        """Process all PDFs in a directory"""
        print("=" * 60)
        print("🧠 STRYDA Big Brain - PDF Chunker")
        print("=" * 60)
        print(f"\n📁 Input directory: {input_dir}")
        
        # Find all PDFs
        pdf_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        print(f"📚 Found {len(pdf_files)} PDF files")
        
        all_chunks = []
        results = {
            "input_dir": input_dir,
            "processed_at": datetime.now().isoformat(),
            "files_processed": [],
            "total_chunks": 0,
            "table_chunks": 0,
            "text_chunks": 0
        }
        
        for pdf_path in pdf_files:
            # Get metadata from manifest if available
            doc_meta = None
            if manifest:
                for doc in manifest.get('documents', []):
                    if doc.get('local_path') == pdf_path:
                        doc_meta = doc
                        break
            
            chunks = self.process_pdf(pdf_path, doc_meta)
            all_chunks.extend(chunks)
            
            results["files_processed"].append({
                "path": pdf_path,
                "chunks": len(chunks),
                "tables": sum(1 for c in chunks if c.chunk_type == 'table')
            })
        
        # Calculate stats
        results["total_chunks"] = len(all_chunks)
        results["table_chunks"] = sum(1 for c in all_chunks if c.chunk_type == 'table')
        results["text_chunks"] = sum(1 for c in all_chunks if c.chunk_type == 'text')
        
        # Save chunks to JSON
        output_file = os.path.join(self.output_dir, "chunks.json")
        chunks_data = [chunk.to_dict() for chunk in all_chunks]
        
        with open(output_file, 'w') as f:
            json.dump(chunks_data, f, indent=2)
        
        print(f"\n" + "=" * 60)
        print(f"📊 PROCESSING SUMMARY")
        print(f"=" * 60)
        print(f"   📄 Files processed: {len(pdf_files)}")
        print(f"   📦 Total chunks: {results['total_chunks']}")
        print(f"   📋 Table chunks: {results['table_chunks']}")
        print(f"   📝 Text chunks: {results['text_chunks']}")
        print(f"\n💾 Chunks saved to: {output_file}")
        
        return results, all_chunks


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF Chunker for Big Brain")
    parser.add_argument("--input", "-i", required=True, help="Input directory with PDFs")
    parser.add_argument("--output", "-o", default="/app/data/processing", help="Output directory")
    parser.add_argument("--manifest", "-m", help="Path to manifest.json for metadata")
    
    args = parser.parse_args()
    
    chunker = PDFChunker(output_dir=args.output)
    
    manifest = None
    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest) as f:
            manifest = json.load(f)
    
    results, chunks = chunker.process_directory(args.input, manifest)
    
    # Save results
    results_file = os.path.join(args.output, "processing_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
