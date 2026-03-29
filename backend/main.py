"""
Structural Intelligence System - FastAPI Backend
Main application entry point.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Environment configuration
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
    version: str


class AnalyzeRequest(BaseModel):
    """Request for floor plan analysis."""

    scale_override: Optional[float] = None
    num_floors: int = 1
    optimize_for: str = "balanced"  # balanced, cost, strength, durability


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("=" * 50)
    print("Structural Intelligence System Starting...")
    print(f"MOCK_MODE: {MOCK_MODE}")
    print(f"Google AI API Key: {'configured' if GOOGLE_AI_API_KEY else 'NOT SET'}")
    print(f"Cerebras API Key: {'configured' if CEREBRAS_API_KEY else 'NOT SET'}")
    print(f"Groq API Key: {'configured' if GROQ_API_KEY else 'NOT SET'}")
    print("=" * 50)
    yield
    # Shutdown
    print("Structural Intelligence System Shutting Down...")


app = FastAPI(
    title="Structural Intelligence System",
    description="Autonomous floor plan analysis and structural recommendation engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", mock_mode=MOCK_MODE, version="0.1.0")


@app.post("/api/upload")
async def upload_floor_plan(file: UploadFile = File(...)):
    """
    Upload a floor plan image for analysis.
    Supported formats: PNG, JPG, JPEG
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}"
        )

    # Read file content
    content = await file.read()

    # TODO: Save to temp location and return file ID
    file_id = "temp_" + file.filename

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "status": "uploaded",
    }


@app.post("/api/analyze/{file_id}")
async def analyze_floor_plan(
    file_id: str,
    scale_override: Optional[float] = Query(
        None, description="Override scale in pixels per meter"
    ),
    num_floors: int = Query(1, ge=1, le=5, description="Number of floors"),
    optimize_for: str = Query("balanced", description="Optimization target"),
):
    """
    Run the full analysis pipeline on an uploaded floor plan.

    Pipeline stages:
    1. Preprocessing (contrast, denoise)
    2. VLM Parsing (Gemini vision)
    3. CV Parsing (OpenCV geometric)
    4. Parser Fusion (merge VLM + CV)
    5. Geometry Analysis (junctions, wall classification)
    6. Structural Validation (spans, load paths)
    7. 3D Extrusion
    8. Material Recommendation
    9. Cost Estimation
    10. Report Generation (LLM explanations)
    """
    # TODO: Implement full pipeline
    if MOCK_MODE:
        return {
            "status": "mock_complete",
            "file_id": file_id,
            "message": "Mock mode - pipeline not executed",
            "stages_completed": [],
        }

    raise HTTPException(status_code=501, detail="Pipeline not yet implemented")


@app.get("/api/materials")
async def get_materials():
    """Get list of available construction materials."""
    import json

    materials_path = os.path.join(
        os.path.dirname(__file__), "data", "materials_db.json"
    )

    try:
        with open(materials_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Materials database not found")


@app.get("/api/scene/{file_id}")
async def get_scene(file_id: str):
    """Get the 3D scene graph for Three.js visualization."""
    # TODO: Return cached scene from analysis
    if MOCK_MODE:
        return {
            "status": "mock",
            "scene": None,
            "message": "Mock mode - no scene available",
        }

    raise HTTPException(status_code=404, detail="Scene not found")


@app.get("/api/report/{file_id}")
async def get_report(file_id: str):
    """Get the full analysis report."""
    # TODO: Return cached report from analysis
    if MOCK_MODE:
        return {
            "status": "mock",
            "report": None,
            "message": "Mock mode - no report available",
        }

    raise HTTPException(status_code=404, detail="Report not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
