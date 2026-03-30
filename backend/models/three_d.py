"""
3D extrusion models - for Three.js visualization.
Includes walls, beams, columns, slabs, and room labels.
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
    vertices_3d: list[Point3D] = Field(default_factory=list)
    faces: list[Face] = Field(default_factory=list)
    classification: Literal["load_bearing", "partition", "structural_spine"] = Field(...)
    thickness_m: float = Field(...)
    height_m: float = Field(default=2.8)
    openings: list[Opening] = Field(default_factory=list)
    color: str = Field(default="#808080")
    is_exterior: bool = Field(default=False)


class Beam3D(BaseModel):
    """A 3D beam element for visualization."""
    beam_id: str
    start: Point3D
    end: Point3D
    width_m: float = Field(..., description="Beam width in meters")
    depth_m: float = Field(..., description="Beam depth in meters")
    span_m: float = Field(..., description="Clear span")

    # Engineering data (IS 456)
    steel_area_mm2: float = Field(default=0, description="Tension steel area")
    tension_bars: str = Field(default="", description="e.g. '3-16mm φ'")
    stirrup_spacing_mm: float = Field(default=150, description="Stirrup spacing")
    stirrup_description: str = Field(default="")
    concrete_grade: str = Field(default="M25")
    steel_grade: str = Field(default="Fe500")

    # Load data
    total_load_kn_per_m: float = Field(default=0)
    max_bending_moment_knm: float = Field(default=0)
    max_shear_force_kn: float = Field(default=0)
    deflection_ok: bool = Field(default=True)

    color: str = Field(default="#3b82f6")
    room_id: Optional[str] = Field(default=None)


class Column3D(BaseModel):
    """A 3D column element for visualization."""
    column_id: str
    position: Point3D
    width_m: float = Field(default=0.23)
    depth_m: float = Field(default=0.23)
    height_m: float = Field(default=2.8)

    # Engineering data
    axial_load_kn: float = Field(default=0)
    steel_area_mm2: float = Field(default=0)
    steel_bars: str = Field(default="")
    tie_spacing_mm: float = Field(default=150)
    load_ratio: float = Field(default=0)

    color: str = Field(default="#f59e0b")
    junction_id: Optional[str] = Field(default=None)


class Slab(BaseModel):
    """A floor or ceiling slab."""
    id: str = Field(..., description="Unique identifier")
    vertices_3d: list[Point3D] = Field(...)
    elevation: float = Field(...)
    type: Literal["floor", "ceiling", "roof"] = Field(...)
    thickness_m: float = Field(default=0.15)
    room_id: Optional[str] = Field(default=None)


class RoomLabel3D(BaseModel):
    """3D room label for visualization."""
    room_id: str
    label: str
    position: Point3D
    area_m2: float
    room_type: str


class CameraBounds(BaseModel):
    """Camera bounds for the 3D scene."""
    min: Point3D
    max: Point3D
    center: Point3D
    recommended_distance: float


class SceneGraph(BaseModel):
    """Complete 3D scene for Three.js visualization."""
    walls: list[ExtrudedWall] = Field(default_factory=list)
    beams: list[Beam3D] = Field(default_factory=list, description="RCC beams")
    columns: list[Column3D] = Field(default_factory=list, description="RCC columns")
    slabs: list[Slab] = Field(default_factory=list)
    room_labels: list[RoomLabel3D] = Field(default_factory=list)
    warnings: list[StructuralWarning] = Field(default_factory=list)
    camera_bounds: CameraBounds = Field(...)
    floor_height_m: float = Field(default=2.8)
    num_floors: int = Field(default=1)
    total_height_m: float = Field(default=2.8)
