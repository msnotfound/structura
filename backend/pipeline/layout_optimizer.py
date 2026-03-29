"""
Layout optimizer - suggests improvements to floor plan layout.
"""

import os
from typing import Optional, List

from ..models.parsing import ParseResult
from ..models.geometry import GeometryResult
from ..models.structural import StructuralAnalysisResult
from ..models.report import OptimizationSuggestion


class LayoutOptimizer:
    """Analyzes layout and suggests optimizations."""

    def __init__(self):
        # Optimal room dimension ratios
        self.optimal_ratios = {
            "bedroom": (1.0, 1.5),  # Slightly rectangular
            "living": (1.0, 1.8),  # Rectangular
            "kitchen": (1.0, 1.5),
            "bathroom": (1.0, 1.3),
            "dining": (1.0, 1.4),
        }

        # Minimum room sizes (sqm)
        self.min_sizes = {
            "bedroom": 9.0,
            "bathroom": 3.5,
            "kitchen": 5.0,
            "living": 12.0,
        }

    def optimize(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        debug_dir: Optional[str] = None,
    ) -> List[OptimizationSuggestion]:
        """
        Generate layout optimization suggestions.

        Args:
            parse_result: Parsing result
            geometry_result: Geometry analysis
            structural_result: Structural analysis
            debug_dir: Directory for debug output

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check room sizes
        size_suggestions = self._check_room_sizes(parse_result.rooms)
        suggestions.extend(size_suggestions)

        # Check room proportions
        proportion_suggestions = self._check_room_proportions(parse_result.rooms)
        suggestions.extend(proportion_suggestions)

        # Check wall efficiency
        wall_suggestions = self._check_wall_efficiency(geometry_result)
        suggestions.extend(wall_suggestions)

        # Check structural opportunities
        structural_suggestions = self._check_structural_opportunities(
            geometry_result, structural_result
        )
        suggestions.extend(structural_suggestions)

        # Sort by priority
        suggestions.sort(key=lambda s: s.priority)

        if debug_dir:
            self._save_debug(suggestions, debug_dir)

        print(f"Layout Optimizer - Generated {len(suggestions)} suggestions")

        return suggestions

    def _check_room_sizes(self, rooms) -> List[OptimizationSuggestion]:
        """Check if rooms meet minimum size requirements."""

        suggestions = []

        for room in rooms:
            min_size = self.min_sizes.get(room.room_type)
            if min_size and room.area_m2 < min_size:
                suggestions.append(
                    OptimizationSuggestion(
                        id=f"size_{room.id}",
                        category="layout",
                        title=f"{room.label} too small",
                        description=f"{room.label} is {room.area_m2:.1f} sqm, below recommended minimum of {min_size} sqm for a {room.room_type}",
                        potential_savings=None,
                        effort_level="high",
                        priority=2,
                    )
                )

        return suggestions

    def _check_room_proportions(self, rooms) -> List[OptimizationSuggestion]:
        """Check room proportions for efficiency."""

        suggestions = []

        for room in rooms:
            if len(room.vertices) < 3:
                continue

            # Calculate bounding box aspect ratio
            xs = [v.x for v in room.vertices]
            ys = [v.y for v in room.vertices]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)

            if width == 0 or height == 0:
                continue

            ratio = max(width, height) / min(width, height)

            # Very narrow rooms are inefficient
            if ratio > 3.0:
                suggestions.append(
                    OptimizationSuggestion(
                        id=f"proportion_{room.id}",
                        category="layout",
                        title=f"{room.label} too narrow",
                        description=f"{room.label} has aspect ratio of {ratio:.1f}:1. Consider making it more square for better usability.",
                        potential_savings=None,
                        effort_level="medium",
                        priority=3,
                    )
                )

        return suggestions

    def _check_wall_efficiency(
        self, geometry_result: GeometryResult
    ) -> List[OptimizationSuggestion]:
        """Check for wall layout efficiency opportunities."""

        suggestions = []

        # Check wall-to-floor ratio
        total_wall_length = geometry_result.total_wall_length_m
        # Rough estimate of floor area from rooms

        # Check for excessive partition walls
        partition_ratio = geometry_result.partition_wall_count / max(
            geometry_result.load_bearing_wall_count, 1
        )

        if partition_ratio > 2.0:
            suggestions.append(
                OptimizationSuggestion(
                    id="partition_ratio",
                    category="cost",
                    title="High partition wall count",
                    description=f"Floor plan has {geometry_result.partition_wall_count} partition walls vs {geometry_result.load_bearing_wall_count} load-bearing. Consider open-plan layout to reduce costs.",
                    potential_savings=geometry_result.partition_wall_count
                    * 5000,  # Rough estimate
                    effort_level="medium",
                    priority=2,
                )
            )

        return suggestions

    def _check_structural_opportunities(
        self,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
    ) -> List[OptimizationSuggestion]:
        """Check for structural optimization opportunities."""

        suggestions = []

        # Check if structural spines could be simplified
        if len(geometry_result.structural_spines) > 2:
            suggestions.append(
                OptimizationSuggestion(
                    id="spine_count",
                    category="structural",
                    title="Multiple structural spines",
                    description=f"Found {len(geometry_result.structural_spines)} structural spines. Consider consolidating for simpler construction.",
                    potential_savings=None,
                    effort_level="high",
                    priority=3,
                )
            )

        # Check spans that could use lighter materials with beams
        large_spans = [s for s in structural_result.span_analyses if s.max_span_m > 4.5]

        if large_spans:
            suggestions.append(
                OptimizationSuggestion(
                    id="beam_opportunity",
                    category="structural",
                    title="Beam opportunity for large spans",
                    description=f"{len(large_spans)} rooms have spans over 4.5m. Adding beams could allow lighter/cheaper wall materials.",
                    potential_savings=len(large_spans) * 15000,
                    effort_level="medium",
                    priority=2,
                )
            )

        return suggestions

    def _save_debug(self, suggestions: List[OptimizationSuggestion], debug_dir: str):
        """Save optimization debug info."""
        import json

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "suggestion_count": len(suggestions),
            "by_category": {},
            "suggestions": [
                {
                    "id": s.id,
                    "category": s.category,
                    "title": s.title,
                    "description": s.description,
                    "potential_savings": s.potential_savings,
                    "priority": s.priority,
                }
                for s in suggestions
            ],
        }

        for s in suggestions:
            if s.category not in debug_info["by_category"]:
                debug_info["by_category"][s.category] = 0
            debug_info["by_category"][s.category] += 1

        with open(os.path.join(debug_dir, "optimizer_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
