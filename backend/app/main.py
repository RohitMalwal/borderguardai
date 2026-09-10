"""BorderGuard AI — FastAPI application entry point.

Local-first, offline-capable. No API keys, no external services. Run with:

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, screening
from app.core.config import settings

settings.ensure_dirs()

# NOTE: PaddleOCR is intentionally NOT preloaded at startup. Loading the models
# eagerly pushes memory over the 512MB limit on small hosts (e.g. Render free
# tier) and OOM-kills the process before it can serve a single request. The OCR
# engine is lazy-loaded on the first /api/screening/analyze call instead (see
# app.services.ocr.paddle_service._get_engine), keeping startup lightweight so
# health checks and the rest of the API stay responsive.

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Explainable, offline-first border document screening prototype. "
        "Independently analyzes visual OCR and machine-readable (MRZ) data to "
        "surface inconsistencies. This prototype does not access any government "
        "database and does not provide certified forensic analysis."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(screening.router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }
