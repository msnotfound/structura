"""
Vision Language Model (VLM) parser using Google Gemini.
Extracts semantic information from floor plans.
"""

import os
import json
import base64
from typing import Optional
import numpy as np

from models.parsing import VLMParseResult, Room, Point2D

# Mock mode flag
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


class VLMParser:
    """Parser using Google Gemini Vision for semantic floor plan understanding."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY", "")
        self.model = None

        if not MOCK_MODE and self.api_key:
            self._init_model()

    def _init_model(self):
        """Initialize the Gemini client."""
        try:
            import google.genai as genai
            self._genai_client = genai.Client(api_key=self.api_key)
            self._model_name = "gemini-2.5-flash"
            # Quick connectivity test
            self._genai_client.models.generate_content(
                model=self._model_name, contents="ping"
            )
            print(f"VLM: Gemini {self._model_name} initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini model: {e}")
            self._genai_client = None

    def _encode_image(self, image: np.ndarray) -> str:
        """Encode image to base64 for API."""
        import cv2

        _, buffer = cv2.imencode(".png", image)
        return base64.b64encode(buffer).decode("utf-8")

    def _get_prompt(self) -> str:
        """Get the prompt for floor plan analysis."""
        return """Analyze this architectural floor plan image and extract the following information in JSON format:

{
    "rooms": [
        {
            "label": "room name/label visible in image",
            "room_type": "one of: bedroom, bathroom, kitchen, living, laundry, foyer, closet, hallway, dining, great_room, other",
            "approximate_location": "description like 'top-left', 'center', 'bottom-right'",
            "estimated_area_sqm": number or null if unclear
        }
    ],
    "building_shape": "one of: rectangular, L-shaped, U-shaped, irregular, unknown",
    "room_count": total number of rooms,
    "wall_count_estimate": approximate number of wall segments,
    "scale_info": {
        "has_scale_bar": true/false,
        "scale_text": "text near scale bar if visible",
        "estimated_door_width_pixels": number or null
    },
    "notes": ["any relevant observations about the floor plan"]
}

Be precise with room labels - use exactly what's written in the image.
If room type is ambiguous, use "other".
Focus on accuracy over completeness."""

    def parse(
        self, image: np.ndarray, debug_dir: Optional[str] = None
    ) -> VLMParseResult:
        """
        Parse a floor plan image using Gemini Vision.

        Args:
            image: BGR image from cv2
            debug_dir: Directory to save debug info

        Returns:
            VLMParseResult with extracted information
        """
        if MOCK_MODE or not hasattr(self, '_genai_client') or self._genai_client is None:
            return self._mock_parse()

        try:
            return self._real_parse(image, debug_dir)
        except Exception as e:
            print(f"VLM parsing failed: {e}, falling back to mock")
            return self._mock_parse()

    def _real_parse(
        self, image: np.ndarray, debug_dir: Optional[str] = None
    ) -> VLMParseResult:
        """Actual Gemini API call using new google-genai SDK."""
        import cv2
        from PIL import Image
        import io

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # Convert PIL to bytes for new SDK
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        import google.genai.types as types
        response = self._genai_client.models.generate_content(
            model=self._model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes.read(), mime_type='image/png'),
                self._get_prompt()
            ]
        )
        raw_response = response.text

        # Save raw response for debugging
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "vlm_raw_response.txt"), "w") as f:
                f.write(raw_response)

        # Parse JSON from response
        try:
            # Try to extract JSON from response
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse VLM JSON response: {e}")
            return self._mock_parse()

        # Convert to VLMParseResult
        rooms = []
        for room_data in data.get("rooms", []):
            rooms.append(
                {
                    "label": room_data.get("label", "Unknown"),
                    "room_type": room_data.get("room_type", "other"),
                    "approximate_location": room_data.get("approximate_location", ""),
                    "estimated_area_sqm": room_data.get("estimated_area_sqm"),
                }
            )

        scale_info = data.get("scale_info", {})
        estimated_scale = None
        if scale_info.get("estimated_door_width_pixels"):
            # Standard door width is ~0.9m
            estimated_scale = scale_info["estimated_door_width_pixels"] / 0.9

        return VLMParseResult(
            rooms=rooms,
            building_shape=data.get("building_shape", "unknown"),
            estimated_scale=estimated_scale,
            room_count=data.get("room_count", len(rooms)),
            wall_count_estimate=data.get("wall_count_estimate", 0),
            notes=data.get("notes", []),
            raw_response=raw_response,
        )

    def _mock_parse(self) -> VLMParseResult:
        """Return mock data for development."""
        return VLMParseResult(
            rooms=[
                {
                    "label": "Living Room",
                    "room_type": "living",
                    "approximate_location": "center-left",
                    "estimated_area_sqm": 25.0,
                },
                {
                    "label": "Kitchen",
                    "room_type": "kitchen",
                    "approximate_location": "top-right",
                    "estimated_area_sqm": 12.0,
                },
                {
                    "label": "Master Bedroom",
                    "room_type": "bedroom",
                    "approximate_location": "bottom-left",
                    "estimated_area_sqm": 18.0,
                },
                {
                    "label": "Bedroom 2",
                    "room_type": "bedroom",
                    "approximate_location": "bottom-right",
                    "estimated_area_sqm": 14.0,
                },
                {
                    "label": "Bathroom",
                    "room_type": "bathroom",
                    "approximate_location": "center-right",
                    "estimated_area_sqm": 6.0,
                },
            ],
            building_shape="rectangular",
            estimated_scale=100.0,  # 100 pixels per meter
            room_count=5,
            wall_count_estimate=12,
            notes=[
                "Mock data - VLM not called",
                "Typical residential floor plan layout",
            ],
            raw_response=None,
        )
