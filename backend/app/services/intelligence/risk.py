"""Risk fusion — FUTURE MODULE (interface only).

Will combine signals from quality, consistency, MRZ validation, forensic and
watchlist stages into a calibrated risk score with per-signal contributions.
Deliberately unimplemented: no fabricated scores.
"""
from __future__ import annotations

from app.schemas.screening import ScreeningResult


class RiskFusionEngine:
    """Extension point for downstream risk scoring."""

    enabled = False

    def score(self, result: ScreeningResult) -> dict:
        raise NotImplementedError("Risk fusion is not implemented in this prototype.")
