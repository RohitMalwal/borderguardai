"""Schemas describing the uploaded document, its quality and preprocessing."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ImageInfo(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    width: int
    height: int
    channels: int


class QualityResult(BaseModel):
    """Real, computed image-quality signals (OpenCV). No hard-coded scores."""

    status: str = Field(description="good | acceptable | poor")
    quality_score: float = Field(description="0-100 composite score")
    blur_score: float = Field(description="Variance of Laplacian (higher = sharper)")
    brightness_score: float = Field(description="Mean luminance 0-255")
    contrast_score: float = Field(description="Std-dev of luminance")
    resolution: dict = Field(description="{width, height, megapixels}")
    warnings: list[str] = Field(default_factory=list)


class PreprocessingStep(BaseModel):
    name: str
    applied: bool
    detail: Optional[str] = None
    artifact_path: Optional[str] = None  # relative path under storage/processed


class PreprocessingResult(BaseModel):
    steps: list[PreprocessingStep] = Field(default_factory=list)
    original_artifact: Optional[str] = None
    primary_artifact: Optional[str] = None  # image handed to OCR
    notes: list[str] = Field(default_factory=list)
