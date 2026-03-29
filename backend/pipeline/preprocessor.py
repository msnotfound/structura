"""
Image preprocessing for floor plan analysis.
Handles contrast enhancement, denoising, and binarization.
"""

import os
from typing import Tuple, Optional
import numpy as np

# Lazy import for cv2
cv2 = None


def _get_cv2():
    global cv2
    if cv2 is None:
        import cv2 as _cv2

        cv2 = _cv2
    return cv2


def preprocess_image(
    image: np.ndarray, debug_dir: Optional[str] = None, debug_prefix: str = "preprocess"
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Preprocess a floor plan image for parsing.

    Args:
        image: Input BGR image from cv2.imread
        debug_dir: Directory to save debug images (if provided)
        debug_prefix: Prefix for debug image filenames

    Returns:
        Tuple of (processed_image, binary_image, metadata)
    """
    cv2 = _get_cv2()

    metadata = {"original_shape": image.shape, "steps_applied": []}

    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    metadata["steps_applied"].append("grayscale")

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    metadata["steps_applied"].append("clahe")

    # Denoise
    denoised = cv2.fastNlMeansDenoising(
        enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21
    )
    metadata["steps_applied"].append("denoise")

    # Adaptive thresholding for binarization
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,
        C=2,
    )
    metadata["steps_applied"].append("adaptive_threshold")

    # Morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    metadata["steps_applied"].append("morphology")

    # Save debug images if requested
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, f"{debug_prefix}_1_gray.png"), gray)
        cv2.imwrite(os.path.join(debug_dir, f"{debug_prefix}_2_enhanced.png"), enhanced)
        cv2.imwrite(os.path.join(debug_dir, f"{debug_prefix}_3_denoised.png"), denoised)
        cv2.imwrite(os.path.join(debug_dir, f"{debug_prefix}_4_binary.png"), binary)
        metadata["debug_images_saved"] = True

    return denoised, binary, metadata


def detect_scale_bar(image: np.ndarray, binary: np.ndarray) -> Optional[dict]:
    """
    Attempt to detect a scale bar in the image.

    Returns:
        Scale information dict or None if not found
    """
    cv2 = _get_cv2()

    # Look for horizontal lines that could be scale bars
    # Typically at bottom or top of image
    h, w = binary.shape[:2]

    # Check bottom 15% of image
    bottom_region = binary[int(h * 0.85) :, :]

    # Detect lines using HoughLinesP
    lines = cv2.HoughLinesP(
        bottom_region,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=50,
        maxLineGap=10,
    )

    if lines is None:
        return None

    # Find horizontal lines (potential scale bars)
    horizontal_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.abs(np.arctan2(y2 - y1, x2 - x1))
        if angle < 0.1:  # Nearly horizontal
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            horizontal_lines.append(
                {
                    "start": (x1, y1 + int(h * 0.85)),
                    "end": (x2, y2 + int(h * 0.85)),
                    "length_px": length,
                }
            )

    if not horizontal_lines:
        return None

    # Return the longest horizontal line as potential scale bar
    longest = max(horizontal_lines, key=lambda x: x["length_px"])

    return {
        "detected": True,
        "line": longest,
        "confidence": 0.5,  # Low confidence, needs OCR verification
        "method": "hough_lines",
    }
