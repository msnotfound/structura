"""
Beam & Column Design Calculator — IS 456:2000 (Indian Standard)

Calculates RCC beam and column dimensions, reinforcement, and loads
using standard civil engineering formulas.

References:
- IS 456:2000 — Plain and Reinforced Concrete Code of Practice
- IS 875 (Part 1-3) — Code of Practice for Design Loads
- SP 16 — Design Aids for Reinforced Concrete (IS 456)
"""

import math
from typing import Optional, List
from pydantic import BaseModel, Field


class BeamDesign(BaseModel):
    """Complete beam design output per IS 456:2000."""
    beam_id: str
    span_m: float = Field(..., description="Clear span in meters")
    width_mm: float = Field(..., description="Beam width in mm")
    depth_mm: float = Field(..., description="Overall beam depth in mm")
    effective_depth_mm: float = Field(..., description="Effective depth d in mm")
    clear_cover_mm: float = Field(default=25, description="Clear cover per IS 456")

    # Loads
    dead_load_kn_per_m: float = Field(..., description="Dead load (self-weight + slab)")
    live_load_kn_per_m: float = Field(..., description="Live load per IS 875")
    total_factored_load_kn_per_m: float = Field(..., description="Wu = 1.5 * (DL + LL)")

    # Bending
    max_bending_moment_knm: float = Field(..., description="Mu = Wu*L²/8")
    moment_of_resistance_knm: float = Field(..., description="Mu_lim from IS 456")

    # Reinforcement
    steel_grade: str = Field(default="Fe500", description="Reinforcement grade")
    concrete_grade: str = Field(default="M25", description="Concrete grade")
    tension_steel_area_mm2: float = Field(..., description="Ast required")
    tension_bars: str = Field(..., description="e.g. '3-16mm φ'")
    compression_steel_area_mm2: float = Field(default=0, description="Asc if doubly reinforced")

    # Shear
    max_shear_force_kn: float = Field(..., description="Vu = Wu*L/2")
    nominal_shear_stress_mpa: float = Field(..., description="τv = Vu / (b*d)")
    shear_capacity_mpa: float = Field(..., description="τc from IS 456 Table 19")
    stirrup_diameter_mm: float = Field(default=8, description="Stirrup bar diameter")
    stirrup_spacing_mm: float = Field(..., description="Sv per IS 456 cl. 26.5.1.6")
    stirrup_description: str = Field(..., description="e.g. '8mm φ @ 150mm c/c'")

    # Deflection
    span_depth_ratio: float = Field(..., description="L/d ratio")
    max_allowed_ratio: float = Field(default=20, description="IS 456 cl. 23.2.1")
    deflection_ok: bool = Field(default=True, description="Whether deflection check passes")

    # Position
    start_x: float = Field(default=0)
    start_y: float = Field(default=0)
    start_z: float = Field(default=0)
    end_x: float = Field(default=0)
    end_y: float = Field(default=0)
    end_z: float = Field(default=0)

    # Classification
    beam_type: str = Field(default="simply_supported", description="simply_supported or continuous")
    support_type: str = Field(default="wall", description="wall or column")
    room_id: Optional[str] = Field(default=None)


class ColumnDesign(BaseModel):
    """Column design output per IS 456:2000."""
    column_id: str
    position_x: float
    position_y: float  # elevation
    position_z: float
    width_mm: float = Field(default=230, description="Column width")
    depth_mm: float = Field(default=230, description="Column depth")
    height_m: float = Field(default=2.8, description="Column height")
    axial_load_kn: float = Field(..., description="Factored axial load")
    concrete_grade: str = Field(default="M25")
    steel_grade: str = Field(default="Fe500")
    steel_area_mm2: float = Field(..., description="Longitudinal steel area")
    steel_bars: str = Field(..., description="e.g. '4-12mm φ'")
    tie_spacing_mm: float = Field(..., description="Lateral tie spacing")
    load_ratio: float = Field(..., description="Pu / Pu_capacity")
    junction_id: Optional[str] = Field(default=None)


class SlabDesign(BaseModel):
    """Slab design per IS 456:2000."""
    slab_id: str
    room_id: str
    slab_type: str = Field(..., description="one_way or two_way")
    shorter_span_m: float
    longer_span_m: float
    aspect_ratio: float = Field(..., description="Ly/Lx — >2 = one-way")
    thickness_mm: float = Field(..., description="Slab thickness")
    main_bar_diameter_mm: float
    main_bar_spacing_mm: float
    distribution_bar_diameter_mm: float
    distribution_bar_spacing_mm: float
    dead_load_kn_per_m2: float
    live_load_kn_per_m2: float
    total_load_kn_per_m2: float


class BeamCalculator:
    """
    IS 456:2000 compliant beam, column, and slab design calculator.

    Standard material properties used:
    - M25 concrete: fck = 25 MPa
    - Fe500 steel: fy = 500 MPa
    - Clear cover: 25mm (beams), 40mm (columns)
    """

    def __init__(self):
        # Default material properties (IS 456:2000)
        self.fck = 25.0       # M25 concrete, N/mm²
        self.fy = 500.0       # Fe500 steel, N/mm²
        self.clear_cover = 25  # mm (beams)
        self.col_cover = 40    # mm (columns)

        # Load factors (IS 456 cl. 36.4.1)
        self.gamma_f = 1.5     # Load factor for DL + LL

        # IS 875 loads
        self.live_load_residential = 2.0  # kN/m² (Part 2, Table 1)
        self.live_load_commercial = 3.0   # kN/m²
        self.floor_finish_load = 1.0      # kN/m²
        self.partition_load = 1.0         # kN/m²

        # Concrete density
        self.concrete_density = 25.0  # kN/m³

        # Xu_max/d for Fe500 (IS 456 cl. 38.1, Table F)
        self.xu_max_ratio = 0.46

    def design_beam(
        self,
        beam_id: str,
        span_m: float,
        tributary_width_m: float = 3.0,
        slab_thickness_mm: float = 125,
        beam_type: str = "simply_supported",
        support_type: str = "wall",
        start_pos: tuple = (0, 0, 0),
        end_pos: tuple = (0, 0, 0),
        room_id: Optional[str] = None,
    ) -> BeamDesign:
        """
        Design an RCC beam per IS 456:2000.

        Steps:
        1. Assume beam size (depth = span/12, width = depth/2)
        2. Calculate loads (dead + live + factored)
        3. Calculate bending moment (M = wl²/8)
        4. Calculate required Ast
        5. Design shear reinforcement
        6. Check deflection (L/d ratio)
        """
        # Step 1: Preliminary beam dimensions
        if beam_type == "simply_supported":
            depth_mm = max(200, math.ceil(span_m * 1000 / 12 / 25) * 25)  # span/12, rounded to 25mm
        else:  # continuous
            depth_mm = max(200, math.ceil(span_m * 1000 / 15 / 25) * 25)

        width_mm = max(200, math.ceil(depth_mm / 2 / 25) * 25)  # typically d/2
        # Minimum width per IS 456 for fire resistance
        width_mm = max(width_mm, 200)

        effective_depth = depth_mm - self.clear_cover - 10  # assuming 20mm bar, d = D - cover - φ/2

        # Step 2: Load calculation
        # Self-weight of beam
        beam_self_weight = (width_mm / 1000) * (depth_mm / 1000) * self.concrete_density  # kN/m

        # Slab load transferred to beam
        slab_dead_load = (slab_thickness_mm / 1000) * self.concrete_density * tributary_width_m  # kN/m
        floor_finish = self.floor_finish_load * tributary_width_m  # kN/m
        partition = self.partition_load * tributary_width_m  # kN/m

        dead_load = beam_self_weight + slab_dead_load + floor_finish + partition  # kN/m
        live_load = self.live_load_residential * tributary_width_m  # kN/m

        total_service_load = dead_load + live_load
        factored_load = self.gamma_f * total_service_load  # Wu

        # Step 3: Bending moment
        if beam_type == "simply_supported":
            Mu = factored_load * span_m**2 / 8  # kN·m
        else:
            Mu = factored_load * span_m**2 / 10  # continuous beam negative moment

        # Step 4: Check if singly reinforced is sufficient
        # Mu_lim = 0.36 * fck * b * xu_max * (d - 0.42*xu_max)
        xu_max = self.xu_max_ratio * effective_depth  # mm
        Mu_lim = 0.36 * self.fck * width_mm * xu_max * (effective_depth - 0.42 * xu_max) / 1e6  # kN·m

        # Calculate required steel area
        if Mu <= Mu_lim:
            # Singly reinforced beam
            # Mu = 0.87 * fy * Ast * (d - 0.42*xu)
            # Simplified: Ast = Mu / (0.87 * fy * lever_arm)
            # Using quadratic formula from IS 456 Annex G
            Ast = self._calc_ast_singly(Mu * 1e6, width_mm, effective_depth)
            Asc = 0
        else:
            # Doubly reinforced (beam too shallow for moment)
            Ast = self._calc_ast_singly(Mu_lim * 1e6, width_mm, effective_depth)
            excess_moment = (Mu - Mu_lim) * 1e6
            Asc = excess_moment / (0.87 * self.fy * (effective_depth - self.clear_cover))
            Ast += Asc
            Asc = max(Asc, 0)

        # Minimum steel (IS 456 cl. 26.5.1.1)
        Ast_min = 0.85 * width_mm * effective_depth / self.fy
        Ast = max(Ast, Ast_min)

        # Select bars
        tension_bars = self._select_bars(Ast)

        # Step 5: Shear design
        Vu = factored_load * span_m / 2  # kN
        tau_v = Vu * 1000 / (width_mm * effective_depth)  # N/mm² = MPa

        # Shear capacity of concrete (IS 456 Table 19, approximate for pt~1%)
        pt = 100 * Ast / (width_mm * effective_depth)
        tau_c = self._shear_capacity(pt)

        # Stirrup design
        if tau_v > tau_c:
            Vus = (tau_v - tau_c) * width_mm * effective_depth / 1000  # kN
            Asv = 2 * math.pi * (8/2)**2 / 4  # 2-legged 8mm stirrup = 100.53 mm²
            Sv = 0.87 * self.fy * Asv * effective_depth / (Vus * 1000)
            Sv = min(Sv, 0.75 * effective_depth, 300)  # IS 456 cl. 26.5.1.5
        else:
            # Minimum shear reinforcement
            Asv = 2 * math.pi * (8/2)**2 / 4
            Sv = 0.87 * self.fy * Asv / (0.4 * width_mm)
            Sv = min(Sv, 0.75 * effective_depth, 300)

        Sv = max(50, math.floor(Sv / 25) * 25)  # Round down to 25mm

        # Step 6: Deflection check
        span_depth = (span_m * 1000) / effective_depth
        max_ratio = 20 if beam_type == "simply_supported" else 26
        deflection_ok = span_depth <= max_ratio * 1.3  # 1.3 modification factor for tension steel

        return BeamDesign(
            beam_id=beam_id,
            span_m=span_m,
            width_mm=width_mm,
            depth_mm=depth_mm,
            effective_depth_mm=effective_depth,
            dead_load_kn_per_m=round(dead_load, 2),
            live_load_kn_per_m=round(live_load, 2),
            total_factored_load_kn_per_m=round(factored_load, 2),
            max_bending_moment_knm=round(Mu, 2),
            moment_of_resistance_knm=round(Mu_lim, 2),
            steel_grade=f"Fe{int(self.fy)}",
            concrete_grade=f"M{int(self.fck)}",
            tension_steel_area_mm2=round(Ast, 1),
            tension_bars=tension_bars,
            compression_steel_area_mm2=round(Asc, 1),
            max_shear_force_kn=round(Vu, 2),
            nominal_shear_stress_mpa=round(tau_v, 3),
            shear_capacity_mpa=round(tau_c, 3),
            stirrup_diameter_mm=8,
            stirrup_spacing_mm=Sv,
            stirrup_description=f"8mm φ @ {int(Sv)}mm c/c",
            span_depth_ratio=round(span_depth, 1),
            max_allowed_ratio=max_ratio,
            deflection_ok=deflection_ok,
            start_x=start_pos[0], start_y=start_pos[1], start_z=start_pos[2],
            end_x=end_pos[0], end_y=end_pos[1], end_z=end_pos[2],
            beam_type=beam_type,
            support_type=support_type,
            room_id=room_id,
        )

    def design_column(
        self,
        column_id: str,
        axial_load_kn: float,
        height_m: float = 2.8,
        position: tuple = (0, 0, 0),
        junction_id: Optional[str] = None,
    ) -> ColumnDesign:
        """
        Design a short column per IS 456:2000 cl. 39.3.

        Pu = 0.4*fck*Ac + 0.67*fy*Asc
        """
        # Start with minimum column size 230x230mm
        b = 230  # mm
        D = 230  # mm

        # IS 456 cl. 39.3: Pu = 0.4*fck*Ac + 0.67*fy*Asc
        # Assume 1% steel initially
        Ag = b * D  # mm²
        Asc = 0.01 * Ag  # 1% steel
        Ac = Ag - Asc

        capacity = (0.4 * self.fck * Ac + 0.67 * self.fy * Asc) / 1000  # kN

        # If load exceeds capacity, increase column size
        while capacity < axial_load_kn and b <= 600:
            b += 25
            D += 25
            Ag = b * D
            Asc = 0.01 * Ag
            Ac = Ag - Asc
            capacity = (0.4 * self.fck * Ac + 0.67 * self.fy * Asc) / 1000

        # Calculate actual steel area required
        # Asc = (Pu - 0.4*fck*b*D) / (0.67*fy - 0.4*fck)
        Asc_req = max(
            (axial_load_kn * 1000 - 0.4 * self.fck * b * D) /
            (0.67 * self.fy - 0.4 * self.fck),
            0.008 * b * D  # Minimum 0.8% (IS 456 cl. 26.5.3.1)
        )
        Asc_req = min(Asc_req, 0.06 * b * D)  # Maximum 6%

        bars = self._select_bars(Asc_req, min_dia=12)

        # Lateral ties (IS 456 cl. 26.5.3.2)
        tie_spacing = min(b, 16 * 12, 300)  # least of: column width, 16*bar_dia, 300mm

        load_ratio = axial_load_kn / max(capacity, 1)

        return ColumnDesign(
            column_id=column_id,
            position_x=position[0],
            position_y=position[1],
            position_z=position[2],
            width_mm=b,
            depth_mm=D,
            height_m=height_m,
            axial_load_kn=round(axial_load_kn, 1),
            steel_area_mm2=round(Asc_req, 1),
            steel_bars=bars,
            tie_spacing_mm=tie_spacing,
            load_ratio=round(load_ratio, 2),
            junction_id=junction_id,
        )

    def design_slab(
        self,
        slab_id: str,
        room_id: str,
        lx_m: float,
        ly_m: float,
    ) -> SlabDesign:
        """
        Design RCC slab per IS 456:2000.
        - Ly/Lx > 2: one-way slab
        - Ly/Lx <= 2: two-way slab
        """
        shorter = min(lx_m, ly_m)
        longer = max(lx_m, ly_m)
        aspect = longer / max(shorter, 0.1)
        slab_type = "one_way" if aspect > 2 else "two_way"

        # Slab thickness: span/28 for simply supported, span/32 for continuous
        thickness = max(100, math.ceil(shorter * 1000 / 28 / 5) * 5)  # round to 5mm

        # Loads
        self_weight = (thickness / 1000) * self.concrete_density  # kN/m²
        dead_load = self_weight + self.floor_finish_load + self.partition_load
        live_load = self.live_load_residential
        factored_load = self.gamma_f * (dead_load + live_load)

        # Effective depth
        d = thickness - self.clear_cover - 5  # 10mm bar, d = D - cover - φ/2

        # Bending moment (IS 456 Table 26 for two-way, wl²/8 for one-way)
        if slab_type == "one_way":
            Mu = factored_load * shorter**2 / 8  # kN·m per meter width
        else:
            # Two-way slab: α * w * lx² (simplified)
            alpha = 0.056  # approximate coefficient for two-way slab
            Mu = alpha * factored_load * shorter**2

        # Main bar design
        Ast = self._calc_ast_singly(Mu * 1e6, 1000, d)
        Ast_min = 0.12 * 1000 * thickness / 100  # IS 456 cl. 26.5.2.1 (0.12% for Fe500)
        Ast = max(Ast, Ast_min)

        # Select main bar spacing
        main_dia = 10 if Ast < 300 else 12
        bar_area = math.pi * (main_dia / 2) ** 2
        spacing = min(math.floor(1000 * bar_area / Ast), 3 * thickness, 300)
        spacing = max(50, math.floor(spacing / 5) * 5)

        # Distribution bars: 0.12% of gross area
        dist_Ast = 0.12 * 1000 * thickness / 100
        dist_dia = 8
        dist_bar_area = math.pi * (dist_dia / 2) ** 2
        dist_spacing = min(math.floor(1000 * dist_bar_area / dist_Ast), 5 * thickness, 450)
        dist_spacing = max(50, math.floor(dist_spacing / 5) * 5)

        return SlabDesign(
            slab_id=slab_id,
            room_id=room_id,
            slab_type=slab_type,
            shorter_span_m=round(shorter, 2),
            longer_span_m=round(longer, 2),
            aspect_ratio=round(aspect, 2),
            thickness_mm=thickness,
            main_bar_diameter_mm=main_dia,
            main_bar_spacing_mm=spacing,
            distribution_bar_diameter_mm=dist_dia,
            distribution_bar_spacing_mm=dist_spacing,
            dead_load_kn_per_m2=round(dead_load, 2),
            live_load_kn_per_m2=round(live_load, 2),
            total_load_kn_per_m2=round(factored_load, 2),
        )

    def _calc_ast_singly(self, Mu_nmm: float, b: float, d: float) -> float:
        """Calculate Ast for singly reinforced section (IS 456 Annex G)."""
        # Mu = 0.87*fy*Ast*d*(1 - Ast*fy/(b*d*fck))
        # Rearranging: Ast² - (b*d*fck/fy)*Ast + (Mu/(0.87*fy*d)*b*d*fck/fy) = 0
        # Or: x² - px + q = 0
        fck = self.fck
        fy = self.fy

        # Alternative formula: Ast = (0.5*fck/fy) * (1 - sqrt(1 - 4.6*Mu/(fck*b*d²))) * b * d
        discriminant = 1 - 4.6 * Mu_nmm / (fck * b * d**2)
        if discriminant < 0:
            # Section insufficient, use Mu_lim Ast
            discriminant = 0

        Ast = (0.5 * fck / fy) * (1 - math.sqrt(discriminant)) * b * d
        return max(Ast, 0)

    def _select_bars(self, Ast: float, min_dia: int = 12) -> str:
        """Select bar combination for given steel area."""
        bar_diameters = [12, 16, 20, 25, 32]

        for dia in bar_diameters:
            if dia < min_dia:
                continue
            area_per_bar = math.pi * (dia / 2) ** 2
            num_bars = math.ceil(Ast / area_per_bar)
            if num_bars <= 6:
                return f"{num_bars}-{dia}mm φ"

        # Fallback: use 25mm bars
        area_per_bar = math.pi * (25 / 2) ** 2
        num_bars = math.ceil(Ast / area_per_bar)
        return f"{num_bars}-25mm φ"

    def _shear_capacity(self, pt: float) -> float:
        """
        Shear capacity of concrete (τc) per IS 456 Table 19.
        For M25 concrete.
        """
        # Interpolated values from Table 19 for M25
        table = [
            (0.15, 0.29), (0.25, 0.36), (0.50, 0.49),
            (0.75, 0.57), (1.00, 0.64), (1.25, 0.70),
            (1.50, 0.75), (1.75, 0.79), (2.00, 0.82),
            (2.25, 0.85), (2.50, 0.88), (2.75, 0.90),
            (3.00, 0.92),
        ]

        pt = max(0.15, min(pt, 3.0))

        # Linear interpolation
        for i in range(len(table) - 1):
            if table[i][0] <= pt <= table[i + 1][0]:
                x1, y1 = table[i]
                x2, y2 = table[i + 1]
                return y1 + (y2 - y1) * (pt - x1) / (x2 - x1)

        return table[-1][1]
