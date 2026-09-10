"""Watchlist screening — FUTURE MODULE (interface only).

Will match extracted identity fields against a LOCAL watchlist dataset. This
prototype does NOT claim access to any government or law-enforcement database.
No lookups are performed and no results are fabricated.
"""
from __future__ import annotations


class WatchlistScreener:
    enabled = False

    def screen(self, identity: dict) -> dict:
        raise NotImplementedError(
            "Watchlist screening is not implemented in this prototype. "
            "This system does not access any government database."
        )
