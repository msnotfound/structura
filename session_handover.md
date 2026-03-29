# Session Handover - Structura

> Created: 2026-03-29
> Hackathon Submission: Tomorrow

## Project Overview

**Structura** is an Autonomous Structural Intelligence System for analyzing floor plans. It:
1. Parses floor plan images using VLM (Gemini) + CV (OpenCV) fusion
2. Classifies walls as load-bearing/partition/structural spine
3. Validates structural integrity (spans, load paths)
4. Extrudes 2D plans to 3D for Three.js visualization
5. Recommends materials with cost-strength-durability tradeoffs
6. Generates cost estimates
7. Produces LLM-powered explanations (Cerebras/Groq)

---

## Current State: v0.3-pipeline-integration

### What's Done
- [x] Git repository with proper `.gitignore`
- [x] **v0.1-scaffold**: Full backend with all Pydantic models, 11 pipeline modules, materials_db.json
- [x] **v0.2-frontend**: React + Vite + Tailwind + Three.js frontend with all components
- [x] **v0.3-pipeline-integration**: FastAPI endpoints wired to pipeline (COMMITTED & TAGGED)
- [x] Backend dependencies installed in `backend/venv/`
- [x] Test floor plan created at `sample_plans/simple_floor_plan.png`
- [x] Backend server starts and `/health` endpoint works
- [x] `/api/upload` endpoint works (tested successfully)

### What's Broken - IMMEDIATE FIX NEEDED

**Pipeline import error** when calling `/api/analyze/{file_id}`:
```
{"detail":"Pipeline import error: attempted relative import beyond top-level package. Check dependencies."}
```

The error occurs in `backend/main.py` around line 34-50 where pipeline modules are imported:
```python
from pipeline import (
    preprocess_image,
    VLMParser,
    CVParser,
    # ... etc
)
```

**Root Cause**: The pipeline modules use relative imports that fail when FastAPI loads them. Need to fix import paths in `backend/pipeline/` modules.

**To Debug**:
```bash
cd backend
source venv/bin/activate
python -c "from pipeline import preprocess_image" 2>&1
```

---

## File Structure

```
structura/
├── backend/
│   ├── venv/                        # Python virtual environment (INSTALLED)
│   ├── uploads/                     # Upload storage (created on-demand)
│   ├── cache/                       # Analysis cache (created on-demand)
│   ├── debug/                       # Debug images output
│   ├── main.py                      # FastAPI app - PIPELINE WIRED BUT IMPORT ERROR
│   ├── pipeline/                    # 11 processing modules
│   │   ├── __init__.py              # Exports all pipeline classes
│   │   ├── preprocessor.py          # preprocess_image()
│   │   ├── vlm_parser.py            # VLMParser class
│   │   ├── cv_parser.py             # CVParser class
│   │   ├── parser_fusion.py         # fuse_parsers()
│   │   ├── geometry.py              # GeometryAnalyzer class
│   │   ├── structural_validator.py  # StructuralValidator class
│   │   ├── extruder.py              # Extruder class
│   │   ├── materials.py             # MaterialEngine class
│   │   ├── cost_engine.py           # CostEngine class
│   │   ├── layout_optimizer.py      # LayoutOptimizer class
│   │   └── explainer.py             # Explainer class
│   ├── models/                      # Pydantic schemas (all implemented)
│   │   ├── parsing.py, geometry.py, structural.py, three_d.py
│   │   ├── materials.py, cost.py, report.py
│   ├── data/materials_db.json       # 7 construction materials
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts            # Axios API client
│   │   ├── components/              # UI components, Three.js, panels
│   │   ├── hooks/useAnalysis.ts
│   │   ├── types/index.ts
│   │   └── App.tsx
│   ├── package.json                 # Dependencies NOT INSTALLED YET
│   └── vite.config.ts
├── sample_plans/
│   └── simple_floor_plan.png        # Test image (created)
├── STATE.md                         # Project state tracking
├── session_handover.md              # THIS FILE
└── .gitignore
```

---

## Immediate Tasks (Priority Order)

### 1. FIX PIPELINE IMPORTS (BLOCKING)
Debug and fix the import error in pipeline modules:
```bash
cd backend && source venv/bin/activate
python -c "from pipeline import preprocess_image"
```

Likely fixes:
- Check `backend/pipeline/__init__.py` for correct exports
- Check individual modules for relative imports like `from .models import ...` that should be `from models import ...`
- May need to add `backend/` to Python path or restructure imports

### 2. Test Full Pipeline
Once imports fixed:
```bash
cd backend && source venv/bin/activate
MOCK_MODE=true uvicorn main:app --reload --port 8000

# In another terminal:
curl -X POST http://localhost:8000/api/upload -F "file=@sample_plans/simple_floor_plan.png"
# Use returned file_id:
curl -X POST http://localhost:8000/api/analyze/{file_id}
```

### 3. Install & Test Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend expects backend at `http://localhost:8000`

### 4. End-to-End Test
- Upload floor plan via frontend
- Run analysis
- View 3D model in Three.js viewer
- Check all panels (walls, structural, materials, cost, report)

### 5. Git Commit After Fixes
```bash
git add -A
git commit -m "fix(backend): resolve pipeline import errors"
```

---

## Environment Setup

### Backend
```bash
cd backend
source venv/bin/activate  # venv already created with deps installed
MOCK_MODE=true uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install  # NOT DONE YET
npm run dev
```

### Environment Variables (for real API calls)
```bash
export GOOGLE_AI_API_KEY=...     # Gemini 2.5 Flash
export CEREBRAS_API_KEY=...      # Qwen 3 32B
export GROQ_API_KEY=...          # Llama 3.3 70B (fallback)
export MOCK_MODE=false           # Set true for template responses
```

---

## API Endpoints

| Endpoint | Method | Status |
|----------|--------|--------|
| `/health` | GET | Working |
| `/api/upload` | POST | Working |
| `/api/analyze/{file_id}` | POST | BROKEN - import error |
| `/api/analysis/{file_id}` | GET | Untested |
| `/api/materials` | GET | Untested |
| `/api/scene/{file_id}` | GET | Untested |
| `/api/report/{file_id}` | GET | Untested |

---

## Key Technical Details

### Pipeline Flow
```
Image Upload → Preprocessor → VLM Parser + CV Parser → Fusion → 
Geometry Analyzer → Structural Validator → Extruder (3D) + 
Materials Engine → Cost Engine → Layout Optimizer → Explainer → Report
```

### Models Used
- **Vision**: Google Gemini 2.5 Flash (`google-generativeai` SDK)
- **Text**: Cerebras Qwen 3 32B (OpenAI-compatible, base_url="https://api.cerebras.ai/v1")
- **Fallback**: Groq Llama 3.3 70B (base_url="https://api.groq.com/openai/v1")

### Frontend Stack
- React 18 + Vite + TypeScript
- Tailwind CSS v4 (with @tailwindcss/vite plugin)
- @react-three/fiber + @react-three/drei for 3D
- Recharts for charts
- lucide-react for icons

---

## Agent Rules (from original instructions)

1. **Debug Images**: Save to `backend/debug/` with detected elements drawn
2. **Print Summaries**: "Detected: X walls, Y rooms, Z openings"
3. **Update STATE.md**: After every commit
4. **Git Commits**: Conventional format - feat(), fix(), refactor(), docs(), test(), chore()
5. **Git Tags**: After each stage - `git tag -a v0.X-stagename -m "description"`
6. **Fallback Rule**: If algorithm fails 3 attempts, implement simpler fallback and move on

---

## Known Issues

1. **Pipeline Import Error**: Main blocker - relative imports failing
2. **Cerebras Model**: Uses `qwen-3-32b` (not 235B as originally noted)
3. **Frontend deps**: Not installed yet

---

## Test Data

- `sample_plans/simple_floor_plan.png` - Simple 800x600 floor plan with:
  - 4 rooms (Living Room, Bedroom, Kitchen, Bath)
  - Outer walls + interior walls
  - Door and window openings
  - Scale indicator (5m)

---

## Server Status (when I left)

Backend server was running on port 8000:
```bash
# To kill if still running:
pkill -f "uvicorn main:app"

# To restart:
cd backend && source venv/bin/activate
MOCK_MODE=true uvicorn main:app --reload --port 8000
```

---

## Next Milestone

After fixing imports and testing, commit as:
```bash
git add -A
git commit -m "fix(backend): resolve pipeline import errors and verify end-to-end flow"
git tag -a v0.4-testing -m "Pipeline tested and working"
```

Then focus on:
- Frontend testing
- UI polish
- Error handling improvements
- Documentation for submission
