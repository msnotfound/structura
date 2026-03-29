"""
Pydantic models for the Structural Intelligence System.
These are the contracts between pipeline stages.
"""

from .parsing import (
    Point2D,
    WallSegment,
    Opening,
    Room,
    ScaleReference,
    VLMParseResult,
    CVParseResult,
    ParseResult,
)
from .geometry import (
    Junction,
    ClassifiedWall,
    GeometryResult,
)
from .structural import (
    SpanAnalysis,
    StructuralWarning,
)
from .three_d import (
    ExtrudedWall,
    SceneGraph,
)
from .materials import (
    Material,
    WeightProfile,
    MaterialRecommendation,
)
from .cost import (
    CostLineItem,
    ProjectCost,
)
from .report import (
    ElementExplanation,
    FullReport,
)

__all__ = [
    # Parsing
    "Point2D",
    "WallSegment",
    "Opening",
    "Room",
    "ScaleReference",
    "VLMParseResult",
    "CVParseResult",
    "ParseResult",
    # Geometry
    "Junction",
    "ClassifiedWall",
    "GeometryResult",
    # Structural
    "SpanAnalysis",
    "StructuralWarning",
    # 3D
    "ExtrudedWall",
    "SceneGraph",
    # Materials
    "Material",
    "WeightProfile",
    "MaterialRecommendation",
    # Cost
    "CostLineItem",
    "ProjectCost",
    # Report
    "ElementExplanation",
    "FullReport",
]
