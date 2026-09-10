"""Experimental tamper / image-anomaly signals (NOT certified forensics).

This module computes simple, transparent OpenCV signals that *may* correlate
with editing artifacts. It is explicitly labelled experimental and must never
be presented as certified forensic detection. It exists so a real model can
replace the implementation behind the same interface later.

Signals computed:
  * ela_mean / ela_max: Error Level Analysis — re-encode the JPEG and measure
    the per-pixel difference. Uniform authentic images show low, even ELA;
    spliced regions can show localized spikes. (Heuristic only.)
  * noise_std: global residual noise estimate (median-blur residual).
  * edge_density: proportion of edge pixels (context signal).
"""
from __future__ import annotations

import cv2
import numpy as np

from app.schemas.analysis import ForensicResult


def _error_level_analysis(image_bgr: np.ndarray, quality: int = 90) -> tuple[float, float]:
    ok, enc = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return (0.0, 0.0)
    recompressed = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    diff = cv2.absdiff(image_bgr, recompressed)
    return (float(diff.mean()), float(diff.max()))


def analyze_tamper(image_bgr: np.ndarray) -> ForensicResult:
    try:
        ela_mean, ela_max = _error_level_analysis(image_bgr)

        median = cv2.medianBlur(image_bgr, 3)
        noise = cv2.absdiff(image_bgr, median)
        noise_std = float(noise.std())

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.count_nonzero(edges)) / edges.size

        signals = {
            "ela_mean": round(ela_mean, 3),
            "ela_max": round(ela_max, 3),
            "noise_std": round(noise_std, 3),
            "edge_density": round(edge_density, 4),
        }
        return ForensicResult(
            status="analyzed",
            signals=signals,
            suspicious_regions=[],  # localization.py can populate this
        )
    except Exception as exc:  # noqa: BLE001
        return ForensicResult(
            status="unavailable",
            message=f"Forensic signal computation failed: {exc}",
        )
