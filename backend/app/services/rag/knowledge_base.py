"""Knowledge base loader — FUTURE MODULE (interface only).

Will index the local `knowledge/` corpus (ICAO rules, document specimens,
issuing-state notes) for offline retrieval. Not implemented in this prototype.
"""
from __future__ import annotations


class KnowledgeBase:
    enabled = False

    def load(self) -> None:
        raise NotImplementedError("Knowledge base is not implemented in this prototype.")
