from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
import uuid
from datetime import datetime
import google.generativeai as genai
import asyncio
from google.api_core import exceptions
import httpx
from collections import defaultdict
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Ghana Health Information Advisor")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting
rate_limit_storage = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # requests
RATE_LIMIT_WINDOW = 60  # seconds

def check_rate_limit(session_id: str) -> bool:
    """Simple rate limiting per session"""
    now = time.time()
    # Clean old entries
    rate_limit_storage[session_id] = [
        timestamp for timestamp in rate_limit_storage[session_id]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    if len(rate_limit_storage[session_id]) >= RATE_LIMIT_REQUESTS:
        return False
    
    rate_limit_storage[session_id].append(now)
    return True

# Initialize AI providers
gemini_api_key = os.environ.get('GEMINI_API_KEY')
grok_api_key = os.environ.get('GROK_API_KEY')

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    logger.warning("GEMINI_API_KEY not found")

if not grok_api_key:
    logger.warning("GROK_API_KEY not found")

# Models
class PatientInfo(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[Literal["male", "female", "other"]] = None
    location: Optional[str] = Field("Ghana", max_length=100)

class ConsultationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)
    patient_info: Optional[PatientInfo] = None
    ai_provider: Literal["gemini", "grok"] = "grok"
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

class ConsultationResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    patient_message: str
    advisor_response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    patient_info: Optional[PatientInfo] = None
    ai_provider: str

class SessionHistory(BaseModel):
    session_id: str
    consultations: List[ConsultationResponse]

def get_health_advisor_system_message():
    """System message for health information advisor"""
    return """You are a Health Information Advisor for Ghana, providing general health education and guidance. You are NOT a doctor and do NOT diagnose or prescribe medications.

CRITICAL RULES:
1. NEVER suggest specific medications or dosages
2. NEVER diagnose medical conditions
3. NEVER replace professional medical care
4. ALWAYS emphasize seeing a healthcare provider for proper diagnosis and treatment

Your role:
1. Provide general health information and education
2. Help users understand when to seek medical care urgently
3. Explain common symptoms and general health practices
4. Recommend lifestyle modifications (hydration, rest, nutrition)
5. Provide culturally appropriate health guidance for Ghana

For emergencies (chest pain, difficulty breathing, severe bleeding, loss of consciousness):
- Immediately advise calling 193 (Ghana emergency number)
- Tell them to go to the nearest hospital

For concerning symptoms (persistent fever, severe pain, unexplained weight loss):
- Recommend seeing a healthcare provider within 24-48 hours
- Explain possible general causes (educational only)

For minor concerns (mild headache, minor cold):
- Provide general wellness advice (rest, hydration, nutrition)
- Suggest monitoring symptoms
- Recommend seeing a doctor if symptoms worsen or persist beyond 3 days

ALWAYS include this disclaimer in your response:
"⚕️ Important: This is general health information only, not medical advice. Please consult a licensed healthcare provider for proper diagnosis and treatment."

Be warm, professional, and culturally sensitive to Ghanaian context."""

async def get_gemini_response(message: str, history: list) -> str:
    """Get response from Gemini"""
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini not configured")
    
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    chat = model.start_chat(history=history)
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = await chat.send_message_async(message)
            return response.text
        except exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                retry_delay *= 2
                logger.warning(f"Gemini rate limit. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again in a few minutes.")
        except Exception as e:
            logger.error(f"Gemini error: {str(e)}")
            raise HTTPException(status_code=500, detail="AI service error")
    
    raise HTTPException(status_code=500, detail="Max retries reached")

async def get_grok_response(message: str, history: list) -> str:
    """Get response from Grok"""
    if not grok_api_key:
        raise HTTPException(status_code=500, detail="Grok not configured")
    
    messages = [{"role": "system", "content": get_health_advisor_system_message()}]
    
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["parts"][0]})
        elif msg["role"] == "model":
            messages.append({"role": "assistant", "content": msg["parts"][0]})
    
    messages.append({"role": "user", "content": message})
    
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            http2=True,
            headers={"Host": "api.x.ai"}
        ) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {grok_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-4-fast-reasoning",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 429:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again in a few minutes.")
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Grok HTTP error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")
    except Exception as e:
        logger.error(f"Grok error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service error")

@api_router.post("/consult", response_model=ConsultationResponse)
async def health_consultation(request: ConsultationRequest):
    """Provide health information and guidance"""
    try:
        # Rate limiting
        if not check_rate_limit(request.session_id):
            raise HTTPException(
                status_code=429, 
                detail="Too many requests. Please wait a minute before trying again."
            )
        
        # Fetch consultation history with safe field access
        consultations = await db.consultations.find(
            {"session_id": request.session_id}
        ).sort("timestamp", 1).limit(20).to_list(20)
        
        history = []
        if consultations:
            for consult in consultations:
                # Safe field access handling old and new schema
                patient_msg = consult.get('patient_message', '')
                advisor_msg = consult.get('advisor_response') or consult.get('doctor_response', '')
                
                if patient_msg and advisor_msg:
                    history.append({"role": "user", "parts": [f"User: {patient_msg}"]})
                    history.append({"role": "model", "parts": [f"Advisor: {advisor_msg}"]})
        
        # Build context
        patient_context = ""
        if request.patient_info:
            context_parts = []
            if request.patient_info.age:
                context_parts.append(f"Age: {request.patient_info.age}")
            if request.patient_info.gender:
                context_parts.append(f"Gender: {request.patient_info.gender}")
            if request.patient_info.location:
                context_parts.append(f"Location: {request.patient_info.location}")
            
            if context_parts:
                patient_context = f"Context - {', '.join(context_parts)}\n\n"
        
        current_message = f"{patient_context}User asks: {request.message}"
        
        # Get AI response based on provider
        if request.ai_provider == "grok":
            advisor_response = await get_grok_response(current_message, history)
        else:
            advisor_response = await get_gemini_response(current_message, history)
        
        # Create consultation record
        consultation = ConsultationResponse(
            session_id=request.session_id,
            patient_message=request.message,
            advisor_response=advisor_response,
            patient_info=request.patient_info,
            ai_provider=request.ai_provider
        )
        
        # Store in database using model_dump() for Pydantic v2
        await db.consultations.insert_one(consultation.model_dump())
        
        logger.info(f"Consultation completed for session: {request.session_id}")
        return consultation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consultation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Consultation failed")

@api_router.get("/consultations/{session_id}", response_model=SessionHistory)
async def get_consultation_history(session_id: str):
    """Get consultation history for a session"""
    try:
        consultations = await db.consultations.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).limit(100).to_list(100)
        
        logger.info(f"Found {len(consultations)} consultations for session {session_id}")
        
        consultation_objects = []
        for idx, c in enumerate(consultations):
            try:
                # Remove MongoDB _id field
                if '_id' in c:
                    del c['_id']
                
                # Handle old schema
                if 'doctor_response' in c and 'advisor_response' not in c:
                    c['advisor_response'] = c.pop('doctor_response')
                if 'ai_provider' not in c:
                    c['ai_provider'] = 'gemini'
                
                consultation_objects.append(ConsultationResponse(**c))
            except Exception as e:
                logger.error(f"Failed to parse consultation {idx}: {e}")
                logger.error(f"Problematic record: {c}")
                # Skip problematic records instead of failing
                continue
        
        return SessionHistory(
            session_id=session_id,
            consultations=consultation_objects
        )
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch history")

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status,
        "gemini": "configured" if gemini_api_key else "not configured",
        "grok": "configured" if grok_api_key else "not configured",
        "service": "Ghana Health Information Advisor"
    }

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ghana Health Information Advisor - General health education and guidance",
        "version": "2.0.0",
        "disclaimer": "This service provides general health information only, not medical advice.",
        "emergency": "For emergencies, call 193 (Ghana)"
    }

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    client.close()