"""
STRYDA.ai PDF Processing System
Specialized for processing NZ Building Code PDFs with intelligent structure recognition
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

class BuildingCodePDFProcessor:
    def __init__(self, document_processor):
        self.document_processor = document_processor
        self.temp_dir = Path("/app/backend/temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        
        # NZ Building Code structure patterns
        self.clause_patterns = [
            r'^([A-Z]\d+(?:\.\d+)*)\s+(.+)$',  # G5.3.2 Clearances
            r'^(Clause\s+[A-Z]\d+(?:\.\d+)*)\s*[-–]\s*(.+)$',  # Clause G5 - Interior Environment
            r'^([A-Z]\d+)\s+(.+)$',  # G5 Interior Environment
            r'^(\d+(?:\.\d+)+)\s+(.+)$',  # 7.5.1 General requirements
        ]
        
        self.section_patterns = [
            r'^PART\s+([A-Z]+)\s*[-–]\s*(.+)$',  # PART G - SERVICES AND FACILITIES
            r'^([A-Z][A-Z\s]+)$',  # GENERAL REQUIREMENTS (all caps)
            r'^([A-Z][a-z][^.!?]*[^.!?\s])$',  # Capitalized section titles
        ]
        
        # Common NZ Building Code terms for metadata
        self.building_code_terms = {
            'structure': ['foundation', 'beam', 'column', 'load', 'seismic', 'structural'],
            'fire_safety': ['fire', 'flame', 'smoke', 'fireplace', 'hearth', 'clearance', 'combustible'],
            'weathertightness': ['weather', 'moisture', 'water', 'cladding', 'flashing', 'cavity'],
            'insulation': ['thermal', 'insulation', 'r-value', 'energy', 'climate', 'zone'],
            'safety': ['safety', 'protection', 'hazard', 'toxic', 'asbestos', 'ventilation'],
            'accessibility': ['access', 'disability', 'ramp', 'door', 'width', 'gradient'],
            'services': ['plumbing', 'drainage', 'electrical', 'lighting', 'water', 'waste']
        }
    
    async def download_and_process_pdf(self, pdf_url: str, title: str = "NZ Building Code Handbook") -> Dict[str, Any]:
        """Download PDF from URL and process it completely"""
        
        logger.info(f"Starting download and processing of PDF: {title}")
        
        # Download PDF
        pdf_path = await self._download_pdf(pdf_url, title)
        if not pdf_path:
            raise Exception("Failed to download PDF")
        
        try:
            # Process PDF content
            processing_result = await self._process_building_code_pdf(pdf_path, title, pdf_url)
            
            # Clean up temp file
            pdf_path.unlink()
            
            return processing_result
            
        except Exception as e:
            # Clean up on error
            if pdf_path.exists():
                pdf_path.unlink()
            raise e
    
    async def _download_pdf(self, pdf_url: str, title: str) -> Optional[Path]:
        """Download PDF from URL to temp directory"""
        
        try:
            logger.info(f"Downloading PDF from: {pdf_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download PDF: HTTP {response.status}")
                        return None
                    
                    # Create filename
                    filename = f"{hashlib.md5(title.encode()).hexdigest()}.pdf"
                    pdf_path = self.temp_dir / filename
                    
                    # Download file
                    with open(pdf_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    logger.info(f"PDF downloaded successfully: {pdf_path}")
                    return pdf_path
                    
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    async def _process_building_code_pdf(self, pdf_path: Path, title: str, source_url: str) -> Dict[str, Any]:
        """Process NZ Building Code PDF with intelligent structure recognition"""
        
        logger.info(f"Processing Building Code PDF: {pdf_path}")
        
        processing_stats = {
            "pdf_path": str(pdf_path),
            "title": title,
            "source_url": source_url,
            "total_pages": 0,
            "pages_processed": 0,
            "sections_found": 0,
            "clauses_found": 0,
            "chunks_created": 0,
            "processing_errors": [],
            "started_at": datetime.now().isoformat()
        }
        
        try:
            # Open PDF
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = pypdf.PdfReader(pdf_file)
                processing_stats["total_pages"] = len(pdf_reader.pages)
                
                logger.info(f"PDF has {processing_stats['total_pages']} pages")
                
                # Process PDF in sections
                current_section = None
                current_clause = None
                accumulated_content = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        # Extract text from page
                        page_text = page.extract_text()
                        
                        if not page_text or len(page_text.strip()) < 50:
                            # Try OCR if text extraction failed
                            page_text = await self._ocr_page_if_needed(pdf_path, page_num)
                        
                        if page_text:
                            # Process page content
                            page_sections = await self._process_page_content(
                                page_text, page_num, current_section, current_clause
                            )
                            
                            # Update tracking
                            if page_sections.get("new_section"):
                                current_section = page_sections["new_section"]
                                processing_stats["sections_found"] += 1
                            
                            if page_sections.get("new_clause"):
                                current_clause = page_sections["new_clause"]
                                processing_stats["clauses_found"] += 1
                            
                            # Accumulate content
                            accumulated_content.extend(page_sections.get("content_blocks", []))
                            
                            processing_stats["pages_processed"] += 1
                            
                            # Process accumulated content in batches
                            if len(accumulated_content) >= 20:  # Process every 20 content blocks
                                await self._process_content_batch(
                                    accumulated_content, title, source_url, processing_stats
                                )
                                accumulated_content = []
                    
                    except Exception as e:
                        processing_stats["processing_errors"].append(f"Page {page_num}: {str(e)}")
                        logger.error(f"Error processing page {page_num}: {e}")
                        continue
                
                # Process remaining content
                if accumulated_content:
                    await self._process_content_batch(
                        accumulated_content, title, source_url, processing_stats
                    )
                
                processing_stats["completed_at"] = datetime.now().isoformat()
                logger.info(f"PDF processing completed: {processing_stats['chunks_created']} chunks created")
                
                return processing_stats
                
        except Exception as e:
            processing_stats["processing_errors"].append(f"Fatal error: {str(e)}")
            logger.error(f"Fatal error processing PDF: {e}")
            raise e
    
    async def _process_page_content(self, page_text: str, page_num: int, 
                                  current_section: Optional[str], current_clause: Optional[str]) -> Dict[str, Any]:
        """Process individual page content and identify structure"""
        
        result = {
            "content_blocks": [],
            "new_section": None,
            "new_clause": None
        }
        
        lines = page_text.split('\n')
        current_block = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for new section
            section_match = self._match_section_pattern(line)
            if section_match:
                # Save current block if it exists
                if current_block:
                    result["content_blocks"].append({
                        "type": "content",
                        "content": '\n'.join(current_block),
                        "page_number": page_num,
                        "section": current_section,
                        "clause": current_clause
                    })
                    current_block = []
                
                result["new_section"] = section_match
                result["content_blocks"].append({
                    "type": "section_header",
                    "content": line,
                    "page_number": page_num,
                    "section": section_match,
                    "clause": None
                })
                continue
            
            # Check for new clause
            clause_match = self._match_clause_pattern(line)
            if clause_match:
                # Save current block if it exists
                if current_block:
                    result["content_blocks"].append({
                        "type": "content",
                        "content": '\n'.join(current_block),
                        "page_number": page_num,
                        "section": current_section,
                        "clause": current_clause
                    })
                    current_block = []
                
                result["new_clause"] = clause_match
                result["content_blocks"].append({
                    "type": "clause_header",
                    "content": line,
                    "page_number": page_num,
                    "section": current_section,
                    "clause": clause_match
                })
                continue
            
            # Regular content line
            current_block.append(line)
        
        # Add final block
        if current_block:
            result["content_blocks"].append({
                "type": "content",
                "content": '\n'.join(current_block),
                "page_number": page_num,
                "section": current_section,
                "clause": current_clause
            })
        
        return result
    
    def _match_section_pattern(self, line: str) -> Optional[str]:
        """Match line against section patterns"""
        
        for pattern in self.section_patterns:
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1)} - {match.group(2)}"
                else:
                    return match.group(1)
        
        return None
    
    def _match_clause_pattern(self, line: str) -> Optional[str]:
        """Match line against clause patterns"""
        
        for pattern in self.clause_patterns:
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1)} {match.group(2)}"
                else:
                    return match.group(1)
        
        return None
    
    async def _process_content_batch(self, content_blocks: List[Dict[str, Any]], 
                                   title: str, source_url: str, stats: Dict[str, Any]):
        """Process a batch of content blocks into document chunks"""
        
        # Group related content blocks into documents
        grouped_content = self._group_content_blocks(content_blocks)
        
        for group in grouped_content:
            try:
                # Create document content
                content_parts = []
                metadata = {
                    "document_type": "nzbc",
                    "pdf_source": True,
                    "section": group.get("section"),
                    "clause": group.get("clause"),
                    "page_numbers": group.get("page_numbers", []),
                    "categories": [],
                    "tags": ["nzbc", "building_code", "official"]
                }
                
                # Build content
                if group.get("section"):
                    content_parts.append(f"SECTION: {group['section']}")
                
                if group.get("clause"):
                    content_parts.append(f"CLAUSE: {group['clause']}")
                
                content_parts.extend(group["content_blocks"])
                content_text = '\n\n'.join(content_parts)
                
                # Add category based on content analysis
                categories = self._categorize_content(content_text)
                metadata["categories"] = categories
                metadata["tags"].extend(categories)
                
                # Create title for chunk
                chunk_title = f"{title}"
                if group.get("clause"):
                    chunk_title += f" - {group['clause']}"
                elif group.get("section"):
                    chunk_title += f" - {group['section']}"
                
                # Process and store document
                doc_id = await self.document_processor.process_and_store_document(
                    title=chunk_title,
                    content=content_text,
                    source_url=source_url,
                    document_type="nzbc",
                    metadata=metadata
                )
                
                stats["chunks_created"] += 1
                logger.info(f"Created chunk: {chunk_title[:100]}...")
                
            except Exception as e:
                stats["processing_errors"].append(f"Error processing content group: {str(e)}")
                logger.error(f"Error processing content group: {e}")
    
    def _group_content_blocks(self, content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group related content blocks into logical documents"""
        
        groups = []
        current_group = {
            "section": None,
            "clause": None,
            "content_blocks": [],
            "page_numbers": []
        }
        
        for block in content_blocks:
            # Start new group on section/clause headers
            if block["type"] in ["section_header", "clause_header"]:
                # Save current group if it has content
                if current_group["content_blocks"]:
                    groups.append(current_group.copy())
                
                # Start new group
                current_group = {
                    "section": block.get("section") or current_group["section"],
                    "clause": block.get("clause") or current_group["clause"],
                    "content_blocks": [block["content"]],
                    "page_numbers": [block["page_number"]]
                }
            else:
                # Add to current group
                current_group["content_blocks"].append(block["content"])
                if block["page_number"] not in current_group["page_numbers"]:
                    current_group["page_numbers"].append(block["page_number"])
                
                # If content section gets too large, split it
                total_content = '\n'.join(current_group["content_blocks"])
                if len(total_content) > 3000:  # Max 3000 characters per chunk
                    groups.append(current_group.copy())
                    current_group = {
                        "section": current_group["section"],
                        "clause": current_group["clause"],
                        "content_blocks": [],
                        "page_numbers": []
                    }
        
        # Add final group
        if current_group["content_blocks"]:
            groups.append(current_group)
        
        return groups
    
    def _categorize_content(self, content: str) -> List[str]:
        """Categorize content based on NZ Building Code terms"""
        
        content_lower = content.lower()
        categories = []
        
        for category, terms in self.building_code_terms.items():
            for term in terms:
                if term in content_lower:
                    categories.append(category)
                    break
        
        return categories
    
    async def _ocr_page_if_needed(self, pdf_path: Path, page_num: int) -> Optional[str]:
        """Use OCR to extract text from page if regular extraction failed"""
        
        try:
            # This is a placeholder - would require more complex PDF to image conversion
            # For now, return None to skip OCR
            logger.warning(f"OCR needed for page {page_num} but not implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary PDF files"""
        
        try:
            for temp_file in self.temp_dir.glob("*.pdf"):
                temp_file.unlink()
            logger.info("Temporary PDF files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")