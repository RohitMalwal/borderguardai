"""Application configuration.

Central, environment-overridable settings for BorderGuard AI. Everything here
has a sane local-first default so the prototype runs fully offline with zero
setup and zero API keys.
"""
from __future__ import annotations

import os
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings. Deliberately dependency-light (no pydantic-settings)
    so the backend boots even in a minimal environment."""

    APP_NAME: str = "BorderGuard AI"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # --- Paths -------------------------------------------------------------
    # backend/app/core/config.py -> project root is three parents up.
    BASE_DIR: Path = Path(__file__).resolve().parents[3]
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    PROCESSED_DIR: Path = STORAGE_DIR / "processed"
    RESULTS_DIR: Path = STORAGE_DIR / "results"

    # --- Upload constraints ------------------------------------------------
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png"}
    ALLOWED_CONTENT_TYPES: set[str] = {"image/jpeg", "image/png"}
    MAX_UPLOAD_BYTES: int = 15 * 1024 * 1024  # 15 MB

    # --- CORS (local React dev servers) -----------------------------------
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # --- OCR ---------------------------------------------------------------
    # PaddleOCR is heavy and may not have wheels on every Python version.
    # When it cannot be loaded the pipeline degrades honestly instead of
    # fabricating text. Set BORDERGUARD_OCR_LANG to change recognition lang.
    OCR_ENABLED: bool = _env_bool("BORDERGUARD_OCR_ENABLED", True)
    OCR_LANG: str = os.getenv("BORDERGUARD_OCR_LANG", "en")
    OCR_MIN_CONFIDENCE: float = float(os.getenv("BORDERGUARD_OCR_MIN_CONF", "0.5"))

    # Persist intermediate artifacts (preprocessed images) to storage/.
    PERSIST_ARTIFACTS: bool = _env_bool("BORDERGUARD_PERSIST_ARTIFACTS", True)

    def ensure_dirs(self) -> None:
        for path in (self.UPLOAD_DIR, self.PROCESSED_DIR, self.RESULTS_DIR):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
