"""
Cost estimation models.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CostLineItem(BaseModel):
    """A single line item in cost estimation."""

    element_id: str = Field(..., description="ID of the structural element")
    element_description: str = Field(..., description="Human-readable description")
    material: str = Field(..., description="Material name")
    quantity: float = Field(..., description="Quantity (area in sqm or length in m)")
    unit: str = Field(default="sqm", description="Unit of measurement")
    unit_cost: float = Field(..., description="Cost per unit in INR")
    total_cost: float = Field(..., description="Total cost for this line item")
    room_id: Optional[str] = Field(
        default=None, description="Associated room ID if applicable"
    )
    category: str = Field(
        default="walls", description="Cost category (walls, flooring, openings, etc.)"
    )


class RoomCost(BaseModel):
    """Cost breakdown for a room."""

    room_id: str = Field(..., description="Room ID")
    room_label: str = Field(..., description="Room label")
    room_type: str = Field(..., description="Room type")
    area_m2: float = Field(..., description="Room area")
    wall_cost: float = Field(default=0.0, description="Cost of walls")
    flooring_cost: float = Field(default=0.0, description="Cost of flooring")
    opening_cost: float = Field(default=0.0, description="Cost of doors/windows")
    total_cost: float = Field(..., description="Total cost for this room")
    cost_per_sqm: float = Field(..., description="Cost per square meter")


class CategoryCost(BaseModel):
    """Cost breakdown by category."""

    category: str = Field(..., description="Category name")
    total_cost: float = Field(..., description="Total cost for this category")
    percentage: float = Field(..., description="Percentage of total project cost")
    line_items: list[CostLineItem] = Field(
        default_factory=list, description="Line items in this category"
    )


class ProjectCost(BaseModel):
    """Complete project cost estimation."""

    line_items: list[CostLineItem] = Field(
        default_factory=list, description="All cost line items"
    )
    room_totals: list[RoomCost] = Field(
        default_factory=list, description="Cost breakdown by room"
    )
    category_totals: list[CategoryCost] = Field(
        default_factory=list, description="Cost breakdown by category"
    )
    grand_total: float = Field(..., description="Total project cost")
    budget_total: float = Field(
        ..., description="Total if all budget materials were used"
    )
    premium_total: float = Field(
        ..., description="Total if all premium materials were used"
    )
    savings_vs_premium: float = Field(
        ..., description="Savings compared to premium option"
    )
    cost_per_sqm: float = Field(..., description="Overall cost per square meter")
    total_area_sqm: float = Field(..., description="Total floor area")
    currency: str = Field(default="INR", description="Currency code")


class CostComparison(BaseModel):
    """Comparison of different cost scenarios."""

    scenario_name: str = Field(..., description="Name of this scenario")
    description: str = Field(..., description="Description of the scenario")
    total_cost: float = Field(..., description="Total cost for this scenario")
    cost_per_sqm: float = Field(..., description="Cost per square meter")
    savings_vs_baseline: float = Field(
        default=0.0, description="Savings compared to baseline"
    )
    tradeoffs: list[str] = Field(
        default_factory=list, description="Tradeoffs made in this scenario"
    )
