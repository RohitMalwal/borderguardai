"""Modular OpenCV preprocessing pipeline.

Each step is a small, independently improvable function. The original image is
never mutated — every step returns a new array, and we persist artifacts
separately under storage/processed so the raw upload is always preserved.

The pipeline produces a `primary` image (the version handed to OCR): a
denoised, contrast-enhanced, deskewed rendering that keeps colour so downstream
face detection still works.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import cv2
import numpy as np


@dataclass
class StepOutcome:
    name: str
    applied: bool
    detail: str = ""
    image: np.ndarray | None = None


# --- Individual steps ------------------------------------------------------ #
def resize_max(image: np.ndarray, max_side: int = 1600) -> StepOutcome:
    """Downscale very large captures for stable, fast processing."""
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return StepOutcome("resize", False, f"within bounds ({w}x{h})", image)
    scale = max_side / float(longest)
    out = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return StepOutcome("resize", True, f"{w}x{h} -> {out.shape[1]}x{out.shape[0]}", out)


def to_grayscale(image: np.ndarray) -> StepOutcome:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return StepOutcome("grayscale", True, "BGR -> GRAY", gray)


def clahe_contrast(image: np.ndarray) -> StepOutcome:
    """CLAHE on the luminance channel; keeps colour for face detection."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    if image.ndim == 2:
        out = clahe.apply(image)
    else:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = clahe.apply(l)
        out = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    return StepOutcome("clahe", True, "adaptive contrast enhancement", out)


def denoise(image: np.ndarray) -> StepOutcome:
    if image.ndim == 2:
        out = cv2.fastNlMeansDenoising(image, h=7)
    else:
        out = cv2.fastNlMeansDenoisingColored(image, h=7, hColor=7)
    return StepOutcome("denoise", True, "fast non-local means", out)


def sharpen(image: np.ndarray) -> StepOutcome:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    out = cv2.filter2D(image, -1, kernel)
    return StepOutcome("sharpen", True, "unsharp-style kernel", out)


def deskew(image: np.ndarray) -> StepOutcome:
    """Estimate small skew from text edges and rotate to correct it.

    Uses a conservative Hough-based angle estimate; only corrects modest
    rotations to avoid making things worse on odd inputs.
    """
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)
    if lines is None:
        return StepOutcome("deskew", False, "no dominant lines detected", image)

    angles = []
    for rho_theta in lines[:100]:
        theta = rho_theta[0][1]
        deg = (theta * 180.0 / np.pi) - 90.0  # relative to horizontal
        if -20 < deg < 20:
            angles.append(deg)
    if not angles:
        return StepOutcome("deskew", False, "no near-horizontal skew found", image)

    angle = float(np.median(angles))
    if abs(angle) < 0.5:
        return StepOutcome("deskew", False, f"skew negligible ({angle:.2f} deg)", image)

    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    out = cv2.warpAffine(
        image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return StepOutcome("deskew", True, f"rotated {angle:.2f} deg", out)


@dataclass
class PreprocessOutput:
    original: np.ndarray
    primary: np.ndarray  # colour image handed to OCR/face
    steps: list[StepOutcome] = field(default_factory=list)


def run_preprocessing(image_bgr: np.ndarray) -> PreprocessOutput:
    """Run the default preprocessing chain, preserving the original."""
    original = image_bgr.copy()

    steps: list[StepOutcome] = []
    working = original.copy()

    pipeline: list[Callable[[np.ndarray], StepOutcome]] = [
        resize_max,
        denoise,
        clahe_contrast,
        deskew,
        sharpen,
    ]

    for step in pipeline:
        outcome = step(working)
        if outcome.image is not None:
            working = outcome.image
        # Do not carry the array into the schema layer.
        steps.append(StepOutcome(outcome.name, outcome.applied, outcome.detail, None))

    return PreprocessOutput(original=original, primary=working, steps=steps)
