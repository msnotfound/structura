"""
Cost estimation engine.
"""

import os
import json
from typing import Optional, List

from ..models.parsing import ParseResult
from ..models.geometry import GeometryResult
from ..models.materials import MaterialsResult
from ..models.cost import (
    CostLineItem,
    RoomCost,
    CategoryCost,
    ProjectCost,
    CostComparison,
)


class CostEngine:
    """Engine for detailed cost estimation."""

    def __init__(self):
        self.wall_height = 2.8  # meters
        self.labor_multiplier = 1.3  # 30% labor cost on top of material

        # Additional cost factors
        self.opening_costs = {
            "door": 8000,  # INR per door
            "window": 6000,  # INR per window
        }
        self.flooring_cost_per_sqm = 800  # INR

    def estimate(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        materials_result: MaterialsResult,
        debug_dir: Optional[str] = None,
    ) -> ProjectCost:
        """
        Generate detailed cost estimation.

        Args:
            parse_result: Parsing result with rooms and openings
            geometry_result: Geometry analysis
            materials_result: Material recommendations
            debug_dir: Directory for debug output

        Returns:
            ProjectCost with detailed breakdown
        """
        line_items = []

        # Wall costs
        for rec in materials_result.recommendations:
            wall = next(
                (
                    cw.wall
                    for cw in geometry_result.classified_walls
                    if cw.wall.id == rec.element_id
                ),
                None,
            )
            if wall is None:
                continue

            area = wall.length_m * self.wall_height
            unit_cost = rec.selected.material.cost_per_sqm * self.labor_multiplier
            total = area * unit_cost

            # Find associated room
            room_id = None
            for cw in geometry_result.classified_walls:
                if cw.wall.id == wall.id and cw.adjacent_rooms:
                    room_id = cw.adjacent_rooms[0]
                    break

            line_items.append(
                CostLineItem(
                    element_id=wall.id,
                    element_description=rec.element_description,
                    material=rec.selected.material.name,
                    quantity=area,
                    unit="sqm",
                    unit_cost=unit_cost,
                    total_cost=total,
                    room_id=room_id,
                    category="walls",
                )
            )

        # Opening costs
        for opening in parse_result.openings:
            cost = self.opening_costs.get(opening.type, 5000)
            line_items.append(
                CostLineItem(
                    element_id=opening.id,
                    element_description=f"{opening.type.capitalize()} ({opening.width_m:.1f}m wide)",
                    material="Standard",
                    quantity=1,
                    unit="unit",
                    unit_cost=cost,
                    total_cost=cost,
                    room_id=None,
                    category="openings",
                )
            )

        # Flooring costs
        for room in parse_result.rooms:
            floor_cost = room.area_m2 * self.flooring_cost_per_sqm
            line_items.append(
                CostLineItem(
                    element_id=f"floor_{room.id}",
                    element_description=f"Flooring for {room.label}",
                    material="Standard Tile",
                    quantity=room.area_m2,
                    unit="sqm",
                    unit_cost=self.flooring_cost_per_sqm,
                    total_cost=floor_cost,
                    room_id=room.id,
                    category="flooring",
                )
            )

        # Calculate room totals
        room_totals = self._calculate_room_totals(line_items, parse_result.rooms)

        # Calculate category totals
        category_totals = self._calculate_category_totals(line_items)

        # Calculate grand total
        grand_total = sum(item.total_cost for item in line_items)

        # Calculate budget and premium scenarios
        budget_total = self._calculate_scenario_total(
            parse_result, geometry_result, materials_result, "budget"
        )
        premium_total = self._calculate_scenario_total(
            parse_result, geometry_result, materials_result, "premium"
        )

        # Total floor area
        total_area = sum(room.area_m2 for room in parse_result.rooms)

        result = ProjectCost(
            line_items=line_items,
            room_totals=room_totals,
            category_totals=category_totals,
            grand_total=grand_total,
            budget_total=budget_total,
            premium_total=premium_total,
            savings_vs_premium=premium_total - grand_total,
            cost_per_sqm=grand_total / total_area if total_area > 0 else 0,
            total_area_sqm=total_area,
            currency="INR",
        )

        if debug_dir:
            self._save_debug(result, debug_dir)

        print(
            f"Cost Engine - Grand Total: ₹{grand_total:,.0f}, Per sqm: ₹{result.cost_per_sqm:,.0f}"
        )

        return result

    def _calculate_room_totals(
        self, line_items: List[CostLineItem], rooms: List
    ) -> List[RoomCost]:
        """Calculate cost totals per room."""

        room_costs = []

        for room in rooms:
            # Get items for this room
            room_items = [item for item in line_items if item.room_id == room.id]

            wall_cost = sum(
                item.total_cost for item in room_items if item.category == "walls"
            )
            floor_cost = sum(
                item.total_cost for item in room_items if item.category == "flooring"
            )
            opening_cost = sum(
                item.total_cost for item in room_items if item.category == "openings"
            )

            total = wall_cost + floor_cost + opening_cost

            room_costs.append(
                RoomCost(
                    room_id=room.id,
                    room_label=room.label,
                    room_type=room.room_type,
                    area_m2=room.area_m2,
                    wall_cost=wall_cost,
                    flooring_cost=floor_cost,
                    opening_cost=opening_cost,
                    total_cost=total,
                    cost_per_sqm=total / room.area_m2 if room.area_m2 > 0 else 0,
                )
            )

        return room_costs

    def _calculate_category_totals(
        self, line_items: List[CostLineItem]
    ) -> List[CategoryCost]:
        """Calculate cost totals by category."""

        categories = {}

        for item in line_items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "items": []}
            categories[item.category]["total"] += item.total_cost
            categories[item.category]["items"].append(item)

        grand_total = sum(c["total"] for c in categories.values())

        return [
            CategoryCost(
                category=cat,
                total_cost=data["total"],
                percentage=data["total"] / grand_total * 100 if grand_total > 0 else 0,
                line_items=data["items"],
            )
            for cat, data in categories.items()
        ]

    def _calculate_scenario_total(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        materials_result: MaterialsResult,
        scenario: str,
    ) -> float:
        """Calculate total cost for a scenario (budget/premium)."""

        # Use pre-calculated values from materials result
        if scenario == "budget":
            wall_cost = materials_result.budget_alternative_cost * self.labor_multiplier
        else:
            wall_cost = (
                materials_result.premium_alternative_cost * self.labor_multiplier
            )

        # Add openings
        opening_cost = sum(
            self.opening_costs.get(o.type, 5000) for o in parse_result.openings
        )

        # Add flooring
        floor_cost = (
            sum(room.area_m2 for room in parse_result.rooms)
            * self.flooring_cost_per_sqm
        )

        return wall_cost + opening_cost + floor_cost

    def _save_debug(self, result: ProjectCost, debug_dir: str):
        """Save cost debug info."""

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "grand_total": result.grand_total,
            "budget_total": result.budget_total,
            "premium_total": result.premium_total,
            "savings_vs_premium": result.savings_vs_premium,
            "cost_per_sqm": result.cost_per_sqm,
            "total_area_sqm": result.total_area_sqm,
            "category_breakdown": [
                {
                    "category": c.category,
                    "total": c.total_cost,
                    "percentage": c.percentage,
                }
                for c in result.category_totals
            ],
            "room_breakdown": [
                {
                    "room": r.room_label,
                    "total": r.total_cost,
                    "cost_per_sqm": r.cost_per_sqm,
                }
                for r in result.room_totals
            ],
        }

        with open(os.path.join(debug_dir, "cost_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
