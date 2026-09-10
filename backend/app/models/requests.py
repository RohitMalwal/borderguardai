"""API-level request descriptors.

The analyze endpoint receives multipart/form-data (files), so there is no JSON
request body to model. This module documents the accepted inputs and holds
options that future versions may accept as form fields.
"""
from __future__ import annotations

from pydantic import BaseModel


class ScreeningOptions(BaseModel):
    """Optional analysis toggles (reserved for future form fields)."""

    run_forensic: bool = True
    run_face: bool = True
