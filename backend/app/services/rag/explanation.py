"""Explanation generation — FUTURE MODULE (interface only).

Will generate a grounded, human-readable narrative of the screening outcome
using retrieved evidence. Runs locally/offline in the final system. Not
implemented in this prototype; no fabricated explanations are produced.
"""
from __future__ import annotations

from app.schemas.screening import ScreeningResult


class ExplanationGenerator:
    enabled = False

    def explain(self, result: ScreeningResult) -> dict:
        raise NotImplementedError("Explanation is not implemented in this prototype.")
