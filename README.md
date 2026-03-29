# Structura - Autonomous Structural Intelligence System

> PS2 Hackathon Submission - Floor Plan Analysis & Structural Intelligence

## Overview

Structura is an AI-powered system that analyzes architectural floor plans to provide:

- **Structural Classification**: Identifies load-bearing walls, partitions, and structural spines
- **Integrity Validation**: Validates spans, load paths, and structural soundness
- **3D Visualization**: Extrudes 2D plans to interactive Three.js models
- **Material Recommendations**: AI-driven material selection with cost-strength-durability tradeoffs
- **Cost Estimation**: Detailed cost breakdowns by room, category, and material
- **Expert Reports**: LLM-generated explanations and optimization suggestions

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **Google Gemini 2.5 Flash** - Vision Language Model for floor plan parsing
- **OpenCV** - Computer vision for wall/room detection
- **Cerebras Qwen 3 235B** - Primary LLM for explanations
- **Groq Llama 3.3 70B** - Fallback LLM

### Frontend
- **React 18** + Vite
- **shadcn/ui** + Tailwind CSS
- **@react-three/fiber** + **@react-three/drei** - 3D visualization
- **Recharts** - Cost/analysis charts

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_AI_API_KEY="your-gemini-key"
export CEREBRAS_API_KEY="your-cerebras-key"
export GROQ_API_KEY="your-groq-key"
export MOCK_MODE="true"  # Set to false for real API calls

# Run server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/upload` | POST | Upload floor plan image |
| `/api/analyze/{file_id}` | POST | Run full analysis pipeline |
| `/api/materials` | GET | Get materials database |
| `/api/scene/{file_id}` | GET | Get Three.js scene graph |
| `/api/report/{file_id}` | GET | Get full analysis report |

## Pipeline Architecture

```
Image Upload → Preprocessing → VLM + CV Parsing → Fusion
     ↓
Geometry Analysis → Structural Validation → 3D Extrusion
     ↓
Material Recommendation → Cost Estimation → Report Generation
```

## Materials Database

7 construction materials with detailed properties:
- AAC Blocks
- Red Brick (Traditional)
- RCC (Reinforced Cement Concrete)
- Steel Frame
- Hollow Concrete Block
- Fly Ash Brick
- Precast Concrete Panel

Each material includes:
- Compressive strength (MPa)
- Thermal conductivity (W/mK)
- Fire rating (hours)
- Cost per unit
- Durability rating
- Environmental score

## Project Structure

```
structura/
├── backend/
│   ├── pipeline/       # 11 processing modules
│   ├── models/         # 7 Pydantic schema files
│   ├── data/           # materials_db.json
│   ├── debug/          # Debug image output
│   ├── main.py         # FastAPI application
│   └── requirements.txt
├── frontend/           # React application
├── sample_plans/       # Test floor plans
├── STATE.md            # Project state tracking
└── README.md           # This file
```

## Development

See `STATE.md` for:
- Current development stage
- Pydantic model locations
- Inter-stage data flow
- Known issues
- Test results

## License

Hackathon submission - All rights reserved.
