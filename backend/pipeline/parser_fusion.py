"""
Parser fusion — merges VLM (AI vision) and CV (computer vision) results.

Key improvements:
1. Uses VLM-extracted dimensions for scale calibration (highest priority)
2. Synthesizes room polygons from VLM bounding boxes when CV misses rooms
3. Fixed area calculation using proper pixel→meter conversion
"""

import os
import json
from typing import Optional, List, Tuple
import numpy as np

from models.parsing import (
    ParseResult, VLMParseResult, CVParseResult,
    WallSegment, Room, Opening, ScaleReference, Point2D,
)


# Room type aliases for fuzzy matching
ROOM_TYPE_MAP = {
    "bedroom": "bedroom", "bed room": "bedroom", "bed": "bedroom", "master bedroom": "bedroom",
    "bathroom": "bathroom", "bath room": "bathroom", "bath": "bathroom", "washroom": "bathroom",
    "toilet": "toilet", "wc": "toilet", "restroom": "toilet", "latrine": "toilet",
    "kitchen": "kitchen", "pantry": "kitchen", "kitchenette": "kitchen",
    "living": "living", "living room": "living", "drawing room": "living", "lounge": "living",
    "hall": "hall", "hallway": "hallway", "corridor": "hallway", "passage": "hallway",
    "dining": "dining", "dining room": "dining",
    "pooja": "pooja", "puja": "pooja", "prayer": "pooja", "mandir": "pooja",
    "staircase": "staircase", "stairs": "staircase", "stair": "staircase",
    "balcony": "balcony", "verandah": "balcony", "terrace": "balcony", "porch": "balcony",
    "foyer": "foyer", "entry": "foyer", "entrance": "foyer", "lobby": "foyer",
    "closet": "closet", "wardrobe": "closet", "store": "closet", "storage": "closet",
    "utility": "utility", "laundry": "laundry",
    "garage": "garage", "parking": "garage", "car porch": "garage",
    "great_room": "great_room",
}


def _classify_room_type(label: str) -> str:
    """Classify room type from its label."""
    label_lower = label.lower().strip()
    for key, rtype in ROOM_TYPE_MAP.items():
        if key in label_lower:
            return rtype
    return "other"


def _determine_scale(
    vlm_result: VLMParseResult,
    cv_result: CVParseResult,
    image_dims: Tuple[int, int],
) -> ScaleReference:
    """
    Determine scale with priority:
    1. VLM dimension-based scale (from plan text)
    2. CV door-width scale
    3. Intelligent default based on image size
    """
    w, h = image_dims

    # Priority 1: VLM-extracted scale from plan dimensions
    if vlm_result.estimated_scale and vlm_result.estimated_scale > 5:
        scale = vlm_result.estimated_scale
        # Sanity check: for a typical residential plan, 10-80 px/m is reasonable
        # for an image 400-2000px wide
        expected_min = w / 30  # building ~30m wide max
        expected_max = w / 3   # building ~3m wide min
        if expected_min < scale < expected_max:
            return ScaleReference(
                pixels_per_meter=scale,
                reference_dimension_m=1.0,
                confidence=0.9,
                method="vlm_estimate",
            )
        else:
            print(f"  VLM scale {scale:.1f} px/m out of range [{expected_min:.0f}, {expected_max:.0f}], adjusting")
            # Clamp to reasonable range
            scale = max(expected_min, min(scale, expected_max))
            return ScaleReference(
                pixels_per_meter=scale,
                reference_dimension_m=1.0,
                confidence=0.7,
                method="vlm_estimate",
            )

    # Priority 2: CV door-width scale
    cv_scale = cv_result.scale
    if cv_scale.method != "default" and cv_scale.confidence > 0.3:
        # Sanity check CV scale too
        expected_min = w / 25
        expected_max = w / 4
        if expected_min < cv_scale.pixels_per_meter < expected_max:
            return cv_scale
        else:
            print(f"  CV scale {cv_scale.pixels_per_meter:.1f} px/m out of range, falling back")

    # Priority 3: VLM room dimensions for scale estimation
    for rd in vlm_result.rooms:
        rm_w = rd.get("width_m")
        rm_l = rd.get("length_m")
        bbox = rd.get("bbox", {})
        if rm_w and rm_l and rm_w > 1 and rm_l > 1 and bbox:
            bbox_w = abs(bbox.get("x_max", 0) - bbox.get("x_min", 0))
            bbox_h = abs(bbox.get("y_max", 0) - bbox.get("y_min", 0))
            if bbox_w > 20 and bbox_h > 20:
                scale_x = bbox_w / float(rm_w)
                scale_y = bbox_h / float(rm_l)
                avg_scale = (scale_x + scale_y) / 2
                return ScaleReference(
                    pixels_per_meter=avg_scale,
                    reference_dimension_m=float(rm_w),
                    confidence=0.75,
                    method="vlm_estimate",
                )

    # Priority 4: Reasonable default based on image size
    # Assume a typical Indian residential plot: ~8m x 10m
    # The building fills roughly 80% of the image
    default_building_width_m = 8.0  # typical Indian residential
    pixels_per_m = (w * 0.75) / default_building_width_m
    print(f"  Using default scale: {pixels_per_m:.1f} px/m (assumed {default_building_width_m}m building in {w}px image)")

    return ScaleReference(
        pixels_per_meter=pixels_per_m,
        reference_dimension_m=default_building_width_m,
        confidence=0.4,
        method="default",
    )


def _synthesize_rooms_from_vlm(
    vlm_result: VLMParseResult,
    ppm: float,
) -> List[Room]:
    """Create Room objects from VLM bounding boxes with accurate area calculation."""
    rooms = []
    for i, rd in enumerate(vlm_result.rooms):
        bbox = rd.get("bbox", {})
        if not bbox or not all(k in bbox for k in ("x_min", "y_min", "x_max", "y_max")):
            continue

        x_min = float(bbox["x_min"])
        y_min = float(bbox["y_min"])
        x_max = float(bbox["x_max"])
        y_max = float(bbox["y_max"])

        if x_max <= x_min or y_max <= y_min:
            continue

        vertices = [
            Point2D(x=x_min, y=y_min),
            Point2D(x=x_max, y=y_min),
            Point2D(x=x_max, y=y_max),
            Point2D(x=x_min, y=y_max),
        ]

        # Calculate area - use VLM-provided dimensions if available, otherwise pixel/scale
        vlm_width = rd.get("width_m")
        vlm_length = rd.get("length_m")
        vlm_area = rd.get("estimated_area_sqm")

        if vlm_width and vlm_length and vlm_width > 0.5 and vlm_length > 0.5:
            area_m2 = float(vlm_width) * float(vlm_length)
        elif vlm_area and vlm_area > 0.5:
            area_m2 = float(vlm_area)
        else:
            # Convert from pixel area
            pixel_area = (x_max - x_min) * (y_max - y_min)
            area_m2 = pixel_area / (ppm * ppm)

        centroid = Point2D(x=(x_min + x_max) / 2, y=(y_min + y_max) / 2)
        label = rd.get("label", f"Room {i + 1}")
        room_type = _classify_room_type(label)

        rooms.append(Room(
            id=f"room_{i:03d}",
            label=label.upper(),
            vertices=vertices,
            area_m2=round(area_m2, 2),
            room_type=room_type,
            centroid=centroid,
        ))

    return rooms


def fuse_parsers(
    vlm_result: VLMParseResult,
    cv_result: CVParseResult,
    image_dims: Tuple[int, int],
    debug_dir: Optional[str] = None,
) -> ParseResult:
    """
    Fuse VLM and CV parsing results into a single ParseResult.
    """
    w, h = image_dims

    # Step 1: Determine scale
    scale = _determine_scale(vlm_result, cv_result, image_dims)
    ppm = scale.pixels_per_meter

    print(f"Fusion: Scale = {ppm:.1f} px/m (method: {scale.method}, conf: {scale.confidence})")

    # Step 2: Use CV walls (they have pixel-accurate geometry)
    walls = cv_result.walls
    # Recalculate wall lengths and thicknesses with corrected scale
    for wall in walls:
        length_px = np.sqrt(
            (wall.end.x - wall.start.x) ** 2 + (wall.end.y - wall.start.y) ** 2
        )
        wall.length_m = round(length_px / ppm, 2)
        wall.thickness_m = max(0.1, round(wall.thickness_px / ppm, 3))

    # Step 3: Get rooms — prefer VLM rooms (they have labels and types)
    vlm_rooms = _synthesize_rooms_from_vlm(vlm_result, ppm)
    cv_rooms = cv_result.rooms

    # Recalculate CV room areas with corrected scale
    for room in cv_rooms:
        if room.vertices:
            xs = [v.x for v in room.vertices]
            ys = [v.y for v in room.vertices]
            pixel_area = abs(max(xs) - min(xs)) * abs(max(ys) - min(ys))
            room.area_m2 = round(pixel_area / (ppm * ppm), 2)

    # Strategy: use VLM rooms if they have more coverage, assign CV geometry where possible
    if len(vlm_rooms) >= len(cv_rooms):
        final_rooms = vlm_rooms
        source = "vlm_primary"
    else:
        # Use CV rooms but apply VLM labels
        final_rooms = cv_rooms
        # Try to assign labels from VLM
        for cv_room in final_rooms:
            best_match = None
            best_dist = float("inf")
            if cv_room.centroid:
                for vlm_room in vlm_rooms:
                    if vlm_room.centroid:
                        dist = np.sqrt(
                            (cv_room.centroid.x - vlm_room.centroid.x) ** 2 +
                            (cv_room.centroid.y - vlm_room.centroid.y) ** 2
                        )
                        if dist < best_dist:
                            best_dist = dist
                            best_match = vlm_room
            if best_match and best_dist < max(w, h) * 0.3:
                cv_room.label = best_match.label
                cv_room.room_type = best_match.room_type
                cv_room.area_m2 = best_match.area_m2 if best_match.area_m2 > cv_room.area_m2 * 0.5 else cv_room.area_m2
        source = "cv_primary"

    print(f"Fusion: {len(final_rooms)} rooms ({source}), {len(walls)} walls")

    # Step 4: Openings from CV
    openings = cv_result.openings
    for opening in openings:
        opening.width_m = round(opening.width_m / (cv_result.scale.pixels_per_meter / ppm) if cv_result.scale.pixels_per_meter != ppm else opening.width_m, 2)

    # Build result
    result = ParseResult(
        walls=walls,
        rooms=final_rooms,
        openings=openings,
        scale=scale,
        image_dims=image_dims,
        building_outline=cv_result.building_outline,
        building_shape=vlm_result.building_shape,
        parsing_method="vlm_cv_fusion",
        confidence=scale.confidence,
        vlm_cv_agreement=min(len(vlm_rooms), len(cv_rooms)) / max(len(vlm_rooms), len(cv_rooms), 1),
    )

    # Debug output
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        debug_data = {
            "parsing_method": source,
            "scale": {
                "pixels_per_meter": ppm,
                "method": scale.method,
                "confidence": scale.confidence,
            },
            "counts": {"walls": len(walls), "rooms": len(final_rooms)},
            "room_details": [
                {"id": r.id, "label": r.label, "type": r.room_type, "area_m2": r.area_m2}
                for r in final_rooms
            ],
            "vlm_counts": {"rooms": len(vlm_rooms)},
            "cv_counts": {"walls": len(cv_result.walls), "rooms": len(cv_rooms)},
            "building_shape": vlm_result.building_shape,
        }
        with open(os.path.join(debug_dir, "fusion_debug.json"), "w") as f:
            json.dump(debug_data, f, indent=2)

    return result
