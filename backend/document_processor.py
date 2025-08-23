"""
STRYDA.ai Enhanced Document Processing System
Handles NZ Building Code documents, manufacturer manuals, and compliance data
"""

import os
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import aiohttp
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pypdf
from PIL import Image
import pytesseract
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentChunk(BaseModel):
    """Represents a processed document chunk with metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    document_type: str  # 'nzbc', 'mbie', 'nzs', 'manufacturer', 'council'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    embeddings: Optional[List[float]] = None

class ProcessedDocument(BaseModel):
    """Represents a fully processed document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source_url: str
    document_type: str
    content_hash: str
    total_chunks: int
    metadata: Dict[str, Any]
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: Optional[datetime] = None

class DocumentProcessor:
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: str):
        self.mongo_client = mongo_client
        self.db = mongo_client[db_name]
        
        # Initialize ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path="/app/backend/chroma_db",
            settings=Settings(allow_reset=True)
        )
        
        # Get or create collection for NZ building documents
        self.collection = self.chroma_client.get_or_create_collection(
            name="nz_building_knowledge",
            metadata={"description": "NZ Building Code and related documents"}
        )
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Priority NZ Building Code URLs (from Gemini's research)
        self.priority_sources = {
            "nzbc_main": "https://www.building.govt.nz/building-code-compliance/",
            "mbie_acceptable": "https://www.building.govt.nz/assets/Uploads/building-code/",
            "nzs_3604": "https://www.standards.govt.nz/shop/nzs-36042011",
            "branz": "https://www.branz.co.nz/",
            "lbp_api": "https://portal.api.business.govt.nz/api/lbp"
        }
        
    async def initialize_knowledge_base(self):
        """Initialize the knowledge base with priority NZ building documents"""
        logger.info("Initializing STRYDA.ai knowledge base...")
        
        # Start with mock high-priority documents (replace with real scraping)
        await self._load_priority_documents()
        
        logger.info("Knowledge base initialization complete!")
    
    async def _load_priority_documents(self):
        """Load priority NZ Building Code documents and create mock knowledge base"""
        
        # Priority 1: NZ Building Code Core Documents
        nzbc_docs = [
            {
                "title": "NZBC Clause G5 - Interior Environment (Solid Fuel Appliances)",
                "content": """
                G5.3 Solid fuel burning appliances
                
                G5.3.1 General requirements
                Solid fuel burning appliances must be installed to prevent fire risk to the building and occupants.
                
                G5.3.2 Clearances to combustible materials
                Minimum clearances from solid fuel burning appliances to combustible materials:
                - Front clearance: 1000mm minimum from front of fireplace opening
                - Side clearances: 300mm minimum from sides of appliance to combustible walls
                - Rear clearance: 300mm minimum from rear of appliance to combustible materials
                - Hearth extension: Must extend 400mm in front of opening and 150mm each side
                
                G5.3.3 Hearth construction
                Hearths must be constructed of non-combustible materials with minimum thickness:
                - Concrete hearths: 100mm minimum thickness
                - Brick/stone hearths: 100mm minimum thickness on concrete base
                - Metal hearths: Must be insulated underneath with non-combustible material
                
                G5.3.4 Manufacturer specifications
                All installations must comply with manufacturer's installation instructions.
                Where manufacturer specifications are more stringent than NZBC minimums, 
                manufacturer specifications take precedence.
                
                Reference: Building Code Clause G5, Building Regulations 1992
                """,
                "source_url": "https://www.building.govt.nz/building-code-compliance/g-services-and-facilities/g5-interior-environment/",
                "document_type": "nzbc",
                "metadata": {
                    "clause": "G5",
                    "section": "Interior Environment",
                    "category": "fire_safety",
                    "tags": ["hearth", "fireplace", "clearances", "solid_fuel", "appliances"]
                }
            },
            {
                "title": "NZBC Clause H1 - Energy Efficiency (Insulation Requirements)",
                "content": """
                H1.2 Thermal insulation requirements
                
                H1.2.1 Climate zones
                New Zealand is divided into three climate zones for insulation requirements:
                - Zone 1: Northland, Auckland, Bay of Plenty, Gisborne (warmer)
                - Zone 2: Most of North Island, Nelson, Marlborough 
                - Zone 3: Canterbury, Otago, Southland, Central North Island (cooler)
                
                H1.2.2 Minimum R-values for residential buildings
                Wall insulation (bulk insulation):
                - Zone 1: R-1.5 minimum
                - Zone 2: R-1.8 minimum  
                - Zone 3: R-2.0 minimum
                
                Ceiling/roof insulation:
                - Zone 1: R-2.9 minimum
                - Zone 2: R-3.3 minimum
                - Zone 3: R-3.6 minimum
                
                Floor insulation:
                - All zones: R-1.3 minimum (suspended floors)
                - Concrete slabs: R-0.64 minimum perimeter insulation
                
                H1.2.3 Thermal bridging
                Continuous insulation must be provided to minimize thermal bridging.
                Steel frame construction requires special consideration for thermal bridging.
                
                H1.2.4 Windows and glazing
                Maximum window to floor area ratio: 30% unless energy modeling demonstrates compliance
                
                Reference: Building Code Clause H1, Acceptable Solution H1/AS1
                """,
                "source_url": "https://www.building.govt.nz/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/",
                "document_type": "nzbc", 
                "metadata": {
                    "clause": "H1",
                    "section": "Energy Efficiency",
                    "category": "insulation",
                    "tags": ["insulation", "r-values", "climate_zones", "thermal", "energy"]
                }
            },
            {
                "title": "NZBC Clause E2 - External Moisture (Weathertightness)",
                "content": """
                E2.1 External moisture requirements
                
                E2.1.1 General
                Buildings must be constructed to prevent external moisture penetration that could cause:
                - Damage to building elements
                - Health problems for occupants
                - Loss of amenity
                
                E2.1.2 Cladding systems
                All external cladding systems must:
                - Shed water away from the building
                - Prevent water penetration to the building frame
                - Allow any water that penetrates to drain out
                
                E2.1.3 Acceptable Solutions - E2/AS1
                Provides deemed-to-comply solutions for:
                - Wind zones and exposure
                - Cladding materials and installation
                - Flashing and sealing details
                - Cavity systems
                
                E2.1.4 Critical design elements
                Particular attention required for:
                - Window and door installations
                - Roof and wall junctions  
                - Penetrations through cladding
                - Horizontal surfaces
                
                E2.1.5 Material compatibility
                Materials in contact must be compatible to prevent:
                - Galvanic corrosion between dissimilar metals
                - Chemical reactions that could cause deterioration
                - Refer to E2/AS1 Table 21 for material compatibility matrix
                
                Reference: Building Code Clause E2, Acceptable Solution E2/AS1
                """,
                "source_url": "https://www.building.govt.nz/building-code-compliance/e-moisture/e2-external-moisture/",
                "document_type": "nzbc",
                "metadata": {
                    "clause": "E2", 
                    "section": "External Moisture",
                    "category": "weathertightness",
                    "tags": ["weathertight", "moisture", "cladding", "external", "flashing"]
                }
            }
        ]
        
        # Priority 2: NZS 3604 Timber Framing Standard
        nzs_3604_docs = [
            {
                "title": "NZS 3604:2011 - Timber Framing Requirements (Dwangs and Nogs)",
                "content": """
                NZS 3604:2011 Section 7 - Wall Framing
                
                7.5 Dwangs and nogs
                
                7.5.1 General requirements
                Dwangs (horizontal blocking) and nogs must be provided to:
                - Provide lateral restraint to wall studs
                - Support cladding fixings
                - Provide fixing points for internal linings
                
                7.5.2 Spacing requirements
                Maximum spacing of dwangs/nogs:
                - Standard walls: 1350mm maximum spacing vertically
                - High wind areas: 1200mm maximum spacing
                - Where cladding requires closer fixings: As per cladding manufacturer requirements
                
                7.5.3 Size requirements  
                Minimum dwang/nog sizes:
                - 90 x 45mm timber (same as stud size)
                - Must be full width between studs
                - Blocking must be tight fitting
                
                7.5.4 Installation
                - Dwangs must be skew nailed to studs with minimum 2 x 75mm nails each end
                - Metal dwang hangers may be used as alternative
                - Ensure dwangs are level for cladding attachment
                
                7.5.5 Braced wall requirements
                In braced walls, additional dwangs may be required:
                - Refer to bracing schedule for specific requirements
                - Plywood bracing sheets require dwangs at sheet edges
                
                Reference: NZS 3604:2011 New Zealand Standard for Timber-framed Buildings
                """,
                "source_url": "https://www.standards.govt.nz/shop/nzs-36042011",
                "document_type": "nzs",
                "metadata": {
                    "standard": "NZS 3604:2011",
                    "section": "Wall Framing", 
                    "category": "timber_framing",
                    "tags": ["dwangs", "nogs", "timber", "framing", "studs", "spacing"]
                }
            }
        ]
        
        # Priority 3: Common Manufacturer Specifications (Mock examples)
        manufacturer_docs = [
            {
                "title": "Metrofires Installation Manual - Solid Fuel Fireplaces",
                "content": """
                Metrofires Installation Requirements
                
                Model: All solid fuel fireplace units
                
                Clearance Requirements:
                IMPORTANT: These clearances are MINIMUM requirements. Local building codes may require greater clearances.
                
                Timber Floor Installation:
                - Front clearance: 400mm minimum from fireplace opening to combustible materials
                - Side clearances: 200mm minimum from fireplace body to combustible walls  
                - Rear clearance: 50mm minimum from rear of fireplace to combustible wall
                - Hearth pad required: 1200mm x 1200mm minimum, non-combustible material
                
                Concrete Floor Installation:
                - Front clearance: 300mm minimum (reduced due to non-combustible floor)
                - Side clearances: 200mm minimum (same as timber floor)
                - Rear clearance: 50mm minimum (same as timber floor)
                - Hearth pad: Still required for ember protection
                
                Approved Hearth Materials:
                - Natural stone (minimum 20mm thick)
                - Concrete pavers (minimum 40mm thick)
                - Ceramic tiles on concrete substrate
                - Steel hearth plates with insulation underneath
                
                NOT APPROVED:
                - Timber of any type
                - Carpet or vinyl flooring
                - Thin tiles without adequate substrate
                
                Flue Requirements:
                - Must comply with NZS 4513 for solid fuel appliances
                - Minimum 150mm diameter flue for most models
                - Flue must extend minimum 600mm above roof penetration
                
                Installation Notes:
                - All installations must be certified by registered installer
                - Building consent required for all installations
                - Refer to NZBC Clause G5 for additional requirements
                
                Contact: Metrofires NZ - 0800 METRO-1
                """,
                "source_url": "https://www.metrofires.co.nz/installation-guide",
                "document_type": "manufacturer",
                "metadata": {
                    "manufacturer": "Metrofires",
                    "product_type": "solid_fuel_fireplace",
                    "category": "installation_manual",
                    "tags": ["metrofires", "fireplace", "installation", "clearances", "hearth"]
                }
            }
        ]
        
        # Process and store all priority documents
        all_docs = nzbc_docs + nzs_3604_docs + manufacturer_docs
        
        for doc in all_docs:
            await self.process_and_store_document(
                title=doc["title"],
                content=doc["content"], 
                source_url=doc["source_url"],
                document_type=doc["document_type"],
                metadata=doc["metadata"]
            )
            
        logger.info(f"Loaded {len(all_docs)} priority documents into knowledge base")
    
    async def process_and_store_document(self, title: str, content: str, source_url: str, 
                                       document_type: str, metadata: Dict[str, Any]) -> str:
        """Process a document and store it in both MongoDB and ChromaDB"""
        
        # Create document hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check if document already exists
        existing_doc = await self.db.processed_documents.find_one({"content_hash": content_hash})
        if existing_doc:
            logger.info(f"Document already processed: {title}")
            return existing_doc["id"]
        
        # Create processed document record
        doc = ProcessedDocument(
            title=title,
            source_url=source_url,
            document_type=document_type,
            content_hash=content_hash,
            total_chunks=0,
            metadata=metadata
        )
        
        # Chunk the document intelligently
        chunks = await self._intelligent_chunk_document(content, title, metadata)
        doc.total_chunks = len(chunks)
        
        # Generate embeddings and store chunks
        chunk_records = []
        for i, chunk_content in enumerate(chunks):
            # Generate embedding
            embedding = self.embedding_model.encode(chunk_content).tolist()
            
            # Create chunk record
            chunk = DocumentChunk(
                document_id=doc.id,
                content=chunk_content,
                metadata={**metadata, "chunk_of": title},
                chunk_index=i,
                source_url=source_url,
                section_title=self._extract_section_title(chunk_content),
                document_type=document_type,
                embeddings=embedding
            )
            
            # Store in MongoDB
            await self.db.document_chunks.insert_one(chunk.dict())
            chunk_records.append(chunk)
            
            # Store in ChromaDB for vector search
            self.collection.add(
                documents=[chunk_content],
                metadatas=[{
                    "document_id": doc.id,
                    "chunk_id": chunk.id,
                    "source_url": source_url,
                    "document_type": document_type,
                    "title": title,
                    "section_title": chunk.section_title or "",
                    "tags": ",".join(metadata.get("tags", [])),  # Convert list to comma-separated string
                    "clause": metadata.get("clause", ""),
                    "category": metadata.get("category", ""),
                    "manufacturer": metadata.get("manufacturer", "")
                }],
                ids=[chunk.id],
                embeddings=[embedding]
            )
        
        # Store document record
        await self.db.processed_documents.insert_one(doc.dict())
        
        logger.info(f"Processed document '{title}' into {len(chunks)} chunks")
        return doc.id
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics"""
        try:
            # Get document counts
            total_documents = await self.db.processed_documents.count_documents({})
            
            # Get chunk counts  
            total_chunks = await self.db.document_chunks.count_documents({})
            
            # Get documents by type
            pipeline = [
                {"$group": {"_id": "$document_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            docs_by_type_cursor = self.db.processed_documents.aggregate(pipeline)
            docs_by_type = {doc["_id"]: doc["count"] async for doc in docs_by_type_cursor}
            
            # Get recent documents (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_documents = await self.db.processed_documents.count_documents({
                "created_at": {"$gte": thirty_days_ago}
            })
            
            # Get chunk statistics
            chunk_stats_pipeline = [
                {"$group": {
                    "_id": None,
                    "avg_chunk_size": {"$avg": {"$strLenCP": "$content"}},
                    "total_content_length": {"$sum": {"$strLenCP": "$content"}}
                }}
            ]
            
            chunk_stats_cursor = self.db.document_chunks.aggregate(chunk_stats_pipeline)
            chunk_stats = None
            async for stat in chunk_stats_cursor:
                chunk_stats = stat
                break
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "documents_by_type": docs_by_type,
                "recent_documents_30_days": recent_documents,
                "average_chunk_size": int(chunk_stats.get("avg_chunk_size", 0)) if chunk_stats else 0,
                "total_content_length": chunk_stats.get("total_content_length", 0) if chunk_stats else 0,
                "knowledge_base_ready": total_documents > 0 and total_chunks > 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting knowledge stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "documents_by_type": {},
                "recent_documents_30_days": 0,
                "average_chunk_size": 0,
                "total_content_length": 0,
                "knowledge_base_ready": False,
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def _intelligent_chunk_document(self, content: str, title: str, 
                                        metadata: Dict[str, Any]) -> List[str]:
        """Intelligently chunk document preserving context"""
        
        # Split by sections first (looking for numbered sections, headings)
        section_patterns = [
            r'\n\d+\.\d+\.?\d*\s+[A-Z]',  # Numbered sections like "7.5.1"
            r'\n[A-Z][A-Z0-9]+\.\d+',     # Code sections like "G5.3"  
            r'\n#+\s+',                    # Markdown headers
            r'\n[A-Z][^a-z]{10,}',        # ALL CAPS section titles
        ]
        
        chunks = []
        current_chunk = ""
        max_chunk_size = 1000  # characters
        
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            # Check if this line starts a new section
            is_section_start = any(re.match(pattern, '\n' + line) for pattern in section_patterns)
            
            if is_section_start and current_chunk:
                # Save current chunk if it's substantial
                if len(current_chunk.strip()) > 100:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
                current_section = line.strip()
            else:
                current_chunk += line + '\n'
                
                # If chunk is getting too large, split it
                if len(current_chunk) > max_chunk_size:
                    # Try to split at sentence boundaries
                    sentences = current_chunk.split('. ')
                    if len(sentences) > 1:
                        # Keep first part as chunk
                        chunk_part = '. '.join(sentences[:-1]) + '.'
                        chunks.append(chunk_part.strip())
                        # Start new chunk with remaining content
                        current_chunk = sentences[-1] + '\n'
                    else:
                        # Force split if no good break point
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure minimum chunk size by combining small chunks
        final_chunks = []
        temp_chunk = ""
        
        for chunk in chunks:
            if len(chunk) < 200 and temp_chunk:  # Combine small chunks
                temp_chunk += "\n\n" + chunk
            else:
                if temp_chunk:
                    final_chunks.append(temp_chunk)
                    temp_chunk = chunk
                else:
                    temp_chunk = chunk
        
        if temp_chunk:
            final_chunks.append(temp_chunk)
            
        return final_chunks
    
    def _extract_section_title(self, content: str) -> Optional[str]:
        """Extract section title from chunk content"""
        lines = content.split('\n')[:3]  # Check first 3 lines
        
        for line in lines:
            line = line.strip()
            # Look for section patterns
            if re.match(r'^\d+\.\d+\.?\d*\s+[A-Z]', line) or \
               re.match(r'^[A-Z][A-Z0-9]+\.\d+', line) or \
               re.match(r'^[A-Z][^a-z]{10,}', line):
                return line
        
        return None
    
    async def search_documents(self, query: str, document_types: Optional[List[str]] = None,
                             limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents using semantic similarity"""
        
        # Build where clause for filtering by document type
        where_clause = {}
        if document_types:
            where_clause["document_type"] = {"$in": document_types}
        
        # Perform vector search
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause if where_clause else None
        )
        
        # Format results with enhanced metadata
        formatted_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                result = {
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "chunk_id": results['ids'][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    async def get_document_citations(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed citation information for document chunks"""
        citations = []
        
        for chunk_id in chunk_ids:
            chunk = await self.db.document_chunks.find_one({"id": chunk_id})
            if chunk:
                citation = {
                    "id": chunk_id,
                    "title": chunk["metadata"].get("chunk_of", "Unknown Document"),
                    "source_url": chunk.get("source_url"),
                    "document_type": chunk["document_type"],
                    "section_title": chunk.get("section_title"),
                    "page_number": chunk.get("page_number"),
                    "snippet": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
                }
                citations.append(citation)
        
        return citations