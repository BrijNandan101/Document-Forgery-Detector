from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
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
import json
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import our AI processing modules
from .forgery_detector import ForgeryDetector
from .pdf_generator import PDFReportGenerator

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Document Forgery Detection API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize AI detector
detector = ForgeryDetector()
pdf_generator = PDFReportGenerator()

# Thread pool for AI processing
executor = ThreadPoolExecutor(max_workers=4)

# Define Models
class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    verdict: str  # "Genuine" or "Forged"
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ela_processed: bool = False
    
class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: Optional[AnalysisResult] = None
    
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Original status endpoints
@api_router.get("/")
async def root():
    return {"message": "Document Forgery Detection API is running"}

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

# Document Forgery Detection endpoints
@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Analyze uploaded document for forgery detection
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are supported")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['jpg', 'jpeg', 'png']:
            raise HTTPException(status_code=400, detail="Only JPG and PNG files are supported")
        
        saved_filename = f"{file_id}.{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image with AI in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor, 
            detector.analyze_image, 
            str(file_path)
        )
        
        # Create analysis result
        analysis = AnalysisResult(
            id=file_id,
            filename=file.filename,
            verdict=result['verdict'],
            confidence=result['confidence'],
            ela_processed=result['ela_processed']
        )
        
        # Save to database
        await db.analyses.insert_one(analysis.dict())
        
        return AnalysisResponse(
            success=True,
            message="Document analyzed successfully",
            data=analysis
        )
        
    except Exception as e:
        logging.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/generate-report/{analysis_id}")
async def generate_report(analysis_id: str):
    """
    Generate PDF report for analysis
    """
    try:
        # Get analysis from database
        analysis = await db.analyses.find_one({"id": analysis_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Generate PDF report
        loop = asyncio.get_event_loop()
        report_path = await loop.run_in_executor(
            executor,
            pdf_generator.generate_report,
            analysis
        )
        
        return FileResponse(
            path=report_path,
            media_type='application/pdf',
            filename=f"forgery_report_{analysis_id}.pdf"
        )
        
    except Exception as e:
        logging.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@api_router.get("/analyses", response_model=List[AnalysisResult])
async def get_analyses():
    """
    Get all analysis results
    """
    analyses = await db.analyses.find().to_list(100)
    return [AnalysisResult(**analysis) for analysis in analyses]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()