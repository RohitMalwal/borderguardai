"""Schemas for OCR, MRZ, consistency, face and forensic analysis blocks."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# OCR
# --------------------------------------------------------------------------- #
class OcrTextLine(BaseModel):
    text: str
    confidence: float
    box: list[list[float]] = Field(
        default_factory=list, description="Four [x,y] polygon points"
    )


class ExtractedField(BaseModel):
    """A field derived from visual OCR. Never fabricated: when it cannot be
    reliably identified, value is null and status says so."""

    value: Optional[str] = None
    confidence: Optional[float] = None
    status: str = Field(description="detected | low_confidence | not_detected")
    source: str = Field(default="visual", description="visual (this block is visual-OCR only)")
    source_text: Optional[str] = None


class VisualOcrResult(BaseModel):
    engine: str = Field(description="paddleocr | unavailable")
    status: str = Field(description="complete | low_confidence | failed | engine_unavailable")
    raw_text: list[OcrTextLine] = Field(default_factory=list)
    fields: dict[str, ExtractedField] = Field(default_factory=dict)
    mean_confidence: Optional[float] = None
    message: Optional[str] = None


# --------------------------------------------------------------------------- #
# MRZ
# --------------------------------------------------------------------------- #
class MrzValidation(BaseModel):
    document_number: Optional[bool] = None
    date_of_birth: Optional[bool] = None
    expiry_date: Optional[bool] = None
    composite: Optional[bool] = None
    line_lengths_ok: Optional[bool] = None


class MrzResult(BaseModel):
    detected: bool
    status: str = Field(description="detected | not_detected | low_confidence | invalid | valid")
    raw_lines: list[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    fields: dict[str, Optional[str]] = Field(default_factory=dict)
    validation: MrzValidation = Field(default_factory=MrzValidation)
    errors: list[str] = Field(default_factory=list)
    message: Optional[str] = None


# --------------------------------------------------------------------------- #
# Consistency (Visual OCR <-> MRZ)
# --------------------------------------------------------------------------- #
class ConsistencyField(BaseModel):
    visual: Optional[str] = None
    mrz: Optional[str] = None
    status: str = Field(description="match | mismatch | not_available | low_confidence")
    detail: Optional[str] = None


class ConsistencyResult(BaseModel):
    overall_status: str = Field(description="match | partial | mismatch | not_available")
    match_count: int = 0
    comparable_count: int = 0
    fields: dict[str, ConsistencyField] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Face
# --------------------------------------------------------------------------- #
class FaceBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float] = None


class FaceResult(BaseModel):
    detected: bool
    status: str = Field(description="detected | not_detected | multiple_detected | unavailable")
    faces: list[FaceBox] = Field(default_factory=list)
    primary_face: Optional[FaceBox] = None
    comparison_available: bool = False
    similarity: Optional[float] = None
    match_status: Optional[str] = None
    message: Optional[str] = None


# --------------------------------------------------------------------------- #
# Forensic (experimental prototype signal — NOT certified)
# --------------------------------------------------------------------------- #
class ForensicResult(BaseModel):
    label: str = "Experimental Prototype Signal"
    status: str = Field(description="analyzed | unavailable")
    signals: dict[str, Any] = Field(default_factory=dict)
    suspicious_regions: list[dict] = Field(default_factory=list)
    disclaimer: str = (
        "Experimental image-anomaly signal only. This is NOT certified forensic "
        "analysis and must not be used as sole evidence of tampering."
    )
    message: Optional[str] = None
