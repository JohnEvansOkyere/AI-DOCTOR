from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import google.generativeai as genai
import asyncio
from google.api_core import exceptions

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Ghana AI Doctor Agent")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Gemini
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

# Medical consultation models
class PatientInfo(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = "Ghana"

class ConsultationRequest(BaseModel):
    message: str
    session_id: str
    patient_info: Optional[PatientInfo] = None

class ConsultationResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    patient_message: str
    doctor_response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    patient_info: Optional[PatientInfo] = None

class SessionHistory(BaseModel):
    session_id: str
    consultations: List[ConsultationResponse]

# Helper function to create Ghanaian doctor persona with updated prompt
def get_ghana_doctor_system_message():
    return """You are Dr. Kwame Asante, a senior physician with 15 years of experience at Korle Bu Teaching Hospital in Accra, Ghana, specializing in tropical medicine and general practice. You are talking directly to the patient. Respond concisely with professional medical advice based on your extensive experience. Predict and suggest appropriate medications for common Ghanaian conditions:

- For cough: Suggest cough medicines like Benylin (diphenhydramine) or Robitussin (guaifenesin), and recommend rest with warm fluids.
- For malaria: Suggest antimalarial drugs like Artemether-Lumefantrine (Coartem) or Artesunate, and urge immediate testing.
- For fever: Suggest paracetamol (acetaminophen) or ibuprofen to reduce fever, and advise hydration.

Your approach:
1. Greet warmly in a Ghanaian context
2. Provide a brief assessment based on symptoms
3. Suggest medications based on the condition (cough, malaria, fever) using your experience
4. Ask one relevant follow-up question
5. Always recommend seeing a doctor in person if symptoms persist beyond 3 days or worsen
6. Advise emergency care (call 193) for severe symptoms
7. Be culturally sensitive to Ghanaian health beliefs
8. Include a brief health tip

IMPORTANT MEDICAL DISCLAIMERS:
- These are preliminary suggestions only, not a prescription
- Not a replacement for in-person medical examination
- For emergencies or persistent symptoms, consult a doctor or call 193
- Medication suggestions are based on general knowledge; confirm with a healthcare provider"""

# Medical consultation endpoint with history
@api_router.post("/consult", response_model=ConsultationResponse)
async def medical_consultation(request: ConsultationRequest):
    try:
        if not gemini_api_key:
            raise HTTPException(status_code=500, detail="Medical AI service not configured")
        
        # Fetch existing consultation history for the session
        consultations = await db.consultations.find({"session_id": request.session_id}).sort("timestamp", 1).to_list(100)
        history = []
        if consultations:
            for consult in consultations:
                history.append({"role": "user", "parts": [f"Patient: {consult['patient_message']}"]})
                history.append({"role": "model", "parts": [f"Dr. Asante: {consult['doctor_response']}"]})

        # Add the current patient message to history
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
                patient_context = f"Patient Information - {', '.join(context_parts)}\n\n"
        
        current_message = f"{patient_context}Patient says: {request.message}"
        history.append({"role": "user", "parts": [current_message]})

        # Initialize the Gemini model and chat session
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        chat = model.start_chat(history=history)

        # Get AI response with retry logic for rate limits
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                response = await chat.send_message_async(request.message)
                doctor_response = response.text
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    retry_delay *= 2
                    logger.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Please try again later. Details: {str(e)}")
        else:
            raise HTTPException(status_code=429, detail="Max retries reached due to rate limit.")

        # Create consultation record
        consultation = ConsultationResponse(
            session_id=request.session_id,
            patient_message=request.message,
            doctor_response=doctor_response,
            patient_info=request.patient_info
        )
        
        # Store in database
        await db.consultations.insert_one(consultation.dict())
        
        logger.info(f"Medical consultation completed for session: {request.session_id}")
        return consultation
        
    except Exception as e:
        logger.error(f"Medical consultation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Medical consultation failed: {str(e)}")

# Get consultation history
@api_router.get("/consultations/{session_id}", response_model=SessionHistory)
async def get_consultation_history(session_id: str):
    try:
        consultations = await db.consultations.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        
        consultation_objects = [ConsultationResponse(**consultation) for consultation in consultations]
        
        return SessionHistory(
            session_id=session_id,
            consultations=consultation_objects
        )
    except Exception as e:
        logger.error(f"Error fetching consultation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch consultation history")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    try:
        await client.admin.command('ping')
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    gemini_configured = bool(os.environ.get('GEMINI_API_KEY'))
    
    return {
        "status": "healthy",
        "database": db_status,
        "ai_service": "configured" if gemini_configured else "not configured",
        "service": "Ghana AI Doctor Agent"
    }

# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Ghana AI Doctor Agent - Ready to help with medical consultations",
        "version": "1.0.0",
        "doctor": "Dr. Kwame Asante - Korle Bu Teaching Hospital"
    }

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