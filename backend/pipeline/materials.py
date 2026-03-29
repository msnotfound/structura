"""
Material recommendation engine with tradeoff optimization.
"""

import os
import json
from typing import Optional, List, Dict
from pathlib import Path

from models.geometry import GeometryResult, ClassifiedWall
from models.parsing import ParseResult, Room
from models.materials import (
    Material,
    WeightProfile,
    MaterialOption,
    MaterialRecommendation,
    MaterialsResult,
)


class MaterialEngine:
    """Engine for material recommendations based on structural requirements."""

    def __init__(self, materials_db_path: Optional[str] = None):
        if materials_db_path is None:
            materials_db_path = (
                Path(__file__).parent.parent / "data" / "materials_db.json"
            )

        self.materials_db = self._load_materials_db(materials_db_path)
        self.materials = [Material(**m) for m in self.materials_db.get("materials", [])]
        self.weight_profiles = self.materials_db.get("weight_profiles", {})
        self.room_type_mapping = self.materials_db.get("room_type_to_element_type", {})

    def _load_materials_db(self, path) -> dict:
        """Load materials database from JSON."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Materials database not found at {path}")
            return {"materials": [], "weight_profiles": {}}

    def recommend(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        optimize_for: str = "balanced",
        debug_dir: Optional[str] = None,
    ) -> MaterialsResult:
        """
        Generate material recommendations for all structural elements.

        Args:
            parse_result: Parsing result with rooms
            geometry_result: Geometry with classified walls
            optimize_for: Optimization strategy (balanced, cost, strength, durability)
            debug_dir: Directory for debug output

        Returns:
            MaterialsResult with recommendations
        """
        recommendations = []

        # Get weight profile based on optimization strategy
        base_profile = self._get_optimization_profile(optimize_for)

        # Recommend materials for each classified wall
        for cw in geometry_result.classified_walls:
            rec = self._recommend_for_wall(cw, parse_result.rooms, base_profile)
            recommendations.append(rec)

        # Calculate totals
        total_cost = sum(
            r.selected.material.cost_per_sqm * self._estimate_wall_area(cw.wall)
            for r, cw in zip(recommendations, geometry_result.classified_walls)
        )

        budget_cost = self._calculate_scenario_cost(
            geometry_result.classified_walls, "budget"
        )
        premium_cost = self._calculate_scenario_cost(
            geometry_result.classified_walls, "premium"
        )

        result = MaterialsResult(
            recommendations=recommendations,
            weight_profile_used=base_profile,
            total_material_cost=total_cost,
            budget_alternative_cost=budget_cost,
            premium_alternative_cost=premium_cost,
        )

        if debug_dir:
            self._save_debug(result, debug_dir)

        print(
            f"Material Engine - Recommendations: {len(recommendations)}, Total Cost: ₹{total_cost:,.0f}"
        )

        return result

    def _get_optimization_profile(self, strategy: str) -> WeightProfile:
        """Get weight profile based on optimization strategy."""

        if strategy == "cost":
            return WeightProfile(
                element_type="partition",
                cost_weight=0.6,
                strength_weight=0.2,
                durability_weight=0.1,
                moisture_weight=0.1,
                rationale="Optimizing for lowest cost",
            )
        elif strategy == "strength":
            return WeightProfile(
                element_type="exterior_load_bearing",
                cost_weight=0.1,
                strength_weight=0.6,
                durability_weight=0.2,
                moisture_weight=0.1,
                rationale="Optimizing for maximum strength",
            )
        elif strategy == "durability":
            return WeightProfile(
                element_type="exterior_load_bearing",
                cost_weight=0.15,
                strength_weight=0.25,
                durability_weight=0.45,
                moisture_weight=0.15,
                rationale="Optimizing for maximum durability",
            )
        else:  # balanced
            return WeightProfile(
                element_type="interior_load_bearing",
                cost_weight=0.25,
                strength_weight=0.35,
                durability_weight=0.25,
                moisture_weight=0.15,
                rationale="Balanced optimization across all factors",
            )

    def _recommend_for_wall(
        self,
        classified_wall: ClassifiedWall,
        rooms: List[Room],
        base_profile: WeightProfile,
    ) -> MaterialRecommendation:
        """Generate recommendation for a single wall."""

        wall = classified_wall.wall

        # Determine element type based on classification and context
        element_type = self._determine_element_type(classified_wall, rooms)

        # Get appropriate weight profile
        profile = self._get_profile_for_element(element_type, base_profile)

        # Score all materials
        options = []
        for material in self.materials:
            option = self._score_material(material, classified_wall, profile)
            options.append(option)

        # Sort by score (descending)
        options.sort(key=lambda x: x.score, reverse=True)

        # Filter out disqualified materials
        valid_options = [o for o in options if o.meets_requirements]

        # Select best option
        selected = valid_options[0] if valid_options else options[0]

        # Generate context factors
        context_factors = self._get_context_factors(classified_wall, rooms)

        return MaterialRecommendation(
            element_id=wall.id,
            element_type=element_type,
            element_description=self._describe_wall(classified_wall),
            options=options[:5],  # Top 5 options
            selected=selected,
            context_factors=context_factors,
        )

    def _determine_element_type(
        self, classified_wall: ClassifiedWall, rooms: List[Room]
    ) -> str:
        """Determine element type based on wall classification and context."""

        wall = classified_wall.wall

        # Check if adjacent to wet area
        wet_room_types = {"bathroom", "kitchen", "laundry"}
        is_wet_area = any(
            rt in wet_room_types for rt in classified_wall.adjacent_room_types
        )

        if is_wet_area:
            return "wet_area"
        elif wall.is_exterior and classified_wall.classification == "load_bearing":
            return "exterior_load_bearing"
        elif classified_wall.classification == "load_bearing":
            return "interior_load_bearing"
        else:
            return "partition"

    def _get_profile_for_element(
        self, element_type: str, base_profile: WeightProfile
    ) -> WeightProfile:
        """Get weight profile for specific element type."""

        profile_data = self.weight_profiles.get(element_type)
        if profile_data:
            return WeightProfile(
                element_type=element_type,
                cost_weight=profile_data.get("cost_weight", base_profile.cost_weight),
                strength_weight=profile_data.get(
                    "strength_weight", base_profile.strength_weight
                ),
                durability_weight=profile_data.get(
                    "durability_weight", base_profile.durability_weight
                ),
                moisture_weight=profile_data.get(
                    "moisture_weight", base_profile.moisture_weight
                ),
                rationale=profile_data.get("rationale", base_profile.rationale),
            )
        return base_profile

    def _score_material(
        self,
        material: Material,
        classified_wall: ClassifiedWall,
        profile: WeightProfile,
    ) -> MaterialOption:
        """Score a material for a specific wall."""

        # Normalize scores to 0-1 range
        # Cost: lower is better, so invert
        max_cost = max(m.cost_per_sqm for m in self.materials)
        cost_score = 1 - (material.cost_per_sqm / max_cost)

        # Strength: higher is better
        max_strength = max(m.compressive_strength_mpa for m in self.materials)
        strength_score = material.compressive_strength_mpa / max_strength

        # Durability and moisture are already 0-1
        durability_score = material.durability_rating
        moisture_score = material.moisture_resistance

        # Weighted total
        total_score = (
            profile.cost_weight * cost_score
            + profile.strength_weight * strength_score
            + profile.durability_weight * durability_score
            + profile.moisture_weight * moisture_score
        )

        # Check hard requirements
        meets_requirements = True
        disqualification_reason = None

        # Load-bearing walls need minimum strength
        if classified_wall.classification == "load_bearing":
            if material.compressive_strength_mpa < 8:
                meets_requirements = False
                disqualification_reason = f"Insufficient strength ({material.compressive_strength_mpa} MPa) for load-bearing wall"

        # Check span capability
        wall_length = classified_wall.wall.length_m
        if wall_length > material.max_span_m:
            meets_requirements = False
            disqualification_reason = f"Wall length ({wall_length:.1f}m) exceeds material max span ({material.max_span_m}m)"

        return MaterialOption(
            material=material,
            score=total_score,
            cost_score=cost_score,
            strength_score=strength_score,
            durability_score=durability_score,
            moisture_score=moisture_score,
            meets_requirements=meets_requirements,
            disqualification_reason=disqualification_reason,
        )

    def _describe_wall(self, classified_wall: ClassifiedWall) -> str:
        """Generate human-readable wall description."""

        wall = classified_wall.wall
        parts = []

        if wall.is_exterior:
            parts.append("Exterior")
        else:
            parts.append("Interior")

        parts.append(classified_wall.classification.replace("_", " "))
        parts.append("wall")
        parts.append(f"({wall.length_m:.1f}m × {wall.thickness_m:.2f}m)")

        return " ".join(parts)

    def _get_context_factors(
        self, classified_wall: ClassifiedWall, rooms: List[Room]
    ) -> List[str]:
        """Get context factors that influenced the recommendation."""

        factors = []
        wall = classified_wall.wall

        if wall.is_exterior:
            factors.append("Exterior wall - weather exposure")

        if classified_wall.classification == "load_bearing":
            factors.append("Load-bearing - strength priority")

        if classified_wall.load_path_continuous:
            factors.append("Part of continuous load path")

        wet_types = {"bathroom", "kitchen", "laundry"}
        if any(rt in wet_types for rt in classified_wall.adjacent_room_types):
            factors.append("Adjacent to wet area - moisture resistance priority")

        if wall.length_m > 4:
            factors.append(
                f"Long span ({wall.length_m:.1f}m) - span capability important"
            )

        return factors

    def _estimate_wall_area(self, wall) -> float:
        """Estimate wall area in square meters."""
        return wall.length_m * 2.8  # Assume 2.8m height

    def _calculate_scenario_cost(
        self, classified_walls: List[ClassifiedWall], cost_level: str
    ) -> float:
        """Calculate total cost for a cost level scenario."""

        materials_by_level = {
            m.name: m for m in self.materials if m.cost_level == cost_level
        }

        if not materials_by_level:
            # Fallback to cheapest/most expensive
            if cost_level == "budget":
                material = min(self.materials, key=lambda m: m.cost_per_sqm)
            else:
                material = max(self.materials, key=lambda m: m.cost_per_sqm)
        else:
            material = list(materials_by_level.values())[0]

        total = 0
        for cw in classified_walls:
            area = self._estimate_wall_area(cw.wall)
            total += material.cost_per_sqm * area

        return total

    def _save_debug(self, result: MaterialsResult, debug_dir: str):
        """Save materials debug info."""

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "total_cost": result.total_material_cost,
            "budget_cost": result.budget_alternative_cost,
            "premium_cost": result.premium_alternative_cost,
            "recommendations": [
                {
                    "element_id": r.element_id,
                    "element_type": r.element_type,
                    "description": r.element_description,
                    "selected_material": r.selected.material.name,
                    "selected_score": r.selected.score,
                    "context_factors": r.context_factors,
                    "top_options": [
                        {"name": o.material.name, "score": o.score}
                        for o in r.options[:3]
                    ],
                }
                for r in result.recommendations
            ],
        }

        with open(os.path.join(debug_dir, "materials_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
