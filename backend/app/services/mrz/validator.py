"""ICAO Doc 9303 check-digit validation for TD3 MRZ.

Check-digit algorithm:
  * Map characters: 0-9 -> value; A-Z -> 10-35; '<' -> 0.
  * Multiply each character value by the repeating weight pattern 7,3,1.
  * Sum, take modulo 10 — that is the expected check digit.

We validate the document number, date of birth, expiry, and the composite
check digit (computed over the concatenation specified by ICAO). Every result
is a real computation; failures name exactly which digit did not verify.
"""
from __future__ import annotations

from app.core.constants import CHECK_DIGIT_WEIGHTS, MrzStatus
from app.schemas.analysis import MrzResult, MrzValidation
from app.services.mrz.parser import ParsedMrz, yymmdd_to_iso


def char_value(ch: str) -> int:
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    if "A" <= ch <= "Z":
        return ord(ch) - ord("A") + 10
    return 0  # unknown chars contribute 0; length checks catch corruption


def compute_check_digit(data: str) -> int:
    total = 0
    for i, ch in enumerate(data):
        total += char_value(ch) * CHECK_DIGIT_WEIGHTS[i % 3]
    return total % 10


def _verify(data: str, expected: str) -> bool | None:
    """Return True/False, or None if the expected digit is missing/non-numeric
    (cannot be meaningfully checked)."""
    if expected is None or expected == "" or expected == "<":
        return None
    if not expected.isdigit():
        return False
    return compute_check_digit(data) == int(expected)


def validate_mrz(parsed: ParsedMrz, detection_confidence: float) -> MrzResult:
    """Build the full MrzResult (fields + validation) from a parsed TD3 MRZ."""
    errors: list[str] = list(parsed.errors)

    # Document-number check uses the raw 9-char MRZ field (fillers included).
    doc_ok = _verify(parsed.line2[0:9], parsed.document_number_check)
    dob_ok = _verify(parsed.date_of_birth, parsed.date_of_birth_check)
    exp_ok = _verify(parsed.expiry_date, parsed.expiry_date_check)

    # Composite check spans: passport no + check + nationality... actually per
    # ICAO it is line2 positions 1-10, 14-20, 22-28, 29-43 concatenated.
    composite_source = (
        parsed.line2[0:10] + parsed.line2[13:20] + parsed.line2[21:28] + parsed.line2[28:43]
    )
    composite_ok = _verify(composite_source, parsed.composite_check)

    line_lengths_ok = len(parsed.line1) == 44 and len(parsed.line2) == 44

    validation = MrzValidation(
        document_number=doc_ok,
        date_of_birth=dob_ok,
        expiry_date=exp_ok,
        composite=composite_ok,
        line_lengths_ok=line_lengths_ok,
    )

    for name, ok in [
        ("document number", doc_ok),
        ("date of birth", dob_ok),
        ("expiry date", exp_ok),
        ("composite", composite_ok),
    ]:
        if ok is False:
            errors.append(f"{name} check digit failed.")

    fields = {
        "document_type": parsed.document_type or None,
        "issuing_country": parsed.issuing_country or None,
        "surname": parsed.surname or None,
        "given_names": parsed.given_names or None,
        "full_name": (
            " ".join(p for p in [parsed.given_names, parsed.surname] if p) or None
        ),
        "document_number": parsed.document_number or None,
        "nationality": parsed.nationality or None,
        "date_of_birth": yymmdd_to_iso(parsed.date_of_birth, expiry=False),
        "sex": parsed.sex or None,
        "expiry_date": yymmdd_to_iso(parsed.expiry_date, expiry=True),
    }

    # Determine an overall status.
    checks = [doc_ok, dob_ok, exp_ok, composite_ok]
    performed = [c for c in checks if c is not None]
    if not line_lengths_ok:
        status = MrzStatus.INVALID
    elif performed and all(performed):
        status = MrzStatus.VALID
    elif any(c is False for c in checks):
        status = MrzStatus.INVALID
    else:
        status = MrzStatus.LOW_CONFIDENCE

    return MrzResult(
        detected=True,
        status=status.value,
        raw_lines=[parsed.line1, parsed.line2],
        confidence=detection_confidence,
        fields=fields,
        validation=validation,
        errors=errors,
        message=(
            None
            if status == MrzStatus.VALID
            else "One or more MRZ checks did not verify; see validation details."
        ),
    )
