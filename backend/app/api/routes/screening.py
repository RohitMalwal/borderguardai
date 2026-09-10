"""Screening endpoints — passport upload and full pipeline analysis."""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.responses import ErrorResponse
from app.orchestrator.screening_pipeline import run_screening
from app.schemas.screening import ScreeningResult
from app.services.document.document_service import DocumentError

# Use uvicorn's error logger so tracebacks are visible in the server console
# under the standard `uvicorn app.main:app` run command.
logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/screening", tags=["screening"])


def _error(status_code: int, code: str, message: str, detail: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message, detail=detail).model_dump(),
    )


@router.post(
    "/analyze",
    response_model=ScreeningResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze(
    passport: UploadFile = File(..., description="Passport biodata page (JPG/PNG)"),
    traveller: UploadFile | None = File(
        None, description="Optional live traveller photo for face comparison"
    ),
):
    """Accept a passport image (and optional traveller photo), run the full
    local analysis pipeline, and return one structured JSON result."""
    try:
        raw = await passport.read()
    except Exception:  # noqa: BLE001
        return _error(400, "read_failed", "Could not read the uploaded file.")

    if not raw:
        return _error(400, "empty_file", "The uploaded passport file is empty.")

    traveller_raw = None
    if traveller is not None:
        try:
            traveller_raw = await traveller.read()
        except Exception:  # noqa: BLE001
            traveller_raw = None

    try:
        result = run_screening(
            raw=raw,
            filename=passport.filename or "passport",
            content_type=passport.content_type,
            traveller_raw=traveller_raw or None,
            traveller_filename=(traveller.filename if traveller else None),
        )
        return result
    except DocumentError as exc:
        return _error(400, exc.code, exc.message)
    except Exception as exc:  # noqa: BLE001 - last-resort professional error
        # Surface the real traceback in the server logs so failures are
        # diagnosable (we never silently swallow it).
        logger.exception("Screening pipeline failed for %r", passport.filename)
        return _error(
            500,
            "processing_error",
            "An unexpected error occurred while analyzing the document. "
            "Please try again with a clear image of the passport biodata page.",
            detail=f"{type(exc).__name__}: {exc}",
        )


@router.get("/config")
def config():
    """Expose non-secret limits so the frontend can validate before upload."""
    return {
        "allowed_extensions": sorted(settings.ALLOWED_EXTENSIONS),
        "max_upload_bytes": settings.MAX_UPLOAD_BYTES,
    }
