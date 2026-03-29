"""
Structural validation - span analysis and warning generation.
"""

import os
from typing import Optional, List
import numpy as np

from models.parsing import ParseResult, Room, Point2D
from models.geometry import GeometryResult, ClassifiedWall
from models.structural import (
    SpanAnalysis,
    StructuralWarning,
    StructuralAnalysisResult,
)


class StructuralValidator:
    """Validates structural integrity and generates warnings."""

    def __init__(self):
        # Span limits (meters)
        self.max_residential_span = 6.0
        self.beam_required_span = 4.5

        # Wall constraints
        self.min_load_bearing_thickness = 0.15
        self.min_exterior_thickness = 0.2

    def validate(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        debug_dir: Optional[str] = None,
    ) -> StructuralAnalysisResult:
        """
        Validate structural integrity and generate warnings.

        Args:
            parse_result: Parsing result with rooms and walls
            geometry_result: Geometry analysis result
            debug_dir: Directory for debug output

        Returns:
            StructuralAnalysisResult with span analysis and warnings
        """
        warnings = []
        span_analyses = []

        # Analyze spans for each room
        for room in parse_result.rooms:
            span = self._analyze_room_span(room, geometry_result)
            span_analyses.append(span)

            # Generate warnings for excessive spans
            if span.requires_intermediate_support:
                warnings.append(
                    StructuralWarning(
                        id=f"warn_span_{room.id}",
                        severity="warning"
                        if span.max_span_m < self.max_residential_span
                        else "critical",
                        element_id=room.id,
                        warning_type="excessive_span",
                        description=f"{room.label} has a span of {span.max_span_m:.1f}m which may require intermediate support",
                        recommendation=span.recommended_support
                        or "Consider adding a beam or intermediate wall",
                        position=room.centroid,
                        affected_rooms=[room.id],
                    )
                )

        # Check wall thicknesses
        wall_warnings = self._check_wall_thicknesses(geometry_result.classified_walls)
        warnings.extend(wall_warnings)

        # Check load path continuity
        load_path_warnings = self._check_load_paths(geometry_result)
        warnings.extend(load_path_warnings)

        # Check opening placements
        opening_warnings = self._check_openings(parse_result, geometry_result)
        warnings.extend(opening_warnings)

        # Calculate statistics
        critical_count = sum(1 for w in warnings if w.severity == "critical")
        warning_count = sum(1 for w in warnings if w.severity == "warning")
        info_count = sum(1 for w in warnings if w.severity == "info")

        # Calculate overall score
        max_span = max((s.max_span_m for s in span_analyses), default=0)
        score = self._calculate_structural_score(warnings, max_span)

        # Determine if engineer review needed
        needs_review = critical_count > 0 or max_span > self.max_residential_span

        result = StructuralAnalysisResult(
            span_analyses=span_analyses,
            warnings=warnings,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            overall_structural_score=score,
            max_span_in_plan=max_span,
            requires_engineer_review=needs_review,
        )

        if debug_dir:
            self._save_debug(result, debug_dir)

        print(
            f"Structural Validation - Warnings: {critical_count} critical, {warning_count} warnings, Score: {score:.2f}"
        )

        return result

    def _analyze_room_span(
        self, room: Room, geometry_result: GeometryResult
    ) -> SpanAnalysis:
        """Analyze the maximum span in a room."""

        if len(room.vertices) < 3:
            return SpanAnalysis(
                room_id=room.id,
                room_label=room.label,
                max_span_m=0,
                span_direction="unknown",
                requires_intermediate_support=False,
                recommended_support=None,
                supporting_walls=[],
            )

        # Calculate bounding box
        xs = [v.x for v in room.vertices]
        ys = [v.y for v in room.vertices]

        width = max(xs) - min(xs)
        height = max(ys) - min(ys)

        # Assume scale is already applied
        # Find the longer dimension
        if width > height:
            max_span = width
            direction = "east_west"
        else:
            max_span = height
            direction = "north_south"

        # Find supporting walls (adjacent load-bearing walls)
        supporting_walls = []
        for cw in geometry_result.classified_walls:
            if room.id in cw.adjacent_rooms and cw.classification != "partition":
                supporting_walls.append(cw.wall.id)

        # Determine if support is needed
        requires_support = max_span > self.beam_required_span

        # Recommend support type
        recommendation = None
        if requires_support:
            if max_span > self.max_residential_span:
                recommendation = (
                    f"Steel beam or RCC beam required for {max_span:.1f}m span"
                )
            else:
                recommendation = f"Consider beam support for {max_span:.1f}m span"

        return SpanAnalysis(
            room_id=room.id,
            room_label=room.label,
            max_span_m=max_span,
            span_direction=direction,
            requires_intermediate_support=requires_support,
            recommended_support=recommendation,
            supporting_walls=supporting_walls,
        )

    def _check_wall_thicknesses(
        self, classified_walls: List[ClassifiedWall]
    ) -> List[StructuralWarning]:
        """Check wall thicknesses meet requirements."""

        warnings = []

        for cw in classified_walls:
            wall = cw.wall

            # Check load-bearing wall thickness
            if cw.classification == "load_bearing":
                if wall.thickness_m < self.min_load_bearing_thickness:
                    warnings.append(
                        StructuralWarning(
                            id=f"warn_thick_{wall.id}",
                            severity="warning",
                            element_id=wall.id,
                            warning_type="insufficient_thickness",
                            description=f"Load-bearing wall {wall.id} has thickness {wall.thickness_m:.2f}m (min: {self.min_load_bearing_thickness}m)",
                            recommendation=f"Increase wall thickness to at least {self.min_load_bearing_thickness}m or use stronger material",
                            position=wall.start,
                        )
                    )

            # Check exterior wall thickness
            if wall.is_exterior:
                if wall.thickness_m < self.min_exterior_thickness:
                    warnings.append(
                        StructuralWarning(
                            id=f"warn_ext_{wall.id}",
                            severity="info",
                            element_id=wall.id,
                            warning_type="insufficient_thickness",
                            description=f"Exterior wall {wall.id} has thickness {wall.thickness_m:.2f}m (recommended: {self.min_exterior_thickness}m)",
                            recommendation="Consider increasing thickness for better insulation and weather resistance",
                            position=wall.start,
                        )
                    )

        return warnings

    def _check_load_paths(
        self, geometry_result: GeometryResult
    ) -> List[StructuralWarning]:
        """Check for continuous load paths."""

        warnings = []

        # Check if there are walls without continuous load paths
        for cw in geometry_result.classified_walls:
            if cw.classification == "load_bearing" and not cw.load_path_continuous:
                warnings.append(
                    StructuralWarning(
                        id=f"warn_path_{cw.wall.id}",
                        severity="warning",
                        element_id=cw.wall.id,
                        warning_type="load_path_break",
                        description=f"Load-bearing wall {cw.wall.id} may not have continuous load path to foundation",
                        recommendation="Verify wall is supported below or add foundation support",
                        position=cw.wall.start,
                    )
                )

        # Check if structural spines are present
        if not geometry_result.structural_spines:
            warnings.append(
                StructuralWarning(
                    id="warn_no_spine",
                    severity="info",
                    element_id=None,
                    warning_type="wall_discontinuity",
                    description="No clear structural spine detected in the floor plan",
                    recommendation="Ensure there is at least one continuous load-bearing wall through the building",
                )
            )

        return warnings

    def _check_openings(
        self, parse_result: ParseResult, geometry_result: GeometryResult
    ) -> List[StructuralWarning]:
        """Check opening placements in walls."""

        warnings = []

        # Check openings in load-bearing walls
        load_bearing_ids = {
            cw.wall.id
            for cw in geometry_result.classified_walls
            if cw.classification == "load_bearing"
        }

        for opening in parse_result.openings:
            if opening.parent_wall_id in load_bearing_ids:
                # Large openings in load-bearing walls need lintels
                if opening.width_m > 1.5:
                    warnings.append(
                        StructuralWarning(
                            id=f"warn_opening_{opening.id}",
                            severity="info",
                            element_id=opening.id,
                            warning_type="opening_placement",
                            description=f"Large {opening.type} ({opening.width_m:.1f}m) in load-bearing wall",
                            recommendation="Ensure proper lintel/beam above opening to transfer loads",
                            position=opening.position,
                        )
                    )

        return warnings

    def _calculate_structural_score(
        self, warnings: List[StructuralWarning], max_span: float
    ) -> float:
        """Calculate overall structural integrity score (0-1)."""

        # Start with perfect score
        score = 1.0

        # Deduct for warnings
        for w in warnings:
            if w.severity == "critical":
                score -= 0.2
            elif w.severity == "warning":
                score -= 0.1
            elif w.severity == "info":
                score -= 0.02

        # Deduct for excessive spans
        if max_span > self.max_residential_span:
            score -= 0.2
        elif max_span > self.beam_required_span:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _save_debug(self, result: StructuralAnalysisResult, debug_dir: str):
        """Save structural validation debug info."""
        import json

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "overall_score": result.overall_structural_score,
            "max_span_m": result.max_span_in_plan,
            "requires_engineer_review": result.requires_engineer_review,
            "warning_counts": {
                "critical": result.critical_count,
                "warning": result.warning_count,
                "info": result.info_count,
            },
            "span_analyses": [
                {
                    "room_id": s.room_id,
                    "room_label": s.room_label,
                    "max_span_m": s.max_span_m,
                    "direction": s.span_direction,
                    "requires_support": s.requires_intermediate_support,
                    "recommendation": s.recommended_support,
                }
                for s in result.span_analyses
            ],
            "warnings": [
                {
                    "id": w.id,
                    "severity": w.severity,
                    "type": w.warning_type,
                    "description": w.description,
                    "recommendation": w.recommendation,
                }
                for w in result.warnings
            ],
        }

        with open(os.path.join(debug_dir, "structural_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
