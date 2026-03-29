# Structura — Session Handover 2

## Context & Current State
The project is **Structura**, an autonomous structural intelligence system built for the AIML PS2 Hackathon. It processes a 2D floor plan image through an 11-stage AI and computer vision pipeline and presents the data in a rich React/Three.js frontend.

Over the current session, the primary goal was to connect the fully scaffolded (but previously failing) backend pipeline to the React frontend, fixing all runtime crashes, aligning data schemas, and moving from mock data to real AI inference.

**The system is currently 100% functional end-to-end.** 

### What Was Accomplished (This Session)
1. **Pipeline Module Resolution:** 
   - Fixed `ImportError: attempted relative import beyond top-level package` across all 11 backend pipeline modules by switching from relative imports (`from ..models`) to absolute imports (`from models`). The FastAPI server now runs successfully.
2. **Frontend Type Alignment:**
   - Overhauled `frontend/src/types/index.ts` to exactly match the backend's actual Pydantic schema return values.
   - Example fixes: `wall.id` ➡️ `wall.wall_id`, `category_costs` ➡️ `category_totals`, `recommended_materials` ➡️ `options`, `impact_level` ➡️ `priority`, etc.
3. **UI Crash Prevention:**
   - Rewrote all 5 primary rendering panels (`WallsPanel`, `StructuralPanel`, `MaterialsPanel`, `CostPanel`, `ReportPanel`) to safely handle `null`/`undefined` properties from the API.
   - Fixed mapping logic for lists (e.g., properly iterating over `room_totals` vs `category_totals` in the charts).
4. **3D Viewer Alignment:**
   - Refactored `ThreeViewer.tsx` to handle the actual `scene_graph` response schema (`wall.vertices_3d` instead of `wall.vertices`).
   - Integrated scaling logic (~60 pixels to 1 meter) so the 3D model properly extrudes in 3D space with correct camera bounds.
   - Removed a `PCFSoftShadowMap` deprecation warning.
5. **Real AI Integration:**
   - Upgraded from the deprecated `google.generativeai` SDK to the new `google-genai` SDK for the Gemini Vision VLM.
   - Locked Gemini model to `gemini-2.5-flash`.
   - Installed and configured the `cerebras-cloud-sdk` and locked the LLM to the valid key-associated model: `qwen-3-235b-a22b-instruct-2507`.
6. **Documentation:**
   - Completely rewrote the main `README.md` to be "teammate-ready" with comprehensive setup instructions for all OSes, API key sources, and pipeline documentation.

---

## Known Environment Configuration
- **Backend Directory:** `structura/backend/`
  - Runs via `MOCK_MODE=false uvicorn main:app --reload --port 8000` (MUST be run from inside the `backend/` directory due to absolute module routing).
  - Virtual environment must have `google-genai`, `cerebras-cloud-sdk`, and `opencv-python` installed.
- **Frontend Directory:** `structura/frontend/`
  - Runs via `npm run dev` (Vite, port 5173).
- **Required API Keys (in environment or bash vars):**
  - `GOOGLE_AI_API_KEY`
  - `CEREBRAS_API_KEY` 
  - `GROQ_API_KEY`
  - Note: VLM parser will fall back to mock data if the Google AI key isn't passed; Cerebras will fallback to Groq if the Groq key is present.

---

## Next Steps / Directives for Incoming Agent

If taking over, your immediate focus should likely be on polish, performance, or specific feature extensions for the hackathon presentation. The core system does not need fixing.

1. **Review Terminal Output:** 
   - Check the `uvicorn` and `vite` processes. There shouldn't be any critical runtime errors, but be aware that React DevTools or Three.js internal deprecation warnings (`THREE.Clock is deprecated`) might occasionally log to the frontend console—these are harmless and originate from dependencies.
2. **React Key Warnings:**
   - There may still be some minor React `key` prop warnings in lists (e.g., inside the `WallsPanel` or `ThreeViewer` component loops). Scrub the console and add robust unique keys to `.map()` loops if requested for clean presentation.
3. **Refinement/Extensions:**
   - If the user wants better visual aesthetics in the 3D model, you can play with `@react-three/drei` materials, lighting, or floor textures in `ThreeViewer.tsx`.
   - If the user needs to fine-tune the Gemini VLM prompt to extract more accurate room names from complex floor plans, that logic lives in `backend/pipeline/vlm_parser.py`.
   - If the user wants to adjust cost estimations, material datasets live in `backend/data/materials_db.json`.

**Agent Note:** Do not blindly rewrite the parsing logic or frontend API destructuring unless you actively break things. It has been painstakingly aligned over the last session. Any UI feature additions should be built *around* the stable `models/parsing.py` schema.
