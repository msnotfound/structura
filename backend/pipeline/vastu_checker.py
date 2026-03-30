"""
Vastu Shastra Compliance Checker.
Checks room placements against traditional Vastu rules for Indian residential buildings.
"""

from typing import List, Tuple, Optional
from models.parsing import ParseResult, Room, Point2D


class VastuRule:
    """A single Vastu compliance rule."""
    def __init__(self, rule_id: str, name: str, description: str,
                 ideal_direction: str, severity: str = "warning"):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.ideal_direction = ideal_direction
        self.severity = severity  # "critical", "warning", "info"


class VastuResult:
    """Result of a single Vastu check."""
    def __init__(self, rule: VastuRule, compliant: bool, actual_direction: str,
                 room_id: str, room_label: str, recommendation: str = ""):
        self.rule_id = rule.rule_id
        self.name = rule.name
        self.description = rule.description
        self.ideal_direction = rule.ideal_direction
        self.severity = rule.severity
        self.compliant = compliant
        self.actual_direction = actual_direction
        self.room_id = room_id
        self.room_label = room_label
        self.recommendation = recommendation

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "ideal_direction": self.ideal_direction,
            "severity": self.severity,
            "compliant": self.compliant,
            "actual_direction": self.actual_direction,
            "room_id": self.room_id,
            "room_label": self.room_label,
            "recommendation": self.recommendation,
            "status": "✅ Compliant" if self.compliant else "❌ Non-compliant",
        }


# Vastu rules for Indian residential buildings
VASTU_RULES = {
    "kitchen": VastuRule(
        "vastu_kitchen", "Kitchen Placement",
        "Kitchen should be in the South-East (Agni corner) of the house",
        "SE", "warning"
    ),
    "bedroom": VastuRule(
        "vastu_master_bed", "Master Bedroom Placement",
        "Master bedroom should be in the South-West for stability and prosperity",
        "SW", "warning"
    ),
    "bathroom": VastuRule(
        "vastu_bathroom", "Bathroom Placement",
        "Bathroom/Toilet should NOT be in the North-East (Ishan corner)",
        "NW", "warning"  # NW or W is ideal
    ),
    "toilet": VastuRule(
        "vastu_toilet", "Toilet Placement",
        "Toilet should be in the North-West or West direction",
        "NW", "warning"
    ),
    "living": VastuRule(
        "vastu_living", "Living Room Placement",
        "Living room should be in the North or East for positive energy",
        "NE", "info"
    ),
    "hall": VastuRule(
        "vastu_hall", "Hall Placement",
        "Hall/Drawing room should be in the North or East direction",
        "NE", "info"
    ),
    "pooja": VastuRule(
        "vastu_pooja", "Pooja Room Placement",
        "Pooja room must be in the North-East (Ishan corner) — most sacred direction",
        "NE", "critical"
    ),
    "dining": VastuRule(
        "vastu_dining", "Dining Room Placement",
        "Dining room should be in the West or East direction",
        "W", "info"
    ),
    "staircase": VastuRule(
        "vastu_stairs", "Staircase Placement",
        "Staircase should be in the South, West, or South-West",
        "SW", "info"
    ),
}

# Directions that are considered acceptable alternatives
DIRECTION_ALTERNATIVES = {
    "NE": ["N", "E", "NE"],
    "SE": ["S", "E", "SE"],
    "SW": ["S", "W", "SW"],
    "NW": ["N", "W", "NW"],
    "N": ["N", "NE", "NW"],
    "S": ["S", "SE", "SW"],
    "E": ["E", "NE", "SE"],
    "W": ["W", "NW", "SW"],
}

# Anti-vastu placements (never put these rooms here)
ANTI_VASTU = {
    "bathroom": ["NE"],   # Toilet in NE is worst
    "toilet": ["NE"],     # Toilet in NE is worst
    "kitchen": ["NE"],    # Kitchen fire in NE is bad
    "staircase": ["NE"],  # Stairs in NE block positive energy
}


class VastuChecker:
    """Checks floor plan compliance with Vastu Shastra principles."""

    def check(self, parse_result: ParseResult) -> dict:
        """
        Analyze Vastu compliance for all rooms in the plan.
        
        Returns dict with:
        - results: list of VastuResult dicts
        - overall_score: 0-100 compliance percentage
        - compliant_count, total_rules
        - summary: text summary
        """
        results = []
        building_center = self._get_building_center(parse_result)
        
        if not building_center:
            return {
                "results": [],
                "overall_score": 0,
                "compliant_count": 0,
                "total_rules": 0,
                "summary": "Could not determine building center for Vastu analysis",
            }

        for room in parse_result.rooms:
            room_type = room.room_type.lower()
            
            # Check if we have a Vastu rule for this room type
            rule = VASTU_RULES.get(room_type)
            if not rule:
                continue
            
            # Determine room's direction relative to building center
            if not room.centroid:
                continue
                
            direction = self._get_direction(building_center, room.centroid)
            
            # Check compliance
            ideal_dirs = DIRECTION_ALTERNATIVES.get(rule.ideal_direction, [rule.ideal_direction])
            anti_dirs = ANTI_VASTU.get(room_type, [])
            
            if direction in anti_dirs:
                compliant = False
                recommendation = f"⚠️ {room.label} is in {direction} which is strongly against Vastu. Move to {rule.ideal_direction} direction."
            elif direction in ideal_dirs:
                compliant = True
                recommendation = f"✅ {room.label} is correctly placed in {direction} as per Vastu."
            else:
                compliant = False
                recommendation = f"💡 {room.label} is in {direction}. Ideally should be in {rule.ideal_direction} direction."
            
            results.append(VastuResult(
                rule=rule,
                compliant=compliant,
                actual_direction=direction,
                room_id=room.id,
                room_label=room.label,
                recommendation=recommendation,
            ))

        # Calculate overall score
        total = len(results)
        compliant_count = sum(1 for r in results if r.compliant)
        score = round((compliant_count / total * 100) if total > 0 else 0)

        # Generate summary
        if score >= 80:
            summary = f"Excellent Vastu compliance ({score}%). This plan follows most Vastu principles."
        elif score >= 50:
            summary = f"Moderate Vastu compliance ({score}%). Some adjustments recommended."
        else:
            summary = f"Low Vastu compliance ({score}%). Significant changes needed for Vastu adherence."

        return {
            "results": [r.to_dict() for r in results],
            "overall_score": score,
            "compliant_count": compliant_count,
            "total_rules": total,
            "summary": summary,
        }

    def _get_building_center(self, parse_result: ParseResult) -> Optional[Point2D]:
        """Get the center point of the building."""
        all_x = []
        all_y = []
        for room in parse_result.rooms:
            for v in room.vertices:
                all_x.append(v.x)
                all_y.append(v.y)
        
        if not all_x:
            return None
        
        return Point2D(
            x=(min(all_x) + max(all_x)) / 2,
            y=(min(all_y) + max(all_y)) / 2,
        )

    def _get_direction(self, center: Point2D, point: Point2D) -> str:
        """
        Determine compass direction of a point relative to center.
        Note: In image coordinates, Y increases downward, so:
        - point.y < center.y = North
        - point.y > center.y = South
        """
        dx = point.x - center.x
        dy = center.y - point.y  # Flip Y for compass (up = North)
        
        # Determine quadrant with thresholds
        threshold = 0.3  # ratio threshold for diagonal vs cardinal
        
        if abs(dx) < abs(dy) * threshold:
            # Mostly vertical
            return "N" if dy > 0 else "S"
        elif abs(dy) < abs(dx) * threshold:
            # Mostly horizontal
            return "E" if dx > 0 else "W"
        else:
            # Diagonal
            if dx > 0 and dy > 0:
                return "NE"
            elif dx < 0 and dy > 0:
                return "NW"
            elif dx > 0 and dy < 0:
                return "SE"
            else:
                return "SW"
