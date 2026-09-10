"""Passport-photo face detection using OpenCV Haar cascades.

We load a Haar cascade and return the detected bounding box(es) with an honest
status. This runs fully offline: the cascade XML is vendored under `models/`
(OpenCV 5's wheel no longer bundles cv2.data cascades), with a fallback to
cv2.data for environments that still ship them. Intentionally lightweight —
face detection is priority 9, below OCR/MRZ/consistency.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.schemas.analysis import FaceBox, FaceResult

_CASCADE_FILE = "haarcascade_frontalface_default.xml"
_cascade = None
# Vendored cascade lives next to this module: portable, no absolute paths.
_VENDORED = Path(__file__).resolve().parent / "models" / _CASCADE_FILE


def _candidate_paths() -> list[Path]:
    paths = [_VENDORED]
    try:
        # Environments still shipping cv2.data cascades (e.g. OpenCV 4.x).
        paths.append(Path(cv2.data.haarcascades) / _CASCADE_FILE)
    except Exception:  # noqa: BLE001 - cv2.data may be absent
        pass
    return paths


def _get_cascade():
    global _cascade
    if _cascade is not None:
        return _cascade
    # Some minimal/preview OpenCV wheels omit the objdetect module entirely.
    if not hasattr(cv2, "CascadeClassifier"):
        return None
    for path in _candidate_paths():
        if not path.is_file():
            continue
        try:
            clf = cv2.CascadeClassifier(str(path))
        except Exception:  # noqa: BLE001
            continue
        if not clf.empty():
            _cascade = clf
            return _cascade
    return None


def detect_faces(image_bgr: np.ndarray) -> FaceResult:
    cascade = _get_cascade()
    if cascade is None:
        return FaceResult(
            detected=False,
            status="unavailable",
            message="Face cascade could not be loaded in this environment.",
        )

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    detections = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )

    if len(detections) == 0:
        return FaceResult(
            detected=False,
            status="not_detected",
            message="No face detected on the document. Ensure the photo area is visible.",
        )

    boxes = [
        FaceBox(x=int(x), y=int(y), width=int(w), height=int(h), confidence=None)
        for (x, y, w, h) in detections
    ]
    # Primary face = largest area (passport photo dominates the biodata page).
    primary = max(boxes, key=lambda b: b.width * b.height)
    status = "detected" if len(boxes) == 1 else "multiple_detected"
    return FaceResult(
        detected=True,
        status=status,
        faces=boxes,
        primary_face=primary,
        comparison_available=False,
    )
