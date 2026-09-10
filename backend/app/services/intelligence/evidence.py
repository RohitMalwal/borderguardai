"""Evidence graph assembly — FUTURE MODULE (interface only).

Will assemble a structured, linkable evidence graph (nodes = signals/fields,
edges = supports/contradicts) for officer review and RAG explanation.
"""
from __future__ import annotations

from app.schemas.screening import ScreeningResult


class EvidenceBuilder:
    enabled = False

    def build(self, result: ScreeningResult) -> dict:
        raise NotImplementedError("Evidence graph is not implemented in this prototype.")
