"""
3D Extruder - converts 2D floor plan to 3D scene for Three.js.
Enhanced: generates beams (IS 456) and columns at wall junctions.
Generates beams for ALL rooms regardless of span analysis results.
"""

import os
import math
from typing import Optional, List
import numpy as np

from models.parsing import ParseResult, Point2D
from models.geometry import GeometryResult, ClassifiedWall
from models.structural import StructuralAnalysisResult
from models.three_d import (
    ExtrudedWall, Beam3D, Column3D, Slab, RoomLabel3D,
    SceneGraph, Point3D, Face, CameraBounds,
)
from pipeline.beam_calculator import BeamCalculator


class Extruder:
    """Converts 2D floor plan geometry to 3D scene graph with beams & columns."""

    def __init__(self):
        self.default_floor_height = 2.8
        self.slab_thickness = 0.15
        self.beam_calculator = BeamCalculator()

        self.colors = {
            "load_bearing": "#4a5568",
            "structural_spine": "#2d3748",
            "partition": "#a0aec0",
            "exterior": "#2b6cb0",
        }

    def extrude(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        structural_result: StructuralAnalysisResult,
        num_floors: int = 1,
        floor_height: Optional[float] = None,
        debug_dir: Optional[str] = None,
    ) -> SceneGraph:
        """Extrude 2D floor plan to 3D with beams and columns."""
        height = floor_height or self.default_floor_height
        ppm = parse_result.scale.pixels_per_meter if parse_result.scale.pixels_per_meter else 1.0

        # Extrude walls
        walls_3d = []
        for cw in geometry_result.classified_walls:
            for floor in range(num_floors):
                extruded = self._extrude_wall(cw, floor, height, ppm)
                walls_3d.append(extruded)

        # Generate beams directly from rooms (not dependent on span analysis)
        beams_3d = self._generate_beams_from_rooms(
            parse_result, geometry_result, height, ppm
        )

        # Generate columns at wall junctions AND at beam endpoints
        columns_3d = self._generate_columns(
            geometry_result, beams_3d, height, ppm
        )

        # Create floor slabs
        slabs = []
        for room in parse_result.rooms:
            for floor in range(num_floors):
                slab = self._create_slab(room, floor, height, ppm)
                slabs.append(slab)

        # Create 3D room labels
        labels = []
        for room in parse_result.rooms:
            if room.centroid:
                label = RoomLabel3D(
                    room_id=room.id,
                    label=room.label,
                    position=Point3D(
                        x=room.centroid.x / ppm,
                        y=height / 2,
                        z=room.centroid.y / ppm,
                    ),
                    area_m2=room.area_m2,
                    room_type=room.room_type,
                )
                labels.append(label)

        bounds = self._calculate_bounds(geometry_result, num_floors, height, ppm)

        scene = SceneGraph(
            walls=walls_3d,
            beams=beams_3d,
            columns=columns_3d,
            slabs=slabs,
            room_labels=labels,
            warnings=structural_result.warnings,
            camera_bounds=bounds,
            floor_height_m=height,
            num_floors=num_floors,
            total_height_m=height * num_floors,
        )

        if debug_dir:
            self._save_debug(scene, debug_dir)

        print(
            f"3D Extrusion - Walls: {len(walls_3d)}, Beams: {len(beams_3d)}, "
            f"Columns: {len(columns_3d)}, Slabs: {len(slabs)}, Floors: {num_floors}"
        )

        return scene

    def _generate_beams_from_rooms(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        floor_height: float,
        ppm: float,
    ) -> List[Beam3D]:
        """Generate beams for ALL rooms using room geometry directly."""
        beams = []
        beam_idx = 0

        for room in parse_result.rooms:
            if not room.vertices or not room.centroid:
                continue
            
            # Skip very small utility rooms (stairs, closets)
            if room.room_type in ("staircase", "closet", "utility"):
                continue

            # Get room bounding box in meters
            xs = [v.x / ppm for v in room.vertices]
            ys = [v.y / ppm for v in room.vertices]
            min_x, max_x = min(xs), max(xs)
            min_z, max_z = min(ys), max(ys)

            width_m = max_x - min_x
            depth_m = max_z - min_z

            # Use VLM-provided area for cross-check
            room_area = room.area_m2

            # Minimum span for a beam: 1.5m (even small rooms get beams in real construction)
            min_span = 1.5
            
            # If both dimensions are too small, check if room area suggests bigger room
            if width_m < min_span and depth_m < min_span:
                # Scale might still be wrong — use area to estimate span
                if room_area > 3:  # 3 sqm = reasonable room
                    estimated_span = math.sqrt(room_area)
                    width_m = estimated_span * 1.2
                    depth_m = estimated_span * 0.8
                    # Adjust positions
                    cx = (min_x + max_x) / 2
                    cz = (min_z + max_z) / 2
                    min_x = cx - width_m / 2
                    max_x = cx + width_m / 2
                    min_z = cz - depth_m / 2
                    max_z = cz + depth_m / 2
                else:
                    continue  # Truly tiny room

            # Place beam along the LONGER span direction (beam spans the longer dimension)
            if width_m >= depth_m:
                center_z = (min_z + max_z) / 2
                span = width_m
                start = Point3D(x=min_x, y=floor_height, z=center_z)
                end = Point3D(x=max_x, y=floor_height, z=center_z)
            else:
                center_x = (min_x + max_x) / 2
                span = depth_m
                start = Point3D(x=center_x, y=floor_height, z=min_z)
                end = Point3D(x=center_x, y=floor_height, z=max_z)

            # Design beam using IS 456
            tributary = min(width_m, depth_m) / 2
            tributary = max(tributary, 1.0)  # minimum 1m tributary

            design = self.beam_calculator.design_beam(
                beam_id=f"beam_{beam_idx:03d}",
                span_m=max(span, min_span),
                tributary_width_m=tributary,
                beam_type="simply_supported",
                start_pos=(start.x, start.y, start.z),
                end_pos=(end.x, end.y, end.z),
                room_id=room.id,
            )

            beams.append(Beam3D(
                beam_id=design.beam_id,
                start=start,
                end=end,
                width_m=design.width_mm / 1000,
                depth_m=design.depth_mm / 1000,
                span_m=round(design.span_m, 2),
                steel_area_mm2=design.tension_steel_area_mm2,
                tension_bars=design.tension_bars,
                stirrup_spacing_mm=design.stirrup_spacing_mm,
                stirrup_description=design.stirrup_description,
                concrete_grade=design.concrete_grade,
                steel_grade=design.steel_grade,
                total_load_kn_per_m=design.total_factored_load_kn_per_m,
                max_bending_moment_knm=design.max_bending_moment_knm,
                max_shear_force_kn=design.max_shear_force_kn,
                deflection_ok=design.deflection_ok,
                color="#3b82f6",
                room_id=room.id,
            ))
            beam_idx += 1

        return beams

    def _generate_columns(
        self,
        geometry_result: GeometryResult,
        beams: List[Beam3D],
        floor_height: float,
        ppm: float,
    ) -> List[Column3D]:
        """Generate columns at junctions and beam endpoints."""
        columns = []
        col_idx = 0
        placed_positions = set()  # avoid duplicates

        def _add_column(px: float, pz: float, load: float, jid: str = ""):
            nonlocal col_idx
            # Round to avoid duplicates
            key = (round(px, 1), round(pz, 1))
            if key in placed_positions:
                return
            placed_positions.add(key)

            design = self.beam_calculator.design_column(
                column_id=f"col_{col_idx:03d}",
                axial_load_kn=load,
                height_m=floor_height,
                position=(px, 0, pz),
                junction_id=jid,
            )
            columns.append(Column3D(
                column_id=design.column_id,
                position=Point3D(x=px, y=floor_height / 2, z=pz),
                width_m=design.width_mm / 1000,
                depth_m=design.depth_mm / 1000,
                height_m=floor_height,
                axial_load_kn=design.axial_load_kn,
                steel_area_mm2=design.steel_area_mm2,
                steel_bars=design.steel_bars,
                tie_spacing_mm=design.tie_spacing_mm,
                load_ratio=design.load_ratio,
                color="#f59e0b",
                junction_id=jid,
            ))
            col_idx += 1

        # Method 1: Columns at T/X junctions of load-bearing walls
        for junction in geometry_result.junctions:
            if junction.type not in ("T", "X"):
                continue

            has_lb = any(
                cw.classification in ("load_bearing", "structural_spine")
                for cw in geometry_result.classified_walls
                if cw.wall.id in junction.connected_wall_ids
            )
            if not has_lb:
                continue

            pos_x = junction.position.x / ppm
            pos_z = junction.position.y / ppm
            tributary_area = 3.0 * 3.0
            axial_load = tributary_area * 10.0 * 1.5
            _add_column(pos_x, pos_z, axial_load, junction.id)

        # Method 2: Columns at beam endpoints (supporting each beam)
        for beam in beams:
            load = beam.total_load_kn_per_m * beam.span_m / 2 if beam.total_load_kn_per_m else 100
            _add_column(beam.start.x, beam.start.z, load)
            _add_column(beam.end.x, beam.end.z, load)

        return columns

    def _extrude_wall(
        self, classified_wall: ClassifiedWall, floor: int, floor_height: float, ppm: float = 1.0
    ) -> ExtrudedWall:
        """Extrude a single wall to 3D."""
        wall = classified_wall.wall
        base_z = floor * floor_height
        top_z = base_z + floor_height

        sx = wall.start.x / ppm
        sy = wall.start.y / ppm
        ex = wall.end.x / ppm
        ey = wall.end.y / ppm

        dx = ex - sx
        dy = ey - sy
        length = np.sqrt(dx * dx + dy * dy)
        if length == 0:
            length = 1

        half_t = max(wall.thickness_m / 2, 0.05)
        perp_x = -dy / length * half_t
        perp_y = dx / length * half_t

        vertices = [
            Point3D(x=sx - perp_x, y=base_z, z=sy - perp_y),
            Point3D(x=sx + perp_x, y=base_z, z=sy + perp_y),
            Point3D(x=ex + perp_x, y=base_z, z=ey + perp_y),
            Point3D(x=ex - perp_x, y=base_z, z=ey - perp_y),
            Point3D(x=sx - perp_x, y=top_z, z=sy - perp_y),
            Point3D(x=sx + perp_x, y=top_z, z=sy + perp_y),
            Point3D(x=ex + perp_x, y=top_z, z=ey + perp_y),
            Point3D(x=ex - perp_x, y=top_z, z=ey - perp_y),
        ]

        faces = [
            Face(vertices=[0, 1, 2]), Face(vertices=[0, 2, 3]),
            Face(vertices=[4, 6, 5]), Face(vertices=[4, 7, 6]),
            Face(vertices=[0, 4, 5]), Face(vertices=[0, 5, 1]),
            Face(vertices=[2, 6, 7]), Face(vertices=[2, 7, 3]),
            Face(vertices=[0, 3, 7]), Face(vertices=[0, 7, 4]),
            Face(vertices=[1, 5, 6]), Face(vertices=[1, 6, 2]),
        ]

        if wall.is_exterior:
            color = self.colors["exterior"]
        else:
            color = self.colors.get(classified_wall.classification, self.colors["partition"])

        return ExtrudedWall(
            wall_id=f"{wall.id}_f{floor}",
            vertices_3d=vertices,
            faces=faces,
            classification=classified_wall.classification,
            thickness_m=wall.thickness_m,
            height_m=floor_height,
            openings=[],
            color=color,
            is_exterior=wall.is_exterior,
        )

    def _create_slab(self, room, floor: int, floor_height: float, ppm: float = 1.0) -> Slab:
        """Create a floor slab for a room."""
        elevation = floor * floor_height
        vertices = [Point3D(x=v.x / ppm, y=elevation, z=v.y / ppm) for v in room.vertices]
        return Slab(
            id=f"slab_{room.id}_f{floor}",
            vertices_3d=vertices,
            elevation=elevation,
            type="floor",
            thickness_m=self.slab_thickness,
            room_id=room.id,
        )

    def _calculate_bounds(
        self, geometry_result: GeometryResult, num_floors: int, floor_height: float, ppm: float = 1.0
    ) -> CameraBounds:
        """Calculate camera bounds for the scene."""
        all_x = []
        all_z = []
        for cw in geometry_result.classified_walls:
            all_x.extend([cw.wall.start.x / ppm, cw.wall.end.x / ppm])
            all_z.extend([cw.wall.start.y / ppm, cw.wall.end.y / ppm])

        if not all_x:
            return CameraBounds(
                min=Point3D(x=0, y=0, z=0),
                max=Point3D(x=10, y=floor_height, z=10),
                center=Point3D(x=5, y=floor_height / 2, z=5),
                recommended_distance=20,
            )

        min_x, max_x = min(all_x), max(all_x)
        min_z, max_z = min(all_z), max(all_z)
        min_y, max_y = 0, num_floors * floor_height

        center = Point3D(x=(min_x + max_x) / 2, y=max_y / 2, z=(min_z + max_z) / 2)
        scene_size = max(max_x - min_x, max_z - min_z, max_y)
        recommended_distance = scene_size * 1.5

        return CameraBounds(
            min=Point3D(x=min_x, y=min_y, z=min_z),
            max=Point3D(x=max_x, y=max_y, z=max_z),
            center=center,
            recommended_distance=recommended_distance,
        )

    def _save_debug(self, scene: SceneGraph, debug_dir: str):
        """Save 3D scene debug info."""
        import json
        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "num_walls": len(scene.walls),
            "num_beams": len(scene.beams),
            "num_columns": len(scene.columns),
            "num_slabs": len(scene.slabs),
            "num_labels": len(scene.room_labels),
            "num_floors": scene.num_floors,
            "beam_details": [
                {
                    "id": b.beam_id,
                    "span": b.span_m,
                    "size": f"{b.width_m*1000:.0f}x{b.depth_m*1000:.0f}mm",
                    "steel": b.tension_bars,
                    "stirrups": b.stirrup_description,
                    "moment": b.max_bending_moment_knm,
                    "room_id": b.room_id,
                }
                for b in scene.beams
            ],
            "column_details": [
                {
                    "id": c.column_id,
                    "size": f"{c.width_m*1000:.0f}x{c.depth_m*1000:.0f}mm",
                    "load": c.axial_load_kn,
                    "steel": c.steel_bars,
                    "ratio": c.load_ratio,
                }
                for c in scene.columns
            ],
        }

        with open(os.path.join(debug_dir, "extrusion_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
