"""
Vision Language Model (VLM) parser using Google Gemini.
Enhanced: extracts room dimensions from plan text, pixel bounding boxes,
and provides Groq Llama 4 Scout fallback.
"""

import os
import json
import base64
from typing import Optional
import numpy as np

from models.parsing import VLMParseResult, Room, Point2D

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


class VLMParser:
    """Parser using Google Gemini Vision (primary) or Groq Llama 4 Scout (fallback)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self._genai_client = None
        self._groq_client = None

        if not MOCK_MODE:
            self._init_model()

    def _init_model(self):
        """Initialize the Gemini client, with Groq fallback."""
        if self.api_key:
            try:
                import google.genai as genai
                self._genai_client = genai.Client(api_key=self.api_key)
                self._model_name = "gemini-2.5-flash"
                self._genai_client.models.generate_content(
                    model=self._model_name, contents="ping"
                )
                print(f"VLM: Gemini {self._model_name} initialized successfully")
                return
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini model: {e}")
                self._genai_client = None

        if self.groq_api_key:
            try:
                from openai import OpenAI
                self._groq_client = OpenAI(
                    api_key=self.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                self._groq_model = "meta-llama/llama-4-scout-17b-16e-instruct"
                print(f"VLM: Groq {self._groq_model} initialized as fallback")
            except Exception as e:
                print(f"Warning: Failed to initialize Groq VLM: {e}")

    def _encode_image(self, image: np.ndarray) -> str:
        import cv2
        _, buffer = cv2.imencode(".png", image)
        return base64.b64encode(buffer).decode("utf-8")

    def _get_prompt(self, h: int, w: int) -> str:
        return f"""You are an expert architectural floor plan analyzer. Analyze this floor plan image ({w}x{h} pixels).

CRITICAL INSTRUCTIONS:
1. Find EVERY room in this floor plan  
2. For each room, estimate its pixel bounding box (x_min, y_min, x_max, y_max) in image coordinates where (0,0) is top-left
3. If rooms have dimension TEXT written on the plan (like "11'-6" x 10'-0"" or "3.5m x 4.0m"), extract those EXACTLY
4. Look for overall building dimensions text (like "20'-0"" or "6.0m") 
5. Look for a scale bar or scale text

Return ONLY valid JSON (no markdown, no backticks):

{{
    "rooms": [
        {{
            "label": "room name exactly as written on plan",
            "room_type": "bedroom/bathroom/kitchen/living/dining/hall/pooja/toilet/balcony/staircase/foyer/closet/other",
            "bbox": {{
                "x_min": pixel_x_start,
                "y_min": pixel_y_start,
                "x_max": pixel_x_end,
                "y_max": pixel_y_end
            }},
            "dimensions_text": "exact dimension text from plan if visible, e.g. 11'-6\" x 10'-0\", otherwise null",
            "width_m": estimated_width_in_meters_or_null,
            "length_m": estimated_length_in_meters_or_null,
            "estimated_area_sqm": number_or_null
        }}
    ],
    "building_dimensions": {{
        "overall_width_text": "e.g. 20'-0\" or 6.1m, null if not visible",
        "overall_depth_text": "e.g. 24'-7½\" or 7.5m, null if not visible",
        "overall_width_m": number_or_null,
        "overall_depth_m": number_or_null,
        "total_area_text": "e.g. 704 SFT, null if not visible",
        "total_area_sqm": number_or_null
    }},
    "building_shape": "rectangular/L-shaped/U-shaped/irregular",
    "room_count": total_number_of_rooms,
    "wall_count_estimate": approximate_number_of_wall_segments,
    "scale_info": {{
        "has_dimensions": true_or_false,
        "has_scale_bar": true_or_false,
        "estimated_door_width_pixels": number_or_null,
        "reference_measurement": {{
            "text": "dimension text e.g. 20'-0\"",
            "value_m": value_in_meters,
            "pixel_length": approximate_pixel_length_of_that_dimension
        }}
    }},
    "notes": ["observations"]
}}

CONVERSION RULES:
- 1 foot = 0.3048 meters. E.g. 11'-6" = 11.5 feet = 3.505m
- If dimensions are in feet-inches: 7'-0" = 7 feet = 2.134m
- SFT = square feet. 704 SFT = 65.4 sqm"""

    def parse(self, image: np.ndarray, debug_dir: Optional[str] = None) -> VLMParseResult:
        if MOCK_MODE:
            return self._mock_parse()

        if self._genai_client:
            try:
                return self._parse_with_gemini(image, debug_dir)
            except Exception as e:
                print(f"Gemini VLM parsing failed: {e}")

        if self._groq_client:
            try:
                return self._parse_with_groq(image, debug_dir)
            except Exception as e:
                print(f"Groq VLM parsing failed: {e}")

        print("All VLM providers failed, using mock data")
        return self._mock_parse()

    def _parse_with_gemini(self, image: np.ndarray, debug_dir: Optional[str] = None) -> VLMParseResult:
        import cv2
        from PIL import Image
        import io

        h, w = image.shape[:2]
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        img_bytes = io.BytesIO()
        pil_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        import google.genai.types as types
        response = self._genai_client.models.generate_content(
            model=self._model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes.read(), mime_type='image/png'),
                self._get_prompt(h, w)
            ]
        )
        return self._parse_response(response.text, h, w, debug_dir, "gemini")

    def _parse_with_groq(self, image: np.ndarray, debug_dir: Optional[str] = None) -> VLMParseResult:
        h, w = image.shape[:2]
        b64_image = self._encode_image(image)

        response = self._groq_client.chat.completions.create(
            model=self._groq_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}},
                    {"type": "text", "text": self._get_prompt(h, w)}
                ]
            }],
            max_tokens=2500,
            temperature=0.2,
        )
        return self._parse_response(response.choices[0].message.content.strip(), h, w, debug_dir, "groq")

    def _parse_response(self, raw_response: str, h: int, w: int,
                         debug_dir: Optional[str] = None, provider: str = "unknown") -> VLMParseResult:
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, f"vlm_raw_response_{provider}.txt"), "w") as f:
                f.write(raw_response)

        try:
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(raw_response[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except json.JSONDecodeError as e:
            print(f"Failed to parse VLM JSON: {e}")
            return self._mock_parse()

        rooms = []
        for rd in data.get("rooms", []):
            bbox = rd.get("bbox", {})
            room_info = {
                "label": rd.get("label", "Unknown"),
                "room_type": rd.get("room_type", "other"),
                "approximate_location": rd.get("approximate_location", ""),
                "estimated_area_sqm": rd.get("estimated_area_sqm"),
                "width_m": rd.get("width_m"),
                "length_m": rd.get("length_m"),
                "dimensions_text": rd.get("dimensions_text"),
            }
            if bbox and all(k in bbox for k in ("x_min", "y_min", "x_max", "y_max")):
                room_info["bbox"] = {
                    "x_min": float(bbox["x_min"]),
                    "y_min": float(bbox["y_min"]),
                    "x_max": float(bbox["x_max"]),
                    "y_max": float(bbox["y_max"]),
                }
            rooms.append(room_info)

        # Extract scale from VLM-detected dimensions
        estimated_scale = None
        building_dims = data.get("building_dimensions", {})
        scale_info = data.get("scale_info", {})

        # Priority 1: reference measurement with pixel length
        ref = scale_info.get("reference_measurement", {})
        if ref and ref.get("value_m") and ref.get("pixel_length"):
            estimated_scale = float(ref["pixel_length"]) / float(ref["value_m"])
            print(f"  VLM scale from reference: {estimated_scale:.1f} px/m ({ref.get('text', '')})")

        # Priority 2: building dimensions + image width
        if not estimated_scale and building_dims.get("overall_width_m"):
            bw = float(building_dims["overall_width_m"])
            if bw > 0:
                estimated_scale = w * 0.85 / bw  # building ~85% of image width
                print(f"  VLM scale from building width: {estimated_scale:.1f} px/m ({bw}m)")

        # Priority 3: room dimensions with bboxes
        if not estimated_scale:
            for rd in data.get("rooms", []):
                rm_w = rd.get("width_m")
                rm_bbox = rd.get("bbox", {})
                if rm_w and rm_w > 0 and rm_bbox:
                    bbox_w_px = abs(rm_bbox.get("x_max", 0) - rm_bbox.get("x_min", 0))
                    if bbox_w_px > 20:
                        estimated_scale = bbox_w_px / float(rm_w)
                        print(f"  VLM scale from room {rd.get('label', '?')}: {estimated_scale:.1f} px/m")
                        break

        # Priority 4: door width fallback
        if not estimated_scale and scale_info.get("estimated_door_width_pixels"):
            estimated_scale = float(scale_info["estimated_door_width_pixels"]) / 0.9
            print(f"  VLM scale from door width: {estimated_scale:.1f} px/m")

        print(f"VLM ({provider}): {len(rooms)} rooms, shape: {data.get('building_shape', '?')}, scale: {estimated_scale}")

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
        return VLMParseResult(
            rooms=[
                {"label": "LIVING ROOM", "room_type": "living", "approximate_location": "top-left",
                 "estimated_area_sqm": 25.0, "width_m": 5.0, "length_m": 5.0,
                 "bbox": {"x_min": 30, "y_min": 50, "x_max": 200, "y_max": 230}},
                {"label": "BEDROOM 1", "room_type": "bedroom", "approximate_location": "top-right",
                 "estimated_area_sqm": 15.0, "width_m": 3.5, "length_m": 4.3,
                 "bbox": {"x_min": 200, "y_min": 50, "x_max": 350, "y_max": 200}},
                {"label": "BEDROOM 2", "room_type": "bedroom", "approximate_location": "bottom-left",
                 "estimated_area_sqm": 16.0, "width_m": 3.5, "length_m": 4.5,
                 "bbox": {"x_min": 30, "y_min": 230, "x_max": 180, "y_max": 380}},
                {"label": "KITCHEN", "room_type": "kitchen", "approximate_location": "bottom-center",
                 "estimated_area_sqm": 10.0, "width_m": 2.5, "length_m": 4.0,
                 "bbox": {"x_min": 180, "y_min": 230, "x_max": 290, "y_max": 380}},
                {"label": "BATH", "room_type": "bathroom", "approximate_location": "bottom-right",
                 "estimated_area_sqm": 5.0, "width_m": 2.0, "length_m": 2.5,
                 "bbox": {"x_min": 290, "y_min": 230, "x_max": 350, "y_max": 380}},
            ],
            building_shape="rectangular",
            estimated_scale=50.0,
            room_count=5,
            wall_count_estimate=15,
            notes=["Mock data"],
            raw_response=None,
        )
