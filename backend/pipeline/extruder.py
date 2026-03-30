"""
3D Extruder - converts 2D floor plan to 3D scene for Three.js.
"""

import os
from typing import Optional, List
import numpy as np

from models.parsing import ParseResult, Point2D
from models.geometry import GeometryResult, ClassifiedWall
from models.structural import StructuralAnalysisResult
from models.three_d import (
    ExtrudedWall,
    Slab,
    RoomLabel3D,
    SceneGraph,
    Point3D,
    Face,
    CameraBounds,
)


class Extruder:
    """Converts 2D floor plan geometry to 3D scene graph."""

    def __init__(self):
        self.default_floor_height = 2.8  # meters
        self.slab_thickness = 0.15  # meters

        # Colors for wall types
        self.colors = {
            "load_bearing": "#4a5568",  # Gray-700
            "structural_spine": "#2d3748",  # Gray-800
            "partition": "#a0aec0",  # Gray-400
            "exterior": "#2b6cb0",  # Blue-600
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
        """
        Extrude 2D floor plan to 3D.

        Args:
            parse_result: Parsing result with walls and rooms
            geometry_result: Geometry analysis with classifications
            structural_result: Structural analysis with warnings
            num_floors: Number of floors to generate
            floor_height: Override floor height (meters)
            debug_dir: Directory for debug output

        Returns:
            SceneGraph for Three.js visualization
        """
        height = floor_height or self.default_floor_height

        # Wall/room pixel coordinates must be converted to meters for the 3D scene.
        # Wall length_m and thickness_m are already in meters; start/end are still pixels.
        ppm = parse_result.scale.pixels_per_meter if parse_result.scale.pixels_per_meter else 1.0

        # Extrude walls
        walls_3d = []
        for cw in geometry_result.classified_walls:
            for floor in range(num_floors):
                extruded = self._extrude_wall(cw, floor, height, ppm)
                walls_3d.append(extruded)

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
                        y=height / 2,  # Mid-height
                        z=room.centroid.y / ppm,
                    ),
                    area_m2=room.area_m2,
                    room_type=room.room_type,
                )
                labels.append(label)

        # Calculate camera bounds
        bounds = self._calculate_bounds(geometry_result, num_floors, height, ppm)

        scene = SceneGraph(
            walls=walls_3d,
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
            f"3D Extrusion - Walls: {len(walls_3d)}, Slabs: {len(slabs)}, Floors: {num_floors}"
        )

        return scene

    def _extrude_wall(
        self, classified_wall: ClassifiedWall, floor: int, floor_height: float, ppm: float = 1.0
    ) -> ExtrudedWall:
        """Extrude a single wall to 3D."""

        wall = classified_wall.wall
        base_z = floor * floor_height
        top_z = base_z + floor_height

        # Convert pixel coords to meters
        sx = wall.start.x / ppm
        sy = wall.start.y / ppm
        ex = wall.end.x / ppm
        ey = wall.end.y / ppm

        # Get wall direction and perpendicular (now in meters)
        dx = ex - sx
        dy = ey - sy
        length = np.sqrt(dx * dx + dy * dy)

        if length == 0:
            length = 1

        # Unit perpendicular vector
        perp_x = -dy / length * wall.thickness_m / 2
        perp_y = dx / length * wall.thickness_m / 2

        # 8 vertices for a box (4 bottom, 4 top)
        # In Three.js coordinate system: Y is up, X is right, Z is forward
        vertices = [
            # Bottom face (y = base_z)
            Point3D(x=sx - perp_x, y=base_z, z=sy - perp_y),  # 0
            Point3D(x=sx + perp_x, y=base_z, z=sy + perp_y),  # 1
            Point3D(x=ex + perp_x, y=base_z, z=ey + perp_y),  # 2
            Point3D(x=ex - perp_x, y=base_z, z=ey - perp_y),  # 3
            # Top face (y = top_z)
            Point3D(x=sx - perp_x, y=top_z, z=sy - perp_y),  # 4
            Point3D(x=sx + perp_x, y=top_z, z=sy + perp_y),  # 5
            Point3D(x=ex + perp_x, y=top_z, z=ey + perp_y),  # 6
            Point3D(x=ex - perp_x, y=top_z, z=ey - perp_y),  # 7
        ]

        # 6 faces (2 triangles each)
        faces = [
            # Bottom
            Face(vertices=[0, 1, 2]),
            Face(vertices=[0, 2, 3]),
            # Top
            Face(vertices=[4, 6, 5]),
            Face(vertices=[4, 7, 6]),
            # Front
            Face(vertices=[0, 4, 5]),
            Face(vertices=[0, 5, 1]),
            # Back
            Face(vertices=[2, 6, 7]),
            Face(vertices=[2, 7, 3]),
            # Left
            Face(vertices=[0, 3, 7]),
            Face(vertices=[0, 7, 4]),
            # Right
            Face(vertices=[1, 5, 6]),
            Face(vertices=[1, 6, 2]),
        ]

        # Determine color
        if wall.is_exterior:
            color = self.colors["exterior"]
        else:
            color = self.colors.get(
                classified_wall.classification, self.colors["partition"]
            )

        return ExtrudedWall(
            wall_id=f"{wall.id}_f{floor}",
            vertices_3d=vertices,
            faces=faces,
            classification=classified_wall.classification,
            thickness_m=wall.thickness_m,
            height_m=floor_height,
            openings=[],  # TODO: Cut openings from geometry
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

        # Get all wall endpoints (converted to meters)
        all_x = []
        all_z = []

        for cw in geometry_result.classified_walls:
            all_x.extend([cw.wall.start.x / ppm, cw.wall.end.x / ppm])
            all_z.extend([cw.wall.start.y / ppm, cw.wall.end.y / ppm])

        if not all_x:
            # Fallback
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

        # Calculate recommended camera distance
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
            "num_slabs": len(scene.slabs),
            "num_labels": len(scene.room_labels),
            "num_floors": scene.num_floors,
            "floor_height_m": scene.floor_height_m,
            "total_height_m": scene.total_height_m,
            "camera_bounds": {
                "min": {
                    "x": scene.camera_bounds.min.x,
                    "y": scene.camera_bounds.min.y,
                    "z": scene.camera_bounds.min.z,
                },
                "max": {
                    "x": scene.camera_bounds.max.x,
                    "y": scene.camera_bounds.max.y,
                    "z": scene.camera_bounds.max.z,
                },
                "center": {
                    "x": scene.camera_bounds.center.x,
                    "y": scene.camera_bounds.center.y,
                    "z": scene.camera_bounds.center.z,
                },
                "recommended_distance": scene.camera_bounds.recommended_distance,
            },
        }

        with open(os.path.join(debug_dir, "extrusion_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
