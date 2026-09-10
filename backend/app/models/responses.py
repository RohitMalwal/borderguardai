"""API-level response envelopes shared by multiple routes."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    capabilities: dict[str, bool]


class ErrorResponse(BaseModel):
    """Uniform, professional error payload. The frontend renders `message`."""

    status: str = "error"
    code: str
    message: str
    detail: Optional[str] = None
