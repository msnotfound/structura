"""
Cost estimation engine — comprehensive Indian construction cost model.

Uses CPWD-based rates and includes ALL construction categories:
Foundation, Structure (RCC), Masonry, Plastering, Flooring,
Painting, Electrical, Plumbing, Doors/Windows, Finishing.
"""

import os
import json
from typing import Optional, List

from models.parsing import ParseResult
from models.geometry import GeometryResult
from models.materials import MaterialsResult
from models.cost import (
    CostLineItem,
    RoomCost,
    CategoryCost,
    ProjectCost,
    CostComparison,
)


class CostEngine:
    """Comprehensive construction cost estimation for Indian residential buildings."""

    def __init__(self):
        self.wall_height = 2.8  # meters
        self.labor_multiplier = 1.35  # 35% labor on materials

        # Real-world Indian construction rates (INR, 2025-26)
        self.rates = {
            # Foundation
            "excavation_per_cum": 350,
            "pcc_per_cum": 5500,
            "rcc_footing_per_cum": 9000,
            "foundation_depth_m": 1.2,
            "foundation_width_m": 0.6,

            # RCC Structure
            "rcc_beam_per_cum": 9500,
            "rcc_column_per_cum": 10000,
            "rcc_slab_per_cum": 9000,
            "rcc_lintel_per_cum": 8000,
            "steel_per_kg": 72,
            "slab_thickness_m": 0.125,

            # Masonry
            "brick_wall_9inch_per_cum": 7500,
            "brick_wall_4inch_per_sqm": 700,
            "aac_block_per_cum": 5000,

            # Plastering
            "internal_plaster_per_sqm": 350,
            "external_plaster_per_sqm": 480,

            # Flooring
            "vitrified_tiles_per_sqm": 950,
            "ceramic_tiles_per_sqm": 650,
            "granite_per_sqm": 1650,
            "bathroom_tiles_per_sqm": 800,

            # Painting
            "interior_paint_per_sqm": 200,
            "exterior_paint_per_sqm": 280,

            # Electrical
            "wiring_per_point": 2200,
            "points_per_room": {"bedroom": 6, "living": 8, "kitchen": 6,
                                "bathroom": 3, "toilet": 3, "hall": 8,
                                "dining": 5, "pooja": 2, "other": 4},
            "main_panel": 12000,

            # Plumbing
            "water_point": 4000,
            "drainage_point": 4500,
            "bathroom_fitting_set": 30000,
            "kitchen_sink": 8000,

            # Doors & Windows
            "main_door": 40000,
            "internal_door": 10000,
            "bathroom_door": 7000,
            "window_per_sqft": 550,
            "avg_window_sqft": 15,

            # Overhead & Finishing
            "waterproofing_per_sqm": 200,
            "contingency_percent": 8,
            "architect_percent": 3,
        }

    def estimate(
        self,
        parse_result: ParseResult,
        geometry_result: GeometryResult,
        materials_result: MaterialsResult,
        debug_dir: Optional[str] = None,
    ) -> ProjectCost:
        """Generate comprehensive cost estimation."""
        line_items = []
        total_floor_area = sum(r.area_m2 for r in parse_result.rooms)

        # Ensure minimum realistic area
        if total_floor_area < 10:
            # Scale correction fallback
            total_floor_area = max(total_floor_area * 100, 50)  # assume at least 50 sqm

        total_wall_length = sum(cw.wall.length_m for cw in geometry_result.classified_walls)
        exterior_wall_length = sum(
            cw.wall.length_m for cw in geometry_result.classified_walls if cw.wall.is_exterior
        )
        interior_wall_length = total_wall_length - exterior_wall_length

        num_rooms = len(parse_result.rooms)
        num_bathrooms = sum(1 for r in parse_result.rooms if r.room_type in ("bathroom", "toilet"))
        num_bedrooms = sum(1 for r in parse_result.rooms if r.room_type == "bedroom")
        has_kitchen = any(r.room_type == "kitchen" for r in parse_result.rooms)

        # ── 1. Foundation ──
        perimeter = exterior_wall_length if exterior_wall_length > 0 else total_wall_length * 0.6
        foundation_volume = perimeter * self.rates["foundation_depth_m"] * self.rates["foundation_width_m"]

        line_items.append(CostLineItem(
            element_id="foundation_excavation",
            element_description="Foundation excavation (1.2m deep)",
            material="Earth work",
            quantity=round(foundation_volume * 1.2, 2),
            unit="cum",
            unit_cost=self.rates["excavation_per_cum"],
            total_cost=foundation_volume * 1.2 * self.rates["excavation_per_cum"],
            category="foundation",
        ))

        line_items.append(CostLineItem(
            element_id="foundation_pcc",
            element_description="PCC 1:4:8 in foundation",
            material="M10 Concrete",
            quantity=round(perimeter * 0.6 * 0.15, 2),
            unit="cum",
            unit_cost=self.rates["pcc_per_cum"],
            total_cost=perimeter * 0.6 * 0.15 * self.rates["pcc_per_cum"],
            category="foundation",
        ))

        line_items.append(CostLineItem(
            element_id="foundation_rcc",
            element_description="RCC footing & plinth beam",
            material="M25 Concrete + Fe500",
            quantity=round(foundation_volume * 0.5, 2),
            unit="cum",
            unit_cost=self.rates["rcc_footing_per_cum"],
            total_cost=foundation_volume * 0.5 * self.rates["rcc_footing_per_cum"],
            category="foundation",
        ))

        # ── 2. RCC Structure ──
        # Slab
        slab_volume = total_floor_area * self.rates["slab_thickness_m"]
        line_items.append(CostLineItem(
            element_id="rcc_slab",
            element_description=f"RCC roof slab ({self.rates['slab_thickness_m']*1000:.0f}mm thick)",
            material="M25 Concrete + Fe500",
            quantity=round(slab_volume, 2),
            unit="cum",
            unit_cost=self.rates["rcc_slab_per_cum"],
            total_cost=slab_volume * self.rates["rcc_slab_per_cum"],
            category="rcc_structure",
        ))

        # Steel in slab (~80 kg/cum)
        slab_steel_kg = slab_volume * 80
        line_items.append(CostLineItem(
            element_id="slab_steel",
            element_description="Reinforcement steel in slab",
            material="Fe500 TMT",
            quantity=round(slab_steel_kg, 1),
            unit="kg",
            unit_cost=self.rates["steel_per_kg"],
            total_cost=slab_steel_kg * self.rates["steel_per_kg"],
            category="rcc_structure",
        ))

        # Beams (~0.2 cum per room span)
        beam_volume = num_rooms * 0.2
        line_items.append(CostLineItem(
            element_id="rcc_beams",
            element_description=f"RCC beams ({num_rooms} spans)",
            material="M25 Concrete + Fe500",
            quantity=round(beam_volume, 2),
            unit="cum",
            unit_cost=self.rates["rcc_beam_per_cum"],
            total_cost=beam_volume * self.rates["rcc_beam_per_cum"],
            category="rcc_structure",
        ))

        # Columns
        num_columns = max(4, len(geometry_result.junctions))
        col_volume = num_columns * 0.23 * 0.23 * self.wall_height  # 230x230mm
        line_items.append(CostLineItem(
            element_id="rcc_columns",
            element_description=f"RCC columns ({num_columns} nos, 230×230mm)",
            material="M25 Concrete + Fe500",
            quantity=round(col_volume, 2),
            unit="cum",
            unit_cost=self.rates["rcc_column_per_cum"],
            total_cost=col_volume * self.rates["rcc_column_per_cum"],
            category="rcc_structure",
        ))

        # Lintels
        num_openings = len(parse_result.openings) or num_rooms * 2
        lintel_volume = num_openings * 0.03  # ~0.03 cum per lintel
        line_items.append(CostLineItem(
            element_id="rcc_lintels",
            element_description=f"RCC lintels ({num_openings} nos)",
            material="M20 Concrete",
            quantity=round(lintel_volume, 2),
            unit="cum",
            unit_cost=self.rates["rcc_lintel_per_cum"],
            total_cost=lintel_volume * self.rates["rcc_lintel_per_cum"],
            category="rcc_structure",
        ))

        # ── 3. Masonry ──
        # Exterior walls (9 inch / 230mm)
        ext_wall_area = exterior_wall_length * self.wall_height
        ext_wall_volume = ext_wall_area * 0.23
        line_items.append(CostLineItem(
            element_id="masonry_exterior",
            element_description="Exterior brick wall 230mm (CM 1:4)",
            material="First class bricks",
            quantity=round(ext_wall_volume, 2),
            unit="cum",
            unit_cost=self.rates["brick_wall_9inch_per_cum"],
            total_cost=ext_wall_volume * self.rates["brick_wall_9inch_per_cum"],
            category="masonry",
        ))

        # Interior walls (4.5 inch / 115mm)
        int_wall_area = interior_wall_length * self.wall_height
        line_items.append(CostLineItem(
            element_id="masonry_interior",
            element_description="Interior brick wall 115mm (CM 1:4)",
            material="First class bricks",
            quantity=round(int_wall_area, 2),
            unit="sqm",
            unit_cost=self.rates["brick_wall_4inch_per_sqm"],
            total_cost=int_wall_area * self.rates["brick_wall_4inch_per_sqm"],
            category="masonry",
        ))

        # ── 4. Plastering ──
        total_wall_area = total_wall_length * self.wall_height * 2  # both sides
        int_plaster_area = total_wall_area * 0.8  # ~80% interior
        ext_plaster_area = total_wall_area * 0.2

        line_items.append(CostLineItem(
            element_id="plaster_internal",
            element_description="Internal cement plaster 12mm (1:4)",
            material="Cement mortar",
            quantity=round(int_plaster_area, 2),
            unit="sqm",
            unit_cost=self.rates["internal_plaster_per_sqm"],
            total_cost=int_plaster_area * self.rates["internal_plaster_per_sqm"],
            category="plastering",
        ))

        line_items.append(CostLineItem(
            element_id="plaster_external",
            element_description="External cement plaster 20mm (1:4)",
            material="Cement mortar",
            quantity=round(ext_plaster_area, 2),
            unit="sqm",
            unit_cost=self.rates["external_plaster_per_sqm"],
            total_cost=ext_plaster_area * self.rates["external_plaster_per_sqm"],
            category="plastering",
        ))

        # ── 5. Flooring ──
        for room in parse_result.rooms:
            area = max(room.area_m2, 2)  # min 2 sqm
            if room.room_type in ("bathroom", "toilet"):
                rate = self.rates["bathroom_tiles_per_sqm"]
                mat = "Anti-skid ceramic tiles"
            elif room.room_type == "kitchen":
                rate = self.rates["ceramic_tiles_per_sqm"]
                mat = "Ceramic tiles"
            else:
                rate = self.rates["vitrified_tiles_per_sqm"]
                mat = "Vitrified tiles 600×600"

            line_items.append(CostLineItem(
                element_id=f"floor_{room.id}",
                element_description=f"Flooring — {room.label}",
                material=mat,
                quantity=round(area, 2),
                unit="sqm",
                unit_cost=rate,
                total_cost=area * rate,
                room_id=room.id,
                category="flooring",
            ))

        # Bathroom wall tiles
        for room in parse_result.rooms:
            if room.room_type in ("bathroom", "toilet"):
                wall_area = max(room.area_m2 * 0.8, 4) * self.wall_height  # perimeter approx
                line_items.append(CostLineItem(
                    element_id=f"wall_tile_{room.id}",
                    element_description=f"Wall tiles — {room.label} (up to ceiling)",
                    material="Ceramic wall tiles",
                    quantity=round(wall_area, 2),
                    unit="sqm",
                    unit_cost=self.rates["bathroom_tiles_per_sqm"],
                    total_cost=wall_area * self.rates["bathroom_tiles_per_sqm"],
                    room_id=room.id,
                    category="flooring",
                ))

        # ── 6. Painting ──
        line_items.append(CostLineItem(
            element_id="painting_interior",
            element_description="Interior painting (primer + putty + 2 coat emulsion)",
            material="Asian Paints / Berger premium",
            quantity=round(int_plaster_area, 2),
            unit="sqm",
            unit_cost=self.rates["interior_paint_per_sqm"],
            total_cost=int_plaster_area * self.rates["interior_paint_per_sqm"],
            category="painting",
        ))

        line_items.append(CostLineItem(
            element_id="painting_exterior",
            element_description="Exterior weather-proof painting (2 coats)",
            material="Apex / Ultima exterior paint",
            quantity=round(ext_plaster_area, 2),
            unit="sqm",
            unit_cost=self.rates["exterior_paint_per_sqm"],
            total_cost=ext_plaster_area * self.rates["exterior_paint_per_sqm"],
            category="painting",
        ))

        # ── 7. Electrical ──
        total_points = 0
        for room in parse_result.rooms:
            pts = self.rates["points_per_room"].get(room.room_type, 4)
            total_points += pts

        line_items.append(CostLineItem(
            element_id="electrical_wiring",
            element_description=f"Electrical wiring & points ({total_points} points)",
            material="Copper wire + modular switches",
            quantity=total_points,
            unit="points",
            unit_cost=self.rates["wiring_per_point"],
            total_cost=total_points * self.rates["wiring_per_point"],
            category="electrical",
        ))

        line_items.append(CostLineItem(
            element_id="electrical_panel",
            element_description="MCB distribution board + earthing",
            material="Havells/Schneider MCB panel",
            quantity=1,
            unit="unit",
            unit_cost=self.rates["main_panel"],
            total_cost=self.rates["main_panel"],
            category="electrical",
        ))

        # ── 8. Plumbing ──
        water_points = num_bathrooms * 3 + (2 if has_kitchen else 0)
        drainage_points = num_bathrooms * 2 + (1 if has_kitchen else 0)

        line_items.append(CostLineItem(
            element_id="plumbing_water",
            element_description=f"Water supply points ({water_points} nos)",
            material="CPVC pipes & fittings",
            quantity=water_points,
            unit="points",
            unit_cost=self.rates["water_point"],
            total_cost=water_points * self.rates["water_point"],
            category="plumbing",
        ))

        line_items.append(CostLineItem(
            element_id="plumbing_drainage",
            element_description=f"Drainage points ({drainage_points} nos)",
            material="PVC pipes & fittings",
            quantity=drainage_points,
            unit="points",
            unit_cost=self.rates["drainage_point"],
            total_cost=drainage_points * self.rates["drainage_point"],
            category="plumbing",
        ))

        for i in range(num_bathrooms):
            line_items.append(CostLineItem(
                element_id=f"bathroom_fittings_{i}",
                element_description=f"Bathroom fittings set #{i+1} (WC + basin + shower + accessories)",
                material="Cera / Hindware",
                quantity=1,
                unit="set",
                unit_cost=self.rates["bathroom_fitting_set"],
                total_cost=self.rates["bathroom_fitting_set"],
                category="plumbing",
            ))

        if has_kitchen:
            line_items.append(CostLineItem(
                element_id="kitchen_sink",
                element_description="Stainless steel kitchen sink with mixer",
                material="SS 304 sink",
                quantity=1,
                unit="unit",
                unit_cost=self.rates["kitchen_sink"],
                total_cost=self.rates["kitchen_sink"],
                category="plumbing",
            ))

        # ── 9. Doors & Windows ──
        num_doors = len([o for o in parse_result.openings if o.type == "door"]) or num_rooms
        num_windows = len([o for o in parse_result.openings if o.type == "window"]) or max(num_rooms - 1, 2)

        line_items.append(CostLineItem(
            element_id="main_door",
            element_description="Main entrance door (teak wood, 7×3.5 ft)",
            material="Teak wood",
            quantity=1,
            unit="unit",
            unit_cost=self.rates["main_door"],
            total_cost=self.rates["main_door"],
            category="doors_windows",
        ))

        internal_doors = max(num_doors - 1, num_rooms - 1)
        bathroom_doors = num_bathrooms
        normal_doors = max(internal_doors - bathroom_doors, 1)

        line_items.append(CostLineItem(
            element_id="internal_doors",
            element_description=f"Internal flush doors ({normal_doors} nos, 7×3 ft)",
            material="Flush door + frame",
            quantity=normal_doors,
            unit="unit",
            unit_cost=self.rates["internal_door"],
            total_cost=normal_doors * self.rates["internal_door"],
            category="doors_windows",
        ))

        if bathroom_doors > 0:
            line_items.append(CostLineItem(
                element_id="bathroom_doors",
                element_description=f"Bathroom doors ({bathroom_doors} nos, PVC/FRP)",
                material="PVC door",
                quantity=bathroom_doors,
                unit="unit",
                unit_cost=self.rates["bathroom_door"],
                total_cost=bathroom_doors * self.rates["bathroom_door"],
                category="doors_windows",
            ))

        window_cost = num_windows * self.rates["avg_window_sqft"] * self.rates["window_per_sqft"]
        line_items.append(CostLineItem(
            element_id="windows",
            element_description=f"Aluminium sliding windows ({num_windows} nos, ~{self.rates['avg_window_sqft']} sqft each)",
            material="Aluminium frame + glass",
            quantity=num_windows,
            unit="unit",
            unit_cost=self.rates["avg_window_sqft"] * self.rates["window_per_sqft"],
            total_cost=window_cost,
            category="doors_windows",
        ))

        # ── 10. Waterproofing ──
        wp_area = total_floor_area + sum(r.area_m2 for r in parse_result.rooms if r.room_type in ("bathroom", "toilet"))
        line_items.append(CostLineItem(
            element_id="waterproofing",
            element_description="Terrace & bathroom waterproofing",
            material="Polymer based coating",
            quantity=round(wp_area, 2),
            unit="sqm",
            unit_cost=self.rates["waterproofing_per_sqm"],
            total_cost=wp_area * self.rates["waterproofing_per_sqm"],
            category="finishing",
        ))

        # Grand total
        subtotal = sum(item.total_cost for item in line_items)

        # Contingency
        contingency = subtotal * self.rates["contingency_percent"] / 100
        line_items.append(CostLineItem(
            element_id="contingency",
            element_description=f"Contingency ({self.rates['contingency_percent']}%)",
            material="—",
            quantity=1,
            unit="lump",
            unit_cost=contingency,
            total_cost=contingency,
            category="overhead",
        ))

        grand_total = subtotal + contingency

        # Budget & premium estimates using per-sqft method
        total_area_sqft = total_floor_area * 10.764
        budget_total = total_area_sqft * 1600  # ₹1600/sqft budget
        premium_total = total_area_sqft * 3000  # ₹3000/sqft premium

        room_totals = self._calculate_room_totals(line_items, parse_result.rooms)
        category_totals = self._calculate_category_totals(line_items)

        result = ProjectCost(
            line_items=line_items,
            room_totals=room_totals,
            category_totals=category_totals,
            grand_total=grand_total,
            budget_total=budget_total,
            premium_total=premium_total,
            savings_vs_premium=premium_total - grand_total,
            cost_per_sqm=grand_total / total_floor_area if total_floor_area > 0 else 0,
            total_area_sqm=total_floor_area,
            currency="INR",
        )

        if debug_dir:
            self._save_debug(result, debug_dir)

        print(f"Cost Engine - Grand Total: ₹{grand_total:,.0f} "
              f"(₹{grand_total/total_floor_area:,.0f}/sqm, "
              f"₹{grand_total/total_area_sqft:,.0f}/sqft for {total_floor_area:.1f} sqm)")

        return result

    def _calculate_room_totals(self, line_items, rooms):
        room_costs = []
        for room in rooms:
            room_items = [i for i in line_items if i.room_id == room.id]
            total = sum(i.total_cost for i in room_items)
            room_costs.append(RoomCost(
                room_id=room.id,
                room_label=room.label,
                room_type=room.room_type,
                area_m2=room.area_m2,
                wall_cost=sum(i.total_cost for i in room_items if i.category == "walls"),
                flooring_cost=sum(i.total_cost for i in room_items if i.category == "flooring"),
                opening_cost=sum(i.total_cost for i in room_items if i.category in ("openings", "doors_windows")),
                total_cost=total,
                cost_per_sqm=total / room.area_m2 if room.area_m2 > 0 else 0,
            ))
        return room_costs

    def _calculate_category_totals(self, line_items):
        categories = {}
        for item in line_items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "items": []}
            categories[item.category]["total"] += item.total_cost
            categories[item.category]["items"].append(item)

        grand_total = sum(c["total"] for c in categories.values())
        return [
            CategoryCost(
                category=cat,
                total_cost=data["total"],
                percentage=data["total"] / grand_total * 100 if grand_total > 0 else 0,
                line_items=data["items"],
            )
            for cat, data in categories.items()
        ]

    def _save_debug(self, result, debug_dir):
        os.makedirs(debug_dir, exist_ok=True)
        debug_info = {
            "grand_total": result.grand_total,
            "budget_total": result.budget_total,
            "premium_total": result.premium_total,
            "cost_per_sqm": result.cost_per_sqm,
            "cost_per_sqft": result.cost_per_sqm / 10.764 if result.cost_per_sqm else 0,
            "total_area_sqm": result.total_area_sqm,
            "category_breakdown": [
                {"category": c.category, "total": c.total_cost, "percentage": round(c.percentage, 1)}
                for c in result.category_totals
            ],
        }
        with open(os.path.join(debug_dir, "cost_debug.json"), "w") as f:
            json.dump(debug_info, f, indent=2)
