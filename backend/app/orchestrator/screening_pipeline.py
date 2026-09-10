"""The single, unified screening pipeline.

`run_screening` is the one entry point the API calls. It executes the
implemented stages in order, records honest per-stage state (including timings),
and assembles one `ScreeningResult`. Each stage is isolated so a failure in one
degrades gracefully (WARNING/ERROR) without crashing the whole request.

Reserved keys (intelligence / explanation / officer_decision) are left present
but null so future modules can attach to the same object.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.core.constants import PipelineStage, StageStatus
from app.schemas.screening import ScreeningResult, StageState
from app.services.consistency.comparison import compare
from app.services.document import document_service as docsvc
from app.services.document.preprocessing import run_preprocessing
from app.services.document.quality import analyze_quality
from app.services.face.detector import detect_faces
from app.services.face.matcher import compare_faces
from app.services.forensic.tamper import analyze_tamper
from app.services.mrz.detector import detect_mrz
from app.services.mrz.parser import parse_td3
from app.services.mrz.validator import validate_mrz
from app.services.ocr.field_extractor import extract_fields
from app.services.ocr.paddle_service import run_ocr
from app.schemas.document import PreprocessingResult, PreprocessingStep

logger = logging.getLogger("uvicorn.error")


class _StageTimer:
    """Collects StageState entries with timings and a running warning list."""

    def __init__(self) -> None:
        self.stages: list[StageState] = []
        self.warnings: list[str] = []

    def record(self, stage: PipelineStage, status: StageStatus, started: float,
               message: str | None = None) -> None:
        self.stages.append(
            StageState(
                stage=stage.value,
                status=status.value,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                message=message,
            )
        )
        if message and status in (StageStatus.WARNING, StageStatus.ERROR):
            self.warnings.append(message)


def run_screening(
    raw: bytes,
    filename: str,
    content_type: str | None,
    traveller_raw: bytes | None = None,
    traveller_filename: str | None = None,
) -> ScreeningResult:
    timer = _StageTimer()
    screening_id = docsvc.new_screening_id()

    # --- Stage: DOCUMENT (decode + persist original) ----------------------
    t = time.perf_counter()
    docsvc.validate_extension(filename)
    image = docsvc.decode_image(raw)  # raises DocumentError -> handled in route
    try:
        # Best-effort audit copy; a storage write failure must not fail analysis.
        docsvc.persist_upload(raw, screening_id, filename)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not persist original upload: %s", exc)
    image_info = docsvc.build_image_info(filename, content_type, len(raw), image)
    timer.record(PipelineStage.DOCUMENT, StageStatus.COMPLETE, t)

    result = ScreeningResult(
        screening_id=screening_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="complete",
        document=image_info,
    )

    # --- Stage: QUALITY ---------------------------------------------------
    t = time.perf_counter()
    try:
        result.quality = analyze_quality(image)
        status = StageStatus.WARNING if result.quality.warnings else StageStatus.COMPLETE
        msg = result.quality.warnings[0] if result.quality.warnings else None
        timer.record(PipelineStage.QUALITY, status, t, msg)
    except Exception as exc:  # noqa: BLE001
        timer.record(PipelineStage.QUALITY, StageStatus.ERROR, t, f"Quality analysis failed: {exc}")

    # --- Stage: PREPROCESSING --------------------------------------------
    t = time.perf_counter()
    primary_image = image
    try:
        pre = run_preprocessing(image)
        primary_image = pre.primary
        original_path = docsvc.persist_artifact(pre.original, screening_id, "original")
        primary_path = docsvc.persist_artifact(pre.primary, screening_id, "primary")
        result.preprocessing = PreprocessingResult(
            steps=[
                PreprocessingStep(name=s.name, applied=s.applied, detail=s.detail)
                for s in pre.steps
            ],
            original_artifact=original_path,
            primary_artifact=primary_path,
        )
        timer.record(PipelineStage.PREPROCESSING, StageStatus.COMPLETE, t)
    except Exception as exc:  # noqa: BLE001
        timer.record(PipelineStage.PREPROCESSING, StageStatus.WARNING, t,
                     f"Preprocessing degraded to original image: {exc}")

    # --- Stage: OCR -------------------------------------------------------
    t = time.perf_counter()
    ocr = run_ocr(primary_image)
    if ocr.status in ("complete", "low_confidence"):
        try:
            ocr = extract_fields(ocr)
            st = StageStatus.WARNING if ocr.status == "low_confidence" else StageStatus.COMPLETE
            timer.record(PipelineStage.OCR, st, t, ocr.message)
        except Exception as exc:  # noqa: BLE001 - field extraction must not 500
            logger.exception("OCR field extraction failed")
            timer.record(PipelineStage.OCR, StageStatus.WARNING, t,
                         f"Field extraction failed; raw text retained. ({exc})")
    else:
        timer.record(PipelineStage.OCR, StageStatus.WARNING, t, ocr.message)
    result.visual_ocr = ocr

    # --- Stage: MRZ (detection) ------------------------------------------
    t = time.perf_counter()
    # Supplement full-page OCR with a higher-resolution pass over the bottom
    # MRZ band. The '<' filler characters are unreadable at page scale, which
    # breaks check-digit validation; the upscaled band recovers them. Boxes are
    # mapped back to full-image coordinates so the detector's position ranking
    # still works. Best-effort: on any issue we fall back to full-page lines.
    mrz_input = list(ocr.raw_text)
    try:
        from app.services.ocr.paddle_service import is_available, ocr_mrz_band
        if is_available():
            # Read the band from the ORIGINAL image (preprocessing degrades the
            # fine MRZ print) and SUPPLEMENT the full-page lines. We never
            # replace them: on scans/screenshots the MRZ is not at the very
            # bottom, so a blind band crop can miss it entirely. detect_mrz
            # selects structurally, so the higher-quality band lines win when
            # present and the full-page lines cover the band's blind spots.
            mrz_input += ocr_mrz_band(image)
    except Exception:  # noqa: BLE001
        pass
    from app.schemas.analysis import MrzResult
    try:
        candidate = detect_mrz(mrz_input)
    except Exception as exc:  # noqa: BLE001 - detection must not 500 the request
        logger.exception("MRZ detection failed")
        candidate = None
        result.mrz = MrzResult(detected=False, status="not_detected",
                               message=f"MRZ detection failed: {exc}")
        timer.record(PipelineStage.MRZ, StageStatus.ERROR, t, result.mrz.message)
        timer.record(PipelineStage.VALIDATION, StageStatus.SKIPPED, t,
                     "Skipped: MRZ detection error.")

    if candidate is not None and candidate.lines and candidate.status.value in ("detected", "low_confidence"):
        try:
            parsed = parse_td3(candidate.lines)
            timer.record(
                PipelineStage.MRZ,
                StageStatus.COMPLETE if candidate.status.value == "detected" else StageStatus.WARNING,
                t,
                None if candidate.status.value == "detected"
                else "MRZ detected with low confidence.",
            )

            # --- Stage: VALIDATION ---------------------------------------
            tv = time.perf_counter()
            result.mrz = validate_mrz(parsed, candidate.confidence)
            vstatus = StageStatus.COMPLETE if result.mrz.status == "valid" else StageStatus.WARNING
            timer.record(PipelineStage.VALIDATION, vstatus, tv, result.mrz.message)
        except Exception as exc:  # noqa: BLE001 - parse/validate must not 500
            logger.exception("MRZ parse/validation failed")
            result.mrz = MrzResult(
                detected=True, status="invalid", raw_lines=candidate.lines,
                message=f"MRZ parsing/validation failed: {exc}",
            )
            timer.record(PipelineStage.VALIDATION, StageStatus.ERROR, t, result.mrz.message)
    elif candidate is not None:
        result.mrz = MrzResult(
            detected=False,
            status="not_detected",
            message="MRZ could not be reliably detected. Ensure the full passport "
                    "biodata page (including the two bottom code lines) is visible.",
        )
        timer.record(PipelineStage.MRZ, StageStatus.WARNING, t, result.mrz.message)
        timer.record(PipelineStage.VALIDATION, StageStatus.SKIPPED, t,
                     "Skipped: no MRZ to validate.")

    # --- Stage: CONSISTENCY ----------------------------------------------
    t = time.perf_counter()
    result.consistency = compare(result.visual_ocr, result.mrz)
    cstat = {
        "match": StageStatus.COMPLETE,
        "partial": StageStatus.WARNING,
        "mismatch": StageStatus.WARNING,
        "not_available": StageStatus.SKIPPED,
    }.get(result.consistency.overall_status, StageStatus.COMPLETE)
    cmsg = None
    if result.consistency.overall_status == "mismatch":
        cmsg = "Visual OCR and MRZ disagree on one or more identity fields."
    elif result.consistency.overall_status == "not_available":
        cmsg = "Insufficient data from OCR/MRZ to cross-validate."
    timer.record(PipelineStage.CONSISTENCY, cstat, t, cmsg)

    # --- Stage: FACE ------------------------------------------------------
    t = time.perf_counter()
    try:
        face = detect_faces(image)
        if traveller_raw:
            try:
                docsvc.validate_extension(traveller_filename or "traveller.jpg")
                _traveller = docsvc.decode_image(traveller_raw)
                face = compare_faces(None, None, face)  # backend not bundled
            except Exception:  # noqa: BLE001 - traveller issues never crash screening
                face.comparison_available = False
        result.face = face
        fstat = StageStatus.COMPLETE if face.detected else StageStatus.WARNING
        timer.record(PipelineStage.FACE, fstat, t, face.message)
    except Exception as exc:  # noqa: BLE001
        from app.schemas.analysis import FaceResult
        result.face = FaceResult(
            detected=False, status="unavailable",
            message=f"Face detection unavailable in this environment: {exc}",
        )
        timer.record(PipelineStage.FACE, StageStatus.WARNING, t, result.face.message)

    # --- Stage: FORENSIC (experimental) ----------------------------------
    t = time.perf_counter()
    try:
        result.forensic = analyze_tamper(image)
        timer.record(PipelineStage.FORENSIC, StageStatus.COMPLETE, t)
    except Exception as exc:  # noqa: BLE001
        timer.record(PipelineStage.FORENSIC, StageStatus.WARNING, t, f"Forensic signal failed: {exc}")

    # --- Finalize ---------------------------------------------------------
    result.stages = timer.stages
    result.warnings = timer.warnings
    if any(s.status == StageStatus.ERROR.value for s in result.stages):
        result.status = "partial"
    return result
