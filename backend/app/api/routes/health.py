"""Health and capability reporting."""
from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.config import settings
from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.head("/health")
@router.get("/health/ping")
def health_ping() -> Response:
    """Lightweight liveness probe for uptime monitors (e.g. UptimeRobot).

    Responds to a cheap HEAD/GET without running the OCR/face capability
    checks, so pinging it every few minutes stays essentially free. HEAD
    responses carry no body by design.
    """
    return Response(status_code=200)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Report capability status WITHOUT initializing PaddleOCR. Forcing a model
    # load here would OOM small hosts (512MB) on the very first health check.
    # OCR is considered "available" if it's enabled and hasn't failed to load;
    # the engine itself is lazily loaded on the first /screening/analyze call.
    try:
        from app.services.ocr.paddle_service import status_without_loading
        ocr_state = status_without_loading()
        ocr_ok = bool(ocr_state["enabled"]) and ocr_state["load_error"] is None
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
