"""
Computer Vision parser using OpenCV.
Extracts geometric information (walls, rooms, openings) from floor plans.
"""

import os
from typing import Optional, List, Tuple
import numpy as np

from ..models.parsing import (
    CVParseResult,
    WallSegment,
    Room,
    Opening,
    ScaleReference,
    Point2D,
)

# Lazy import for cv2
cv2 = None


def _get_cv2():
    global cv2
    if cv2 is None:
        import cv2 as _cv2

        cv2 = _cv2
    return cv2


class CVParser:
    """Parser using OpenCV for geometric floor plan extraction."""

    def __init__(self):
        self.min_wall_length_px = 20
        self.wall_thickness_range = (3, 30)  # pixels

    def parse(
        self, image: np.ndarray, binary: np.ndarray, debug_dir: Optional[str] = None
    ) -> CVParseResult:
        """
        Parse a floor plan using computer vision techniques.

        Args:
            image: Original BGR image
            binary: Preprocessed binary image
            debug_dir: Directory to save debug images

        Returns:
            CVParseResult with detected walls, rooms, openings
        """
        cv2 = _get_cv2()

        h, w = binary.shape[:2]

        # Detect walls using line detection
        walls = self._detect_walls(binary, debug_dir)

        # Detect rooms using contour analysis
        rooms = self._detect_rooms(binary, debug_dir)

        # Detect openings (doors/windows) by finding gaps in walls
        openings = self._detect_openings(binary, walls, debug_dir)

        # Estimate scale
        scale = self._estimate_scale(binary, walls, openings)

        # Convert pixel measurements to meters
        walls = self._apply_scale(walls, scale)

        # Detect building outline
        outline = self._detect_building_outline(binary)

        # Save debug image with all detections
        if debug_dir:
            self._save_debug_image(image, walls, rooms, openings, outline, debug_dir)

        # Print detection summary
        print(
            f"CV Parser - Detected: {len(walls)} walls, {len(rooms)} rooms, {len(openings)} openings"
        )

        return CVParseResult(
            walls=walls,
            rooms=rooms,
            openings=openings,
            scale=scale,
            building_outline=outline,
        )

    def _detect_walls(
        self, binary: np.ndarray, debug_dir: Optional[str] = None
    ) -> List[WallSegment]:
        """Detect wall segments using Hough Line Transform."""
        cv2 = _get_cv2()

        walls = []

        # Use probabilistic Hough transform
        lines = cv2.HoughLinesP(
            binary,
            rho=1,
            theta=np.pi / 180,
            threshold=50,
            minLineLength=self.min_wall_length_px,
            maxLineGap=10,
        )

        if lines is None:
            return walls

        wall_id = 0
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculate length
            length_px = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            # Skip very short segments
            if length_px < self.min_wall_length_px:
                continue

            # Estimate thickness by checking perpendicular profile
            thickness_px = self._estimate_wall_thickness(binary, (x1, y1), (x2, y2))

            # Check if wall is on exterior (near image boundary)
            h, w = binary.shape[:2]
            margin = 50
            is_exterior = (
                min(x1, x2) < margin
                or max(x1, x2) > w - margin
                or min(y1, y2) < margin
                or max(y1, y2) > h - margin
            )

            walls.append(
                WallSegment(
                    id=f"wall_{wall_id:03d}",
                    start=Point2D(x=float(x1), y=float(y1)),
                    end=Point2D(x=float(x2), y=float(y2)),
                    thickness_px=thickness_px,
                    thickness_m=0.15,  # Will be updated with scale
                    length_m=length_px,  # Will be updated with scale
                    is_exterior=is_exterior,
                    source="cv",
                )
            )
            wall_id += 1

        # Merge collinear walls
        walls = self._merge_collinear_walls(walls)

        return walls

    def _estimate_wall_thickness(
        self, binary: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]
    ) -> float:
        """Estimate wall thickness by sampling perpendicular to wall."""
        cv2 = _get_cv2()

        x1, y1 = start
        x2, y2 = end

        # Get midpoint
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2

        # Get perpendicular direction
        dx = x2 - x1
        dy = y2 - y1
        length = np.sqrt(dx * dx + dy * dy)
        if length == 0:
            return 10.0

        # Perpendicular unit vector
        perp_x = -dy / length
        perp_y = dx / length

        # Sample along perpendicular
        max_dist = 30
        thickness = 0

        for sign in [1, -1]:
            for d in range(1, max_dist):
                px = int(mid_x + sign * d * perp_x)
                py = int(mid_y + sign * d * perp_y)

                if 0 <= px < binary.shape[1] and 0 <= py < binary.shape[0]:
                    if binary[py, px] == 0:  # Found edge of wall
                        thickness += d
                        break
                else:
                    thickness += d
                    break

        return max(thickness, 5.0)

    def _merge_collinear_walls(self, walls: List[WallSegment]) -> List[WallSegment]:
        """Merge collinear wall segments that are close together."""
        if len(walls) < 2:
            return walls

        # Simple implementation - could be improved
        # For now, just return as-is
        # TODO: Implement proper collinear merging
        return walls

    def _detect_rooms(
        self, binary: np.ndarray, debug_dir: Optional[str] = None
    ) -> List[Room]:
        """Detect rooms using contour analysis."""
        cv2 = _get_cv2()

        rooms = []

        # Invert binary (rooms are white spaces)
        inverted = cv2.bitwise_not(binary)

        # Find contours
        contours, hierarchy = cv2.findContours(
            inverted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return rooms

        # Filter contours by area and shape
        min_room_area = 1000  # pixels
        h, w = binary.shape[:2]
        max_room_area = h * w * 0.8  # Room shouldn't be more than 80% of image

        room_id = 0
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)

            if area < min_room_area or area > max_room_area:
                continue

            # Simplify contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Convert to Point2D list
            vertices = [Point2D(x=float(pt[0][0]), y=float(pt[0][1])) for pt in approx]

            # Calculate centroid
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
            else:
                cx, cy = vertices[0].x, vertices[0].y

            rooms.append(
                Room(
                    id=f"room_{room_id:03d}",
                    label=f"Room {room_id + 1}",
                    vertices=vertices,
                    area_m2=area,  # Will be updated with scale
                    room_type="other",
                    centroid=Point2D(x=cx, y=cy),
                )
            )
            room_id += 1

        return rooms

    def _detect_openings(
        self,
        binary: np.ndarray,
        walls: List[WallSegment],
        debug_dir: Optional[str] = None,
    ) -> List[Opening]:
        """Detect door and window openings."""
        cv2 = _get_cv2()

        openings = []

        # Look for gaps in walls
        # Doors: typically 0.8-1.0m wide
        # Windows: typically 0.6-1.5m wide

        # For now, use a simplified approach:
        # Find small gaps in the binary image along wall directions

        opening_id = 0
        for wall in walls:
            # Sample along wall to find gaps
            x1, y1 = int(wall.start.x), int(wall.start.y)
            x2, y2 = int(wall.end.x), int(wall.end.y)

            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length == 0:
                continue

            dx = (x2 - x1) / length
            dy = (y2 - y1) / length

            # Sample points along wall
            num_samples = int(length)
            gap_start = None

            for i in range(num_samples):
                px = int(x1 + i * dx)
                py = int(y1 + i * dy)

                if 0 <= px < binary.shape[1] and 0 <= py < binary.shape[0]:
                    is_wall = binary[py, px] > 0

                    if not is_wall and gap_start is None:
                        gap_start = i
                    elif is_wall and gap_start is not None:
                        gap_length = i - gap_start

                        # Check if gap is door/window sized (30-150 pixels)
                        if 30 < gap_length < 150:
                            gap_center = gap_start + gap_length / 2
                            pos_x = x1 + gap_center * dx
                            pos_y = y1 + gap_center * dy

                            # Classify as door or window based on size
                            # Doors are typically larger
                            opening_type = "door" if gap_length > 60 else "window"

                            openings.append(
                                Opening(
                                    id=f"opening_{opening_id:03d}",
                                    position=Point2D(x=pos_x, y=pos_y),
                                    width_m=float(gap_length),  # Will be scaled
                                    type=opening_type,
                                    parent_wall_id=wall.id,
                                )
                            )
                            opening_id += 1

                        gap_start = None

        return openings

    def _estimate_scale(
        self, binary: np.ndarray, walls: List[WallSegment], openings: List[Opening]
    ) -> ScaleReference:
        """Estimate scale from detected features."""

        # Default: assume standard door width of 0.9m
        # Look for door-sized openings
        door_openings = [o for o in openings if o.type == "door"]

        if door_openings:
            # Average door width in pixels
            avg_door_width_px = np.mean([o.width_m for o in door_openings])
            # Standard door is ~0.9m
            pixels_per_meter = avg_door_width_px / 0.9

            return ScaleReference(
                pixels_per_meter=pixels_per_meter,
                reference_dimension_m=0.9,
                confidence=0.6,
                method="door_width",
            )

        # Fallback: use image size heuristic
        # Assume typical room is ~4m wide
        h, w = binary.shape[:2]
        estimated_ppm = min(w, h) / 10.0  # Assume 10m across smallest dimension

        return ScaleReference(
            pixels_per_meter=estimated_ppm,
            reference_dimension_m=10.0,
            confidence=0.3,
            method="default",
        )

    def _apply_scale(
        self, walls: List[WallSegment], scale: ScaleReference
    ) -> List[WallSegment]:
        """Apply scale to convert pixel measurements to meters."""
        ppm = scale.pixels_per_meter

        for wall in walls:
            # Convert length
            length_px = np.sqrt(
                (wall.end.x - wall.start.x) ** 2 + (wall.end.y - wall.start.y) ** 2
            )
            wall.length_m = length_px / ppm

            # Convert thickness
            wall.thickness_m = wall.thickness_px / ppm
            # Clamp to reasonable values
            wall.thickness_m = max(0.1, min(0.5, wall.thickness_m))

        return walls

    def _detect_building_outline(self, binary: np.ndarray) -> List[Point2D]:
        """Detect the exterior building outline."""
        cv2 = _get_cv2()

        # Dilate to connect nearby walls
        kernel = np.ones((10, 10), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=2)

        # Find largest contour
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return []

        largest = max(contours, key=cv2.contourArea)

        # Simplify to polygon
        epsilon = 0.01 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)

        return [Point2D(x=float(pt[0][0]), y=float(pt[0][1])) for pt in approx]

    def _save_debug_image(
        self,
        image: np.ndarray,
        walls: List[WallSegment],
        rooms: List[Room],
        openings: List[Opening],
        outline: List[Point2D],
        debug_dir: str,
    ):
        """Save debug image with all detections visualized."""
        cv2 = _get_cv2()

        os.makedirs(debug_dir, exist_ok=True)
        debug_img = image.copy()

        # Draw building outline (yellow)
        if outline:
            pts = np.array([[int(p.x), int(p.y)] for p in outline], np.int32)
            cv2.polylines(debug_img, [pts], True, (0, 255, 255), 2)

        # Draw rooms (blue fill with transparency)
        overlay = debug_img.copy()
        for room in rooms:
            pts = np.array([[int(v.x), int(v.y)] for v in room.vertices], np.int32)
            cv2.fillPoly(overlay, [pts], (255, 100, 100))  # Blue fill
            if room.centroid:
                cv2.putText(
                    debug_img,
                    room.label,
                    (int(room.centroid.x), int(room.centroid.y)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )
        cv2.addWeighted(overlay, 0.3, debug_img, 0.7, 0, debug_img)

        # Draw walls (green)
        for wall in walls:
            color = (0, 255, 0) if not wall.is_exterior else (0, 200, 0)
            thickness = 2 if not wall.is_exterior else 3
            cv2.line(
                debug_img,
                (int(wall.start.x), int(wall.start.y)),
                (int(wall.end.x), int(wall.end.y)),
                color,
                thickness,
            )

        # Draw openings (orange)
        for opening in openings:
            color = (0, 165, 255)  # Orange
            radius = 8 if opening.type == "door" else 5
            cv2.circle(
                debug_img,
                (int(opening.position.x), int(opening.position.y)),
                radius,
                color,
                -1,
            )

        # Save
        cv2.imwrite(os.path.join(debug_dir, "cv_detections.png"), debug_img)

        print(f"Debug image saved to {debug_dir}/cv_detections.png")
