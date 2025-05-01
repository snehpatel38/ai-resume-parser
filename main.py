from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from models import Resume, ChatMessage, ChatResponse, CandidateRanking
from resume_parser import ResumeParser
from candidate_analyzer import CandidateAnalyzer
from chatbot import HRChatbot
import uuid
from typing import List
import os
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Parser and Candidate Analysis System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize components
resume_parser = ResumeParser()
candidate_analyzer = CandidateAnalyzer()
chatbot = HRChatbot(candidate_analyzer)

@app.get("/")
async def read_root():
    """Serve the main page."""
    return FileResponse("static/index.html")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse a resume."""
    try:
        # Validate file type
        if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")

        # Parse resume
        resume = resume_parser.parse_resume(content, file.content_type)
        
        # Generate unique ID for the candidate
        candidate_id = str(uuid.uuid4())
        
        # Add to candidate analyzer
        candidate_analyzer.add_candidate(candidate_id, resume)
        
        return {"message": "Resume uploaded successfully", "candidate_id": candidate_id}

    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-candidates")
async def analyze_candidates(query: str):
    """Analyze and rank candidates based on a query."""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        rankings = candidate_analyzer.rank_candidates(query)
        return rankings

    except Exception as e:
        logger.error(f"Error analyzing candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: ChatMessage):
    """Process a chat message."""
    try:
        if not message.message:
            raise HTTPException(status_code=400, detail="Message is required")

        response = chatbot.process_message(message)
        return response

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidates")
async def get_candidates():
    """Get all candidates."""
    try:
        candidates = candidate_analyzer.get_all_candidates()
        return candidates

    except Exception as e:
        logger.error(f"Error getting candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 