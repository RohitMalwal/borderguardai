"""Officer recommendation — FUTURE MODULE (interface only).

Will translate fused risk + evidence into a recommended action (e.g. CLEAR /
REFER / HOLD) with rationale, always leaving the final decision to a human
officer. Not implemented; no fabricated recommendations.
"""
from __future__ import annotations

from app.schemas.screening import ScreeningResult


class RecommendationEngine:
    enabled = False

    def recommend(self, result: ScreeningResult) -> dict:
        raise NotImplementedError("Recommendation is not implemented in this prototype.")
