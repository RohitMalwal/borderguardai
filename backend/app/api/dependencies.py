"""Shared FastAPI dependencies.

Kept minimal for the prototype (no auth, no DB). This is the seam where future
concerns — auth, rate limiting, request context, an offline job queue — will
be introduced without touching route handlers.
"""
from __future__ import annotations

from app.core.config import settings


def get_settings():
    return settings
