"""BorderGuard AI — FastAPI application entry point.

Local-first, offline-capable. No API keys, no external services. Run with:

    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, screening
from app.core.config import settings

settings.ensure_dirs()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload PaddleOCR models during startup so first request doesn't timeout on Render
    from app.services.ocr.paddle_service import preload
    preload()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Explainable, offline-first border document screening prototype. "
        "Independently analyzes visual OCR and machine-readable (MRZ) data to "
        "surface inconsistencies. This prototype does not access any government "
        "database and does not provide certified forensic analysis."
    ),
    lifespan=lifespan,
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
