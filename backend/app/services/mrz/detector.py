"""MRZ candidate detection from OCR output.

The Machine Readable Zone of a TD3 passport is two lines of 44 characters over
the OCR alphabet [A-Z0-9<]. OCR rarely returns these two lines cleanly, so we:

  1. Collect all OCR lines, uppercased and stripped of spaces.
  2. Keep those that are strongly "MRZ-like": high proportion of [A-Z0-9<] and
     containing filler '<' characters.
  3. Normalize common OCR confusions conservatively.
  4. Pad/trim toward 44 chars and return the best two consecutive candidates.

We never invent characters; padding uses '<' (the MRZ filler) only, and we
report a confidence and an honest status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.constants import TD3_LINE_LENGTH, MrzStatus
from app.schemas.analysis import OcrTextLine

MRZ_CHARS = re.compile(r"[A-Z0-9<]")
# Conservative OCR-confusion fixes applied ONLY to MRZ candidate lines.
_CONFUSIONS = str.maketrans({" ": "", "«": "<", "»": "<", "€": "<", "‹": "<", "›": "<"})


@dataclass
class MrzCandidate:
    lines: list[str]
    status: MrzStatus
    confidence: float


def _mrz_score(text: str) -> float:
    """Fraction of characters that belong to the MRZ alphabet."""
    if not text:
        return 0.0
    hits = len(MRZ_CHARS.findall(text))
    return hits / len(text)


def _clean(text: str) -> str:
    t = text.upper().translate(_CONFUSIONS)
    # Drop anything outside the MRZ alphabet (stray punctuation/diacritics).
    return "".join(ch for ch in t if MRZ_CHARS.match(ch))


def _fit_length(line: str) -> str:
    if len(line) > TD3_LINE_LENGTH:
        return line[:TD3_LINE_LENGTH]
    if len(line) < TD3_LINE_LENGTH:
        return line.ljust(TD3_LINE_LENGTH, "<")
    return line


def detect_mrz(ocr_lines: list[OcrTextLine]) -> MrzCandidate:
    """Find the two MRZ lines among OCR output."""
    if not ocr_lines:
        return MrzCandidate([], MrzStatus.NOT_DETECTED, 0.0)

    # Collect qualifying lines with position. We select structurally, NOT by
    # raw position: TD3 line 2 is unmistakable (dense digits + fillers), and
    # line 1 is the MRZ-like line DIRECTLY ABOVE it. Selecting line 1 as
    # "closest line above line 2" means prose that sits *below* the MRZ
    # (page footers, disclaimers, signatures) can never be mistaken for it.
    candidates: list[dict] = []
    for line in ocr_lines:
        cleaned = _clean(line.text)
        if len(cleaned) < 12 or _mrz_score(cleaned) < 0.8:
            continue
        y = max((p[1] for p in line.box), default=0.0)
        digits = sum(ch.isdigit() for ch in cleaned)
        candidates.append({
            "conf": line.confidence, "text": cleaned, "y": y,
            "digits": digits, "digit_ratio": digits / len(cleaned),
            "fills": cleaned.count("<"), "has_dd": "<<" in cleaned,
            "alpha": sum(ch.isalpha() for ch in cleaned),
        })

    if not candidates:
        return MrzCandidate([], MrzStatus.NOT_DETECTED, 0.0)

    # --- Line 2: the digit-dense code line (dates, numbers, check digits) ---
    line2_pool = [c for c in candidates if c["digit_ratio"] >= 0.30 and len(c["text"]) >= 28]
    if not line2_pool:
        # No structural line 2 -> cannot parse/validate a TD3 MRZ honestly.
        return MrzCandidate([], MrzStatus.NOT_DETECTED, 0.0)

    def _line2_score(c: dict) -> float:
        return (
            c["digit_ratio"] * 3.0
            + min(c["fills"], 8) * 0.15
            + (1.0 - abs(len(c["text"]) - TD3_LINE_LENGTH) / TD3_LINE_LENGTH)
            + c["conf"] * 0.5
        )

    l2 = max(line2_pool, key=_line2_score)

    # --- Line 1: the MRZ-like line immediately ABOVE line 2 -----------------
    above = [
        c for c in candidates
        if c is not l2 and c["y"] < l2["y"] and c["alpha"] >= 3
    ]
    if above:
        # Closest above wins; break ties toward name-field fillers.
        l1 = max(above, key=lambda c: (c["y"], c["has_dd"]))
        lines = [_fit_length(l1["text"]), _fit_length(l2["text"])]
        conf = round((l1["conf"] + l2["conf"]) / 2.0, 4)
    else:
        # Line 2 found but no plausible line 1: report low confidence with the
        # single line rather than inventing one.
        return MrzCandidate([_fit_length(l2["text"])], MrzStatus.LOW_CONFIDENCE, l2["conf"])

    status = MrzStatus.DETECTED if conf >= 0.5 else MrzStatus.LOW_CONFIDENCE
    return MrzCandidate(lines, status, conf)
