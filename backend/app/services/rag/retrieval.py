"""Evidence retrieval — FUTURE MODULE (interface only).

Will perform offline retrieval over the indexed knowledge base to ground
explanations in cited source material. Not implemented in this prototype.
"""
from __future__ import annotations


class Retriever:
    enabled = False

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        raise NotImplementedError("Retrieval is not implemented in this prototype.")
