"""
Report models - LLM-generated explanations and final report.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .structural import StructuralWarning
from .cost import ProjectCost


class ElementExplanation(BaseModel):
    """LLM-generated explanation for a structural element."""

    element_id: str = Field(..., description="ID of the element")
    element_description: str = Field(..., description="Human-readable description")
    recommendation_text: str = Field(..., description="Natural language recommendation")
    tradeoff_summary: str = Field(..., description="Summary of tradeoffs considered")
    structural_notes: Optional[str] = Field(
        default=None, description="Structural engineering notes"
    )
    measurements_cited: list[str] = Field(
        default_factory=list, description="Specific measurements referenced"
    )
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence in this explanation"
    )


class OptimizationSuggestion(BaseModel):
    """A suggestion for layout or design optimization."""

    id: str = Field(..., description="Unique identifier")
    category: str = Field(
        ..., description="Category (layout, structural, cost, efficiency)"
    )
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed description")
    potential_savings: Optional[float] = Field(
        default=None, description="Potential cost savings if applicable"
    )
    effort_level: str = Field(
        default="medium", description="Implementation effort (low, medium, high)"
    )
    priority: int = Field(
        default=2, ge=1, le=3, description="Priority (1=high, 2=medium, 3=low)"
    )


class FullReport(BaseModel):
    """Complete analysis report."""

    project_summary: str = Field(..., description="Executive summary of the project")
    element_explanations: list[ElementExplanation] = Field(
        default_factory=list, description="Explanations for each element"
    )
    structural_warnings: list[StructuralWarning] = Field(
        default_factory=list, description="All structural warnings"
    )
    cost_summary: ProjectCost = Field(..., description="Cost summary")
    optimization_suggestions: list[OptimizationSuggestion] = Field(
        default_factory=list, description="Optimization suggestions"
    )
    overall_assessment: str = Field(
        ..., description="Overall assessment and conclusion"
    )
    methodology_notes: str = Field(default="", description="Notes on methodology used")
    limitations: list[str] = Field(
        default_factory=list, description="Known limitations of this analysis"
    )
    generated_at: str = Field(..., description="Timestamp of report generation")
    version: str = Field(default="1.0", description="Report version")
