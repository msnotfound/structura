# Structura - Project State

> Last Updated: 2026-03-29

## Current Stage: v0.3-pipeline-integration

### Completed Stages
- [x] **v0.1-scaffold** - Project structure, Pydantic models, material DB, FastAPI skeleton
- [x] **v0.2-frontend** - React + Vite + Tailwind + Three.js setup
- [x] **v0.3-pipeline-integration** - Wire up all pipeline modules to FastAPI

### Pending Stages
- [ ] **v0.4-testing** - Integration tests with sample floor plans
- [ ] **v0.5-polish** - UI polish, error handling, documentation

---

## Pydantic Models

| Model File | Classes | Location |
|------------|---------|----------|
| `parsing.py` | Point2D, WallSegment, Opening, Room, ScaleReference, VLMParseResult, CVParseResult, ParseResult | `backend/models/parsing.py` |
| `geometry.py` | Junction, ClassifiedWall, GeometryResult | `backend/models/geometry.py` |
| `structural.py` | SpanAnalysis, StructuralWarning, StructuralAnalysisResult | `backend/models/structural.py` |
| `three_d.py` | Point3D, Face, ExtrudedWall, Slab, RoomLabel3D, CameraBounds, SceneGraph | `backend/models/three_d.py` |
| `materials.py` | Material, WeightProfile, MaterialOption, MaterialRecommendation, MaterialsResult | `backend/models/materials.py` |
| `cost.py` | CostLineItem, RoomCost, CategoryCost, ProjectCost, CostComparison | `backend/models/cost.py` |
| `report.py` | ElementExplanation, OptimizationSuggestion, FullReport | `backend/models/report.py` |

---

## Frontend Components

| Component | Location | Description |
|-----------|----------|-------------|
| `FileUpload` | `frontend/src/components/ui/FileUpload.tsx` | Drag-and-drop image upload |
| `Button` | `frontend/src/components/ui/Button.tsx` | Styled button with variants |
| `Card` | `frontend/src/components/ui/Card.tsx` | Card container components |
| `Badge` | `frontend/src/components/ui/Badge.tsx` | Status badges (severity, wall type) |
| `Progress` | `frontend/src/components/ui/Progress.tsx` | Progress bars and score displays |
| `ThreeViewer` | `frontend/src/components/three/ThreeViewer.tsx` | 3D floor plan visualization |
| `WallsPanel` | `frontend/src/components/panels/WallsPanel.tsx` | Wall classification display |
| `StructuralPanel` | `frontend/src/components/panels/StructuralPanel.tsx` | Structural analysis results |
| `MaterialsPanel` | `frontend/src/components/panels/MaterialsPanel.tsx` | Material recommendations |
| `CostPanel` | `frontend/src/components/panels/CostPanel.tsx` | Cost estimation with charts |
| `ReportPanel` | `frontend/src/components/panels/ReportPanel.tsx` | Full analysis report |

---

## Inter-Stage Data Flow

```
┌─────────────────┐
│  Image Upload   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Preprocessor   │────▶│  Debug Images   │
│  (preprocessor) │     │  backend/debug/ │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   VLM Parser    │     │   CV Parser     │
│  (vlm_parser)   │     │  (cv_parser)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Parser Fusion  │
            │ (parser_fusion) │
            └────────┬────────┘
                     │ ParseResult
                     ▼
            ┌─────────────────┐
            │    Geometry     │
            │   (geometry)    │
            └────────┬────────┘
                     │ GeometryResult
                     ▼
            ┌─────────────────┐
            │   Structural    │
            │   Validator     │
            └────────┬────────┘
                     │ StructuralAnalysisResult
                     ▼
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌─────────────────┐     ┌─────────────────┐
│    Extruder     │     │    Materials    │
│   (extruder)    │     │   (materials)   │
└────────┬────────┘     └────────┬────────┘
         │ SceneGraph            │ MaterialsResult
         │                       │
         │              ┌────────┴────────┐
         │              │                 │
         │              ▼                 ▼
         │     ┌─────────────────┐ ┌─────────────────┐
         │     │   Cost Engine   │ │ Layout Optimizer│
         │     │  (cost_engine)  │ │(layout_optimizer│
         │     └────────┬────────┘ └────────┬────────┘
         │              │ ProjectCost       │
         │              │                   │
         └──────────────┼───────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │    Explainer    │
               │   (explainer)   │
               └────────┬────────┘
                        │ FullReport
                        ▼
               ┌─────────────────┐
               │   JSON Response │
               └─────────────────┘
```

---

## API Endpoints

| Endpoint | Method | Input | Output | Status |
|----------|--------|-------|--------|--------|
| `/health` | GET | - | `{"status": "healthy"}` | ✅ Implemented |
| `/api/upload` | POST | `multipart/form-data` (image) | `{"file_id": str}` | ✅ Implemented |
| `/api/analyze/{file_id}` | POST | file_id | Full analysis result | ✅ Implemented |
| `/api/analysis/{file_id}` | GET | file_id | Cached analysis result | ✅ Implemented |
| `/api/materials` | GET | - | Materials database | ✅ Implemented |
| `/api/scene/{file_id}` | GET | file_id | SceneGraph (Three.js) | ✅ Implemented |
| `/api/report/{file_id}` | GET | file_id | FullReport | ✅ Implemented |

---

## Pipeline Modules

| Module | Function | Input | Output | Status |
|--------|----------|-------|--------|--------|
| `preprocessor.py` | `preprocess_image()` | np.ndarray | ProcessedImage | ✅ Implemented |
| `vlm_parser.py` | `parse_with_vlm()` | image bytes | VLMParseResult | ✅ Implemented |
| `cv_parser.py` | `parse_with_cv()` | np.ndarray | CVParseResult | ✅ Implemented |
| `parser_fusion.py` | `fuse_results()` | VLM + CV results | ParseResult | ✅ Implemented |
| `geometry.py` | `analyze_geometry()` | ParseResult | GeometryResult | ✅ Implemented |
| `structural_validator.py` | `validate_structure()` | GeometryResult | StructuralAnalysisResult | ✅ Implemented |
| `extruder.py` | `extrude_to_3d()` | GeometryResult | SceneGraph | ✅ Implemented |
| `materials.py` | `recommend_materials()` | GeometryResult | MaterialsResult | ✅ Implemented |
| `cost_engine.py` | `estimate_costs()` | MaterialsResult | ProjectCost | ✅ Implemented |
| `layout_optimizer.py` | `suggest_optimizations()` | GeometryResult | list[OptimizationSuggestion] | ✅ Implemented |
| `explainer.py` | `generate_report()` | all results | FullReport | ✅ Implemented |

---

## Known Issues

1. **Cerebras model**: Uses `qwen-3-32b` (not 235B as originally specified)
2. **Upload/cache dirs**: Created on-demand at `backend/uploads/` and `backend/cache/`

---

## Test Results

- **v0.3-pipeline-integration**: Pending manual testing

---

## Environment Variables

```bash
GOOGLE_AI_API_KEY=     # Gemini 2.5 Flash for VLM parsing
CEREBRAS_API_KEY=      # Qwen 3 235B for explanations (primary)
GROQ_API_KEY=          # Llama 3.3 70B for explanations (fallback)
MOCK_MODE=true         # Set to false for real API calls
```

---

## File Structure

```
structura/
├── backend/
│   ├── pipeline/           # Processing modules
│   │   ├── __init__.py
│   │   ├── preprocessor.py
│   │   ├── vlm_parser.py
│   │   ├── cv_parser.py
│   │   ├── parser_fusion.py
│   │   ├── geometry.py
│   │   ├── structural_validator.py
│   │   ├── extruder.py
│   │   ├── materials.py
│   │   ├── cost_engine.py
│   │   ├── layout_optimizer.py
│   │   └── explainer.py
│   ├── models/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── parsing.py
│   │   ├── geometry.py
│   │   ├── structural.py
│   │   ├── three_d.py
│   │   ├── materials.py
│   │   ├── cost.py
│   │   └── report.py
│   ├── data/
│   │   └── materials_db.json
│   ├── uploads/           # Uploaded images (created on-demand)
│   ├── cache/             # Analysis result cache (created on-demand)
│   ├── debug/              # Debug images output
│   ├── main.py             # FastAPI app (fully wired pipeline)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API client
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ui/         # Base UI components
│   │   │   ├── three/      # Three.js components
│   │   │   └── panels/     # Analysis panels
│   │   ├── hooks/          # React hooks
│   │   │   └── useAnalysis.ts
│   │   ├── lib/            # Utilities
│   │   │   └── utils.ts
│   │   ├── types/          # TypeScript types
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── sample_plans/           # Test floor plans (empty)
├── STATE.md                # This file
├── README.md
└── .gitignore
```
