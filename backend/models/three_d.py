"""
3D extrusion models - for Three.js visualization.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

from .parsing import Point2D, Opening
from .structural import StructuralWarning


class Point3D(BaseModel):
    """A 3D point."""

    x: float
    y: float
    z: float

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


class Face(BaseModel):
    """A face defined by vertex indices."""

    vertices: list[int] = Field(..., description="Indices into the vertices array")
    normal: Optional[Point3D] = Field(default=None, description="Face normal vector")


class ExtrudedWall(BaseModel):
    """A 3D extruded wall for visualization."""

    wall_id: str = Field(..., description="ID of the source wall")
    vertices_3d: list[Point3D] = Field(
        default_factory=list, description="3D vertices of the wall geometry"
    )
    faces: list[Face] = Field(
        default_factory=list, description="Faces of the wall geometry"
    )
    classification: Literal["load_bearing", "partition", "structural_spine"] = Field(
        ..., description="Structural classification"
    )
    thickness_m: float = Field(..., description="Wall thickness in meters")
    height_m: float = Field(default=2.8, description="Wall height in meters")
    openings: list[Opening] = Field(
        default_factory=list, description="Openings in this wall"
    )
    color: str = Field(default="#808080", description="Color for visualization (hex)")
    is_exterior: bool = Field(
        default=False, description="Whether this is an exterior wall"
    )


class Slab(BaseModel):
    """A floor or ceiling slab."""

    id: str = Field(..., description="Unique identifier")
    vertices_3d: list[Point3D] = Field(..., description="3D vertices of slab boundary")
    elevation: float = Field(..., description="Elevation of the slab in meters")
    type: Literal["floor", "ceiling", "roof"] = Field(..., description="Type of slab")
    thickness_m: float = Field(default=0.15, description="Slab thickness")
    room_id: Optional[str] = Field(default=None, description="Associated room ID")


class RoomLabel3D(BaseModel):
    """3D room label for visualization."""

    room_id: str = Field(..., description="ID of the room")
    label: str = Field(..., description="Room label text")
    position: Point3D = Field(..., description="3D position for the label")
    area_m2: float = Field(..., description="Room area for display")
    room_type: str = Field(..., description="Room type")


class CameraBounds(BaseModel):
    """Camera bounds for the 3D scene."""

    min: Point3D = Field(..., description="Minimum bounds")
    max: Point3D = Field(..., description="Maximum bounds")
    center: Point3D = Field(..., description="Center of the scene")
    recommended_distance: float = Field(
        ..., description="Recommended camera distance for full view"
    )


class SceneGraph(BaseModel):
    """Complete 3D scene for Three.js visualization."""

    walls: list[ExtrudedWall] = Field(
        default_factory=list, description="All extruded walls"
    )
    slabs: list[Slab] = Field(
        default_factory=list, description="Floor and ceiling slabs"
    )
    room_labels: list[RoomLabel3D] = Field(
        default_factory=list, description="3D room labels"
    )
    warnings: list[StructuralWarning] = Field(
        default_factory=list, description="Structural warnings for visualization"
    )
    camera_bounds: CameraBounds = Field(..., description="Camera positioning bounds")
    floor_height_m: float = Field(default=2.8, description="Floor-to-floor height")
    num_floors: int = Field(default=1, description="Number of floors")
    total_height_m: float = Field(default=2.8, description="Total building height")
