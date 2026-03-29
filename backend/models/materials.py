"""
Materials models - material database and recommendation engine.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Material(BaseModel):
    """A construction material with properties."""

    name: str = Field(..., description="Material name")
    cost_per_sqm: float = Field(..., description="Cost per square meter in INR")
    cost_level: Literal["budget", "standard", "premium"] = Field(
        ..., description="Cost tier"
    )
    compressive_strength_mpa: float = Field(
        ..., description="Compressive strength in MPa"
    )
    strength_level: Literal["low", "medium", "high", "very_high"] = Field(
        ..., description="Strength tier"
    )
    durability_rating: float = Field(
        ..., ge=0.0, le=1.0, description="Durability score (0-1)"
    )
    durability_level: Literal["low", "medium", "high"] = Field(
        ..., description="Durability tier"
    )
    moisture_resistance: float = Field(
        ..., ge=0.0, le=1.0, description="Moisture resistance (0-1)"
    )
    thermal_insulation: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Thermal insulation rating (0-1)"
    )
    weight_kg_per_sqm: float = Field(..., description="Weight per square meter in kg")
    best_use: list[str] = Field(
        default_factory=list, description="Best use cases for this material"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Limitations or constraints"
    )
    max_span_m: float = Field(..., description="Maximum unsupported span in meters")


class WeightProfile(BaseModel):
    """Weight profile for material selection optimization."""

    element_type: Literal[
        "exterior_load_bearing",
        "interior_load_bearing",
        "partition",
        "wet_area",
        "foundation",
        "slab",
    ] = Field(..., description="Type of structural element")
    cost_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Weight for cost optimization"
    )
    strength_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Weight for strength optimization"
    )
    durability_weight: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for durability optimization"
    )
    moisture_weight: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for moisture resistance"
    )
    rationale: str = Field(..., description="Explanation for this weight profile")


class MaterialOption(BaseModel):
    """A material option with computed score."""

    material: Material = Field(..., description="The material")
    score: float = Field(..., description="Computed fitness score")
    cost_score: float = Field(..., description="Cost component score")
    strength_score: float = Field(..., description="Strength component score")
    durability_score: float = Field(..., description="Durability component score")
    moisture_score: float = Field(..., description="Moisture component score")
    meets_requirements: bool = Field(
        default=True, description="Whether material meets all hard requirements"
    )
    disqualification_reason: Optional[str] = Field(
        default=None, description="Reason if material doesn't meet requirements"
    )


class MaterialRecommendation(BaseModel):
    """Material recommendation for a structural element."""

    element_id: str = Field(..., description="ID of the structural element")
    element_type: Literal[
        "exterior_load_bearing",
        "interior_load_bearing",
        "partition",
        "wet_area",
        "foundation",
        "slab",
    ] = Field(..., description="Type of structural element")
    element_description: str = Field(
        ..., description="Human-readable element description"
    )
    options: list[MaterialOption] = Field(
        default_factory=list, description="Ranked material options"
    )
    selected: MaterialOption = Field(..., description="Selected/recommended material")
    context_factors: list[str] = Field(
        default_factory=list,
        description="Contextual factors considered in recommendation",
    )
    alternative_rationale: Optional[str] = Field(
        default=None, description="Why alternatives might be considered"
    )


class MaterialsResult(BaseModel):
    """Complete materials recommendation result."""

    recommendations: list[MaterialRecommendation] = Field(
        default_factory=list, description="All material recommendations"
    )
    weight_profile_used: WeightProfile = Field(
        ..., description="Weight profile used for optimization"
    )
    total_material_cost: float = Field(
        default=0.0, description="Total estimated material cost"
    )
    budget_alternative_cost: float = Field(
        default=0.0, description="Cost if all budget options selected"
    )
    premium_alternative_cost: float = Field(
        default=0.0, description="Cost if all premium options selected"
    )
