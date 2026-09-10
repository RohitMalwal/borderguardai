"""Document I/O: safe decoding of uploads and persistence of artifacts.

This service owns the boundary between raw bytes and numpy image arrays, and
between in-memory arrays and on-disk artifacts. It raises clear, typed errors
so the API can respond with professional messages instead of crashing.
"""
from __future__ import annotations

import uuid
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings
from app.schemas.document import ImageInfo


class DocumentError(Exception):
    """Raised for invalid/corrupt/unsupported document inputs."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def validate_extension(filename: str) -> None:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise DocumentError(
            "unsupported_format",
            f"Unsupported file type '{suffix or 'unknown'}'. "
            "Please upload a JPG, JPEG or PNG passport image.",
        )


def decode_image(raw: bytes) -> np.ndarray:
    """Decode raw bytes to a BGR image, raising DocumentError on failure."""
    if not raw:
        raise DocumentError("empty_file", "The uploaded file is empty.")
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise DocumentError(
            "file_too_large",
            f"File exceeds the {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )
    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise DocumentError(
            "corrupt_image",
            "The image could not be decoded. It may be corrupt or not a real image.",
        )
    return image


def new_screening_id() -> str:
    return uuid.uuid4().hex[:12]


def build_image_info(
    filename: str, content_type: str | None, size_bytes: int, image: np.ndarray
) -> ImageInfo:
    h, w = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    return ImageInfo(
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        width=w,
        height=h,
        channels=channels,
    )


def persist_artifact(image: np.ndarray, screening_id: str, name: str) -> str | None:
    """Write an image under storage/processed/<screening_id>/ and return the
    path relative to the storage root (or None if persistence is disabled)."""
    if not settings.PERSIST_ARTIFACTS:
        return None
    out_dir = settings.PROCESSED_DIR / screening_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.png"
    cv2.imwrite(str(out_path), image)
    return str(out_path.relative_to(settings.STORAGE_DIR))


def persist_upload(raw: bytes, screening_id: str, filename: str) -> str | None:
    """Save the untouched original upload for audit/traceability."""
    if not settings.PERSIST_ARTIFACTS:
        return None
    suffix = Path(filename).suffix.lower() or ".img"
    out_dir = settings.UPLOAD_DIR / screening_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"original{suffix}"
    out_path.write_bytes(raw)
    return str(out_path.relative_to(settings.STORAGE_DIR))
