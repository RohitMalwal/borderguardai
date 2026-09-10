"""Health and capability reporting."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Report real capability status so the UI can be honest about OCR.
    try:
        from app.services.ocr.paddle_service import is_available as ocr_available
        ocr_ok = bool(ocr_available())
    except Exception:  # noqa: BLE001
        ocr_ok = False

    try:
        from app.services.face.detector import _get_cascade
        face_ok = _get_cascade() is not None
    except Exception:  # noqa: BLE001
        face_ok = False

    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        capabilities={
            "ocr": ocr_ok,
            "face_detection": face_ok,
            "mrz_validation": True,
            "quality_analysis": True,
            "forensic_experimental": True,
        },
    )
