"""
Geometry models - wall graph, junctions, and structural classification.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

from .parsing import Point2D, WallSegment, Room


class Junction(BaseModel):
    """A junction point where walls meet."""

    id: str = Field(..., description="Unique identifier for this junction")
    position: Point2D = Field(..., description="Position of the junction")
    type: Literal["L", "T", "X", "endpoint"] = Field(
        ..., description="Junction type based on connected walls"
    )
    connected_wall_ids: list[str] = Field(
        default_factory=list, description="IDs of walls connected at this junction"
    )


class ClassifiedWall(BaseModel):
    """A wall with structural classification."""

    wall: WallSegment = Field(..., description="The underlying wall segment")
    classification: Literal["load_bearing", "partition", "structural_spine"] = Field(
        ..., description="Structural classification of the wall"
    )
    reason: str = Field(..., description="Explanation for the classification")
    load_path_continuous: bool = Field(
        default=False,
        description="Whether wall is part of continuous load path to foundation",
    )
    adjacent_rooms: list[str] = Field(
        default_factory=list, description="IDs of rooms adjacent to this wall"
    )
    adjacent_room_types: list[str] = Field(
        default_factory=list, description="Types of rooms adjacent to this wall"
    )
    confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Confidence in classification"
    )


class GeometryResult(BaseModel):
    """Complete geometry analysis result."""

    junctions: list[Junction] = Field(
        default_factory=list, description="All detected wall junctions"
    )
    classified_walls: list[ClassifiedWall] = Field(
        default_factory=list, description="All walls with structural classification"
    )
    room_polygons: list[Room] = Field(
        default_factory=list, description="Room polygons with computed properties"
    )
    structural_spines: list[list[str]] = Field(
        default_factory=list, description="Lists of wall IDs forming structural spines"
    )
    building_footprint: list[Point2D] = Field(
        default_factory=list, description="Building exterior footprint polygon"
    )
    total_wall_length_m: float = Field(
        default=0.0, description="Total length of all walls in meters"
    )
    exterior_wall_length_m: float = Field(
        default=0.0, description="Total length of exterior walls in meters"
    )
    interior_wall_length_m: float = Field(
        default=0.0, description="Total length of interior walls in meters"
    )
    load_bearing_wall_count: int = Field(
        default=0, description="Number of load-bearing walls"
    )
    partition_wall_count: int = Field(
        default=0, description="Number of partition walls"
    )
