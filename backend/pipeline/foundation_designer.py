"""
Foundation Design module — IS 1904:1986 compliant.
Designs isolated footings and calculates plinth area / FAR.
"""

import math
from typing import List, Optional
from models.parsing import ParseResult
from models.geometry import GeometryResult
from models.structural import StructuralAnalysisResult


class FoundationDesign:
    """Result for a single footing."""
    def __init__(self, footing_id: str, position: dict, footing_type: str,
                 length_m: float, width_m: float, depth_m: float,
                 net_sbc_kpa: float, gross_pressure_kpa: float,
                 axial_load_kn: float, safe: bool, rebar: str, concrete_grade: str):
        self.footing_id = footing_id
        self.position = position
        self.footing_type = footing_type
        self.length_m = length_m
        self.width_m = width_m
        self.depth_m = depth_m
        self.net_sbc_kpa = net_sbc_kpa
        self.gross_pressure_kpa = gross_pressure_kpa
        self.axial_load_kn = axial_load_kn
        self.safe = safe
        self.rebar = rebar
        self.concrete_grade = concrete_grade

    def to_dict(self):
        return {
            "footing_id": self.footing_id,
            "position": self.position,
            "footing_type": self.footing_type,
            "size": f"{self.length_m:.2f}m × {self.width_m:.2f}m",
            "depth_m": self.depth_m,
            "net_sbc_kpa": self.net_sbc_kpa,
            "gross_pressure_kpa": round(self.gross_pressure_kpa, 1),
            "axial_load_kn": round(self.axial_load_kn, 1),
            "safe": self.safe,
            "rebar": self.rebar,
            "concrete_grade": self.concrete_grade,
            "status": "✅ Safe" if self.safe else "⚠️ Needs redesign",
        }


class PlinthAreaResult:
    """Plinth area and FAR calculation result."""
    def __init__(self, built_up_area_sqm: float, built_up_area_sqft: float,
                 carpet_area_sqm: float, carpet_area_sqft: float,
                 wall_area_sqm: float, num_floors: int,
                 total_built_up_sqm: float, plot_area_sqm: float,
                 far: float, ground_coverage: float):
        self.built_up_area_sqm = built_up_area_sqm
        self.built_up_area_sqft = built_up_area_sqft
        self.carpet_area_sqm = carpet_area_sqm
        self.carpet_area_sqft = carpet_area_sqft
        self.wall_area_sqm = wall_area_sqm
        self.num_floors = num_floors
        self.total_built_up_sqm = total_built_up_sqm
        self.plot_area_sqm = plot_area_sqm
        self.far = far
        self.ground_coverage = ground_coverage

    def to_dict(self):
        return {
            "built_up_area": {
                "sqm": round(self.built_up_area_sqm, 2),
                "sqft": round(self.built_up_area_sqft, 1),
            },
            "carpet_area": {
                "sqm": round(self.carpet_area_sqm, 2),
                "sqft": round(self.carpet_area_sqft, 1),
            },
            "wall_area_sqm": round(self.wall_area_sqm, 2),
            "super_built_up_sqm": round(self.built_up_area_sqm * 1.25, 2),
            "super_built_up_sqft": round(self.built_up_area_sqft * 1.25, 1),
            "num_floors": self.num_floors,
            "total_built_up_sqm": round(self.total_built_up_sqm, 2),
            "plot_area_sqm": round(self.plot_area_sqm, 2),
            "far": round(self.far, 2),
            "ground_coverage_percent": round(self.ground_coverage, 1),
            "far_status": "✅ Within limit" if self.far <= 2.5 else "⚠️ Exceeds typical FAR limit",
        }


class FoundationDesigner:
    """
    Designs foundations per IS 1904:1986 and calculates plinth/FAR.
    Assumes: medium soil (SBC = 150 kPa), M25 concrete, Fe500 steel.
    """

    def __init__(self):
        # Soil properties (medium soil - typical Indian residential)
        self.net_sbc_kpa = 150  # Safe bearing capacity kPa
        self.soil_density = 18  # kN/m³
        self.foundation_depth = 1.2  # meters (minimum per IS 1904)
        self.fck = 25  # M25 concrete
        self.fy = 500  # Fe500 steel

    def design_foundations(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
    ) -> dict:
        """Design foundations for all column positions."""
        ppm = parse_result.scale.pixels_per_meter or 1.0
        footings = []

        # Design footings at junction points (column locations)
        for i, junction in enumerate(geometry_result.junctions):
            if junction.type not in ("T", "X", "L"):
                continue

            # Estimate axial load from tributary area
            tributary_area = 3.0 * 3.0  # ~9 sqm per column
            # Dead load + Live load + Self weight
            dead_load = tributary_area * 3.5  # 3.5 kN/m² floor
            live_load = tributary_area * 2.0  # 2.0 kN/m² residential
            wall_load = 5.0  # kN/m per wall height
            self_weight = 2.0  # kN column self weight
            total_load = (dead_load + live_load + wall_load + self_weight)
            factored_load = total_load * 1.5  # IS 456 factor

            footing = self._design_isolated_footing(
                footing_id=f"F{i+1}",
                axial_load_kn=factored_load,
                position={
                    "x": round(junction.position.x / ppm, 2),
                    "z": round(junction.position.y / ppm, 2),
                },
            )
            footings.append(footing)

        # If no junctions, create footings at room corners
        if not footings:
            corner_positions = set()
            for room in parse_result.rooms:
                for v in room.vertices:
                    key = (round(v.x / ppm, 1), round(v.y / ppm, 1))
                    if key not in corner_positions:
                        corner_positions.add(key)
                        if len(corner_positions) <= 12:
                            footing = self._design_isolated_footing(
                                footing_id=f"F{len(corner_positions)}",
                                axial_load_kn=50,
                                position={"x": key[0], "z": key[1]},
                            )
                            footings.append(footing)

        # Summary
        total_concrete = sum(f.length_m * f.width_m * f.depth_m for f in footings)
        safe_count = sum(1 for f in footings if f.safe)

        return {
            "footings": [f.to_dict() for f in footings],
            "total_footings": len(footings),
            "safe_count": safe_count,
            "soil_type": "Medium soil (as per IS 1904)",
            "net_sbc_kpa": self.net_sbc_kpa,
            "foundation_depth_m": self.foundation_depth,
            "concrete_grade": f"M{self.fck}",
            "steel_grade": f"Fe{self.fy}",
            "total_concrete_cum": round(total_concrete, 2),
            "total_steel_kg": round(total_concrete * 80, 1),  # ~80 kg/cum
            "design_standard": "IS 1904:1986 + IS 456:2000",
        }

    def _design_isolated_footing(self, footing_id: str, axial_load_kn: float,
                                  position: dict) -> FoundationDesign:
        """Design an isolated square footing per IS 456."""
        # Required area = Load / SBC
        required_area = axial_load_kn / self.net_sbc_kpa
        # Square footing side
        side = math.sqrt(required_area)
        # Round up to nearest 50mm
        side = math.ceil(side * 20) / 20
        side = max(side, 0.6)  # Minimum 600mm

        # Depth calculation (one-way shear governs)
        # Simplified: d = side/4 for typical residential
        depth = max(side / 3, 0.3)  # min 300mm
        depth = round(depth, 2)

        # Check gross soil pressure
        footing_weight = side * side * depth * 25  # concrete weight
        soil_weight = side * side * self.foundation_depth * self.soil_density
        gross_pressure = (axial_load_kn + footing_weight + soil_weight) / (side * side)

        safe = gross_pressure <= self.net_sbc_kpa * 1.25  # 25% overstress allowed short-term

        # Reinforcement
        # Mu = q * B * (B-b)² / 8, where b = column width (~230mm)
        q = axial_load_kn / (side * side)
        cantilever = (side - 0.23) / 2
        mu = q * side * cantilever * cantilever / 2  # kN·m
        # Ast = Mu / (0.87 * fy * 0.9 * d * 1000)
        d_mm = depth * 1000
        ast = mu * 1e6 / (0.87 * self.fy * 0.9 * d_mm) if d_mm > 0 else 200
        ast = max(ast, 0.12 / 100 * side * 1000 * d_mm)  # min steel

        # Bar selection
        bar_area = math.pi * 12 * 12 / 4  # 12mm bars
        num_bars = max(math.ceil(ast / bar_area), 4)
        spacing = round((side * 1000 - 2 * 50) / (num_bars - 1))
        rebar = f"{num_bars}-12mm φ @ {spacing}mm c/c both ways"

        return FoundationDesign(
            footing_id=footing_id,
            position=position,
            footing_type="Isolated Square Footing",
            length_m=round(side, 2),
            width_m=round(side, 2),
            depth_m=depth,
            net_sbc_kpa=self.net_sbc_kpa,
            gross_pressure_kpa=gross_pressure,
            axial_load_kn=axial_load_kn,
            safe=safe,
            rebar=rebar,
            concrete_grade=f"M{self.fck}",
        )

    def calculate_plinth_area(
        self,
        parse_result: ParseResult,
        num_floors: int = 1,
        plot_area_sqm: float = 0,
    ) -> dict:
        """Calculate plinth area, carpet area, and FAR."""
        ppm = parse_result.scale.pixels_per_meter or 1.0

        # Carpet area = sum of all room areas
        carpet_area = sum(r.area_m2 for r in parse_result.rooms)

        # Wall area = total wall length * wall thickness
        wall_area = 0
        for wall in parse_result.walls:
            wall_area += wall.length_m * wall.thickness_m

        # Built-up area = carpet area + wall area
        built_up_area = carpet_area + wall_area

        # If no plot area given, estimate as 1.3x built-up
        if plot_area_sqm <= 0:
            plot_area_sqm = built_up_area * 1.4

        # Total built-up for all floors
        total_built_up = built_up_area * num_floors

        # FAR = Total built-up / Plot area
        far = total_built_up / plot_area_sqm if plot_area_sqm > 0 else 0

        # Ground coverage = built-up / plot area
        ground_coverage = (built_up_area / plot_area_sqm * 100) if plot_area_sqm > 0 else 0

        result = PlinthAreaResult(
            built_up_area_sqm=built_up_area,
            built_up_area_sqft=built_up_area * 10.764,
            carpet_area_sqm=carpet_area,
            carpet_area_sqft=carpet_area * 10.764,
            wall_area_sqm=wall_area,
            num_floors=num_floors,
            total_built_up_sqm=total_built_up,
            plot_area_sqm=plot_area_sqm,
            far=far,
            ground_coverage=ground_coverage,
        )

        return result.to_dict()
