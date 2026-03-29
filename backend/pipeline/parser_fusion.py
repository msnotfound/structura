"""
Parser fusion - combines VLM and CV parsing results.
"""

import os
from typing import Optional, List
import numpy as np

from models.parsing import (
    ParseResult,
    VLMParseResult,
    CVParseResult,
    WallSegment,
    Room,
    Opening,
    ScaleReference,
    Point2D,
)


def fuse_parsers(
    vlm_result: VLMParseResult,
    cv_result: CVParseResult,
    image_dims: tuple[int, int],
    debug_dir: Optional[str] = None,
) -> ParseResult:
    """
    Fuse VLM and CV parsing results into a unified ParseResult.

    Strategy:
    - Use CV for geometric accuracy (walls, precise room boundaries)
    - Use VLM for semantic labels (room types, building shape)
    - Cross-validate scale estimates
    - Flag disagreements for review

    Args:
        vlm_result: Result from VLM parser
        cv_result: Result from CV parser
        image_dims: (width, height) of original image
        debug_dir: Directory for debug output

    Returns:
        Fused ParseResult
    """

    # Determine final scale
    scale = _fuse_scale(vlm_result, cv_result)

    # Use CV walls as primary (geometric accuracy)
    walls = cv_result.walls

    # Fuse rooms: CV geometry + VLM labels
    rooms = _fuse_rooms(vlm_result, cv_result, scale)

    # Use CV openings
    openings = cv_result.openings

    # Apply final scale to openings
    for opening in openings:
        opening.width_m = opening.width_m / scale.pixels_per_meter

    # Apply final scale to rooms
    for room in rooms:
        room.area_m2 = room.area_m2 / (scale.pixels_per_meter**2)

    # Calculate agreement score
    agreement = _calculate_agreement(vlm_result, cv_result)

    # Determine if fallback was needed
    fallback_used = len(walls) == 0 or len(rooms) == 0

    # Determine parsing method
    if fallback_used:
        parsing_method = "vlm_only" if len(walls) == 0 else "cv_only"
    else:
        parsing_method = "vlm_cv_fusion"

    # Calculate overall confidence
    confidence = _calculate_confidence(vlm_result, cv_result, agreement)

    result = ParseResult(
        walls=walls,
        rooms=rooms,
        openings=openings,
        scale=scale,
        image_dims=image_dims,
        building_outline=cv_result.building_outline,
        building_shape=vlm_result.building_shape,
        fallback_used=fallback_used,
        parsing_method=parsing_method,
        confidence=confidence,
        vlm_cv_agreement=agreement,
    )

    # Save debug info
    if debug_dir:
        _save_fusion_debug(result, vlm_result, cv_result, debug_dir)

    print(
        f"Parser Fusion - Method: {parsing_method}, Confidence: {confidence:.2f}, Agreement: {agreement:.2f}"
    )

    return result


def _fuse_scale(vlm_result: VLMParseResult, cv_result: CVParseResult) -> ScaleReference:
    """Fuse scale estimates from VLM and CV."""

    cv_scale = cv_result.scale
    vlm_scale = vlm_result.estimated_scale

    if vlm_scale is None:
        return cv_scale

    # If both have estimates, average if close, otherwise prefer CV
    if cv_scale.confidence >= 0.5:
        # Check if estimates are within 30% of each other
        ratio = vlm_scale / cv_scale.pixels_per_meter
        if 0.7 <= ratio <= 1.3:
            # Average them
            avg_ppm = (vlm_scale + cv_scale.pixels_per_meter) / 2
            return ScaleReference(
                pixels_per_meter=avg_ppm,
                reference_dimension_m=cv_scale.reference_dimension_m,
                confidence=min(cv_scale.confidence + 0.1, 0.9),
                method="vlm_cv_fusion",
            )

    # Prefer CV scale (geometric accuracy)
    return cv_scale


def _fuse_rooms(
    vlm_result: VLMParseResult, cv_result: CVParseResult, scale: ScaleReference
) -> List[Room]:
    """Fuse room information from VLM and CV."""

    rooms = cv_result.rooms.copy()
    vlm_rooms = vlm_result.rooms

    if not vlm_rooms:
        return rooms

    # Try to match VLM rooms to CV rooms by location
    for room in rooms:
        if room.centroid is None:
            continue

        # Find best matching VLM room
        best_match = None
        best_score = 0

        for vlm_room in vlm_rooms:
            # Score based on location description match
            location = vlm_room.get("approximate_location", "")
            score = _location_match_score(
                room.centroid, location, scale.pixels_per_meter
            )

            if score > best_score:
                best_score = score
                best_match = vlm_room

        # Apply VLM labels if good match found
        if best_match and best_score > 0.5:
            room.label = best_match.get("label", room.label)
            room.room_type = best_match.get("room_type", room.room_type)

    return rooms


def _location_match_score(centroid: Point2D, location_desc: str, ppm: float) -> float:
    """Score how well a centroid matches a location description."""

    # Normalize location description
    location = location_desc.lower().strip()

    if not location:
        return 0.0

    # Simple heuristic based on position
    # Assume image is roughly 1000x1000 pixels for normalization
    norm_x = centroid.x / 1000
    norm_y = centroid.y / 1000

    score = 0.0

    # Horizontal position
    if "left" in location:
        score += 1 - norm_x
    elif "right" in location:
        score += norm_x
    elif "center" in location:
        score += 1 - abs(norm_x - 0.5) * 2

    # Vertical position
    if "top" in location:
        score += 1 - norm_y
    elif "bottom" in location:
        score += norm_y
    elif "center" in location:
        score += 1 - abs(norm_y - 0.5) * 2

    return score / 2  # Normalize to 0-1


def _calculate_agreement(vlm_result: VLMParseResult, cv_result: CVParseResult) -> float:
    """Calculate agreement score between VLM and CV results."""

    scores = []

    # Room count agreement
    vlm_count = vlm_result.room_count
    cv_count = len(cv_result.rooms)
    if vlm_count > 0 and cv_count > 0:
        count_agreement = 1 - abs(vlm_count - cv_count) / max(vlm_count, cv_count)
        scores.append(count_agreement)

    # Wall count agreement
    vlm_walls = vlm_result.wall_count_estimate
    cv_walls = len(cv_result.walls)
    if vlm_walls > 0 and cv_walls > 0:
        wall_agreement = 1 - abs(vlm_walls - cv_walls) / max(vlm_walls, cv_walls)
        scores.append(wall_agreement)

    # Scale agreement
    if vlm_result.estimated_scale and cv_result.scale.pixels_per_meter:
        ratio = vlm_result.estimated_scale / cv_result.scale.pixels_per_meter
        scale_agreement = 1 - min(abs(ratio - 1), 1)
        scores.append(scale_agreement)

    return np.mean(scores) if scores else 0.5


def _calculate_confidence(
    vlm_result: VLMParseResult, cv_result: CVParseResult, agreement: float
) -> float:
    """Calculate overall confidence in the fused result."""

    # Base confidence from CV scale
    cv_confidence = cv_result.scale.confidence

    # Boost from agreement
    agreement_boost = agreement * 0.2

    # Penalty if few features detected
    detection_score = min(len(cv_result.walls) / 10, 1.0) * 0.3
    detection_score += min(len(cv_result.rooms) / 5, 1.0) * 0.2

    confidence = cv_confidence * 0.5 + agreement_boost + detection_score

    return min(max(confidence, 0.1), 0.95)


def _save_fusion_debug(
    result: ParseResult,
    vlm_result: VLMParseResult,
    cv_result: CVParseResult,
    debug_dir: str,
):
    """Save fusion debug information."""
    import json

    os.makedirs(debug_dir, exist_ok=True)

    debug_info = {
        "parsing_method": result.parsing_method,
        "confidence": result.confidence,
        "vlm_cv_agreement": result.vlm_cv_agreement,
        "scale": {
            "pixels_per_meter": result.scale.pixels_per_meter,
            "method": result.scale.method,
            "confidence": result.scale.confidence,
        },
        "counts": {
            "walls": len(result.walls),
            "rooms": len(result.rooms),
            "openings": len(result.openings),
        },
        "vlm_counts": {
            "rooms": vlm_result.room_count,
            "walls_estimate": vlm_result.wall_count_estimate,
        },
        "cv_counts": {
            "walls": len(cv_result.walls),
            "rooms": len(cv_result.rooms),
            "openings": len(cv_result.openings),
        },
        "building_shape": result.building_shape,
    }

    with open(os.path.join(debug_dir, "fusion_debug.json"), "w") as f:
        json.dump(debug_info, f, indent=2)
