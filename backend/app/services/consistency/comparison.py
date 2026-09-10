"""Visual OCR <-> MRZ cross-validation.

Two independent sources of truth are compared field by field:
  SOURCE A: visual passport OCR (field_extractor)
  SOURCE B: MRZ parsing/validation

Values are normalized before comparison (dates to ISO, names collapsed and
uppercased, document numbers stripped) so cosmetic differences don't create
false mismatches. Each field gets its own status; there is no single opaque
score. This is the signal that catches many document-integrity problems.
"""
from __future__ import annotations

import re

from app.core.constants import DocField, FieldStatus
from app.schemas.analysis import (
    ConsistencyField,
    ConsistencyResult,
    MrzResult,
    VisualOcrResult,
)

# Fields we attempt to cross-check, mapped to (ocr_key, mrz_key).
COMPARISONS: list[tuple[str, str, str]] = [
    ("full_name", DocField.FULL_NAME.value, "full_name"),
    ("document_number", DocField.DOCUMENT_NUMBER.value, "document_number"),
    ("nationality", DocField.NATIONALITY.value, "nationality"),
    ("date_of_birth", DocField.DATE_OF_BIRTH.value, "date_of_birth"),
    ("expiry_date", DocField.EXPIRY_DATE.value, "expiry_date"),
    ("sex", DocField.SEX.value, "sex"),
]


def _norm_name(v: str) -> str:
    v = v.upper().replace("<", " ")
    v = re.sub(r"[^A-Z ]", " ", v)
    return " ".join(sorted(v.split()))  # order-insensitive token set


def _norm_docnum(v: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", v.upper())


def _norm_generic(v: str) -> str:
    return re.sub(r"\s+", "", v.upper())


def _normalize(field_key: str, value: str) -> str:
    if field_key == "full_name":
        return _norm_name(value)
    if field_key == "document_number":
        return _norm_docnum(value)
    return _norm_generic(value)


def _compare_pair(field_key: str, visual: str | None, mrz: str | None) -> ConsistencyField:
    if not visual or not mrz:
        return ConsistencyField(
            visual=visual, mrz=mrz, status=FieldStatus.NOT_AVAILABLE.value,
            detail="One or both sources did not provide this field.",
        )
    nv, nm = _normalize(field_key, visual), _normalize(field_key, mrz)
    if not nv or not nm:
        return ConsistencyField(
            visual=visual, mrz=mrz, status=FieldStatus.NOT_AVAILABLE.value
        )
    if nv == nm:
        return ConsistencyField(visual=visual, mrz=mrz, status=FieldStatus.MATCH.value)

    # Names: allow partial (one is a subset of the other's tokens).
    if field_key == "full_name":
        tv, tm = set(nv.split()), set(nm.split())
        if tv and tm and (tv <= tm or tm <= tv):
            return ConsistencyField(
                visual=visual, mrz=mrz, status=FieldStatus.MATCH.value,
                detail="Partial name match (subset).",
            )
    return ConsistencyField(
        visual=visual, mrz=mrz, status=FieldStatus.MISMATCH.value,
        detail="Normalized values differ.",
    )


def compare(ocr: VisualOcrResult | None, mrz: MrzResult | None) -> ConsistencyResult:
    fields: dict[str, ConsistencyField] = {}

    ocr_fields = ocr.fields if ocr else {}
    mrz_fields = mrz.fields if (mrz and mrz.detected) else {}

    for out_key, ocr_key, mrz_key in COMPARISONS:
        visual = None
        ef = ocr_fields.get(ocr_key)
        if ef and ef.status in ("detected", "low_confidence"):
            visual = ef.value
        mrz_val = mrz_fields.get(mrz_key)
        result = _compare_pair(out_key, visual, mrz_val)
        # Downgrade to low_confidence when OCR flagged the field as such.
        if (
            result.status == FieldStatus.MATCH.value
            and ef is not None
            and ef.status == "low_confidence"
        ):
            result.status = FieldStatus.LOW_CONFIDENCE.value
            result.detail = "Match, but visual OCR confidence was low."
        fields[out_key] = result

    comparable = [f for f in fields.values() if f.status not in (FieldStatus.NOT_AVAILABLE.value,)]
    matches = [f for f in comparable if f.status == FieldStatus.MATCH.value]

    if not comparable:
        overall = "not_available"
    elif any(f.status == FieldStatus.MISMATCH.value for f in comparable):
        overall = "mismatch" if len(matches) == 0 else "partial"
    elif len(matches) == len(comparable):
        overall = "match"
    else:
        overall = "partial"

    return ConsistencyResult(
        overall_status=overall,
        match_count=len(matches),
        comparable_count=len(comparable),
        fields=fields,
    )
