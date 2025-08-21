from fastapi import FastAPI, APIRouter, HTTPException
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

# Import AI integration after loading env
from emergentintegrations.llm.chat import LlmChat, UserMessage

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

# NZ Building Code Web Scraper
class NZBuildingCodeScraper:
    def __init__(self):
        self.base_urls = [
            "https://www.building.govt.nz/building-code-compliance/",
            "https://www.building.govt.nz/assets/Uploads/building-code/",
            "https://www.branz.co.nz/",
        ]
    
    async def scrape_building_code_info(self, query: str) -> List[Dict[str, Any]]:
        """Scrape relevant NZ building code information based on query"""
        try:
            citations = []
            
            # Search MBIE Building Performance website
            mbie_results = await self._search_mbie(query)
            citations.extend(mbie_results)
            
            # Add some mock citations for now (replace with real scraping)
            if "hearth" in query.lower() or "fireplace" in query.lower():
                citations.append({
                    "id": str(uuid.uuid4()),
                    "title": "NZBC Clause G5 - Interior environment",
                    "url": "https://www.building.govt.nz/building-code-compliance/g-services-and-facilities/g5-interior-environment/",
                    "snippet": "Minimum clearances for solid fuel burning appliances to combustible materials"
                })
            
            if "insulation" in query.lower() or "h1" in query.lower():
                citations.append({
                    "id": str(uuid.uuid4()),
                    "title": "NZBC Clause H1 - Energy efficiency",
                    "url": "https://www.building.govt.nz/building-code-compliance/h-energy-efficiency/h1-energy-efficiency/",
                    "snippet": "Requirements for thermal insulation in different climate zones"
                })
            
            if "weathertight" in query.lower() or "e2" in query.lower():
                citations.append({
                    "id": str(uuid.uuid4()),
                    "title": "NZBC Clause E2 - External moisture",
                    "url": "https://www.building.govt.nz/building-code-compliance/e-moisture/e2-external-moisture/",
                    "snippet": "Prevention of external moisture penetration into buildings"
                })
            
            return citations
            
        except Exception as e:
            logger.error(f"Error scraping building code info: {e}")
            return []
    
    async def _search_mbie(self, query: str) -> List[Dict[str, Any]]:
        """Search MBIE building website"""
        try:
            # This is a simplified version - in production you'd implement proper web scraping
            # For now, return relevant mock results based on query
            return []
        except Exception as e:
            logger.error(f"Error searching MBIE: {e}")
            return []

# Initialize scraper
scraper = NZBuildingCodeScraper()

# Initialize AI Chat
def get_ai_chat(session_id: str) -> LlmChat:
    system_message = """You are STRYDA.ai, a knowledgeable assistant for New Zealand tradies (builders, electricians, plumbers, etc.). 

Your expertise includes:
- NZ Building Code (NZBC) compliance and interpretation
- New Zealand construction standards and acceptable solutions
- Product specifications and installation requirements
- Building consent and compliance processes
- NZ-specific terminology and practices

Guidelines:
- Use NZ English spelling and terminology (e.g., "metres" not "meters")
- Understand tradie lingo: nogs, dwangs, gib, sarking, fixings, weathertightness, metrofires
- Provide direct, practical answers - "no faff"
- Always mention sources and relevant code clauses when possible
- If unsure about compliance, suggest consulting the local council or a building professional
- For clearances and technical specs, always recommend checking the specific manufacturer's instructions
- Be safety-conscious and conservative with recommendations

Respond in a friendly, professional NZ tone. Keep answers concise but comprehensive."""

    return LlmChat(
        api_key=os.environ['EMERGENT_LLM_KEY'],
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "STRYDA.ai Backend API"}

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
async def chat_with_ai(request: ChatRequest):
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
        
        # Get relevant NZ building code information
        citations = await scraper.scrape_building_code_info(request.message)
        
        # Build context for AI from citations
        context_info = ""
        if citations:
            context_info = "\n\nRelevant NZ Building Code information:\n"
            for citation in citations:
                context_info += f"- {citation['title']}: {citation.get('snippet', '')}\n"
        
        # Prepare message for AI
        enhanced_message = f"{request.message}{context_info}"
        
        # Get AI response
        chat = get_ai_chat(session_id)
        user_msg = UserMessage(text=enhanced_message)
        ai_response = await chat.send_message(user_msg)
        
        # Store bot message
        bot_message_doc = ChatMessage(
            session_id=session_id,
            message=ai_response,
            sender="bot",
            citations=[citation for citation in citations]
        )
        await db.chat_messages.insert_one(bot_message_doc.dict())
        
        return ChatResponse(
            response=ai_response,
            citations=citations,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Sorry, I'm having trouble right now. Please try again.")

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()