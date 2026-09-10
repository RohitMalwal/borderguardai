"""Image quality analysis using OpenCV.

All metrics are computed from the actual uploaded image. Nothing here is
hard-coded. The composite `quality_score` combines sharpness, exposure,
contrast and resolution into a single 0-100 indicator, but every raw signal is
returned separately so the UI (and future risk fusion) can reason about them.
"""
from __future__ import annotations

import cv2
import numpy as np

from app.core.constants import QualityStatus
from app.schemas.document import QualityResult


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, v)))


def analyze_quality(image_bgr: np.ndarray) -> QualityResult:
    """Compute quality signals from a BGR image array."""
    height, width = image_bgr.shape[:2]
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # Sharpness: variance of the Laplacian. Higher = sharper.
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Exposure and contrast from the luminance channel.
    brightness_score = float(gray.mean())
    contrast_score = float(gray.std())

    megapixels = round((width * height) / 1_000_000.0, 2)

    warnings: list[str] = []

    # --- Sub-scores (each normalized to 0-100) ----------------------------
    # Blur: ~100+ variance is typically crisp for document photos.
    sharpness_sub = _clamp((blur_score / 150.0) * 100.0)
    if blur_score < 60:
        warnings.append("Image appears blurry; text extraction may be unreliable.")

    # Brightness: ideal band ~110-180. Penalize distance from centre (145).
    brightness_sub = _clamp(100.0 - abs(brightness_score - 145.0) * (100.0 / 145.0))
    if brightness_score < 60:
        warnings.append("Image is very dark.")
    elif brightness_score > 210:
        warnings.append("Image is over-exposed; glare may hide security features.")

    # Contrast: std-dev >= 50 is healthy for a document.
    contrast_sub = _clamp((contrast_score / 60.0) * 100.0)
    if contrast_score < 25:
        warnings.append("Low contrast; MRZ and print may be hard to read.")

    # Resolution: 2 MP+ is comfortable for a biodata page.
    resolution_sub = _clamp((megapixels / 2.0) * 100.0)
    if min(width, height) < 480:
        warnings.append("Low resolution; consider a higher-quality capture.")

    quality_score = round(
        0.40 * sharpness_sub
        + 0.20 * brightness_sub
        + 0.20 * contrast_sub
        + 0.20 * resolution_sub,
        1,
    )

    if quality_score >= 70:
        status = QualityStatus.GOOD
    elif quality_score >= 45:
        status = QualityStatus.ACCEPTABLE
    else:
        status = QualityStatus.POOR

    return QualityResult(
        status=status.value,
        quality_score=quality_score,
        blur_score=round(blur_score, 2),
        brightness_score=round(brightness_score, 2),
        contrast_score=round(contrast_score, 2),
        resolution={"width": width, "height": height, "megapixels": megapixels},
        warnings=warnings,
    )
