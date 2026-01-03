#!/usr/bin/env python3
"""
STRYDA Big Brain - PDF Chunker v2 with Vision
Extracts text, tables, AND diagrams from PDFs
Uses GPT-4o-mini for diagram captioning to make visuals searchable
"""

import os
import sys
import json
import hashlib
import re
import base64
import io
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

import pdfplumber
from PIL import Image
from tabulate import tabulate
from openai import OpenAI

# Add backend to path
sys.path.insert(0, '/app/backend-minimal')
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

# Configuration
CHUNK_SIZE = 1500  # Target characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
MIN_IMAGE_WIDTH = 150  # Minimum width to process (ignore icons)
MIN_IMAGE_HEIGHT = 150  # Minimum height to process
MIN_IMAGE_AREA = 30000  # Minimum area (w*h) to process
VISION_MODEL = "gpt-4o-mini"  # Cost-effective vision model
VISION_ENABLED = True  # Master switch for vision processing

# OpenAI client for vision
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@dataclass
class DocumentChunk:
    """Represents a single chunk of extracted content"""
    chunk_id: str
    source: str
    page: int
    content: str
    chunk_type: str  # 'text', 'table', 'diagram', 'mixed'
    section: Optional[str] = None
    table_data: Optional[Dict] = None
    diagram_data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class VisionPDFChunker:
    """Extracts and chunks PDF content with table AND diagram awareness"""
    
    def __init__(self, output_dir: str = "/app/data/processing", enable_vision: bool = True):
        self.output_dir = output_dir
        self.enable_vision = enable_vision and VISION_ENABLED
        self.openai_client = None
        
        if self.enable_vision and OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Stats tracking
        self.stats = {
            "pages_processed": 0,
            "images_found": 0,
            "images_captioned": 0,
            "tables_extracted": 0,
            "vision_errors": 0
        }
    
    def extract_images_from_page(self, page, page_num: int, pdf_path: str) -> List[Dict]:
        """Extract significant images from a page"""
        images = []
        
        try:
            # Get page images
            page_images = page.images
            
            for idx, img in enumerate(page_images):
                # Calculate dimensions
                width = img.get('width', 0) or (img.get('x1', 0) - img.get('x0', 0))
                height = img.get('height', 0) or (img.get('top', 0) - img.get('bottom', 0))
                
                # Skip small images (likely icons, logos)
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    continue
                
                area = width * height
                if area < MIN_IMAGE_AREA:
                    continue
                
                self.stats["images_found"] += 1
                
                images.append({
                    "index": idx,
                    "page": page_num,
                    "width": width,
                    "height": height,
                    "area": area,
                    "x0": img.get('x0', 0),
                    "y0": img.get('top', 0),
                    "stream": img.get('stream', None)
                })
        
        except Exception as e:
            print(f"   ⚠️ Image extraction error on page {page_num}: {e}")
        
        return images
    
    def render_page_region_to_image(self, page, bbox: Tuple[float, float, float, float]) -> Optional[bytes]:
        """Render a region of the page to an image"""
        try:
            # Crop and render the page region
            cropped = page.crop(bbox)
            img = cropped.to_image(resolution=150)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
        except Exception as e:
            print(f"   ⚠️ Page region render error: {e}")
            return None
    
    def render_full_page_to_image(self, page) -> Optional[bytes]:
        """Render full page to image for vision analysis"""
        try:
            img = page.to_image(resolution=100)  # Lower res for full page
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
        except Exception as e:
            print(f"   ⚠️ Full page render error: {e}")
            return None
    
    def caption_image_with_vision(self, image_bytes: bytes, context: str = "") -> Optional[str]:
        """Send image to GPT-4o-mini for captioning"""
        if not self.openai_client or not self.enable_vision:
            return None
        
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Build prompt
            prompt = """Analyze this construction detail/diagram from a building product installation manual.

Describe in technical terms:
1. What components are shown (e.g., cladding, framing, flashings, fixings)
2. Key measurements or spacings if visible
3. Assembly order or installation sequence if shown
4. Any critical details like overlaps, gaps, or minimum clearances

Keep the description concise but technically accurate. Use NZ/AU construction terminology.
If this is not a construction diagram (e.g., it's a logo or decorative image), just say "Non-technical image"."""

            if context:
                prompt += f"\n\nPage context: {context[:200]}"
            
            response = self.openai_client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "low"  # Cost optimization
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            caption = response.choices[0].message.content
            
            # Filter out non-technical responses
            if caption and "non-technical" not in caption.lower():
                self.stats["images_captioned"] += 1
                return caption
            
            return None
            
        except Exception as e:
            self.stats["vision_errors"] += 1
            print(f"   ⚠️ Vision API error: {e}")
            return None
    
    def extract_tables_from_page(self, page) -> List[Dict]:
        """Extract tables from a single page"""
        tables = []
        try:
            page_tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3,
            })
            
            for idx, table in enumerate(page_tables):
                if table and len(table) > 1:
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [cell.strip() if cell else "" for cell in row]
                        if any(cleaned_row):
                            cleaned_table.append(cleaned_row)
                    
                    if cleaned_table:
                        headers = cleaned_table[0] if cleaned_table else []
                        data_rows = cleaned_table[1:] if len(cleaned_table) > 1 else []
                        
                        table_text = self._table_to_markdown(headers, data_rows)
                        
                        self.stats["tables_extracted"] += 1
                        
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
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            print(f"   ⚠️ Text extraction error: {e}")
            return ""
    
    def identify_section(self, text: str) -> Optional[str]:
        """Try to identify section headers in text"""
        patterns = [
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)',
            r'^([A-Z]{2,}[A-Z\s]+)',
            r'^(James\s+Hardie|Linea|Axon|Hardie)',
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
                
                overlap_text = current_chunk[-CHUNK_OVERLAP:] if len(current_chunk) > CHUNK_OVERLAP else ""
                current_chunk = overlap_text + " " + sentence
        
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
        """Process a single PDF file with vision support"""
        source_name = os.path.basename(pdf_path).replace('.pdf', '').replace('_', ' ')
        print(f"\n📄 Processing: {source_name}")
        print(f"   👁️ Vision: {'ENABLED' if self.enable_vision else 'DISABLED'}")
        
        all_chunks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   📖 Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.stats["pages_processed"] += 1
                    
                    if page_num % 10 == 0 or page_num == 1:
                        print(f"   📃 Processing page {page_num}/{total_pages}...")
                    
                    # 1. Extract tables first
                    tables = self.extract_tables_from_page(page)
                    for table in tables:
                        if table['row_count'] > 0:
                            table_content = f"TABLE DATA:\n{table['markdown']}"
                            chunk_id = f"{source_name}_p{page_num}_table{table['index']}"
                            
                            all_chunks.append(DocumentChunk(
                                chunk_id=chunk_id,
                                source=source_name,
                                page=page_num,
                                content=table_content,
                                chunk_type="table",
                                table_data={
                                    "headers": table['headers'],
                                    "row_count": table['row_count'],
                                    "col_count": table['col_count']
                                },
                                metadata={"extraction_method": "pdfplumber_table"}
                            ))
                    
                    # 2. Extract text
                    text = self.extract_text_from_page(page)
                    text_chunks = self.chunk_text(text, page_num, source_name)
                    all_chunks.extend(text_chunks)
                    
                    # 3. Vision Pass - Process diagrams
                    if self.enable_vision:
                        images = self.extract_images_from_page(page, page_num, pdf_path)
                        
                        if images:
                            # Render full page for vision analysis
                            page_image = self.render_full_page_to_image(page)
                            
                            if page_image:
                                # Get caption for page with diagrams
                                context = text[:300] if text else ""
                                caption = self.caption_image_with_vision(page_image, context)
                                
                                if caption:
                                    diagram_content = f"DIAGRAM DESCRIPTION:\n{caption}\n\nPage context: {context[:200]}"
                                    chunk_id = f"{source_name}_p{page_num}_diagram"
                                    
                                    all_chunks.append(DocumentChunk(
                                        chunk_id=chunk_id,
                                        source=source_name,
                                        page=page_num,
                                        content=diagram_content,
                                        chunk_type="diagram",
                                        diagram_data={
                                            "image_count": len(images),
                                            "caption_length": len(caption)
                                        },
                                        metadata={
                                            "extraction_method": "vision_gpt4o",
                                            "has_diagram": True
                                        }
                                    ))
                
                # Summary
                table_count = sum(1 for c in all_chunks if c.chunk_type == 'table')
                diagram_count = sum(1 for c in all_chunks if c.chunk_type == 'diagram')
                print(f"   ✅ Extracted {len(all_chunks)} chunks ({table_count} tables, {diagram_count} diagrams)")
        
        except Exception as e:
            print(f"   ❌ Error processing {pdf_path}: {e}")
        
        return all_chunks
    
    def process_directory(self, input_dir: str, manifest: Dict = None) -> Tuple[Dict, List[DocumentChunk]]:
        """Process all PDFs in a directory"""
        print("=" * 60)
        print("🧠 STRYDA Big Brain - Vision PDF Chunker v2")
        print("=" * 60)
        print(f"\n📁 Input directory: {input_dir}")
        print(f"👁️ Vision processing: {'ENABLED' if self.enable_vision else 'DISABLED'}")
        
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
            "vision_enabled": self.enable_vision,
            "files_processed": [],
            "total_chunks": 0,
            "table_chunks": 0,
            "text_chunks": 0,
            "diagram_chunks": 0,
            "stats": {}
        }
        
        for pdf_path in pdf_files:
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
                "tables": sum(1 for c in chunks if c.chunk_type == 'table'),
                "diagrams": sum(1 for c in chunks if c.chunk_type == 'diagram')
            })
        
        results["total_chunks"] = len(all_chunks)
        results["table_chunks"] = sum(1 for c in all_chunks if c.chunk_type == 'table')
        results["text_chunks"] = sum(1 for c in all_chunks if c.chunk_type == 'text')
        results["diagram_chunks"] = sum(1 for c in all_chunks if c.chunk_type == 'diagram')
        results["stats"] = self.stats
        
        # Save chunks
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
        print(f"   🖼️ Diagram chunks: {results['diagram_chunks']}")
        print(f"   👁️ Images found: {self.stats['images_found']}")
        print(f"   ✨ Images captioned: {self.stats['images_captioned']}")
        print(f"\n💾 Chunks saved to: {output_file}")
        
        return results, all_chunks


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vision PDF Chunker for Big Brain")
    parser.add_argument("--input", "-i", required=True, help="Input directory with PDFs")
    parser.add_argument("--output", "-o", default="/app/data/processing", help="Output directory")
    parser.add_argument("--manifest", "-m", help="Path to manifest.json for metadata")
    parser.add_argument("--no-vision", action="store_true", help="Disable vision processing")
    
    args = parser.parse_args()
    
    chunker = VisionPDFChunker(
        output_dir=args.output,
        enable_vision=not args.no_vision
    )
    
    manifest = None
    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest) as f:
            manifest = json.load(f)
    
    results, chunks = chunker.process_directory(args.input, manifest)
    
    results_file = os.path.join(args.output, "processing_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
