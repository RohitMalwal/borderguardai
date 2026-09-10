"""Top-level screening result schema — the single object the API returns and
future modules (watchlist, risk fusion, RAG, officer decision) will consume."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.analysis import (
    ConsistencyResult,
    FaceResult,
    ForensicResult,
    MrzResult,
    VisualOcrResult,
)
from app.schemas.document import ImageInfo, PreprocessingResult, QualityResult


class StageState(BaseModel):
    """Per-stage state so the frontend can render the pipeline honestly."""

    stage: str
    status: str
    duration_ms: Optional[float] = None
    message: Optional[str] = None


class ScreeningResult(BaseModel):
    """Stable, modular contract. See docs/api-contract.md."""

    screening_id: str
    schema_version: str = "1.0"
    created_at: str
    status: str = Field(description="complete | partial | error")

    document: ImageInfo
    quality: Optional[QualityResult] = None
    preprocessing: Optional[PreprocessingResult] = None
    visual_ocr: Optional[VisualOcrResult] = None
    mrz: Optional[MrzResult] = None
    consistency: Optional[ConsistencyResult] = None
    face: Optional[FaceResult] = None
    forensic: Optional[ForensicResult] = None

    # Ordered stage timeline for the UI.
    stages: list[StageState] = Field(default_factory=list)

    # Reserved extension points for future modules. Present but null/empty so
    # downstream consumers can rely on the keys existing.
    intelligence: Optional[dict] = Field(
        default=None,
        description="Reserved: watchlist, risk fusion, evidence, recommendation.",
    )
    explanation: Optional[dict] = Field(
        default=None, description="Reserved: RAG-backed narrative explanation."
    )
    officer_decision: Optional[dict] = Field(
        default=None, description="Reserved: human-in-the-loop officer decision."
    )

    warnings: list[str] = Field(default_factory=list)
