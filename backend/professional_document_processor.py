"""
STRYDA.ai Professional Document Processor
Advanced PDF processing for comprehensive building documents with intelligent chunking
"""

import os
import asyncio
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import aiohttp
import pypdf
from PIL import Image
import pytesseract
import io

logger = logging.getLogger(__name__)

class ProfessionalDocumentProcessor:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.temp_dir = Path("/app/backend/temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Document type detection patterns
        self.document_types = {
            'structural_guide': {
                'patterns': [r'structural\s+guide', r'beam\s+sizing', r'load\s+tables', r'engineering\s+reference'],
                'chunk_size': 3000,  # Large chunks for structural data
                'overlap': 500,
                'min_chunk_size': 1500
            },
            'metal_roofing': {
                'patterns': [r'metal\s+roof', r'roofing\s+code', r'cladding\s+practice', r'fixing\s+requirements'],
                'chunk_size': 2500,  # Medium-large chunks for installation guides
                'overlap': 400,
                'min_chunk_size': 1200
            },
            'building_code': {
                'patterns': [r'nzbc\s+clause', r'building\s+code', r'clause\s+[a-z]\d+'],
                'chunk_size': 2000,  # Standard chunks for building codes
                'overlap': 300,
                'min_chunk_size': 1000
            },
            'manufacturer_spec': {
                'patterns': [r'installation\s+manual', r'product\s+specification', r'technical\s+data'],
                'chunk_size': 2200,  # Good size for installation guides
                'overlap': 350,
                'min_chunk_size': 1100
            },
            'default': {
                'patterns': [],
                'chunk_size': 2000,
                'overlap': 300,
                'min_chunk_size': 1000
            }
        }
        
        # Structural content patterns for better organization
        self.structural_patterns = {
            'load_tables': [
                r'load\s+table', r'span\s+table', r'beam\s+table', r'joist\s+table',
                r'rafter\s+table', r'purlin\s+table', r'lintel\s+table'
            ],
            'calculations': [
                r'design\s+load', r'dead\s+load', r'live\s+load', r'wind\s+load',
                r'seismic\s+load', r'snow\s+load', r'point\s+load', r'distributed\s+load'
            ],
            'specifications': [
                r'material\s+properties', r'steel\s+grade', r'timber\s+grade',
                r'concrete\s+strength', r'fastener\s+requirements', r'connection\s+details'
            ],
            'installation': [
                r'installation\s+procedure', r'fixing\s+method', r'connection\s+detail',
                r'assembly\s+instruction', r'installation\s+sequence'
            ]
        }
    
    def detect_document_type(self, title: str, content_sample: str) -> str:
        """Detect document type for optimal processing"""
        
        combined_text = (title + " " + content_sample).lower()
        
        for doc_type, config in self.document_types.items():
            if doc_type == 'default':
                continue
                
            for pattern in config['patterns']:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    logger.info(f"Detected document type: {doc_type}")
                    return doc_type
        
        logger.info("Using default document type")
        return 'default'
    
    async def process_pdf_with_intelligent_chunking(self, pdf_url: str, title: str, 
                                                  document_type: str = "building_document") -> Dict[str, Any]:
        """Process PDF with intelligent chunking based on document type"""
        
        logger.info(f"🔄 Starting professional PDF processing: {title}")
        
        # Download PDF
        pdf_path = await self._download_pdf(pdf_url, title)
        if not pdf_path:
            raise Exception("Failed to download PDF")
        
        try:
            # Extract full text first
            full_text = await self._extract_full_text(pdf_path)
            if not full_text:
                raise Exception("No text could be extracted from PDF")
            
            # Detect document type
            detected_type = self.detect_document_type(title, full_text[:2000])
            config = self.document_types[detected_type]
            
            logger.info(f"📋 Document type: {detected_type}")
            logger.info(f"⚙️ Chunk size: {config['chunk_size']}, Overlap: {config['overlap']}")
            
            # Create intelligent chunks
            chunks = await self._create_intelligent_chunks(
                full_text, title, pdf_url, config, detected_type
            )
            
            # Store chunks in knowledge base
            stored_chunks = 0
            for chunk_data in chunks:
                try:
                    success = await self.document_processor.store_document(
                        title=chunk_data['title'],
                        content=chunk_data['content'],
                        source_url=pdf_url,
                        document_type=document_type,
                        metadata=chunk_data['metadata']
                    )
                    if success:
                        stored_chunks += 1
                except Exception as e:
                    logger.error(f"Error storing chunk: {e}")
                    continue
            
            logger.info(f"✅ Professional processing complete: {stored_chunks} chunks stored")
            
            return {
                "success": True,
                "chunks_created": stored_chunks,
                "document_type_detected": detected_type,
                "chunk_config": config,
                "processing_method": "professional_intelligent_chunking"
            }
            
        finally:
            # Clean up
            if pdf_path and pdf_path.exists():
                pdf_path.unlink()
    
    async def _download_pdf(self, pdf_url: str, title: str) -> Optional[Path]:
        """Download PDF to temporary location"""
        
        try:
            safe_filename = re.sub(r'[^\w\-_\.]', '_', title)[:100] + '.pdf'
            pdf_path = self.temp_dir / safe_filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        with open(pdf_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        logger.info(f"📥 PDF downloaded: {pdf_path}")
                        return pdf_path
                    else:
                        logger.error(f"HTTP {response.status} downloading PDF: {pdf_url}")
                        
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
        
        return None
    
    async def _extract_full_text(self, pdf_path: Path) -> str:
        """Extract complete text from PDF"""
        
        try:
            full_text = ""
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = pypdf.PdfReader(pdf_file)
                
                logger.info(f"📄 Extracting text from {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        
                        if page_text and len(page_text.strip()) > 50:
                            # Clean and normalize text
                            cleaned_text = self._clean_text(page_text)
                            full_text += f"\n\n=== PAGE {page_num + 1} ===\n\n{cleaned_text}"
                        else:
                            logger.warning(f"Page {page_num + 1}: Limited text extracted")
                            
                    except Exception as e:
                        logger.error(f"Error extracting page {page_num + 1}: {e}")
                        continue
            
            logger.info(f"📝 Extracted {len(full_text)} characters total")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', text)  # Space between numbers and letters
        text = re.sub(r'([A-Za-z])(\d+)', r'\1 \2', text)  # Space between letters and numbers
        
        # Clean up punctuation
        text = re.sub(r'\.{2,}', '...', text)  # Multiple dots to ellipsis
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # Remove space before punctuation
        
        return text.strip()
    
    async def _create_intelligent_chunks(self, full_text: str, title: str, source_url: str,
                                       config: Dict, doc_type: str) -> List[Dict[str, Any]]:
        """Create intelligent chunks based on document type and structure"""
        
        chunks = []
        
        # Detect major sections first
        sections = self._detect_major_sections(full_text, doc_type)
        
        if not sections:
            # Fallback to size-based chunking
            sections = [{"title": title, "content": full_text, "start": 0, "end": len(full_text)}]
        
        logger.info(f"🔍 Detected {len(sections)} major sections")
        
        chunk_id = 1
        for section in sections:
            # Create chunks from each section
            section_chunks = self._chunk_section_intelligently(
                section, config, title, source_url, chunk_id
            )
            chunks.extend(section_chunks)
            chunk_id += len(section_chunks)
        
        logger.info(f"📦 Created {len(chunks)} intelligent chunks")
        return chunks
    
    def _detect_major_sections(self, text: str, doc_type: str) -> List[Dict[str, Any]]:
        """Detect major sections in the document"""
        
        sections = []
        
        if doc_type == 'structural_guide':
            # Look for structural section patterns
            patterns = [
                r'^(\d+\.?\d*)\s+([A-Z][^.\n]+)$',  # 1.1 Section Title
                r'^([A-Z][A-Z\s]+)$',  # ALL CAPS SECTIONS
                r'(LOAD\s+TABLE[S]?.*?)(?=\n\s*\n|\n[A-Z]|\Z)',  # Load tables
                r'(SPAN\s+TABLE[S]?.*?)(?=\n\s*\n|\n[A-Z]|\Z)',  # Span tables
                r'(BEAM\s+SIZING.*?)(?=\n\s*\n|\n[A-Z]|\Z)',  # Beam sizing
            ]
        elif doc_type == 'metal_roofing':
            patterns = [
                r'(\d+\.?\d*\s+[A-Z][^.\n]+)',  # Numbered sections
                r'(INSTALLATION.*?)(?=\n[A-Z]|\Z)',  # Installation sections
                r'(FIXING.*?)(?=\n[A-Z]|\Z)',  # Fixing sections
                r'(COMPLIANCE.*?)(?=\n[A-Z]|\Z)',  # Compliance sections
            ]
        else:
            # Generic section detection
            patterns = [
                r'^(\d+\.?\d*)\s+([A-Z][^.\n]+)$',  # Numbered sections
                r'^([A-Z][A-Z\s]+)$',  # All caps sections
            ]
        
        # Find sections using patterns
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                start_pos = match.start()
                section_title = match.group().strip()
                
                # Find content until next section or end
                next_match = None
                for next_pattern in patterns:
                    next_matches = list(re.finditer(next_pattern, text[start_pos + len(section_title):], re.MULTILINE))
                    if next_matches:
                        if not next_match or next_matches[0].start() < next_match.start():
                            next_match = next_matches[0]
                
                if next_match:
                    end_pos = start_pos + len(section_title) + next_match.start()
                else:
                    end_pos = len(text)
                
                content = text[start_pos:end_pos].strip()
                
                if len(content) > 200:  # Only include substantial sections
                    sections.append({
                        "title": section_title,
                        "content": content,
                        "start": start_pos,
                        "end": end_pos
                    })
        
        # Remove overlapping sections and sort by position
        sections = self._remove_overlapping_sections(sections)
        sections.sort(key=lambda x: x['start'])
        
        return sections
    
    def _remove_overlapping_sections(self, sections: List[Dict]) -> List[Dict]:
        """Remove overlapping sections, keeping the longest ones"""
        
        if not sections:
            return sections
        
        # Sort by start position
        sections.sort(key=lambda x: x['start'])
        
        filtered = [sections[0]]
        
        for section in sections[1:]:
            last_section = filtered[-1]
            
            # Check for overlap
            if section['start'] < last_section['end']:
                # Keep the longer section
                if (section['end'] - section['start']) > (last_section['end'] - last_section['start']):
                    filtered[-1] = section
            else:
                filtered.append(section)
        
        return filtered
    
    def _chunk_section_intelligently(self, section: Dict, config: Dict, 
                                   title: str, source_url: str, start_chunk_id: int) -> List[Dict[str, Any]]:
        """Break a section into intelligent chunks"""
        
        content = section['content']
        section_title = section['title']
        
        chunk_size = config['chunk_size']
        overlap = config['overlap']
        min_chunk_size = config['min_chunk_size']
        
        chunks = []
        
        # If section is small enough, keep as single chunk
        if len(content) <= chunk_size:
            chunks.append({
                'title': f"{title} - {section_title}",
                'content': content,
                'metadata': {
                    'section_title': section_title,
                    'chunk_index': start_chunk_id,
                    'section_length': len(content),
                    'processing_method': 'single_section_chunk'
                }
            })
            return chunks
        
        # Break large sections into overlapping chunks
        chunk_index = start_chunk_id
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at natural boundaries (sentences, paragraphs)
            if end < len(content):
                # Look for paragraph break
                para_break = content.rfind('\n\n', start, end)
                if para_break > start + min_chunk_size:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = content.rfind('. ', start, end)
                    if sent_break > start + min_chunk_size:
                        end = sent_break + 1
            
            chunk_content = content[start:end].strip()
            
            if len(chunk_content) >= min_chunk_size:
                chunks.append({
                    'title': f"{title} - {section_title} (Part {chunk_index - start_chunk_id + 1})",
                    'content': chunk_content,
                    'metadata': {
                        'section_title': section_title,
                        'chunk_index': chunk_index,
                        'section_part': chunk_index - start_chunk_id + 1,
                        'chunk_start': start,
                        'chunk_end': end,
                        'section_length': len(content),
                        'processing_method': 'intelligent_section_chunk'
                    }
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
            
            # Prevent infinite loop
            if start >= len(content) - min_chunk_size:
                break
        
        return chunks


# Global instance for use in server
professional_processor = None

def get_professional_processor(document_processor):
    global professional_processor
    if professional_processor is None:
        professional_processor = ProfessionalDocumentProcessor(document_processor)
    return professional_processor