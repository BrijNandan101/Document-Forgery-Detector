from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import logging
import shutil
import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from bson.errors import InvalidDocument
from pdf_generator import PDFReportGenerator


# Load environment variables
ROOT_DIR = Path(__file__).parent.resolve()
load_dotenv(ROOT_DIR / ".env")

# MongoDB setup
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# App instance with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background cleanup task
    cleanup_task = asyncio.create_task(delete_old_uploads())
    yield
    cleanup_task.cancel()
    client.close()

app = FastAPI(title="Document Forgery Detection API", version="1.0.0", lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Upload directory setup
UPLOAD_DIR = (ROOT_DIR / "static" / "uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Thread pool for heavy processing
executor = ThreadPoolExecutor(max_workers=4)

# Import AI modules
import sys
sys.path.append(str(ROOT_DIR))
from forgery_detector import ForgeryDetector
from pdf_generator import PDFReportGenerator

detector = ForgeryDetector()
pdf_generator = PDFReportGenerator()

# Models
class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    verdict: str
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

# Middleware: Request logging (optional, disable in prod)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"➡️ {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"⬅️ {response.status_code} {request.url}")
    return response

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Document Forgery Detection API is running"}

# Status API
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**doc) for doc in status_checks]

# Analyze document
@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        file_id = str(uuid.uuid4())
        ext = file.filename.split('.')[-1].lower()
        saved_filename = f"{file_id}.{ext}"
        file_path = UPLOAD_DIR / saved_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, detector.analyze_image, str(file_path))

        analysis = AnalysisResult(
            id=file_id,
            filename=file.filename,
            verdict=result['verdict'],
            confidence=result['confidence'],
            ela_processed=result['ela_processed']
        )

        try:
            await db.analyses.insert_one(analysis.dict())
        except InvalidDocument as e:
            raise HTTPException(status_code=500, detail="Failed to save analysis in database")

        return AnalysisResponse(success=True, message="Document analyzed", data=analysis)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

# Generate PDF report
@api_router.get("/generate-report/{analysis_id}")
async def generate_report(analysis_id: str):
    try:
        analysis = await db.analyses.find_one({"id": analysis_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        loop = asyncio.get_event_loop()
        report_path = await loop.run_in_executor(executor, pdf_generator.generate_report, analysis)

        return FileResponse(
            path=report_path,
            media_type="application/pdf",
            filename=f"forgery_report_{analysis_id}.pdf"
        )

    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

# Get all analyses
@api_router.get("/analyses", response_model=List[AnalysisResult])
async def get_analyses():
    docs = await db.analyses.find().to_list(100)
    return [AnalysisResult(**doc) for doc in docs]

# Include routes
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task: Delete files older than 1 day
async def delete_old_uploads():
    while True:
        try:
            for file in UPLOAD_DIR.glob("*"):
                if time.time() - file.stat().st_mtime > 86400:
                    logger.info(f"🧹 Deleting old file: {file}")
                    file.unlink()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
        await asyncio.sleep(3600)  # Run hourly

# Optional: Run directly with Python for dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
