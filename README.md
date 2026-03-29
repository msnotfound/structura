# Structura — Autonomous Structural Intelligence System

> **AIML PS2 Hackathon Submission** · Floor Plan Analysis & Structural Intelligence

---

## What It Does

Upload any architectural floor plan image → get a full AI-powered structural analysis:

| Feature | How |
|---------|-----|
| 🏗️ Wall Classification | Load-bearing / partition / structural spine via OpenCV + Gemini |
| 📐 Structural Validation | Span analysis, load paths, code compliance warnings |
| 🧱 Material Recommendations | Cost-strength-durability tradeoff ranking (7 materials) |
| 💰 Cost Estimation | Per-room / per-category breakdown with budget vs premium |
| 🌐 3D Visualization | Interactive extruded building model (Three.js) |
| 📝 Expert Report | LLM-generated explanations and optimization suggestions |

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## API Keys Required

You need **3 API keys**. Get them free:

| Key | Where to get | Env var |
|-----|-------------|---------|
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) → Get API Key | `GOOGLE_AI_API_KEY` |
| Cerebras | [cloud.cerebras.ai](https://cloud.cerebras.ai) → API Keys | `CEREBRAS_API_KEY` |
| Groq (fallback) | [console.groq.com](https://console.groq.com) → API Keys | `GROQ_API_KEY` |

> **Note**: If you don't have keys, set `MOCK_MODE=true` to run with pre-generated mock data. The pipeline still runs all 11 stages using deterministic mock responses.

---

## Setup & Run

### 1 — Clone

```bash
git clone <repo-url>
cd structura
```

### 2 — Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate
# Activate (Windows CMD)
venv\Scripts\activate.bat
# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Install all dependencies (includes google-genai, cerebras-cloud-sdk, opencv)
pip install -r requirements.txt

# Set API keys — Linux/Mac:
export GOOGLE_AI_API_KEY="your-gemini-key"
export CEREBRAS_API_KEY="your-cerebras-key"
export GROQ_API_KEY="your-groq-key"
export MOCK_MODE="false"

# Set API keys — Windows CMD:
set GOOGLE_AI_API_KEY=your-gemini-key
set CEREBRAS_API_KEY=your-cerebras-key
set GROQ_API_KEY=your-groq-key
set MOCK_MODE=false

# Run backend (must be run FROM the backend/ directory)
uvicorn main:app --reload --port 8000
```

Backend will start at **http://localhost:8000**  
Swagger docs at **http://localhost:8000/docs**

> ⚠️ **Always run from the `backend/` directory** — the pipeline uses absolute imports relative to that folder.

### 3 — Frontend (separate terminal)

```bash
cd frontend

npm install

npm run dev
```

Frontend will start at **http://localhost:5173**

---

## Quick Test

Once both are running:

1. Open **http://localhost:5173**
2. Click **"Analyze Floor Plan"**
3. Upload `sample_plans/simple_floor_plan.png` (included in repo)
4. Wait ~10-30 seconds (real APIs) or ~5 seconds (MOCK_MODE=true)
5. Explore: Walls tab → Structural tab → Materials → Cost → Report → 3D viewer

---

## MOCK_MODE vs Real APIs

```bash
# Mock mode — no API keys needed, instant results, deterministic
MOCK_MODE=true uvicorn main:app --reload --port 8000

# Real mode — uses Gemini Vision + Cerebras/Groq LLMs, richer results
MOCK_MODE=false uvicorn main:app --reload --port 8000
```

**What changes between modes:**
- **Stage 2 (VLM)**: Real = Gemini 2.5 Flash reads the image; Mock = 5 hardcoded rooms
- **Stage 11 (Report)**: Real = Cerebras Qwen 3 generates expert text; Mock = template text
- **Stages 1,3-10**: Identical in both modes (pure OpenCV + algorithmic)

---

## Pipeline (11 Stages)

```
Image → [1] Preprocess → [2] VLM Parse (Gemini)
                       → [3] CV Parse (OpenCV)
                       → [4] Fusion
                       → [5] Geometry
                       → [6] Structural Validation
                       → [7] 3D Extrusion
                       → [8] Material Recommendations
                       → [9] Cost Estimation
                       → [10] Layout Optimization
                       → [11] Report (Cerebras/Groq)
```

---

## Project Structure

```
structura/
├── backend/
│   ├── pipeline/           # 11 processing modules
│   │   ├── cv_parser.py    # OpenCV wall/room detection
│   │   ├── vlm_parser.py   # Gemini Vision (google-genai SDK)
│   │   ├── geometry.py     # Wall classification & junctions
│   │   ├── structural_validator.py
│   │   ├── extruder.py     # 2D → 3D scene graph
│   │   ├── materials.py    # Material recommendation engine
│   │   ├── cost_engine.py  # Cost estimation
│   │   ├── explainer.py    # LLM report (Cerebras → Groq fallback)
│   │   └── ...
│   ├── models/             # 7 Pydantic schema files
│   ├── data/               # materials_db.json (7 materials)
│   ├── main.py             # FastAPI app + all endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── panels/     # WallsPanel, StructuralPanel, etc.
│   │   │   └── three/      # ThreeViewer (Three.js 3D viewer)
│   │   ├── types/          # TypeScript types (aligned to API)
│   │   └── App.tsx
│   └── package.json
├── sample_plans/
│   └── simple_floor_plan.png   ← use this for testing
└── README.md
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + API key status |
| `/api/upload` | POST | Upload floor plan (multipart/form-data, field: `file`) |
| `/api/analyze/{file_id}` | POST | Run full 11-stage pipeline |
| `/api/analysis/{file_id}` | GET | Get cached analysis result |
| `/api/materials` | GET | Materials database |
| `/api/scene/{file_id}` | GET | Three.js scene graph |
| `/api/report/{file_id}` | GET | Full analysis report |

---

## Troubleshooting

**`ImportError: attempted relative import beyond top-level package`**  
→ You're not running from `backend/`. `cd backend` first, then run uvicorn.

**`Cannot apply unknown utility class 'btn'`**  
→ Tailwind v4 issue, already fixed in `index.css`. Run `npm install` then `npm run dev`.

**VLM falls back to mock (even with MOCK_MODE=false)**  
→ Check your `GOOGLE_AI_API_KEY` is set correctly. See `/health` endpoint for key status.

**Cerebras 404 / model not found**  
→ The model is `qwen-3-235b-a22b-instruct-2507`. Already set in `explainer.py`. If you get a 404, Groq will auto-fallback.

**3D viewer is blank**  
→ WebGL required. Use Chrome or Firefox. Try resizing the window to trigger a re-render.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.12, FastAPI, Uvicorn |
| Vision AI | Google Gemini 2.5 Flash (`google-genai` SDK) |
| Computer Vision | OpenCV 4, NumPy |
| LLM (Primary) | Cerebras Qwen 3 235B |
| LLM (Fallback) | Groq Llama 3.3 70B |
| Frontend | React 18, Vite, TypeScript |
| 3D | Three.js, @react-three/fiber, @react-three/drei |
| Charts | Recharts |
| Styling | Tailwind CSS v4 |

---

## License

Hackathon submission — All rights reserved.
