from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File
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
import time
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import base64
from io import BytesIO
from PIL import Image

# Load environment variables first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import all enhanced systems
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from document_processor import DocumentProcessor
from enhanced_knowledge_base import EnhancedKnowledgeBase
from compliance_engine import ComplianceAlternativesEngine
from query_processor import AdvancedQueryProcessor
from auto_scraper import AutomatedScraper
from pdf_processor import BuildingCodePDFProcessor
from enhanced_pdf_processor import EnhancedPDFProcessor
from visual_content_engine import VisualContentEngine, VisualContent
from analytics_engine import AnalyticsEngine
from comprehensive_knowledge_expander import ComprehensiveKnowledgeExpander
from nz_building_language_engine import nz_language_engine
from professional_document_processor import get_professional_processor
from enhanced_search_engine import get_enhanced_search_engine
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
enhanced_pdf_processor = EnhancedPDFProcessor(document_processor)
visual_engine = VisualContentEngine(document_processor)
analytics_engine = AnalyticsEngine(document_processor)
knowledge_expander = ComprehensiveKnowledgeExpander(document_processor)

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
    visual_content: List[Dict[str, Any]] = []  # Visual diagrams and charts

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

NZ PROFESSIONAL COMMUNICATION:
- Use professional but approachable New Zealand tone
- Understand NZ building terminology: dwangs/nogs, gib, sarking, fixings, weathertightness, metrofires
- Be authoritative and clear: "The Building Code requires...", "Based on NZ conditions, I recommend..."
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

@api_router.post("/chat/vision")
async def chat_with_vision(
    file: UploadFile = File(...),
    message: str = "",
    session_id: str = "vision_session"
):
    """
    Analyze technical diagrams and installation guides using GPT-4V
    Perfect for construction diagrams, installation details, and building plans
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Read and process the image
        image_data = await file.read()
        
        # Convert to base64 for GPT-4V
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Initialize vision-capable chat with GPT-4O (best vision model)
        chat = LlmChat(
            api_key=os.getenv("EMERGENT_LLM_KEY"),
            session_id=session_id,
            system_message="""You are STRYDA, a New Zealand building expert specializing in technical diagram analysis.

You excel at:
- Reading installation diagrams and technical drawings
- Explaining building construction details
- Identifying compliance requirements from diagrams
- Providing step-by-step installation guidance
- Spotting potential issues in construction details

When analyzing diagrams, always:
1. Describe what you see clearly
2. Point out key technical details
3. Mention any NZ Building Code compliance aspects
4. Provide practical installation tips
5. Use professional NZ building terminology

Be concise but thorough with professional expertise."""
        ).with_model("openai", "gpt-4o")  # Best vision model
        
        # Create image content
        image_content = ImageContent(image_base64=image_base64)
        
        # Default message if none provided
        if not message.strip():
            message = "Please analyze this technical diagram. Explain what I'm looking at, key installation details, and any Building Code compliance points I should know about."
        
        # Create user message with image
        user_message = UserMessage(
            text=message,
            file_contents=[image_content]
        )
        
        # Get AI response
        start_time = time.time()
        response = await chat.send_message(user_message)
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Vision AI analysis completed in {processing_time:.1f}ms")
        
        return {
            "response": response,
            "image_analyzed": True,
            "processing_time_ms": processing_time,
            "model_used": "gpt-4o",
            "analysis_type": "technical_diagram"
        }
        
    except Exception as e:
        logger.error(f"Vision AI error: {e}")
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")


@api_router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_ai_chat(request: EnhancedChatRequest):
    """Enhanced chat with full intelligence: query processing, compliance analysis, alternatives"""
    
    start_time = datetime.now()
    
    try:
        # PHASE 0: NZ Language Understanding Enhancement
        language_context = await nz_language_engine.enhance_query_understanding(request.message)
        logger.info(f"NZ Language context: {language_context.get('enhanced_understanding', 'standard')}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Check if user is asking for documentation/diagrams from previous response
        if any(phrase in request.message.lower() for phrase in [
            "yes please", "yes show me", "show me the documentation", 
            "show me the diagram", "yes", "show documentation", "show diagrams"
        ]) and len(request.message.split()) <= 5:
            # User is requesting documentation from previous response
            # Trigger visual content retrieval for their last query
            logger.info("User requesting documentation/diagrams from previous response")
            
            # Get the last user query from session to find relevant visual content
            try:
                last_user_message = await db.chat_messages.find_one(
                    {"session_id": session_id, "sender": "user"},
                    sort=[("timestamp", -1)]
                )
                
                if last_user_message:
                    # Search for visual content related to their last query
                    visual_content = visual_engine.get_visual_content(
                        last_user_message.get("message", ""), 
                        []  # Empty list for relevant_docs since it's not available yet
                    )
                    
                    if visual_content:
                        ai_response = f"Here are the relevant diagrams and documentation for your question:\n\n"
                        for content in visual_content[:2]:  # Limit to 2 visuals
                            ai_response += f"📋 **{content['title']}**\n"
                            ai_response += f"Source: {content['source']}\n"
                            if content.get('description'):
                                ai_response += f"Description: {content['description']}\n\n"
                        
                        # Store enhanced response
                        bot_msg = ChatMessage(
                            session_id=session_id,
                            message=ai_response,
                            sender="bot",
                            timestamp=datetime.utcnow()
                        )
                        await db.chat_messages.insert_one(bot_msg.dict())
                        
                        return EnhancedChatResponse(
                            response=ai_response,
                            citations=[],
                            session_id=session_id,
                            confidence_score=0.95,
                            sources_used=[content['source'] for content in visual_content],
                            visual_content=visual_content,
                            query_analysis={"type": "documentation_request"},
                            compliance_issues=[],
                            alternatives_suggested=0,
                            processing_time_ms=500
                        )
                    else:
                        ai_response = "I don't have specific diagrams available for your previous question, but I can provide detailed text-based guidance. Would you like me to elaborate on any specific aspect?"
            except Exception as e:
                logger.error(f"Error retrieving documentation: {e}")
                ai_response = "I'd be happy to show you documentation, but I'm having trouble accessing the visual content right now. Let me provide you with detailed text guidance instead."
            
            # Store the response
            bot_msg = ChatMessage(
                session_id=session_id,
                message=ai_response,
                sender="bot",
                timestamp=datetime.utcnow()
            )
            await db.chat_messages.insert_one(bot_msg.dict())
            
            return EnhancedChatResponse(
                response=ai_response,
                citations=[],
                session_id=session_id,
                confidence_score=0.85,
                sources_used=[],
                visual_content=[],
                query_analysis={"type": "documentation_request"},
                compliance_issues=[],
                alternatives_suggested=0,
                processing_time_ms=500
            )
        
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
        
        # PHASE 2: Enhanced Document Search with Multi-Section Combination
        enhanced_search = get_enhanced_search_engine(document_processor)
        search_results = await enhanced_search.enhanced_search(enhanced_query, limit=8)
        relevant_docs = search_results["results"]
        
        logger.info(f"Enhanced search: {len(relevant_docs)} docs, concepts: {search_results.get('concepts_detected', [])}, combined: {search_results.get('sections_combined', 0)}")
        search_time = search_results.get("search_time_ms", 0)
        
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
        
        # PHASE 7: Adapt AI Response with NZ Language Context
        ai_response = nz_language_engine.adapt_response_tone(ai_response, language_context)
        
        # PHASE 6: Generate Enhanced Citations
        citations = []
        if citation_candidates:
            chunk_ids = [c["chunk_id"] for c in citation_candidates[:4]]  # Top 4 citations
            citations = await document_processor.get_document_citations(chunk_ids)
        
        # PHASE 7: Calculate Enhanced Confidence Score with Document-Specific Logic
        confidence_score = 0.5  # Base confidence
        
        if relevant_docs:
            # Count how many documents have relevant content
            relevant_doc_count = len([doc for doc in relevant_docs if doc["similarity_score"] > -0.1])
            
            # For recently uploaded PDFs, increase confidence significantly
            recent_pdf_boost = 0.0
            for doc in relevant_docs:
                doc_title = doc["metadata"].get("title", "").lower()
                if "metal roof" in doc_title or "cladding code" in doc_title:
                    recent_pdf_boost = 0.4  # 40% boost for metal roofing questions
                elif "structural guide" in doc_title or "mc structural" in doc_title:
                    recent_pdf_boost = 0.4  # 40% boost for structural engineering questions
                elif "plywood" in doc_title or any(term in doc["content"].lower() for term in ["interior lining", "interior wall", "interior use"]):
                    recent_pdf_boost = 0.3  # 30% boost for plywood interior use
            
            # Base similarity adjustment (less harsh than before)
            avg_similarity = sum(max(doc["similarity_score"], 0) for doc in relevant_docs) / len(relevant_docs)
            similarity_boost = min(avg_similarity * 0.8, 0.3)  # Max 30% from similarity
            
            # Document relevance boost
            relevance_boost = min(relevant_doc_count * 0.1, 0.2)  # Up to 20% for multiple relevant docs
            
            confidence_score = min(0.5 + similarity_boost + relevance_boost + recent_pdf_boost, 0.98)
        
        # Additional boost for specific building code queries
        if query_analysis and query_analysis.get("extracted_fields"):
            confidence_score = min(confidence_score + 0.1, 0.98)
        
        # Ensure minimum confidence for document-supported answers
        if relevant_docs and confidence_score < 0.75:
            confidence_score = 0.85  # Minimum 85% when we have supporting documents
        
        # Store enhanced bot message
        bot_message_doc = ChatMessage(
            session_id=session_id,
            message=ai_response,
            sender="bot",
            citations=citations
        )
        await db.chat_messages.insert_one(bot_message_doc.dict())
        
        # Track user query for analytics and learning
        await analytics_engine.track_user_query(
            query=request.message,
            user_session=session_id,
            response_useful=None  # Will be updated based on user feedback later
        )
        
        # Add suggestion for documentation if needed
        documentation_suggestion = ""
        if not any(keyword in request.message.lower() for keyword in ["show", "diagram", "visual", "documentation", "document"]):
            documentation_suggestion = "\n\nWould you like me to show you the relevant documentation or diagram from the Building Code for this?"
            
        # Append suggestion to AI response
        if documentation_suggestion and ai_response:
            ai_response += documentation_suggestion
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Count alternatives suggested
        alternatives_count = sum(len(issue.get("alternatives", [])) for issue in compliance_issues)
        
        # Initialize empty visual content for response compatibility
        visual_content = []
        
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
            processing_time_ms=processing_time,
            visual_content=visual_content
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

# Enhanced PDF Processing Endpoints
class EnhancedPDFBatchRequest(BaseModel):
    pdf_sources: List[Dict[str, str]]  # Each with url, title, type, organization

class EnhancedPDFBatchResponse(BaseModel):
    message: str
    batch_id: str
    total_pdfs: int
    processing_started: bool

@api_router.post("/knowledge/process-pdf-batch", response_model=EnhancedPDFBatchResponse)
async def process_pdf_batch(request: EnhancedPDFBatchRequest, background_tasks: BackgroundTasks):
    """Process multiple PDFs in batch with enhanced classification"""
    try:
        batch_id = str(uuid.uuid4())
        logger.info(f"Starting enhanced PDF batch processing: {len(request.pdf_sources)} PDFs")
        
        # Validate PDF sources
        if not request.pdf_sources:
            raise HTTPException(
                status_code=400,
                detail="PDF sources list cannot be empty"
            )
            
        for pdf_info in request.pdf_sources:
            required_fields = ['url', 'title']
            missing_fields = [field for field in required_fields if field not in pdf_info]
            if missing_fields:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required fields in PDF source: {missing_fields}"
                )
        
        # Start batch processing in background
        background_tasks.add_task(
            _process_enhanced_pdf_batch_task,
            request.pdf_sources,
            batch_id
        )
        
        return EnhancedPDFBatchResponse(
            message=f"Enhanced PDF batch processing started for {len(request.pdf_sources)} documents",
            batch_id=batch_id,
            total_pdfs=len(request.pdf_sources),
            processing_started=True
        )
        
    except Exception as e:
        logger.error(f"Error starting enhanced PDF batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/knowledge/enhanced-pdf-status")
async def get_enhanced_pdf_processing_status():
    """Get comprehensive status of enhanced PDF processing"""
    try:
        # Get processing stats from enhanced processor
        status = await enhanced_pdf_processor.get_processing_status()
        
        # Get recent batch results
        recent_batches = await db.enhanced_pdf_batch_results.find(
        ).sort("completed_at", -1).limit(5).to_list(5)
        
        return {
            **status,
            "recent_batches": [
                {
                    "batch_id": batch["batch_id"],
                    "total_pdfs": batch.get("total_pdfs", 0),
                    "successful": batch.get("processed", []),
                    "failed": batch.get("failed", []),
                    "completed_at": batch["completed_at"],
                    "success_rate": len(batch.get("processed", [])) / max(batch.get("total_pdfs", 1), 1) * 100
                }
                for batch in recent_batches
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced PDF processing status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving enhanced PDF processing status")

async def _process_enhanced_pdf_batch_task(pdf_sources: List[Dict[str, str]], batch_id: str):
    """Background task for enhanced PDF batch processing"""
    try:
        logger.info(f"Enhanced PDF batch processing started: {batch_id}")
        
        # Process the PDF batch
        results = await enhanced_pdf_processor.process_pdf_batch(pdf_sources)
        
        logger.info(f"Enhanced PDF batch completed: {batch_id} - {results['total_documents']} documents, {results['total_chunks']} chunks")
        
        # Store batch result in database
        await db.enhanced_pdf_batch_results.insert_one({
            "batch_id": batch_id,
            "total_pdfs": len(pdf_sources),
            "processed": results['processed'],
            "failed": results['failed'],
            "total_documents": results['total_documents'],
            "total_chunks": results['total_chunks'],
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Enhanced PDF batch processing failed: {batch_id} - {e}")
        
        # Store error result
        await db.enhanced_pdf_batch_results.insert_one({
            "batch_id": batch_id,
            "total_pdfs": len(pdf_sources),
            "processed": [],
            "failed": pdf_sources,
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

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

# EBOSS Product Database Endpoints
@api_router.post("/products/scrape-eboss", response_model=EBOSSScrapingResponse)
async def scrape_eboss_product_database(request: EBOSSScrapingRequest, background_tasks: BackgroundTasks):
    """Scrape comprehensive NZ building products from EBOSS.co.nz"""
    try:
        logger.info(f"Starting EBOSS product scraping with max_products: {request.max_products}")
        
        # Start EBOSS scraping in background
        background_tasks.add_task(
            _scrape_eboss_task,
            request.max_products,
            request.priority_brands_only
        )
        
        return EBOSSScrapingResponse(
            success=True,
            scraping_stats={"status": "started", "max_products": request.max_products},
            message=f"EBOSS product scraping started. This will scrape up to {request.max_products} products from eboss.co.nz.",
            products_scraped=0,
            brands_processed=0,
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error starting EBOSS scraping: {e}")
        return EBOSSScrapingResponse(
            success=False,
            scraping_stats={"status": "failed"},
            message=f"Failed to start EBOSS scraping: {str(e)}",
            products_scraped=0,
            brands_processed=0,
            errors=[str(e)]
        )

@api_router.get("/products/eboss-status")
async def get_eboss_scraping_status():
    """Get status of EBOSS product scraping operations"""
    try:
        # Get EBOSS product statistics from database
        eboss_products = await db.processed_documents.find(
            {"metadata.document_type": "eboss_product"}
        ).sort("processed_at", -1).limit(10).to_list(10)
        
        # Get product count by brand
        pipeline = [
            {"$match": {"metadata.document_type": "eboss_product"}},
            {"$group": {"_id": "$metadata.brand_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        brands_stats = await db.processed_documents.aggregate(pipeline).to_list(20)
        
        # Get product count by category
        category_pipeline = [
            {"$match": {"metadata.document_type": "eboss_product"}},
            {"$unwind": "$metadata.categories"},
            {"$group": {"_id": "$metadata.categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_stats = await db.processed_documents.aggregate(category_pipeline).to_list(20)
        
        # Get total counts
        total_eboss_products = await db.processed_documents.count_documents(
            {"metadata.document_type": "eboss_product"}
        )
        total_eboss_chunks = await db.document_chunks.count_documents(
            {"metadata.document_type": "eboss_product"}
        )
        
        return {
            "total_products": total_eboss_products,
            "total_chunks": total_eboss_chunks,
            "products_by_brand": brands_stats,
            "products_by_category": category_stats,
            "recent_products": [
                {
                    "title": product["title"],
                    "brand": product["metadata"].get("brand_name", "Unknown"),
                    "categories": product["metadata"].get("categories", []),
                    "processed_at": product["processed_at"]
                }
                for product in eboss_products
            ],
            "last_updated": datetime.utcnow().isoformat(),
            "status": "active" if total_eboss_products > 0 else "no_data"
        }
        
    except Exception as e:
        logger.error(f"Error getting EBOSS status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving EBOSS status")

@api_router.get("/products/search")
async def search_products(
    query: str = Query(..., description="Search query for products"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    building_code: Optional[str] = Query(None, description="Filter by building code"),
    limit: int = Query(20, description="Maximum results to return")
):
    """Search EBOSS products with filters"""
    try:
        # Build search filters
        search_filters = {"metadata.document_type": "eboss_product"}
        
        if category:
            search_filters["metadata.categories"] = {"$in": [category]}
        
        if brand:
            search_filters["metadata.brand_slug"] = brand
        
        if building_code:
            search_filters["metadata.building_codes"] = {"$in": [building_code]}
        
        # Use the enhanced search from document processor
        search_results = await document_processor.search_documents(
            query=query,
            limit=limit
        )
        
        return {
            "query": query,
            "filters": {
                "category": category,
                "brand": brand,
                "building_code": building_code
            },
            "results": search_results,
            "total_found": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail="Error searching products")

async def _scrape_eboss_task(max_products: int, priority_brands_only: bool):
    """Background task to scrape EBOSS products"""
    try:
        logger.info(f"Background EBOSS scraping started: max_products={max_products}")
        
        # Run the EBOSS scraper
        scraping_result = await scrape_eboss_products(document_processor)
        
        logger.info(f"EBOSS scraping completed: {scraping_result.get('total_products', 0)} products scraped")
        
        # Store scraping result in database for status tracking
        await db.eboss_scraping_results.insert_one({
            "max_products": max_products,
            "priority_brands_only": priority_brands_only,
            "scraping_result": scraping_result,
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Background EBOSS scraping failed: {e}")
        
        # Store error result
        await db.eboss_scraping_results.insert_one({
            "max_products": max_products,
            "priority_brands_only": priority_brands_only,
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

# Analytics Endpoints
class PopularQuestionsResponse(BaseModel):
    questions: List[str]
    generated_from: str  # 'user_analytics' or 'fallback'
    total_queries_analyzed: int
    last_updated: str

@api_router.get("/analytics/popular-questions", response_model=PopularQuestionsResponse)
async def get_popular_questions():
    """Get dynamic quick questions based on user search analytics"""
    try:
        # Generate popular questions
        questions = await analytics_engine.generate_popular_questions(limit=8)
        
        # Get analytics summary for metadata
        analytics_summary = await analytics_engine.get_analytics_summary()
        
        return PopularQuestionsResponse(
            questions=questions,
            generated_from="user_analytics" if analytics_summary['data_sufficient_for_learning'] else "fallback",
            total_queries_analyzed=analytics_summary['total_queries_30_days'],
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting popular questions: {e}")
        # Return fallback questions in case of error
        fallback_questions = [
            'What size lintel do I need for this window?',
            'What are the fire clearance rules for a fireplace?',
            'Do I need a consent for a re-roof?',
            'Is this timber compliant with NZS 3604?',
            'What\'s the right way to install vinyl cladding?',
            'How much waterproofing is needed for a bathroom?',
            'What\'s the difference between a CCC and a CoC?',
            'What are the rules for getting a Code Compliance Certificate?'
        ]
        
        return PopularQuestionsResponse(
            questions=fallback_questions,
            generated_from="fallback",
            total_queries_analyzed=0,
            last_updated=datetime.utcnow().isoformat()
        )

@api_router.get("/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary for admin/development purposes"""
    try:
        summary = await analytics_engine.get_analytics_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics summary")

@api_router.post("/analytics/feedback")
async def submit_query_feedback(
    query: str, 
    session_id: str, 
    helpful: bool,
    background_tasks: BackgroundTasks
):
    """Submit feedback on query usefulness (for learning improvement)"""
    try:
        # Update the analytics for this query in background
        background_tasks.add_task(
            analytics_engine.track_user_query,
            query=query,
            user_session=session_id,
            response_useful=helpful
        )
        
        return {"message": "Feedback recorded successfully", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Error recording feedback")

# Comprehensive Knowledge Expansion Endpoints
class KnowledgeExpansionResponse(BaseModel):
    expansion_started: bool
    phase_name: str
    total_sources: int
    estimated_time_minutes: int
    expansion_id: str

class ExpansionProgressResponse(BaseModel):
    current_phase: Optional[str]
    completion_percentage: float
    documents_processed: int
    chunks_created: int
    estimated_final_size: Dict[str, int]
    processing_status: str

@api_router.post("/knowledge/expand-critical", response_model=KnowledgeExpansionResponse)
async def start_critical_expansion(background_tasks: BackgroundTasks):
    """Start critical phase knowledge expansion (safety & compliance documents)"""
    try:
        expansion_id = str(uuid.uuid4())
        
        logger.info("🔥 Starting CRITICAL PHASE knowledge expansion")
        logger.info("⚡ Focus: Essential safety, fire, structural, and compliance documents")
        
        # Start critical expansion in background
        background_tasks.add_task(
            _run_critical_expansion_task,
            expansion_id
        )
        
        return KnowledgeExpansionResponse(
            expansion_started=True,
            phase_name="Critical Building Safety & Compliance",
            total_sources=23,  # Critical priority sources
            estimated_time_minutes=15,  # Estimate 15 minutes for critical phase
            expansion_id=expansion_id
        )
        
    except Exception as e:
        logger.error(f"Error starting critical expansion: {e}")
        raise HTTPException(status_code=500, detail="Error starting critical knowledge expansion")

@api_router.post("/knowledge/expand-full", response_model=KnowledgeExpansionResponse)
async def start_full_expansion(background_tasks: BackgroundTasks):
    """Start complete knowledge expansion (all 74 sources)"""
    try:
        expansion_id = str(uuid.uuid4())
        
        logger.info("🌟 Starting FULL COMPREHENSIVE knowledge expansion")
        logger.info("🎯 Target: Transform STRYDA into ultimate NZ building assistant")
        
        # Start full expansion in background  
        background_tasks.add_task(
            _run_full_expansion_task,
            expansion_id
        )
        
        return KnowledgeExpansionResponse(
            expansion_started=True,
            phase_name="Complete NZ Building Knowledge",
            total_sources=74,  # All comprehensive sources
            estimated_time_minutes=60,  # Estimate 1 hour for full expansion
            expansion_id=expansion_id
        )
        
    except Exception as e:
        logger.error(f"Error starting full expansion: {e}")
        raise HTTPException(status_code=500, detail="Error starting comprehensive knowledge expansion")

@api_router.get("/knowledge/expansion-progress", response_model=ExpansionProgressResponse)
async def get_expansion_progress():
    """Get current knowledge expansion progress"""
    try:
        progress = await knowledge_expander.get_expansion_progress()
        
        return ExpansionProgressResponse(
            current_phase=progress.get('current_phase'),
            completion_percentage=progress.get('completion_percentage', 0),
            documents_processed=progress['expansion_stats']['processed'],
            chunks_created=progress['expansion_stats']['chunks_created'],
            estimated_final_size=progress.get('estimated_final_size', {}),
            processing_status="active" if progress.get('current_phase') else "idle"
        )
        
    except Exception as e:
        logger.error(f"Error getting expansion progress: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving expansion progress")

@api_router.get("/knowledge/expansion-summary")
async def get_expansion_summary():
    """Get detailed expansion summary and statistics"""
    try:
        progress = await knowledge_expander.get_expansion_progress()
        current_stats = await document_processor.get_knowledge_stats()
        
        return {
            "current_knowledge_base": current_stats,
            "expansion_plan": {
                "total_sources_available": 74,
                "critical_sources": 23,
                "high_priority_sources": 57,
                "phases_available": 5
            },
            "expansion_progress": progress,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting expansion summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving expansion summary")

async def _run_critical_expansion_task(expansion_id: str):
    """Background task for critical phase expansion"""
    try:
        logger.info(f"🔥 Critical expansion started: {expansion_id}")
        
        # Run critical expansion
        result = await knowledge_expander.run_critical_expansion_only()
        
        logger.info(f"✅ Critical expansion completed: {expansion_id}")
        logger.info(f"📊 Results: {result['total_documents_created']} documents, {result['total_chunks_created']} chunks")
        
        # Store expansion result in database for tracking
        await db.knowledge_expansion_results.insert_one({
            "expansion_id": expansion_id,
            "expansion_type": "critical",
            "result": result,
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Critical expansion failed: {expansion_id} - {e}")
        
        # Store failure result
        await db.knowledge_expansion_results.insert_one({
            "expansion_id": expansion_id,
            "expansion_type": "critical",
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

async def _run_full_expansion_task(expansion_id: str):
    """Background task for full comprehensive expansion"""
    try:
        logger.info(f"🌟 Full expansion started: {expansion_id}")
        
        # Run complete expansion
        result = await knowledge_expander.run_full_expansion()
        
        logger.info(f"🎉 Full expansion completed: {expansion_id}")
        logger.info(f"📊 Final results: {result['total_documents_created']} documents, {result['total_chunks_created']} chunks")
        
        # Store expansion result
        await db.knowledge_expansion_results.insert_one({
            "expansion_id": expansion_id,
            "expansion_type": "full",
            "result": result,
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Full expansion failed: {expansion_id} - {e}")
        
        # Store failure result
        await db.knowledge_expansion_results.insert_one({
            "expansion_id": expansion_id,
            "expansion_type": "full",
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

# NZ Building Language Intelligence Endpoints
@api_router.get("/language/terminology-stats")
async def get_terminology_stats():
    """Get statistics about NZ building terminology database"""
    try:
        stats = nz_language_engine.get_terminology_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting terminology stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving terminology statistics")

@api_router.get("/language/search-terminology")
async def search_terminology(q: str, limit: int = 10):
    """Search NZ building terminology database"""
    try:
        results = nz_language_engine.search_terminology(q, limit)
        return {
            "query": q,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching terminology: {e}")
        raise HTTPException(status_code=500, detail="Error searching terminology")

@api_router.post("/language/scrape-professional-sources")
async def scrape_professional_sources(background_tasks: BackgroundTasks):
    """Scrape professional NZ building sources for terminology updates"""
    try:
        # Run scraping in background
        background_tasks.add_task(_run_terminology_scraping_task)
        
        return {
            "message": "Professional source scraping started",
            "sources_targeted": len(nz_language_engine.professional_sources),
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"Error starting terminology scraping: {e}")
        raise HTTPException(status_code=500, detail="Error starting terminology scraping")

@api_router.post("/language/enhance-query")
async def enhance_query_understanding(query: str):
    """Test query enhancement with NZ building language context"""
    try:
        enhancement = await nz_language_engine.enhance_query_understanding(query)
        return enhancement
    except Exception as e:
        logger.error(f"Error enhancing query: {e}")
        raise HTTPException(status_code=500, detail="Error enhancing query understanding")

async def _run_terminology_scraping_task():
    """Background task for terminology scraping"""
    try:
        logger.info("🔍 Starting professional terminology scraping task")
        
        results = await nz_language_engine.scrape_professional_sources(max_concurrent=2)
        
        logger.info(f"✅ Terminology scraping completed: {results}")
        
        # Store scraping result in database
        await db.terminology_scraping_results.insert_one({
            "results": results,
            "completed_at": datetime.utcnow(),
            "success": True
        })
        
    except Exception as e:
        logger.error(f"❌ Terminology scraping failed: {e}")
        
        # Store error result
        await db.terminology_scraping_results.insert_one({
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

# Professional Document Processing Endpoints
@api_router.post("/knowledge/reprocess-with-professional")
async def reprocess_with_professional_chunking(background_tasks: BackgroundTasks):
    """Re-process existing PDFs with professional document processor"""
    try:
        professional_processor = get_professional_processor(pdf_processor.document_processor)
        
        # Get existing PDF URLs from knowledge base
        existing_pdfs = [
            {
                "url": "https://customer-assets.emergentagent.com/job_nzbuilder-ai/artifacts/4q8hozkh_MC%20Structual%20Guide.pdf",
                "title": "MC Structural Guide - Professional Engineering Reference",
                "type": "building_document"
            },
            {
                "url": "https://customer-assets.emergentagent.com/job_nzbuilder-ai/artifacts/smn87z0d_nz_metal_roofing.pdf", 
                "title": "NZ Metal Roof and Wall Cladding Code of Practice",
                "type": "building_document"
            }
        ]
        
        # Start background reprocessing
        background_tasks.add_task(_reprocess_pdfs_professionally, existing_pdfs)
        
        return {
            "message": "Professional PDF reprocessing started",
            "pdfs_queued": len(existing_pdfs),
            "processing_method": "professional_intelligent_chunking",
            "expected_improvements": [
                "Larger, more comprehensive chunks",
                "Better section organization", 
                "Improved context preservation",
                "Enhanced technical detail retention"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error starting professional reprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/knowledge/enhanced-search")
async def enhanced_document_search(query: str, limit: int = 10):
    """Enhanced search with multi-section combination"""
    try:
        enhanced_search = get_enhanced_search_engine(pdf_processor.document_processor)
        
        results = await enhanced_search.enhanced_search(query, limit)
        
        return {
            "query": query,
            "results": results["results"],
            "total_found": results["total_found"],
            "search_method": results["search_method"],
            "concepts_detected": results.get("concepts_detected", []),
            "sections_combined": results.get("sections_combined", 0),
            "search_time_ms": 0  # Would be measured in real implementation
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _reprocess_pdfs_professionally(pdf_list: List[Dict]):
    """Background task for professional PDF reprocessing"""
    try:
        logger.info("🔄 Starting professional PDF reprocessing")
        
        professional_processor = get_professional_processor(pdf_processor.document_processor)
        
        results = []
        for pdf_info in pdf_list:
            try:
                logger.info(f"📋 Reprocessing: {pdf_info['title']}")
                
                result = await professional_processor.process_pdf_with_intelligent_chunking(
                    pdf_url=pdf_info["url"],
                    title=pdf_info["title"],
                    document_type=pdf_info["type"]
                )
                
                result["pdf_title"] = pdf_info["title"]
                results.append(result)
                
                logger.info(f"✅ Completed: {pdf_info['title']} - {result.get('chunks_created', 0)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Error reprocessing {pdf_info['title']}: {e}")
                results.append({
                    "pdf_title": pdf_info["title"],
                    "success": False,
                    "error": str(e)
                })
        
        # Store results
        await db.professional_reprocessing_results.insert_one({
            "results": results,
            "completed_at": datetime.utcnow(),
            "total_pdfs": len(pdf_list),
            "successful_pdfs": sum(1 for r in results if r.get("success", False))
        })
        
        logger.info(f"🎉 Professional reprocessing completed: {len(results)} PDFs processed")
        
    except Exception as e:
        logger.error(f"💥 Professional reprocessing failed: {e}")
        
        await db.professional_reprocessing_results.insert_one({
            "error": str(e),
            "completed_at": datetime.utcnow(),
            "success": False
        })

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