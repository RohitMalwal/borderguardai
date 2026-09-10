"""Suspicious-region localization interface (future work).

Fraud localization — pointing at *where* a document may have been altered —
requires a trained segmentation model. This module defines the interface so it
can be implemented later without touching the pipeline. It intentionally
returns no regions rather than guessing.
"""
from __future__ import annotations

import numpy as np


def localize_suspicious_regions(image_bgr: np.ndarray) -> list[dict]:
    """Return a list of {x, y, width, height, score} regions.

    Not implemented in the prototype: returns an empty list so nothing is
    fabricated. Replace with a real model behind this signature.
    """
    return []
