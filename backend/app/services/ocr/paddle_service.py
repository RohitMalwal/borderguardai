"""Local OCR via PaddleOCR.

Design goals:
  * Run entirely offline (models cache locally after first download).
  * Never fabricate text. If PaddleOCR cannot be loaded (e.g. no wheel for the
    running Python version), we return an explicit `engine_unavailable` result
    rather than inventing passport data.
  * Lazy, cached engine init so importing this module is cheap and app startup
    stays fast.
"""
from __future__ import annotations

import threading

import cv2
import numpy as np

from app.core.config import settings
from app.schemas.analysis import OcrTextLine, VisualOcrResult

_engine = None
_engine_lock = threading.Lock()
_load_error: str | None = None


def _construct(PaddleOCR):
    """Build a PaddleOCR engine, tolerating constructor differences between
    releases. Preferred kwargs match the 2.x series this project targets; if a
    build rejects them we retry with a minimal constructor rather than failing."""
    attempts = (
        {"use_angle_cls": True, "lang": settings.OCR_LANG, "show_log": False},
        {"use_angle_cls": True, "lang": settings.OCR_LANG},
        {"lang": settings.OCR_LANG},
        {},
    )
    last_exc = None
    for kwargs in attempts:
        try:
            return PaddleOCR(**kwargs)
        except TypeError as exc:  # unknown/removed kwarg for this version
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    return PaddleOCR()


def _get_engine():
    """Return a cached PaddleOCR instance, or None if unavailable."""
    global _engine, _load_error
    if _engine is not None or _load_error is not None:
        return _engine
    with _engine_lock:
        if _engine is not None or _load_error is not None:
            return _engine
        try:
            from paddleocr import PaddleOCR  # type: ignore

            _engine = _construct(PaddleOCR)
        except Exception as exc:  # noqa: BLE001 - report any load failure honestly
            _load_error = str(exc)
            _engine = None
    return _engine


def preload() -> dict:
    """Force model download/initialization so an offline demo has everything
    cached. Returns a small status dict. Safe to call repeatedly."""
    engine = _get_engine()
    if engine is None:
        return {"ocr": False, "error": _load_error or "PaddleOCR unavailable"}
    # Run one tiny inference to ensure detection+recognition models are fetched.
    try:
        probe = np.full((64, 192, 3), 255, dtype=np.uint8)
        _run_engine(engine, probe)
    except Exception as exc:  # noqa: BLE001 - preload probe is best-effort
        return {"ocr": True, "warmup_warning": str(exc)}
    return {"ocr": True}


def _run_engine(engine, image_bgr: np.ndarray):
    """Call the engine's OCR, tolerating the `cls` kwarg being absent."""
    rgb = image_bgr[:, :, ::-1]
    try:
        return engine.ocr(rgb, cls=True)
    except TypeError:
        return engine.ocr(rgb)


def ocr_mrz_band(image_bgr: np.ndarray, top_frac: float = 0.72, scale: int = 4) -> list[OcrTextLine]:
    """OCR only the bottom MRZ band, upscaled, and return lines with boxes
    mapped back to full-image coordinates.

    The MRZ's '<' filler characters are read unreliably at biodata-page scale
    (they get mistaken for letters), which breaks check-digit validation.
    Reading a higher-resolution crop of just the bottom band recovers them.
    Returns [] if OCR is unavailable or the crop is empty — never fabricated.
    """
    engine = _get_engine()
    if engine is None:
        return []
    h, w = image_bgr.shape[:2]
    y0 = int(h * top_frac)
    band = image_bgr[y0:h, 0:w]
    if band.size == 0:
        return []
    band = cv2.resize(
        band, (w * scale, band.shape[0] * scale), interpolation=cv2.INTER_CUBIC
    )
    try:
        raw = _run_engine(engine, band)
    except Exception:  # noqa: BLE001 - supplementary pass must never crash screening
        return []
    lines = _normalize_paddle_result(raw)
    for ln in lines:  # map band-space boxes back to full-image coordinates
        ln.box = [[x / scale, y0 + y / scale] for x, y in ln.box]
    return lines


def is_available() -> bool:
    if not settings.OCR_ENABLED:
        return False
    return _get_engine() is not None


def _normalize_paddle_result(result) -> list[OcrTextLine]:
    """PaddleOCR's output shape has varied across versions. Handle the common
    `[[ [box, (text, conf)], ... ]]` layout defensively."""
    lines: list[OcrTextLine] = []
    if not result:
        return lines
    # result is typically a list with one element per image.
    page = result[0] if len(result) == 1 and isinstance(result[0], list) else result
    for entry in page or []:
        try:
            box = entry[0]
            text, conf = entry[1][0], float(entry[1][1])
            poly = [[float(p[0]), float(p[1])] for p in box]
            lines.append(OcrTextLine(text=str(text), confidence=conf, box=poly))
        except Exception:  # noqa: BLE001 - skip malformed entries, keep the rest
            continue
    return lines


def run_ocr(image_bgr: np.ndarray) -> VisualOcrResult:
    """Run OCR on a BGR image and return raw lines (fields added later)."""
    if not settings.OCR_ENABLED:
        return VisualOcrResult(
            engine="unavailable",
            status="engine_unavailable",
            message="OCR is disabled by configuration.",
        )

    engine = _get_engine()
    if engine is None:
        return VisualOcrResult(
            engine="unavailable",
            status="engine_unavailable",
            message=(
                "PaddleOCR could not be loaded in this environment"
                + (f" ({_load_error})." if _load_error else ".")
                + " Install a compatible paddleocr/paddlepaddle build to enable "
                "real text extraction. No text is fabricated in the meantime."
            ),
        )

    try:
        raw = _run_engine(engine, image_bgr)
    except Exception as exc:  # noqa: BLE001
        return VisualOcrResult(
            engine="paddleocr",
            status="failed",
            message=f"OCR engine raised an error: {exc}",
        )

    lines = _normalize_paddle_result(raw)
    if not lines:
        return VisualOcrResult(
            engine="paddleocr",
            status="failed",
            message="No text was detected in the image.",
        )

    mean_conf = round(sum(l.confidence for l in lines) / len(lines), 4)
    status = "complete" if mean_conf >= settings.OCR_MIN_CONFIDENCE else "low_confidence"
    return VisualOcrResult(
        engine="paddleocr",
        status=status,
        raw_text=lines,
        mean_confidence=mean_conf,
        message=(
            None
            if status == "complete"
            else "Overall OCR confidence is low. Manual review may be required."
        ),
    )
