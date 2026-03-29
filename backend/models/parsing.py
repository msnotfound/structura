"""
Parsing models - contracts for floor plan parsing stages.
VLM (Vision Language Model) + CV (Computer Vision) fusion.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Point2D(BaseModel):
    """A 2D point in pixel or meter coordinates."""

    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class WallSegment(BaseModel):
    """A detected wall segment from floor plan parsing."""

    id: str = Field(..., description="Unique identifier for this wall")
    start: Point2D = Field(..., description="Start point of wall segment")
    end: Point2D = Field(..., description="End point of wall segment")
    thickness_px: float = Field(..., description="Wall thickness in pixels")
    thickness_m: float = Field(default=0.15, description="Wall thickness in meters")
    length_m: float = Field(..., description="Wall length in meters")
    is_exterior: bool = Field(
        default=False, description="Whether this is an exterior wall"
    )
    source: Literal["cv", "vlm", "manual"] = Field(
        default="cv", description="Source of this wall detection"
    )


class Opening(BaseModel):
    """A door or window opening in a wall."""

    id: str = Field(..., description="Unique identifier for this opening")
    position: Point2D = Field(..., description="Center position of the opening")
    width_m: float = Field(..., description="Width of opening in meters")
    height_m: float = Field(default=2.1, description="Height of opening in meters")
    type: Literal["door", "window"] = Field(..., description="Type of opening")
    parent_wall_id: Optional[str] = Field(
        default=None, description="ID of the wall containing this opening"
    )


class Room(BaseModel):
    """A detected room from floor plan parsing."""

    id: str = Field(..., description="Unique identifier for this room")
    label: str = Field(..., description="Human-readable room label")
    vertices: list[Point2D] = Field(
        ..., description="Polygon vertices defining room boundary"
    )
    area_m2: float = Field(..., description="Room area in square meters")
    room_type: Literal[
        "bedroom",
        "bathroom",
        "kitchen",
        "living",
        "laundry",
        "foyer",
        "closet",
        "hallway",
        "dining",
        "great_room",
        "other",
    ] = Field(default="other", description="Classified room type")
    centroid: Optional[Point2D] = Field(
        default=None, description="Room centroid for labeling"
    )


class ScaleReference(BaseModel):
    """Scale calibration data for converting pixels to meters."""

    pixels_per_meter: float = Field(
        ..., description="Conversion factor from pixels to meters"
    )
    reference_dimension_m: float = Field(
        default=0.9,
        description="Reference dimension used for calibration (e.g., door width)",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in scale accuracy"
    )
    method: Literal["scale_bar", "door_width", "vlm_estimate", "default"] = Field(
        default="default", description="Method used to determine scale"
    )


class VLMParseResult(BaseModel):
    """Result from Vision Language Model parsing."""

    rooms: list[dict] = Field(
        default_factory=list,
        description="Rooms detected by VLM with labels and approximate locations",
    )
    building_shape: Literal[
        "rectangular", "L-shaped", "U-shaped", "irregular", "unknown"
    ] = Field(default="unknown", description="Overall building footprint shape")
    estimated_scale: Optional[float] = Field(
        default=None, description="VLM's estimate of pixels per meter"
    )
    room_count: int = Field(default=0, description="Number of rooms detected")
    wall_count_estimate: int = Field(default=0, description="Estimated wall count")
    notes: list[str] = Field(
        default_factory=list, description="Additional observations from VLM"
    )
    raw_response: Optional[str] = Field(
        default=None, description="Raw VLM response for debugging"
    )


class CVParseResult(BaseModel):
    """Result from Computer Vision parsing."""

    walls: list[WallSegment] = Field(
        default_factory=list, description="Detected wall segments"
    )
    rooms: list[Room] = Field(default_factory=list, description="Detected rooms")
    openings: list[Opening] = Field(
        default_factory=list, description="Detected openings"
    )
    scale: ScaleReference = Field(..., description="Scale calibration data")
    building_outline: list[Point2D] = Field(
        default_factory=list, description="Exterior building boundary polygon"
    )


class ParseResult(BaseModel):
    """Fused result from VLM + CV parsing."""

    walls: list[WallSegment] = Field(
        default_factory=list, description="All detected walls"
    )
    rooms: list[Room] = Field(default_factory=list, description="All detected rooms")
    openings: list[Opening] = Field(
        default_factory=list, description="All detected openings"
    )
    scale: ScaleReference = Field(..., description="Final scale calibration")
    image_dims: tuple[int, int] = Field(
        ..., description="Original image dimensions (width, height)"
    )
    building_outline: list[Point2D] = Field(
        default_factory=list, description="Building footprint polygon"
    )
    building_shape: Literal[
        "rectangular", "L-shaped", "U-shaped", "irregular", "unknown"
    ] = Field(default="unknown", description="Building footprint shape classification")
    fallback_used: bool = Field(
        default=False, description="Whether fallback parsing was used"
    )
    parsing_method: Literal["vlm_cv_fusion", "cv_only", "vlm_only", "manual"] = Field(
        default="vlm_cv_fusion", description="Method used for final parsing"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Overall confidence in parse result"
    )
    vlm_cv_agreement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agreement score between VLM and CV results",
    )
