"""
Structural Intelligence System - FastAPI Backend
Main application entry point.
"""

import os
import uuid
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Environment configuration
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Storage directories
UPLOAD_DIR = Path(__file__).parent / "uploads"
DEBUG_DIR = Path(__file__).parent / "debug"
CACHE_DIR = Path(__file__).parent / "cache"

# In-memory cache for analysis results (in production, use Redis or database)
analysis_cache: Dict[str, Dict[str, Any]] = {}


class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
    version: str


class AnalysisResponse(BaseModel):
    file_id: str
    status: str
    message: str
    stages_completed: list
    parse_result: Optional[dict] = None
    geometry_result: Optional[dict] = None
    structural_result: Optional[dict] = None
    scene_graph: Optional[dict] = None
    materials_result: Optional[dict] = None
    cost_result: Optional[dict] = None
    report: Optional[dict] = None


def serialize_pydantic(obj) -> dict:
    """Recursively serialize Pydantic models to dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, list):
        return [serialize_pydantic(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_pydantic(v) for k, v in obj.items()}
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


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

    # Create directories
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    yield
    # Shutdown
    print("Structural Intelligence System Shutting Down...")


app = FastAPI(
    title="Structural Intelligence System",
    description="Autonomous floor plan analysis and structural recommendation engine",
    version="0.3.0",
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
    return HealthResponse(status="healthy", mock_mode=MOCK_MODE, version="0.3.0")


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

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "status": "uploaded",
        "path": str(file_path),
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
    # Check if already in cache
    if file_id in analysis_cache:
        cached = analysis_cache[file_id]
        return {
            "file_id": file_id,
            "status": "cached",
            "message": "Analysis retrieved from cache",
            **cached,
        }

    # Find uploaded file
    file_path = None
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = UPLOAD_DIR / f"{file_id}{ext}"
        if candidate.exists():
            file_path = candidate
            break

    if file_path is None:
        raise HTTPException(status_code=404, detail=f"File not found for ID: {file_id}")

    # Create debug directory for this analysis
    analysis_debug_dir = str(DEBUG_DIR / file_id)
    os.makedirs(analysis_debug_dir, exist_ok=True)

    stages_completed = []

    try:
        # Lazy import cv2 and pipeline modules
        import cv2
        from pipeline import (
            preprocess_image,
            VLMParser,
            CVParser,
            fuse_parsers,
            GeometryAnalyzer,
            StructuralValidator,
            Extruder,
            MaterialEngine,
            CostEngine,
            LayoutOptimizer,
            Explainer,
        )

        # Stage 1: Load and preprocess image
        print(f"\n[{file_id}] Stage 1: Preprocessing...")
        image = cv2.imread(str(file_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to load image")

        processed, binary, preprocess_meta = preprocess_image(
            image, debug_dir=analysis_debug_dir, debug_prefix="preprocess"
        )
        stages_completed.append("preprocessing")
        print(f"  Preprocessing complete: {preprocess_meta}")

        # Stage 2: VLM Parsing
        print(f"\n[{file_id}] Stage 2: VLM Parsing...")
        vlm_parser = VLMParser(api_key=GOOGLE_AI_API_KEY)
        vlm_result = vlm_parser.parse(image, debug_dir=analysis_debug_dir)
        stages_completed.append("vlm_parsing")
        print(
            f"  VLM detected {vlm_result.room_count} rooms, shape: {vlm_result.building_shape}"
        )

        # Stage 3: CV Parsing
        print(f"\n[{file_id}] Stage 3: CV Parsing...")
        cv_parser = CVParser()
        cv_result = cv_parser.parse(image, binary, debug_dir=analysis_debug_dir)
        stages_completed.append("cv_parsing")
        # CV parser prints its own summary

        # Stage 4: Parser Fusion
        print(f"\n[{file_id}] Stage 4: Parser Fusion...")
        h, w = image.shape[:2]
        parse_result = fuse_parsers(
            vlm_result, cv_result, (w, h), debug_dir=analysis_debug_dir
        )
        stages_completed.append("parser_fusion")
        # Fusion prints its own summary

        # Override scale if provided
        if scale_override:
            parse_result.scale.pixels_per_meter = scale_override
            parse_result.scale.method = "user_override"
            parse_result.scale.confidence = 1.0

        # Stage 5: Geometry Analysis
        print(f"\n[{file_id}] Stage 5: Geometry Analysis...")
        geometry_analyzer = GeometryAnalyzer()
        geometry_result = geometry_analyzer.analyze(
            parse_result, debug_dir=analysis_debug_dir
        )
        stages_completed.append("geometry_analysis")
        # Analyzer prints its own summary

        # Stage 6: Structural Validation
        print(f"\n[{file_id}] Stage 6: Structural Validation...")
        structural_validator = StructuralValidator()
        structural_result = structural_validator.validate(
            parse_result, geometry_result, debug_dir=analysis_debug_dir
        )
        stages_completed.append("structural_validation")
        # Validator prints its own summary

        # Stage 7: 3D Extrusion
        print(f"\n[{file_id}] Stage 7: 3D Extrusion...")
        extruder = Extruder()
        scene_graph = extruder.extrude(
            parse_result,
            geometry_result,
            structural_result,
            num_floors=num_floors,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("3d_extrusion")
        # Extruder prints its own summary

        # Stage 8: Material Recommendation
        print(f"\n[{file_id}] Stage 8: Material Recommendation...")
        material_engine = MaterialEngine()
        materials_result = material_engine.recommend(
            parse_result,
            geometry_result,
            optimize_for=optimize_for,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("materials")
        # Engine prints its own summary

        # Stage 9: Cost Estimation
        print(f"\n[{file_id}] Stage 9: Cost Estimation...")
        cost_engine = CostEngine()
        cost_result = cost_engine.estimate(
            parse_result,
            geometry_result,
            materials_result,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("cost_estimation")
        # Engine prints its own summary

        # Stage 10: Layout Optimization
        print(f"\n[{file_id}] Stage 10: Layout Optimization...")
        layout_optimizer = LayoutOptimizer()
        optimization_suggestions = layout_optimizer.optimize(
            parse_result,
            geometry_result,
            structural_result,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("layout_optimization")
        # Optimizer prints its own summary

        # Stage 11: Report Generation
        print(f"\n[{file_id}] Stage 11: Report Generation...")
        explainer = Explainer()
        report = explainer.generate_report(
            parse_result,
            geometry_result,
            structural_result,
            materials_result,
            cost_result,
            optimization_suggestions,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("report_generation")

        print(
            f"\n[{file_id}] Analysis complete! {len(stages_completed)} stages completed."
        )

        # Serialize results
        result_data = {
            "stages_completed": stages_completed,
            "parse_result": serialize_pydantic(parse_result),
            "geometry_result": serialize_pydantic(geometry_result),
            "structural_result": serialize_pydantic(structural_result),
            "scene_graph": serialize_pydantic(scene_graph),
            "materials_result": serialize_pydantic(materials_result),
            "cost_result": serialize_pydantic(cost_result),
            "report": serialize_pydantic(report),
            "analyzed_at": datetime.now().isoformat(),
        }

        # Cache results
        analysis_cache[file_id] = result_data

        # Save to disk cache
        cache_path = CACHE_DIR / f"{file_id}.json"
        with open(cache_path, "w") as f:
            json.dump(result_data, f, indent=2, default=str)

        return {
            "file_id": file_id,
            "status": "complete",
            "message": f"Analysis complete. {len(stages_completed)} stages processed.",
            **result_data,
        }

    except ImportError as e:
        print(f"Import error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline import error: {str(e)}. Check dependencies.",
        )
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed at stage {stages_completed[-1] if stages_completed else 'init'}: {str(e)}",
        )


@app.get("/api/materials")
async def get_materials():
    """Get list of available construction materials."""
    materials_path = Path(__file__).parent / "data" / "materials_db.json"

    try:
        with open(materials_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Materials database not found")


@app.get("/api/scene/{file_id}")
async def get_scene(file_id: str):
    """Get the 3D scene graph for Three.js visualization."""
    # Check cache
    if file_id in analysis_cache:
        scene_data = analysis_cache[file_id].get("scene_graph")
        if scene_data:
            return {"status": "success", "scene": scene_data}

    # Check disk cache
    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        scene_data = data.get("scene_graph")
        if scene_data:
            return {"status": "success", "scene": scene_data}

    raise HTTPException(
        status_code=404,
        detail=f"Scene not found for file {file_id}. Run analysis first.",
    )


@app.get("/api/report/{file_id}")
async def get_report(file_id: str):
    """Get the full analysis report."""
    # Check cache
    if file_id in analysis_cache:
        report_data = analysis_cache[file_id].get("report")
        if report_data:
            return {"status": "success", "report": report_data}

    # Check disk cache
    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        report_data = data.get("report")
        if report_data:
            return {"status": "success", "report": report_data}

    raise HTTPException(
        status_code=404,
        detail=f"Report not found for file {file_id}. Run analysis first.",
    )


@app.get("/api/analysis/{file_id}")
async def get_analysis(file_id: str):
    """Get complete analysis results for a file."""
    # Check cache
    if file_id in analysis_cache:
        return {
            "status": "success",
            "file_id": file_id,
            **analysis_cache[file_id],
        }

    # Check disk cache
    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        # Populate memory cache
        analysis_cache[file_id] = data
        return {"status": "success", "file_id": file_id, **data}

    raise HTTPException(
        status_code=404,
        detail=f"Analysis not found for file {file_id}. Upload and analyze first.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
