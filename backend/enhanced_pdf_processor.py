"""
STRYDA.ai Enhanced PDF Processing System
Handles multiple document types: Building Codes, Council Regulations, Manufacturer Specs
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
import io
import json
from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.temp_dir = Path("/app/backend/temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Document type classifications
        self.document_types = {
            'building_code': {
                'patterns': [r'building\s+code', r'nzbc', r'clause\s+[a-z]\d+'],
                'metadata_prefix': 'NZBC'
            },
            'council_regulation': {
                'patterns': [r'council', r'district\s+plan', r'resource\s+consent', r'bylaw'],
                'metadata_prefix': 'COUNCIL'
            },
            'manufacturer_spec': {
                'patterns': [r'installation\s+guide', r'specification', r'datasheet', r'product\s+information'],
                'metadata_prefix': 'MANUFACTURER'
            },
            'nz_standard': {
                'patterns': [r'nzs\s+\d+', r'standards\s+new\s+zealand', r'as/nzs'],
                'metadata_prefix': 'NZS'
            }
        }
        
        # Enhanced clause/section patterns for different document types
        self.extraction_patterns = {
            'building_code': [
                r'^([A-Z]\d+(?:\.\d+)*)\s+(.+)$',  # G5.3.2 Clearances
                r'^(Clause\s+[A-Z]\d+(?:\.\d+)*)\s*[-–]\s*(.+)$',  # Clause G5 - Interior Environment
            ],
            'council_regulation': [
                r'^(Rule\s+\d+(?:\.\d+)*)\s*[-–]?\s*(.+)$',  # Rule 14.2.1 - Height Requirements
                r'^(Section\s+\d+(?:\.\d+)*)\s+(.+)$',  # Section 2.1 General Provisions
            ],
            'manufacturer_spec': [
                r'^(\d+(?:\.\d+)+)\s+(.+)$',  # 3.1.2 Installation Requirements
                r'^([A-Z][A-Z\s]+)$',  # INSTALLATION PROCEDURES
            ],
            'nz_standard': [
                r'^(NZS\s+\d+(?:\.\d+)*)\s+(.+)$',  # NZS 3604.1 Timber Framing
                r'^(\d+(?:\.\d+)+)\s+(.+)$',  # 4.2.1 Connection Details
            ]
        }
    
    async def process_pdf_batch(self, pdf_sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process multiple PDFs in batch"""
        results = {
            'processed': [],
            'failed': [],
            'total_documents': 0,
            'total_chunks': 0
        }
        
        for pdf_info in pdf_sources:
            try:
                result = await self.process_single_pdf(
                    pdf_url=pdf_info['url'],
                    title=pdf_info['title'],
                    document_type=pdf_info.get('type', 'unknown'),
                    source_organization=pdf_info.get('organization', 'Unknown')
                )
                
                if result['success']:
                    results['processed'].append(result)
                    results['total_documents'] += result['documents_created']
                    results['total_chunks'] += result['chunks_created']
                else:
                    results['failed'].append({
                        'title': pdf_info['title'],
                        'url': pdf_info['url'],
                        'error': result['error']
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process PDF {pdf_info['title']}: {e}")
                results['failed'].append({
                    'title': pdf_info['title'],
                    'url': pdf_info['url'],
                    'error': str(e)
                })
        
        return results
    
    async def process_single_pdf(self, pdf_url: str, title: str, document_type: str = 'unknown', 
                                source_organization: str = 'Unknown') -> Dict[str, Any]:
        """Process a single PDF with intelligent structure detection"""
        
        logger.info(f"Processing PDF: {title} ({document_type})")
        
        try:
            # Download PDF
            pdf_path = await self._download_pdf(pdf_url, title)
            if not pdf_path:
                return {'success': False, 'error': 'Failed to download PDF'}
            
            # Extract and process content
            processing_result = await self._process_pdf_content(
                pdf_path, title, pdf_url, document_type, source_organization
            )
            
            # Cleanup
            pdf_path.unlink()
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing PDF {title}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _download_pdf(self, pdf_url: str, title: str) -> Optional[Path]:
        """Download PDF from URL"""
        try:
            safe_filename = re.sub(r'[^\w\-_\.]', '_', title)[:50] + '.pdf'
            pdf_path = self.temp_dir / safe_filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        with open(pdf_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return pdf_path
                    else:
                        logger.error(f"Failed to download PDF: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    async def _process_pdf_content(self, pdf_path: Path, title: str, pdf_url: str, 
                                  document_type: str, source_organization: str) -> Dict[str, Any]:
        """Extract and process PDF content with document type awareness"""
        
        try:
            # Extract text content
            text_content = await self._extract_pdf_text(pdf_path)
            if not text_content:
                return {'success': False, 'error': 'Failed to extract text from PDF'}
            
            # Detect document type if unknown
            if document_type == 'unknown':
                document_type = self._detect_document_type(text_content, title)
            
            # Process content based on document type
            processed_sections = self._extract_structured_content(text_content, document_type)
            
            # Create documents and chunks
            documents_created = 0
            chunks_created = 0
            
            for section in processed_sections:
                # Create document
                doc_id = await self.document_processor.store_document({
                    'title': f"{title} - {section['title']}",
                    'content': section['content'],
                    'source_url': pdf_url,
                    'document_type': document_type,
                    'source_organization': source_organization,
                    'section_type': section['section_type'],
                    'metadata': section['metadata']
                })
                
                if doc_id:
                    documents_created += 1
                    
                    # Create chunks for this document
                    chunks = await self.document_processor.create_chunks(
                        content=section['content'],
                        document_id=doc_id,
                        metadata={
                            'document_type': document_type,
                            'source_organization': source_organization,
                            'section_title': section['title'],
                            'section_type': section['section_type'],
                            'keywords': section['metadata'].get('keywords', [])
                        }
                    )
                    chunks_created += len(chunks)
            
            logger.info(f"PDF processed: {documents_created} documents, {chunks_created} chunks")
            
            return {
                'success': True,
                'title': title,
                'documents_created': documents_created,
                'chunks_created': chunks_created,
                'document_type': document_type,
                'source_organization': source_organization
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF content: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        try:
            text_content = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _detect_document_type(self, content: str, title: str) -> str:
        """Detect document type based on content and title"""
        content_lower = content.lower()
        title_lower = title.lower()
        
        for doc_type, config in self.document_types.items():
            for pattern in config['patterns']:
                if re.search(pattern, content_lower) or re.search(pattern, title_lower):
                    return doc_type
        
        return 'unknown'
    
    def _extract_structured_content(self, content: str, document_type: str) -> List[Dict[str, Any]]:
        """Extract structured content based on document type"""
        
        sections = []
        lines = content.split('\n')
        current_section = {
            'title': 'Introduction',
            'content': '',
            'section_type': 'general',
            'metadata': {'keywords': []}
        }
        
        patterns = self.extraction_patterns.get(document_type, [])
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            section_match = None
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    section_match = match
                    break
            
            if section_match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    current_section['metadata']['keywords'] = self._extract_keywords(
                        current_section['content'], document_type
                    )
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': section_match.group(2) if len(section_match.groups()) > 1 else section_match.group(1),
                    'content': line + '\n',
                    'section_type': self._classify_section_type(line, document_type),
                    'metadata': {'section_number': section_match.group(1), 'keywords': []}
                }
            else:
                # Add line to current section
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            current_section['metadata']['keywords'] = self._extract_keywords(
                current_section['content'], document_type
            )
            sections.append(current_section)
        
        return sections
    
    def _classify_section_type(self, line: str, document_type: str) -> str:
        """Classify the type of section based on content"""
        line_lower = line.lower()
        
        classification_rules = {
            'building_code': {
                'compliance': ['requirement', 'shall', 'must', 'compliance'],
                'specification': ['dimension', 'material', 'thickness', 'strength'],
                'procedure': ['install', 'construct', 'apply', 'method']
            },
            'manufacturer_spec': {
                'installation': ['install', 'assembly', 'mounting', 'fixing'],
                'specification': ['dimension', 'weight', 'capacity', 'performance'],
                'maintenance': ['maintenance', 'cleaning', 'service', 'repair']
            }
        }
        
        rules = classification_rules.get(document_type, {})
        for section_type, keywords in rules.items():
            if any(keyword in line_lower for keyword in keywords):
                return section_type
        
        return 'general'
    
    def _extract_keywords(self, content: str, document_type: str) -> List[str]:
        """Extract relevant keywords from content based on document type"""
        content_lower = content.lower()
        keywords = []
        
        # Common building terms
        building_terms = [
            'installation', 'requirement', 'specification', 'clearance', 'dimension',
            'material', 'thickness', 'strength', 'compliance', 'safety', 'fire',
            'structural', 'insulation', 'weatherproof', 'foundation', 'framing'
        ]
        
        for term in building_terms:
            if term in content_lower:
                keywords.append(term)
        
        # Document-specific terms
        if document_type == 'building_code':
            nzbc_terms = ['clause', 'nzbc', 'building code', 'acceptable solution', 'verification method']
            for term in nzbc_terms:
                if term in content_lower:
                    keywords.append(term.replace(' ', '_'))
        
        return list(set(keywords))  # Remove duplicates
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current PDF processing status"""
        try:
            # Get document counts from MongoDB directly
            db = self.document_processor.db
            
            # Get total document count
            total_documents = await db.processed_documents.count_documents({})
            
            # Get total chunk count
            total_chunks = await db.document_chunks.count_documents({})
            
            # Get documents by type
            pipeline = [
                {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
            ]
            doc_counts = await db.processed_documents.aggregate(pipeline).to_list(100)
            documents_by_type = {item["_id"]: item["count"] for item in doc_counts}
            
            return {
                'total_documents': total_documents,
                'total_chunks': total_chunks,
                'documents_by_type': documents_by_type,
                'temp_files': len(list(self.temp_dir.glob('*.pdf'))),
                'processing_ready': True
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'documents_by_type': {},
                'temp_files': 0,
                'processing_ready': False,
                'error': str(e)
            }