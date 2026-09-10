"""Face matching interface.

Face *matching* (verifying a live traveller image against the passport photo)
requires an embedding model. To keep the prototype stable and honest we expose
a modular interface but DO NOT fabricate a similarity score. When no real
matcher backend is wired in, `compare_faces` reports comparison_available=False.

To enable real matching later, implement a backend that returns an embedding
per face (e.g. an ONNX ArcFace model shipped locally) and compute cosine
similarity here — no other module needs to change.
"""
from __future__ import annotations

import numpy as np

from app.schemas.analysis import FaceResult


def matcher_available() -> bool:
    """No local embedding backend is bundled in this prototype."""
    return False


def compare_faces(
    document_face: np.ndarray | None,
    traveller_face: np.ndarray | None,
    base_result: FaceResult,
) -> FaceResult:
    """Attach comparison outcome to an existing FaceResult.

    Returns comparison_available=False unless a real backend is present. Never
    invents a similarity percentage.
    """
    if not matcher_available() or document_face is None or traveller_face is None:
        base_result.comparison_available = False
        base_result.similarity = None
        base_result.match_status = None
        base_result.message = (
            base_result.message
            or "Face comparison backend is not enabled in this prototype build."
        )
        return base_result

    # --- Placeholder for a real embedding-based comparison -----------------
    # embedding_a = _embed(document_face)
    # embedding_b = _embed(traveller_face)
    # similarity = cosine_similarity(embedding_a, embedding_b)
    # base_result.comparison_available = True
    # base_result.similarity = round(float(similarity), 4)
    # base_result.match_status = "match" if similarity >= 0.6 else "mismatch"
    raise NotImplementedError("No face-embedding backend is bundled.")
