from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import AI integration and document processor after loading env
from emergentintegrations.llm.chat import LlmChat, UserMessage
from document_processor import DocumentProcessor

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Document Processor
document_processor = DocumentProcessor(client, os.environ['DB_NAME'])

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    sender: str  # 'user' or 'bot'
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: List[Dict[str, Any]] = []

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    citations: List[Dict[str, Any]] = []
    session_id: str
    confidence_score: Optional[float] = None
    sources_used: List[str] = []

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    status: str = "active"  # active, pending, complete
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    questions_count: int = 0

class JobCreate(BaseModel):
    name: str
    address: str

class DocumentUpload(BaseModel):
    title: str
    content: str
    source_url: str
    document_type: str  # 'nzbc', 'mbie', 'nzs', 'manufacturer', 'council'
    metadata: Dict[str, Any] = {}

class KnowledgeSearchRequest(BaseModel):
    query: str
    document_types: Optional[List[str]] = None
    limit: int = 5

class KnowledgeSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float

# Enhanced AI Chat with Knowledge Base Integration
def get_enhanced_ai_chat(session_id: str) -> LlmChat:
    system_message = """You are STRYDA.ai, the most knowledgeable AI assistant for New Zealand tradies and building professionals.

Your expertise includes:
- Complete NZ Building Code (NZBC) knowledge with exact clause references
- NZS standards, especially NZS 3604:2011 for timber framing
- Manufacturer installation requirements and specifications
- MBIE Acceptable Solutions and Verification Methods
- Real-world compliance scenarios and alternatives

CRITICAL INSTRUCTIONS:
1. Always provide EXACT code references (e.g., "NZBC Clause G5.3.2", "NZS 3604:2011 Section 7.5.1")
2. When citing clearances, give precise measurements and conditions
3. Distinguish between MINIMUM code requirements and manufacturer specifications
4. If manufacturer specs are stricter than NZBC minimums, always note this
5. For any ambiguous situations, recommend consulting local council or professional

NZ Terminology (use these terms naturally):
- dwangs/nogs (horizontal blocking in walls)
- gib (plasterboard/drywall)
- sarking (building wrap/house wrap)
- weathertightness (not waterproofing)
- fixings (fasteners/screws/nails)
- metrofires (popular NZ fireplace brand)
- LBP (Licensed Building Practitioner)

Response Style:
- Start with direct answer, then provide supporting details
- Use "metres" not "meters", NZ spelling throughout
- Be conversational but professional: "G'day! Here's what you need to know..."
- Always end with practical next steps or recommendations
- If uncertain about compliance, say so clearly and suggest verification steps

SAFETY FIRST: Always err on the side of caution. If there's any doubt about compliance or safety, recommend consulting a qualified professional."""

    return LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "STRYDA.ai Backend API - Enhanced with Knowledge Base"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/chat", response_model=ChatResponse)
async def enhanced_chat_with_ai(request: ChatRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Store user message
        user_message_doc = ChatMessage(
            session_id=session_id,
            message=request.message,
            sender="user"
        )
        await db.chat_messages.insert_one(user_message_doc.dict())
        
        # ENHANCED: Search knowledge base for relevant information
        search_start = datetime.now()
        relevant_docs = await document_processor.search_documents(
            query=request.message,
            limit=5
        )
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        
        # Build enhanced context from knowledge base
        context_sections = []
        citation_candidates = []
        sources_used = []
        
        if relevant_docs:
            context_sections.append("=== RELEVANT NZ BUILDING CODE INFORMATION ===")
            
            for i, doc in enumerate(relevant_docs):
                # Only include high-relevance results
                if doc["similarity_score"] > 0.3:
                    section_title = doc["metadata"].get("section_title", "")
                    doc_type = doc["metadata"].get("document_type", "")
                    
                    context_sections.append(f"\n--- Source {i+1}: {doc['metadata'].get('title', 'Unknown')} ---")
                    if section_title:
                        context_sections.append(f"Section: {section_title}")
                    context_sections.append(doc["content"])
                    
                    # Prepare citation info
                    citation_candidates.append({
                        "chunk_id": doc["chunk_id"],
                        "similarity_score": doc["similarity_score"]
                    })
                    
                    sources_used.append(f"{doc_type.upper()}: {doc['metadata'].get('title', 'Unknown')}")
        
        # Build the complete context for AI
        if context_sections:
            knowledge_context = "\n".join(context_sections)
            enhanced_message = f"""USER QUESTION: {request.message}

{knowledge_context}

INSTRUCTIONS: Using the above NZ Building Code information, provide a comprehensive answer. Always cite specific clauses, sections, and measurements. If the user's question relates to the provided information, reference it directly. If additional considerations apply, mention them."""
        else:
            enhanced_message = f"""USER QUESTION: {request.message}

No specific documents found in knowledge base. Provide general NZ building code guidance based on your training, but recommend consulting official sources for definitive answers."""
        
        # Get AI response
        chat = get_enhanced_ai_chat(session_id)
        user_msg = UserMessage(text=enhanced_message)
        ai_response = await chat.send_message(user_msg)
        
        # Get detailed citations for the most relevant chunks
        citations = []
        if citation_candidates:
            chunk_ids = [c["chunk_id"] for c in citation_candidates[:3]]  # Top 3 most relevant
            citations = await document_processor.get_document_citations(chunk_ids)
        
        # Calculate confidence score based on search results
        confidence_score = None
        if relevant_docs:
            avg_similarity = sum(doc["similarity_score"] for doc in relevant_docs) / len(relevant_docs)
            confidence_score = min(avg_similarity * 1.2, 1.0)  # Boost slightly, cap at 1.0
        
        # Store bot message with enhanced metadata
        bot_message_doc = ChatMessage(
            session_id=session_id,
            message=ai_response,
            sender="bot",
            citations=citations
        )
        await db.chat_messages.insert_one(bot_message_doc.dict())
        
        logger.info(f"Enhanced chat response: {len(relevant_docs)} docs found, {len(citations)} citations, {search_time:.1f}ms search time")
        
        return ChatResponse(
            response=ai_response,
            citations=citations,
            session_id=session_id,
            confidence_score=confidence_score,
            sources_used=list(set(sources_used))  # Remove duplicates
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Sorry, I'm having trouble accessing the knowledge base right now. Please try again.")

@api_router.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        return [ChatMessage(**msg) for msg in messages]
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history")

# Knowledge Base Management Endpoints
@api_router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """Search the STRYDA.ai knowledge base"""
    try:
        search_start = datetime.now()
        
        results = await document_processor.search_documents(
            query=request.query,
            document_types=request.document_types,
            limit=request.limit
        )
        
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        
        return KnowledgeSearchResponse(
            results=results,
            total_found=len(results),
            search_time_ms=search_time
        )
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Error searching knowledge base")

@api_router.post("/knowledge/documents")
async def upload_document(document: DocumentUpload, background_tasks: BackgroundTasks):
    """Upload a new document to the knowledge base"""
    try:
        # Process document in background
        background_tasks.add_task(
            document_processor.process_and_store_document,
            title=document.title,
            content=document.content,
            source_url=document.source_url,
            document_type=document.document_type,
            metadata=document.metadata
        )
        
        return {"message": f"Document '{document.title}' queued for processing"}
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

@api_router.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        # Get document counts by type
        doc_counts = await db.processed_documents.aggregate([
            {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
        ]).to_list(100)
        
        chunk_count = await db.document_chunks.count_documents({})
        total_docs = await db.processed_documents.count_documents({})
        
        return {
            "total_documents": total_docs,
            "total_chunks": chunk_count,
            "documents_by_type": {item["_id"]: item["count"] for item in doc_counts},
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving knowledge base statistics")

@api_router.post("/knowledge/initialize")
async def initialize_knowledge_base(background_tasks: BackgroundTasks):
    """Initialize the knowledge base with priority NZ building documents"""
    try:
        background_tasks.add_task(document_processor.initialize_knowledge_base)
        return {"message": "Knowledge base initialization started"}
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Error initializing knowledge base")

# Job Management Endpoints (existing)
@api_router.post("/jobs", response_model=Job)
async def create_job(job_data: JobCreate):
    try:
        job = Job(
            name=job_data.name,
            address=job_data.address
        )
        await db.jobs.insert_one(job.dict())
        return job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="Error creating job")

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs():
    try:
        jobs = await db.jobs.find().sort("last_activity", -1).to_list(100)
        return [Job(**job) for job in jobs]
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving jobs")

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        job = await db.jobs.find_one({"id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return Job(**job)
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving job")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize knowledge base
@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge base on startup"""
    try:
        # Initialize knowledge base with priority documents
        await document_processor.initialize_knowledge_base()
        logger.info("STRYDA.ai knowledge base initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()