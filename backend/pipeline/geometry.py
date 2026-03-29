"""
Geometry analysis - wall graph, junctions, and structural classification.
"""

import os
from typing import Optional, List, Tuple, Set
import numpy as np

from models.parsing import ParseResult, WallSegment, Room, Point2D
from models.geometry import Junction, ClassifiedWall, GeometryResult


class GeometryAnalyzer:
    """Analyzes wall geometry to build graph and classify structural roles."""

    def __init__(self):
        # NOTE: junction_threshold is in PIXEL units (not meters),
        # because junction detection runs before scale conversion.
        # 15px ~= 0.25m at typical 60px/m scale.
        self.junction_threshold = 15.0  # pixels
        self.exterior_wall_min_thickness = 0.2  # meters
        self.load_bearing_min_length = 1.5  # meters

    def analyze(
        self, parse_result: ParseResult, debug_dir: Optional[str] = None
    ) -> GeometryResult:
        """
        Analyze geometry and classify walls.

        Args:
            parse_result: Fused parsing result
            debug_dir: Directory for debug output

        Returns:
            GeometryResult with junctions and classified walls
        """
        walls = parse_result.walls
        rooms = parse_result.rooms

        # Build wall graph and find junctions
        junctions = self._find_junctions(walls)

        # Classify walls based on position, thickness, and connectivity
        classified_walls = self._classify_walls(
            walls, junctions, rooms, parse_result.building_outline
        )

        # Find structural spines (continuous load paths)
        spines = self._find_structural_spines(classified_walls, junctions)

        # Calculate statistics
        total_length = sum(w.wall.length_m for w in classified_walls)
        exterior_length = sum(
            w.wall.length_m for w in classified_walls if w.wall.is_exterior
        )
        interior_length = total_length - exterior_length
        load_bearing_count = sum(
            1 for w in classified_walls if w.classification == "load_bearing"
        )
        partition_count = sum(
            1 for w in classified_walls if w.classification == "partition"
        )

        result = GeometryResult(
            junctions=junctions,
            classified_walls=classified_walls,
            room_polygons=rooms,
            structural_spines=spines,
            building_footprint=parse_result.building_outline,
            total_wall_length_m=total_length,
            exterior_wall_length_m=exterior_length,
            interior_wall_length_m=interior_length,
            load_bearing_wall_count=load_bearing_count,
            partition_wall_count=partition_count,
        )

        if debug_dir:
            self._save_debug(result, debug_dir)

        print(
            f"Geometry Analysis - Junctions: {len(junctions)}, Load-bearing: {load_bearing_count}, Partitions: {partition_count}"
        )

        return result

    def _find_junctions(self, walls: List[WallSegment]) -> List[Junction]:
        """Find junction points where walls meet."""

        junctions = []
        junction_id = 0

        # Collect all endpoints
        endpoints = []
        for wall in walls:
            endpoints.append((wall.start, wall.id, "start"))
            endpoints.append((wall.end, wall.id, "end"))

        # Cluster nearby endpoints
        used = set()

        for i, (pt1, wall1_id, end1) in enumerate(endpoints):
            if i in used:
                continue

            cluster = [(pt1, wall1_id)]
            used.add(i)

            for j, (pt2, wall2_id, end2) in enumerate(endpoints):
                if j in used or wall2_id == wall1_id:
                    continue

                dist = self._point_distance(pt1, pt2)
                if dist < self.junction_threshold:
                    cluster.append((pt2, wall2_id))
                    used.add(j)

            if len(cluster) >= 2:
                # Calculate centroid of cluster
                cx = np.mean([p[0].x for p in cluster])
                cy = np.mean([p[0].y for p in cluster])

                # Determine junction type
                connected_ids = list(set(p[1] for p in cluster))
                junction_type = self._determine_junction_type(len(connected_ids))

                junctions.append(
                    Junction(
                        id=f"junction_{junction_id:03d}",
                        position=Point2D(x=cx, y=cy),
                        type=junction_type,
                        connected_wall_ids=connected_ids,
                    )
                )
                junction_id += 1

        return junctions

    def _point_distance(self, p1: Point2D, p2: Point2D) -> float:
        """Calculate Euclidean distance between two points."""
        return np.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    def _determine_junction_type(self, num_walls: int) -> str:
        """Determine junction type based on number of connected walls."""
        if num_walls == 1:
            return "endpoint"
        elif num_walls == 2:
            return "L"
        elif num_walls == 3:
            return "T"
        else:
            return "X"

    def _classify_walls(
        self,
        walls: List[WallSegment],
        junctions: List[Junction],
        rooms: List[Room],
        building_outline: List[Point2D],
    ) -> List[ClassifiedWall]:
        """Classify each wall as load-bearing, partition, or structural spine."""

        classified = []

        # Build junction lookup
        wall_junctions = {}
        for junction in junctions:
            for wall_id in junction.connected_wall_ids:
                if wall_id not in wall_junctions:
                    wall_junctions[wall_id] = []
                wall_junctions[wall_id].append(junction)

        for wall in walls:
            # Find adjacent rooms
            adjacent_rooms = self._find_adjacent_rooms(wall, rooms)
            adjacent_room_types = [r.room_type for r in adjacent_rooms]

            # Determine classification
            classification, reason, load_path = self._classify_single_wall(
                wall,
                wall_junctions.get(wall.id, []),
                adjacent_room_types,
                building_outline,
            )

            classified.append(
                ClassifiedWall(
                    wall=wall,
                    classification=classification,
                    reason=reason,
                    load_path_continuous=load_path,
                    adjacent_rooms=[r.id for r in adjacent_rooms],
                    adjacent_room_types=adjacent_room_types,
                )
            )

        return classified

    def _classify_single_wall(
        self,
        wall: WallSegment,
        junctions: List[Junction],
        adjacent_room_types: List[str],
        building_outline: List[Point2D],
    ) -> Tuple[str, str, bool]:
        """
        Classify a single wall.

        Returns: (classification, reason, load_path_continuous)
        """
        reasons = []
        score = 0  # Higher score = more likely load-bearing

        # Exterior walls are typically load-bearing
        if wall.is_exterior:
            score += 3
            reasons.append("exterior wall")

        # Thick walls are more likely load-bearing
        if wall.thickness_m >= self.exterior_wall_min_thickness:
            score += 2
            reasons.append(f"thick ({wall.thickness_m:.2f}m)")

        # Long walls are more likely load-bearing
        if wall.length_m >= self.load_bearing_min_length:
            score += 1
            reasons.append(f"long ({wall.length_m:.1f}m)")

        # Walls at T or X junctions are more likely load-bearing
        has_structural_junction = any(j.type in ["T", "X"] for j in junctions)
        if has_structural_junction:
            score += 2
            reasons.append("T/X junction")

        # Walls separating large rooms are more likely load-bearing
        large_room_adjacent = any(
            rt in ["living", "great_room", "dining"] for rt in adjacent_room_types
        )
        if large_room_adjacent:
            score += 1
            reasons.append("supports large room")

        # Classify based on score
        if score >= 3:
            classification = "load_bearing"
            load_path = True
        elif score >= 2:
            classification = "load_bearing"
            load_path = has_structural_junction
        else:
            classification = "partition"
            load_path = False

        # Check for structural spine (continuous load path through building)
        if wall.is_exterior and wall.length_m > 3.0:
            classification = "structural_spine"
            load_path = True
            reasons.append("potential spine")

        reason = "; ".join(reasons) if reasons else "default classification"

        return classification, reason, load_path

    def _find_adjacent_rooms(self, wall: WallSegment, rooms: List[Room]) -> List[Room]:
        """Find rooms adjacent to a wall."""

        adjacent = []

        # Get wall midpoint
        mid_x = (wall.start.x + wall.end.x) / 2
        mid_y = (wall.start.y + wall.end.y) / 2

        for room in rooms:
            if room.centroid is None:
                continue

            # Simple distance check (could be improved with proper polygon intersection)
            dist = np.sqrt(
                (room.centroid.x - mid_x) ** 2 + (room.centroid.y - mid_y) ** 2
            )

            # If room centroid is within reasonable distance of wall
            if dist < max(wall.length_m * 50, 200):  # Scale-dependent threshold
                adjacent.append(room)

        return adjacent[:2]  # A wall has at most 2 adjacent rooms

    def _find_structural_spines(
        self, classified_walls: List[ClassifiedWall], junctions: List[Junction]
    ) -> List[List[str]]:
        """Find continuous structural spines through the building."""

        spines = []

        # Find load-bearing walls
        load_bearing_ids = {
            cw.wall.id
            for cw in classified_walls
            if cw.classification in ["load_bearing", "structural_spine"]
        }

        # Build adjacency graph of load-bearing walls
        graph = {}
        for junction in junctions:
            lb_walls = [
                wid for wid in junction.connected_wall_ids if wid in load_bearing_ids
            ]
            if len(lb_walls) >= 2:
                for wid in lb_walls:
                    if wid not in graph:
                        graph[wid] = set()
                    graph[wid].update(w for w in lb_walls if w != wid)

        # Find connected components (spines)
        visited = set()

        for start_wall in load_bearing_ids:
            if start_wall in visited:
                continue

            # BFS to find connected walls
            spine = []
            queue = [start_wall]

            while queue:
                wall_id = queue.pop(0)
                if wall_id in visited:
                    continue

                visited.add(wall_id)
                spine.append(wall_id)

                for neighbor in graph.get(wall_id, []):
                    if neighbor not in visited:
                        queue.append(neighbor)

            if len(spine) >= 2:
                spines.append(spine)

        return spines

    def _save_debug(self, result: GeometryResult, debug_dir: str):
        """Save geometry debug information."""
        import json

        os.makedirs(debug_dir, exist_ok=True)

        debug_info = {
            "junction_count": len(result.junctions),
            "junctions": [
                {
                    "id": j.id,
                    "type": j.type,
                    "position": {"x": j.position.x, "y": j.position.y},
                    "connected_walls": j.connected_wall_ids,
                }
                for j in result.junctions
            ],
            "wall_classifications": [
                {
                    "wall_id": cw.wall.id,
                    "classification": cw.classification,
                    "reason": cw.reason,
                    "load_path": cw.load_path_continuous,
                    "adjacent_room_types": cw.adjacent_room_types,
                }
                for cw in result.classified_walls
            ],
            "structural_spines": result.structural_spines,
            "statistics": {
                "total_wall_length_m": result.total_wall_length_m,
                "exterior_wall_length_m": result.exterior_wall_length_m,
                "interior_wall_length_m": result.interior_wall_length_m,
                "load_bearing_count": result.load_bearing_wall_count,
                "partition_count": result.partition_wall_count,
            },
        }

        with open(os.path.join(debug_dir, "geometry_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
