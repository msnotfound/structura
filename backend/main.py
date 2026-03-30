"""
Structural Intelligence System - FastAPI Backend
Main application entry point with auth, save/history, and full pipeline.
"""

import os
import uuid
import json
import hashlib
import secrets
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

# Environment configuration
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Storage directories
UPLOAD_DIR = Path(__file__).parent / "uploads"
DEBUG_DIR = Path(__file__).parent / "debug"
CACHE_DIR = Path(__file__).parent / "cache"
DATA_DIR = Path(__file__).parent / "data"

# In-memory cache for analysis results
analysis_cache: Dict[str, Dict[str, Any]] = {}

# Simple user store
USERS_FILE = DATA_DIR / "users.json"
SESSIONS: Dict[str, dict] = {}  # token -> {email, expires}


# ── Auth Models ──────────────────────────────────────────

class AuthRegister(BaseModel):
    name: str
    email: str
    password: str

class AuthLogin(BaseModel):
    email: str
    password: str

class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
    version: str


# ── Auth Helpers ─────────────────────────────────────────

def _load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_users(users: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def _hash_password(password: str) -> str:
    salt = "structura_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def _create_session(email: str, name: str) -> str:
    token = secrets.token_hex(32)
    SESSIONS[token] = {
        "email": email,
        "name": name,
        "expires": (datetime.now() + timedelta(days=7)).isoformat()
    }
    return token

def _get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    session = SESSIONS.get(token)
    if session:
        if datetime.fromisoformat(session["expires"]) > datetime.now():
            return session
        del SESSIONS[token]
    return None


# ── Serialization ────────────────────────────────────────

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


# ── App Lifecycle ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("=" * 50)
    print("Structural Intelligence System Starting...")
    print(f"MOCK_MODE: {MOCK_MODE}")
    print(f"Google AI API Key: {'configured' if GOOGLE_AI_API_KEY else 'NOT SET'}")
    print(f"Cerebras API Key: {'configured' if CEREBRAS_API_KEY else 'NOT SET'}")
    print(f"Groq API Key: {'configured' if GROQ_API_KEY else 'NOT SET'}")
    print("=" * 50)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load cached analyses from disk
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            file_id = cache_file.stem
            analysis_cache[file_id] = data
        except Exception:
            pass
    print(f"Loaded {len(analysis_cache)} cached analyses from disk")

    yield
    print("Structural Intelligence System Shutting Down...")


app = FastAPI(
    title="Structural Intelligence System",
    description="Autonomous floor plan analysis and structural recommendation engine",
    version="0.4.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth Endpoints ───────────────────────────────────────

@app.post("/auth/register")
async def register(body: AuthRegister):
    """Register a new user."""
    users = _load_users()
    if body.email in users:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    users[body.email] = {
        "name": body.name,
        "email": body.email,
        "password_hash": _hash_password(body.password),
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    
    token = _create_session(body.email, body.name)
    return {"token": token, "user": {"name": body.name, "email": body.email}}


@app.post("/auth/login")
async def login(body: AuthLogin):
    """Login with email and password."""
    users = _load_users()
    user = users.get(body.email)
    if not user or user["password_hash"] != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = _create_session(body.email, user["name"])
    return {"token": token, "user": {"name": user["name"], "email": user["email"]}}


@app.get("/auth/me")
async def get_me(user: Optional[dict] = Depends(_get_current_user)):
    """Get current user info."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": {"name": user["name"], "email": user["email"]}}


# ── Health ───────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", mock_mode=MOCK_MODE, version="0.4.0")


# ── Upload ───────────────────────────────────────────────

@app.post("/api/upload")
async def upload_floor_plan(file: UploadFile = File(...)):
    """Upload a floor plan image for analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = {".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}")

    content = await file.read()
    file_id = str(uuid.uuid4())

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


# ── Analysis Pipeline ───────────────────────────────────

@app.post("/api/analyze/{file_id}")
async def analyze_floor_plan(
    file_id: str,
    scale_override: Optional[float] = Query(None),
    num_floors: int = Query(1, ge=1, le=5),
    optimize_for: str = Query("balanced"),
):
    """Run the full analysis pipeline on an uploaded floor plan."""
    if file_id in analysis_cache:
        cached = analysis_cache[file_id]
        return {"file_id": file_id, "status": "cached", "message": "Analysis retrieved from cache", **cached}

    file_path = None
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = UPLOAD_DIR / f"{file_id}{ext}"
        if candidate.exists():
            file_path = candidate
            break

    if file_path is None:
        raise HTTPException(status_code=404, detail=f"File not found for ID: {file_id}")

    analysis_debug_dir = str(DEBUG_DIR / file_id)
    os.makedirs(analysis_debug_dir, exist_ok=True)

    stages_completed = []

    try:
        import cv2
        from pipeline import (
            preprocess_image, VLMParser, CVParser, fuse_parsers,
            GeometryAnalyzer, StructuralValidator, Extruder,
            MaterialEngine, CostEngine, LayoutOptimizer, Explainer,
        )

        # Stage 1: Preprocess
        print(f"\n[{file_id}] Stage 1: Preprocessing...")
        image = cv2.imread(str(file_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to load image")

        processed, binary, preprocess_meta = preprocess_image(
            image, debug_dir=analysis_debug_dir, debug_prefix="preprocess"
        )
        stages_completed.append("preprocessing")

        # Stage 2: VLM Parsing
        print(f"\n[{file_id}] Stage 2: VLM Parsing...")
        vlm_parser = VLMParser(api_key=GOOGLE_AI_API_KEY)
        vlm_result = vlm_parser.parse(image, debug_dir=analysis_debug_dir)
        stages_completed.append("vlm_parsing")

        # Stage 3: CV Parsing
        print(f"\n[{file_id}] Stage 3: CV Parsing...")
        cv_parser = CVParser()
        cv_result = cv_parser.parse(image, binary, debug_dir=analysis_debug_dir)
        stages_completed.append("cv_parsing")

        # Stage 4: Parser Fusion
        print(f"\n[{file_id}] Stage 4: Parser Fusion...")
        h, w = image.shape[:2]
        parse_result = fuse_parsers(vlm_result, cv_result, (w, h), debug_dir=analysis_debug_dir)
        stages_completed.append("parser_fusion")

        if scale_override:
            parse_result.scale.pixels_per_meter = scale_override
            parse_result.scale.method = "user_override"
            parse_result.scale.confidence = 1.0

        # Stage 5: Geometry Analysis
        print(f"\n[{file_id}] Stage 5: Geometry Analysis...")
        geometry_analyzer = GeometryAnalyzer()
        geometry_result = geometry_analyzer.analyze(parse_result, debug_dir=analysis_debug_dir)
        stages_completed.append("geometry_analysis")

        # Stage 6: Structural Validation
        print(f"\n[{file_id}] Stage 6: Structural Validation...")
        structural_validator = StructuralValidator()
        structural_result = structural_validator.validate(parse_result, geometry_result, debug_dir=analysis_debug_dir)
        stages_completed.append("structural_validation")

        # Stage 7: 3D Extrusion (now includes beams & columns)
        print(f"\n[{file_id}] Stage 7: 3D Extrusion...")
        extruder = Extruder()
        scene_graph = extruder.extrude(
            parse_result, geometry_result, structural_result,
            num_floors=num_floors, debug_dir=analysis_debug_dir,
        )
        stages_completed.append("3d_extrusion")

        # Stage 8: Material Recommendation
        print(f"\n[{file_id}] Stage 8: Material Recommendation...")
        material_engine = MaterialEngine()
        materials_result = material_engine.recommend(
            parse_result, geometry_result, optimize_for=optimize_for, debug_dir=analysis_debug_dir,
        )
        stages_completed.append("materials")

        # Stage 9: Cost Estimation
        print(f"\n[{file_id}] Stage 9: Cost Estimation...")
        cost_engine = CostEngine()
        cost_result = cost_engine.estimate(
            parse_result, geometry_result, materials_result, debug_dir=analysis_debug_dir,
        )
        stages_completed.append("cost_estimation")

        # Stage 10: Vastu Compliance
        print(f"\n[{file_id}] Stage 10: Vastu Compliance Check...")
        from pipeline.vastu_checker import VastuChecker
        vastu_result = VastuChecker().check(parse_result)
        stages_completed.append("vastu_check")

        # Stage 11: Foundation Design (IS 1904)
        print(f"\n[{file_id}] Stage 11: Foundation Design...")
        from pipeline.foundation_designer import FoundationDesigner
        fd = FoundationDesigner()
        foundation_result = fd.design_foundations(parse_result, geometry_result, structural_result)
        plinth_result = fd.calculate_plinth_area(parse_result, num_floors=num_floors)
        stages_completed.append("foundation_design")

        # Stage 12: Layout Optimization
        print(f"\n[{file_id}] Stage 12: Layout Optimization...")
        layout_optimizer = LayoutOptimizer()
        optimization_suggestions = layout_optimizer.optimize(
            parse_result, geometry_result, structural_result, debug_dir=analysis_debug_dir,
        )
        stages_completed.append("layout_optimization")

        # Stage 13: Report Generation
        print(f"\n[{file_id}] Stage 13: Report Generation...")
        explainer = Explainer()
        report = explainer.generate_report(
            parse_result, geometry_result, structural_result,
            materials_result, cost_result, optimization_suggestions,
            debug_dir=analysis_debug_dir,
        )
        stages_completed.append("report_generation")

        print(f"\n[{file_id}] Analysis complete! {len(stages_completed)} stages completed.")

        room_count = len(parse_result.rooms)
        room_names = [r.label for r in parse_result.rooms]

        result_data = {
            "stages_completed": stages_completed,
            "parse_result": serialize_pydantic(parse_result),
            "geometry_result": serialize_pydantic(geometry_result),
            "structural_result": serialize_pydantic(structural_result),
            "scene_graph": serialize_pydantic(scene_graph),
            "materials_result": serialize_pydantic(materials_result),
            "cost_result": serialize_pydantic(cost_result),
            "vastu_result": vastu_result,
            "foundation_result": foundation_result,
            "plinth_result": plinth_result,
            "report": serialize_pydantic(report),
            "analyzed_at": datetime.now().isoformat(),
            "summary": {
                "room_count": room_count,
                "room_names": room_names,
                "wall_count": len(geometry_result.classified_walls),
                "structural_score": structural_result.overall_structural_score,
                "total_cost": cost_result.grand_total,
                "beam_count": len(scene_graph.beams),
                "column_count": len(scene_graph.columns),
                "vastu_score": vastu_result.get("overall_score", 0),
            }
        }

        # Cache results
        analysis_cache[file_id] = result_data

        # Save to disk
        cache_path = CACHE_DIR / f"{file_id}.json"
        with open(cache_path, "w") as f:
            json.dump(result_data, f, indent=2, default=str)

        return {"file_id": file_id, "status": "complete",
                "message": f"Analysis complete. {len(stages_completed)} stages processed.",
                **result_data}

    except ImportError as e:
        print(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline import error: {str(e)}. Check dependencies.")
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed at stage {stages_completed[-1] if stages_completed else 'init'}: {str(e)}",
        )


# ── Analysis History ─────────────────────────────────────

@app.get("/api/analyses")
async def list_analyses():
    """List all saved analyses."""
    analyses = []
    for file_id, data in analysis_cache.items():
        summary = data.get("summary", {})
        analyses.append({
            "file_id": file_id,
            "analyzed_at": data.get("analyzed_at", ""),
            "room_count": summary.get("room_count", 0),
            "room_names": summary.get("room_names", []),
            "wall_count": summary.get("wall_count", 0),
            "structural_score": summary.get("structural_score", 0),
            "total_cost": summary.get("total_cost", 0),
            "beam_count": summary.get("beam_count", 0),
            "column_count": summary.get("column_count", 0),
        })
    # Sort by most recent
    analyses.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
    return {"analyses": analyses, "count": len(analyses)}


@app.delete("/api/analysis/{file_id}")
async def delete_analysis(file_id: str):
    """Delete a saved analysis."""
    if file_id in analysis_cache:
        del analysis_cache[file_id]
    
    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        cache_path.unlink()
    
    # Also delete uploaded file
    for ext in [".png", ".jpg", ".jpeg"]:
        upload_path = UPLOAD_DIR / f"{file_id}{ext}"
        if upload_path.exists():
            upload_path.unlink()
    
    return {"status": "deleted", "file_id": file_id}


# ── Data Endpoints ───────────────────────────────────────

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


@app.get("/api/construction-costs")
async def get_construction_costs():
    """Get construction cost database."""
    costs_path = Path(__file__).parent / "data" / "construction_costs_db.json"
    try:
        with open(costs_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Cost database not found")


@app.get("/api/scene/{file_id}")
async def get_scene(file_id: str):
    """Get the 3D scene graph for Three.js visualization."""
    if file_id in analysis_cache:
        scene_data = analysis_cache[file_id].get("scene_graph")
        if scene_data:
            return {"status": "success", "scene": scene_data}

    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        scene_data = data.get("scene_graph")
        if scene_data:
            return {"status": "success", "scene": scene_data}

    raise HTTPException(status_code=404, detail=f"Scene not found for file {file_id}.")


@app.get("/api/report/{file_id}")
async def get_report(file_id: str):
    """Get the full analysis report."""
    if file_id in analysis_cache:
        report_data = analysis_cache[file_id].get("report")
        if report_data:
            return {"status": "success", "report": report_data}

    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        report_data = data.get("report")
        if report_data:
            return {"status": "success", "report": report_data}

    raise HTTPException(status_code=404, detail=f"Report not found for file {file_id}.")


@app.get("/api/analysis/{file_id}")
async def get_analysis(file_id: str):
    """Get complete analysis results for a file."""
    if file_id in analysis_cache:
        return {"status": "success", "file_id": file_id, **analysis_cache[file_id]}

    cache_path = CACHE_DIR / f"{file_id}.json"
    if cache_path.exists():
        with open(cache_path, "r") as f:
            data = json.load(f)
        analysis_cache[file_id] = data
        return {"status": "success", "file_id": file_id, **data}

    raise HTTPException(status_code=404, detail=f"Analysis not found for file {file_id}.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
