"""
Structural analysis models - span analysis and warnings.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

from .parsing import Point2D


class SpanAnalysis(BaseModel):
    """Span analysis for a room."""

    room_id: str = Field(..., description="ID of the analyzed room")
    room_label: str = Field(..., description="Human-readable room label")
    max_span_m: float = Field(..., description="Maximum unsupported span in meters")
    span_direction: Literal["north_south", "east_west", "diagonal"] = Field(
        ..., description="Direction of the maximum span"
    )
    requires_intermediate_support: bool = Field(
        default=False,
        description="Whether intermediate support (beam/column) is needed",
    )
    recommended_support: Optional[str] = Field(
        default=None, description="Recommended support type if needed"
    )
    supporting_walls: list[str] = Field(
        default_factory=list, description="IDs of walls supporting this span"
    )


class StructuralWarning(BaseModel):
    """A structural warning or issue detected."""

    id: str = Field(..., description="Unique identifier for this warning")
    severity: Literal["critical", "warning", "info"] = Field(
        ..., description="Severity level of the warning"
    )
    element_id: Optional[str] = Field(
        default=None, description="ID of the element this warning relates to"
    )
    warning_type: Literal[
        "excessive_span",
        "unsupported_load",
        "missing_support",
        "wall_discontinuity",
        "insufficient_thickness",
        "opening_placement",
        "load_path_break",
        "material_mismatch",
        "other",
    ] = Field(..., description="Category of warning")
    description: str = Field(..., description="Human-readable description of the issue")
    recommendation: str = Field(
        ..., description="Recommended action to address the issue"
    )
    position: Optional[Point2D] = Field(
        default=None, description="Position of the issue for visualization"
    )
    affected_rooms: list[str] = Field(
        default_factory=list, description="IDs of rooms affected by this warning"
    )
    code_reference: Optional[str] = Field(
        default=None, description="Relevant building code reference"
    )


class StructuralAnalysisResult(BaseModel):
    """Complete structural analysis result."""

    span_analyses: list[SpanAnalysis] = Field(
        default_factory=list, description="Span analysis for each room"
    )
    warnings: list[StructuralWarning] = Field(
        default_factory=list, description="All structural warnings"
    )
    critical_count: int = Field(default=0, description="Number of critical warnings")
    warning_count: int = Field(default=0, description="Number of warnings")
    info_count: int = Field(default=0, description="Number of info messages")
    overall_structural_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall structural integrity score"
    )
    max_span_in_plan: float = Field(
        default=0.0, description="Maximum span found in the entire plan"
    )
    requires_engineer_review: bool = Field(
        default=False,
        description="Whether professional structural engineer review is recommended",
    )
