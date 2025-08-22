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

# Import all enhanced systems
from emergentintegrations.llm.chat import LlmChat, UserMessage
from document_processor import DocumentProcessor
from enhanced_knowledge_base import EnhancedKnowledgeBase
from compliance_engine import ComplianceAlternativesEngine
from query_processor import AdvancedQueryProcessor
from auto_scraper import AutomatedScraper
from pdf_processor import BuildingCodePDFProcessor
from eboss_scraper import scrape_eboss_products, get_eboss_scraping_stats

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize all enhanced systems
document_processor = DocumentProcessor(client, os.environ['DB_NAME'])
enhanced_kb = EnhancedKnowledgeBase(document_processor)
compliance_engine = ComplianceAlternativesEngine(document_processor)
query_processor = AdvancedQueryProcessor(document_processor)
auto_scraper = AutomatedScraper(document_processor)
pdf_processor = BuildingCodePDFProcessor(document_processor)

# Create the main app without a prefix
app = FastAPI(title="STRYDA.ai Enhanced API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enhanced Models
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

class EnhancedChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    session_id: Optional[str] = None
    enable_compliance_analysis: bool = True
    enable_query_processing: bool = True

class EnhancedChatResponse(BaseModel):
    response: str
    citations: List[Dict[str, Any]] = []
    session_id: str
    confidence_score: Optional[float] = None
    sources_used: List[str] = []
    query_analysis: Optional[Dict[str, Any]] = None
    compliance_issues: List[Dict[str, Any]] = []
    alternatives_suggested: int = 0
    processing_time_ms: float = 0

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
    enable_query_processing: bool = True

class KnowledgeSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float
    query_analysis: Optional[Dict[str, Any]] = None

class ComplianceAnalysisRequest(BaseModel):
    query: str
    context: Optional[str] = ""

class ScrapingRequest(BaseModel):
    target_name: Optional[str] = None
    force_update: bool = False

class PDFProcessingRequest(BaseModel):
    pdf_url: str
    title: Optional[str] = "NZ Building Code Handbook"
    document_type: str = "nzbc"
    
class PDFProcessingResponse(BaseModel):
    success: bool
    processing_stats: Dict[str, Any]
    message: str
    chunks_created: int = 0
    errors: List[str] = []

class EBOSSScrapingRequest(BaseModel):
    max_products: Optional[int] = 1000
    priority_brands_only: bool = False
    
class EBOSSScrapingResponse(BaseModel):
    success: bool
    scraping_stats: Dict[str, Any]
    message: str
    products_scraped: int = 0
    brands_processed: int = 0
    errors: List[str] = []

# Enhanced AI Chat with Full Intelligence System
def get_super_enhanced_ai_chat(session_id: str) -> LlmChat:
    system_message = """You are STRYDA.ai, New Zealand's most advanced AI assistant for building professionals and tradies.

Your enhanced capabilities include:
- Complete NZ Building Code knowledge with exact clause references and alternatives
- Real-time compliance analysis with alternative solutions for fail cases
- Advanced understanding of NZ Standards (NZS 3604, NZS 4230, etc.)
- Comprehensive manufacturer specifications and installation requirements
- Intelligent query processing that extracts dimensions, materials, and context
- Proactive compliance guidance with cost-effective alternatives

ENHANCED RESPONSE PROTOCOL:
1. **Direct Answer First**: Always start with the specific answer to the question
2. **Exact References**: Provide precise code clauses (e.g., "NZBC G5.3.2", "NZS 3604:2011 Section 7.5")  
3. **Compliance Analysis**: If compliance issues detected, offer 2-3 practical alternatives
4. **Cost Guidance**: Indicate relative cost impact (low/medium/high) for alternatives
5. **Next Steps**: Always end with clear, actionable next steps

NZ TRADIE COMMUNICATION:
- Use natural Kiwi tone: "G'day!", "Right, here's the deal...", "No worries"
- Understand slang: dwangs/nogs, gib, sarking, fixings, weathertightness, metrofires
- Be conversational but authoritative: "This is what the code says, but here's what I'd do..."
- Always consider practical site conditions and NZ climate

COMPLIANCE INTELLIGENCE:
- When manufacturer specs conflict with NZBC, flag which takes precedence
- Suggest compliant alternatives if proposed solution has issues
- Consider regional variations (wind zones, climate zones, council requirements)
- Emphasize safety and long-term durability

ADVANCED CONTEXT AWARENESS:
- Extract and use specific dimensions, materials, brands mentioned
- Consider building type (residential vs commercial)
- Account for climate zones and site conditions
- Reference latest document versions and updates

Remember: You're not just answering questions - you're providing expert building guidance that keeps tradies compliant, safe, and efficient on NZ construction sites."""

    return LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")

# Enhanced API Routes
@api_router.get("/")
async def root():
    return {"message": "STRYDA.ai Enhanced Backend API v2.0 - Complete NZ Building Intelligence System"}

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

@api_router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_ai_chat(request: EnhancedChatRequest):
    """Enhanced chat with full intelligence: query processing, compliance analysis, alternatives"""
    
    start_time = datetime.now()
    
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
        
        # PHASE 1: Advanced Query Processing
        query_analysis = None
        enhanced_query = request.message
        search_keywords = []
        
        if request.enable_query_processing:
            processed_query = await query_processor.process_query(request.message)
            query_context = await query_processor.get_contextual_response(processed_query)
            
            query_analysis = query_context["query_analysis"]
            enhanced_query = processed_query.enhanced_query
            search_keywords = processed_query.search_keywords
        
        # PHASE 2: Knowledge Base Search with Enhanced Context
        search_start = datetime.now()
        relevant_docs = await document_processor.search_documents(
            query=enhanced_query,
            limit=7
        )
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        
        # PHASE 3: Compliance Analysis and Alternatives
        compliance_issues = []
        if request.enable_compliance_analysis:
            context = " ".join([doc["content"] for doc in relevant_docs]) if relevant_docs else ""
            compliance_guidance = await compliance_engine.get_compliance_guidance(request.message)
            compliance_issues = compliance_guidance.get("issues", [])
        
        # PHASE 4: Build Comprehensive Context for AI
        knowledge_sections = []
        citation_candidates = []
        sources_used = []
        
        if relevant_docs:
            knowledge_sections.append("=== ENHANCED NZ BUILDING INTELLIGENCE ===")
            
            for i, doc in enumerate(relevant_docs):
                if doc["similarity_score"] > 0.25:  # Slightly lower threshold for more context
                    section_title = doc["metadata"].get("section_title", "")
                    doc_type = doc["metadata"].get("document_type", "").upper()
                    
                    knowledge_sections.append(f"\n--- {doc_type} Source {i+1}: {doc['metadata'].get('title', 'Unknown')} ---")
                    if section_title:
                        knowledge_sections.append(f"Section: {section_title}")
                    knowledge_sections.append(doc["content"])
                    
                    citation_candidates.append({
                        "chunk_id": doc["chunk_id"],
                        "similarity_score": doc["similarity_score"]
                    })
                    
                    sources_used.append(f"{doc_type}: {doc['metadata'].get('title', 'Unknown')}")
        
        # Add compliance issues to context if found
        if compliance_issues:
            knowledge_sections.append("\n=== COMPLIANCE ANALYSIS ===")
            for issue in compliance_issues:
                knowledge_sections.append(f"\nISSUE: {issue['description']}")
                knowledge_sections.append(f"SEVERITY: {issue['severity'].upper()}")
                knowledge_sections.append(f"CODE REFERENCE: {issue['code_reference']}")
                
                if issue['alternatives']:
                    knowledge_sections.append("COMPLIANT ALTERNATIVES:")
                    for alt in issue['alternatives'][:2]:  # Top 2 alternatives
                        knowledge_sections.append(f"- {alt['title']}: {alt['description']}")
                        knowledge_sections.append(f"  Cost: {alt['cost_impact']}, Difficulty: {alt['difficulty']}")
        
        # PHASE 5: Enhanced AI Processing
        if knowledge_sections:
            knowledge_context = "\n".join(knowledge_sections)
            
            ai_prompt = f"""USER QUESTION: {request.message}

EXTRACTED CONTEXT: {query_analysis if query_analysis else 'Standard processing'}

{knowledge_context}

ENHANCED INSTRUCTIONS: 
Using the comprehensive NZ building intelligence above, provide an expert response that:
1. Directly answers the user's question with exact measurements and specifications
2. References specific building code clauses and standards
3. If compliance issues were identified, present the compliant alternatives clearly
4. Consider cost implications and practical installation factors
5. End with clear next steps for the tradie

Use natural NZ English and tradie-friendly language. Be authoritative but approachable."""
        
        else:
            ai_prompt = f"""USER QUESTION: {request.message}

No specific documents found in enhanced knowledge base. Provide general NZ building code guidance based on your training. Always recommend consulting official sources for definitive answers and mention that more specific guidance may be available with additional context."""
        
        # Get enhanced AI response
        chat = get_super_enhanced_ai_chat(session_id)
        user_msg = UserMessage(text=ai_prompt)
        ai_response = await chat.send_message(user_msg)
        
        # PHASE 6: Generate Enhanced Citations
        citations = []
        if citation_candidates:
            chunk_ids = [c["chunk_id"] for c in citation_candidates[:4]]  # Top 4 citations
            citations = await document_processor.get_document_citations(chunk_ids)
        
        # PHASE 7: Calculate Enhanced Confidence Score
        confidence_score = 0.5  # Base confidence
        if relevant_docs:
            avg_similarity = sum(doc["similarity_score"] for doc in relevant_docs) / len(relevant_docs)
            confidence_score = min(avg_similarity * 1.3, 1.0)
        
        if query_analysis and query_analysis.get("extracted_fields"):
            confidence_score = min(confidence_score + 0.15, 1.0)  # Boost for extracted fields
        
        # Store enhanced bot message
        bot_message_doc = ChatMessage(
            session_id=session_id,
            message=ai_response,
            sender="bot",
            citations=citations
        )
        await db.chat_messages.insert_one(bot_message_doc.dict())
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Count alternatives suggested
        alternatives_count = sum(len(issue.get("alternatives", [])) for issue in compliance_issues)
        
        logger.info(f"Enhanced chat: {len(relevant_docs)} docs, {len(citations)} citations, {len(compliance_issues)} issues, {processing_time:.1f}ms")
        
        return EnhancedChatResponse(
            response=ai_response,
            citations=citations,
            session_id=session_id,
            confidence_score=confidence_score,
            sources_used=list(set(sources_used)),
            query_analysis=query_analysis,
            compliance_issues=compliance_issues,
            alternatives_suggested=alternatives_count,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Sorry, the enhanced AI system is having trouble right now. Please try again.")

# Legacy chat endpoint (for compatibility)
@api_router.post("/chat")
async def legacy_chat_endpoint(request: Dict[str, Any]):
    """Legacy chat endpoint - redirects to enhanced version"""
    
    enhanced_request = EnhancedChatRequest(
        message=request.get("message", ""),
        context=request.get("context"),
        session_id=request.get("session_id")
    )
    
    enhanced_response = await enhanced_ai_chat(enhanced_request)
    
    # Convert to legacy format
    return {
        "response": enhanced_response.response,
        "citations": enhanced_response.citations,
        "session_id": enhanced_response.session_id,
        "confidence_score": enhanced_response.confidence_score,
        "sources_used": enhanced_response.sources_used
    }

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

# Enhanced Knowledge Base Management
@api_router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def enhanced_knowledge_search(request: KnowledgeSearchRequest):
    """Enhanced knowledge base search with query processing"""
    try:
        search_start = datetime.now()
        
        query_analysis = None
        search_query = request.query
        
        if request.enable_query_processing:
            processed_query = await query_processor.process_query(request.query)
            query_context = await query_processor.get_contextual_response(processed_query)
            query_analysis = query_context["query_analysis"]
            search_query = processed_query.enhanced_query
        
        results = await document_processor.search_documents(
            query=search_query,
            document_types=request.document_types,
            limit=request.limit
        )
        
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        
        return KnowledgeSearchResponse(
            results=results,
            total_found=len(results),
            search_time_ms=search_time,
            query_analysis=query_analysis
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced knowledge search: {e}")
        raise HTTPException(status_code=500, detail="Error searching enhanced knowledge base")

@api_router.post("/compliance/analyze")
async def analyze_compliance(request: ComplianceAnalysisRequest):
    """Analyze compliance and suggest alternatives"""
    try:
        guidance = await compliance_engine.get_compliance_guidance(request.query)
        return guidance
    except Exception as e:
        logger.error(f"Error in compliance analysis: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing compliance requirements")

@api_router.post("/knowledge/documents")
async def upload_document(document: DocumentUpload, background_tasks: BackgroundTasks):
    """Upload document to enhanced knowledge base"""
    try:
        background_tasks.add_task(
            document_processor.process_and_store_document,
            title=document.title,
            content=document.content,
            source_url=document.source_url,
            document_type=document.document_type,
            metadata=document.metadata
        )
        
        return {"message": f"Document '{document.title}' queued for enhanced processing"}
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error uploading document")

@api_router.post("/knowledge/expand")
async def expand_knowledge_base(background_tasks: BackgroundTasks):
    """Expand knowledge base with comprehensive NZ building documents"""
    try:
        background_tasks.add_task(enhanced_kb.load_all_comprehensive_documents)
        return {"message": "Comprehensive knowledge base expansion started"}
    except Exception as e:
        logger.error(f"Error expanding knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Error expanding knowledge base")

@api_router.get("/knowledge/stats")
async def get_enhanced_knowledge_stats():
    """Get enhanced knowledge base statistics"""
    try:
        # Get document counts by type
        doc_counts = await db.processed_documents.aggregate([
            {"$group": {"_id": "$document_type", "count": {"$sum": 1}}}
        ]).to_list(100)
        
        chunk_count = await db.document_chunks.count_documents({})
        total_docs = await db.processed_documents.count_documents({})
        
        # Get latest documents
        recent_docs = await db.processed_documents.find().sort("processed_at", -1).limit(5).to_list(5)
        
        return {
            "total_documents": total_docs,
            "total_chunks": chunk_count,
            "documents_by_type": {item["_id"]: item["count"] for item in doc_counts},
            "recent_documents": [{"title": doc["title"], "type": doc["document_type"], "processed_at": doc["processed_at"]} for doc in recent_docs],
            "enhanced_features": {
                "query_processing": True,
                "compliance_analysis": True,
                "alternative_suggestions": True,
                "automated_scraping": True
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced knowledge stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving enhanced knowledge statistics")

# Automated Scraping Endpoints
@api_router.post("/scraping/run")
async def run_automated_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Run automated web scraping for latest NZ building documents"""
    try:
        if request.target_name and request.force_update:
            # Force update specific target
            background_tasks.add_task(auto_scraper.force_update_target, request.target_name)
            return {"message": f"Force update started for target: {request.target_name}"}
        else:
            # Run full automated scraping
            background_tasks.add_task(auto_scraper.run_automated_scraping)
            return {"message": "Automated scraping started for all configured targets"}
            
    except Exception as e:
        logger.error(f"Error starting automated scraping: {e}")
        raise HTTPException(status_code=500, detail="Error starting automated scraping")

@api_router.get("/scraping/targets")
async def get_scraping_targets():
    """Get configured automated scraping targets"""
    try:
        targets = []
        for target in auto_scraper.scraping_targets:
            targets.append({
                "name": target.name,
                "base_url": target.base_url,
                "document_type": target.document_type,
                "update_frequency_hours": target.update_frequency.total_seconds() / 3600,
                "last_scraped": target.last_scraped.isoformat() if target.last_scraped else None
            })
        
        return {"targets": targets, "total_targets": len(targets)}
    except Exception as e:
        logger.error(f"Error getting scraping targets: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving scraping targets")

# PDF Processing Endpoints
@api_router.post("/knowledge/process-pdf", response_model=PDFProcessingResponse)
async def process_building_code_pdf(request: PDFProcessingRequest, background_tasks: BackgroundTasks):
    """Process NZ Building Code PDF and integrate into knowledge base"""
    try:
        logger.info(f"Starting PDF processing for: {request.title}")
        
        # Start PDF processing in background
        background_tasks.add_task(
            _process_pdf_task,
            request.pdf_url,
            request.title,
            request.document_type
        )
        
        return PDFProcessingResponse(
            success=True,
            processing_stats={"status": "started", "pdf_url": request.pdf_url},
            message=f"PDF processing started for '{request.title}'. This may take several minutes.",
            chunks_created=0,
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error starting PDF processing: {e}")
        return PDFProcessingResponse(
            success=False,
            processing_stats={"status": "failed"},
            message=f"Failed to start PDF processing: {str(e)}",
            chunks_created=0,
            errors=[str(e)]
        )

@api_router.get("/knowledge/pdf-status")
async def get_pdf_processing_status():
    """Get status of PDF processing operations"""
    try:
        # Get recent PDF processing results from database
        recent_docs = await db.processed_documents.find(
            {"metadata.pdf_source": True}
        ).sort("processed_at", -1).limit(10).to_list(10)
        
        # Get chunk count for PDF documents
        pdf_chunk_count = await db.document_chunks.count_documents(
            {"metadata.pdf_source": True}
        )
        
        return {
            "total_pdf_documents": len(recent_docs),
            "total_pdf_chunks": pdf_chunk_count,
            "recent_pdf_documents": [
                {
                    "title": doc["title"],
                    "processed_at": doc["processed_at"],
                    "total_chunks": doc["total_chunks"],
                    "document_type": doc["document_type"]
                }
                for doc in recent_docs
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF processing status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving PDF processing status")

async def _process_pdf_task(pdf_url: str, title: str, document_type: str):
    """Background task to process PDF"""
    try:
        logger.info(f"Background PDF processing started: {title}")
        
        # Process the PDF
        processing_result = await pdf_processor.download_and_process_pdf(
            pdf_url=pdf_url,
            title=title
        )
        
        logger.info(f"PDF processing completed: {processing_result['chunks_created']} chunks created")
        
        # Store processing result in database for status tracking
        await db.pdf_processing_results.insert_one({
            "title": title,
            "pdf_url": pdf_url,
            "document_type": document_type,
            "processing_result": processing_result,
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Background PDF processing failed: {e}")
        
        # Store error result
        await db.pdf_processing_results.insert_one({
            "title": title,
            "pdf_url": pdf_url,
            "document_type": document_type,
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

# Job Management (existing endpoints)
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

# Enhanced startup event
@app.on_event("startup")
async def startup_event():
    """Initialize enhanced STRYDA.ai system"""
    try:
        # Initialize core knowledge base
        await document_processor.initialize_knowledge_base()
        logger.info("✅ Core knowledge base initialized")
        
        # Load comprehensive documents
        comprehensive_count = await enhanced_kb.load_all_comprehensive_documents()
        logger.info(f"✅ Comprehensive knowledge base loaded: {comprehensive_count} documents")
        
        # Start periodic scraping (optional - runs in background)
        # asyncio.create_task(auto_scraper.schedule_periodic_scraping(24))
        # logger.info("✅ Automated scraping scheduled")
        
        logger.info("🚀 STRYDA.ai Enhanced System fully initialized!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced system: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()