# STRUCTURA — Autonomous Structural Intelligence System

> **AI-powered floor plan analysis with IS 456:2000 structural design, 3D visualization, and comprehensive cost estimation.**

## 🏗️ Team TylerDurden

| Name | 
|------|
| **Mayank Sahu** | 
| **Abhinav Shrivastava** | 
| **Rishikant Kushwaha** | 

**College:** IIIT Naya Raipur

---

## ✨ Features

### 🔍 Intelligent Floor Plan Analysis
- Upload any floor plan image (PNG/JPG/WebP) — simple or professional
- **Hybrid AI Pipeline**: Google Gemini 2.5 Flash (VLM) + OpenCV (computer vision) fusion
- Automatic room detection, wall classification, and opening identification
- VLM extracts dimensions text from professional plans for accurate scaling

### 🏛️ IS 456:2000 Structural Design
- **Beam Design**: Bending moment, shear reinforcement, deflection checks per IS 456
- **Column Design**: Axial capacity with steel ratio optimization
- **Slab Classification**: One-way vs two-way slab detection
- Wall classification: Load Bearing, Structural Spine, Partition
- Structural integrity scoring with sigmoid-based penalty function

### 🎮 Interactive 3D Visualization
- Real-time 3D model with Three.js / React Three Fiber
- Color-coded walls (Load Bearing = Red, Spine = Orange, Partition = Blue)
- **RCC Beams** (Blue) and **Columns** (Amber) rendered at structural positions
- Click any element → Engineering popup with IS 456 design data
- Toggle filters: Walls / Beams / Columns / Slabs / Labels
- Shadows, ACES tone mapping, hemisphere lighting

### 💰 Comprehensive Cost Estimation
- **10 categories**: Foundation, RCC Structure, Masonry, Plastering, Flooring, Painting, Electrical, Plumbing, Doors/Windows, Waterproofing
- Based on CPWD Schedule of Rates 2025-26
- Budget (₹1600/sqft) / Standard / Premium (₹3000/sqft) tiers
- Per-room and per-category cost breakdown

### 🔐 Authentication & History
- Email/password login with session tokens
- Analysis history — save, load, delete past analyses
- Disk-cached persistence (survives server restarts)

### 🚀 Deployment Ready
- Backend: `render.yaml` for Render
- Frontend: `netlify.toml` with API proxy redirects

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS |
| **3D Engine** | Three.js, React Three Fiber, Drei |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI/ML** | Google Gemini 2.5 Flash, Cerebras Qwen 3 235B, Groq Llama 4 Scout |
| **Computer Vision** | OpenCV, NumPy, Pillow |
| **Structural Eng.** | IS 456:2000 calculation engine |
| **Auth** | SHA-256 + session tokens |

---

## 📦 Project Structure

```
structura/
├── backend/
│   ├── main.py                     # FastAPI server + auth + history
│   ├── pipeline/
│   │   ├── vlm_parser.py           # Gemini/Groq VLM parser
│   │   ├── cv_parser.py            # OpenCV wall/room detection
│   │   ├── parser_fusion.py        # VLM + CV result fusion
│   │   ├── geometry_analyzer.py    # Wall classification
│   │   ├── structural_validator.py # Span analysis + warnings
│   │   ├── beam_calculator.py      # IS 456:2000 beam/column design
│   │   ├── extruder.py             # 2D → 3D scene generation
│   │   ├── cost_engine.py          # Comprehensive cost estimation
│   │   ├── material_advisor.py     # Material recommendations
│   │   └── report_writer.py        # AI report generation
│   ├── models/                     # Pydantic data models
│   ├── data/
│   │   └── construction_costs_db.json  # CPWD cost database
│   └── .env                        # API keys
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── three/ThreeViewer.tsx    # 3D viewer with beams/columns
│   │   │   ├── panels/                 # Analysis panels
│   │   │   └── LoginPage.tsx           # Authentication UI
│   │   ├── hooks/useAnalysis.ts
│   │   ├── api/client.ts
│   │   └── App.tsx
│   └── vite.config.ts
├── render.yaml                     # Render deployment
├── netlify.toml                    # Netlify deployment
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- API Keys: Google AI, Cerebras, Groq

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_AI_API_KEY=your_key" > .env
echo "CEREBRAS_API_KEY=your_key" >> .env
echo "GROQ_API_KEY=your_key" >> .env
echo "MOCK_MODE=false" >> .env

# Run
python -m uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and upload a floor plan!

---

## 📊 Analysis Pipeline

```
Floor Plan Image
       │
       ├── VLM Parser (Gemini 2.5 Flash)
       │   └── Room labels, dimensions, bounding boxes
       │
       ├── CV Parser (OpenCV)
       │   └── Wall segments, room contours, openings
       │
       └── Parser Fusion
            └── Best-of-both: VLM labels + CV geometry
                     │
          ┌──────────┼──────────┐
          │          │          │
    Wall       Structural    3D
  Classifier   Validator   Extruder
          │          │          │
    Material    IS 456       Beam &
    Advisor    Scoring      Column
          │          │     Generation
          └──────────┼──────────┘
                     │
              Cost Engine
            (CPWD 2025-26)
                     │
              AI Report
           (Cerebras Qwen 3)
```

---

## 📐 IS 456:2000 Calculations

| Parameter | Formula | Reference |
|-----------|---------|-----------|
| Beam Depth | `d = L/12` (simply supported) | Cl. 23.2.1 |
| Beam Width | `b = d/2` (min 200mm) | Best practice |
| Bending Moment | `Mu = Wu·L²/8` | Statics |
| Steel Area | Quadratic: `Mu = 0.87·fy·Ast·d·(1 - Ast·fy/(b·d·fck))` | Annex G |
| Shear Stirrups | `Sv = 0.87·fy·Asv·d/Vus` | Cl. 26.5.1.6 |
| Column Capacity | `Pu = 0.4·fck·Ac + 0.67·fy·Asc` | Cl. 39.3 |
| Slab Type | `Ly/Lx > 2` → one-way | Cl. 24.4 |
| Deflection | `L/d ≤ 20` (simply supported) | Cl. 23.2.1 |

---

## 🏗️ Built for Technovate Hackathon

This project was built at the Technovate Hackathon as a prototype for autonomous structural intelligence — bringing civil engineering expertise to anyone with a floor plan.

**The system handles:**
- ✅ Simple hand-drawn floor plans
- ✅ Professional architectural drawings with dimensions
- ✅ Indian Standard compliant structural analysis
- ✅ Real-world cost estimation based on CPWD rates

---

## 📝 License

MIT License — Built with ❤️ by Team TylerDurden at IIIT Naya Raipur
