"""Heuristic passport-field extraction from visual OCR lines.

Passport biodata layouts differ enormously between issuing states, so this
layer combines several independent signals instead of relying on one fragile
label regex:

  * Fuzzy, multilingual label matching tolerant of OCR errors (e.g. the German
    "Geburtstag/Date of birth" often OCRs as "Gobutstag /Date af birth").
  * Bounding-box layout: on a biodata page the value sits directly BELOW its
    label (occasionally to the right), so we search that column first and
    reject lines that themselves look like labels.
  * Value-shape validation: a value is an uppercase name, a date, a sex token
    or an alphanumeric code — not a mixed-case label full of slashes.
  * Chronology + pattern fallbacks when a label is missing or unreadable
    (classify the three dates; recover a top-of-page document number).

Everything here is visual-only (``source="visual"``). When a field cannot be
identified it is returned null with status ``not_detected`` — nothing invented.
MRZ is handled separately as an independent structured source.
"""
from __future__ import annotations

import re

from app.core.constants import DocField
from app.schemas.analysis import ExtractedField, OcrTextLine, VisualOcrResult

# --- Label vocabularies (normalized substrings, multilingual + OCR-tolerant) - #
LABELS: dict[str, list[str]] = {
    DocField.SURNAME.value: [
        "surname", "nom", "apellido", "apelido", "familyname", "cognome",
        "nachname", "prijmeni",
    ],
    DocField.GIVEN_NAMES.value: [
        "givenname", "givennames", "prenom", "forename", "nombre", "vorname",
        "jmena", "jmeno", "given",
    ],
    DocField.DOCUMENT_NUMBER.value: [
        "passportno", "passportnumber", "documentno", "docno", "passno",
        "passnr", "cislopasu", "cislodokladu", "passeportno", "numero",
    ],
    DocField.NATIONALITY.value: [
        "nationality", "nationalite", "nacionalidad", "staatsang", "angeh",
        "statniprisl", "statni", "nationalit",
    ],
    DocField.DATE_OF_BIRTH.value: [
        "dateofbirth", "birth", "naissance", "nacimiento", "geburt",
        "datumnaroz", "narozeni", "dob",
    ],
    DocField.SEX.value: ["sex", "sexe", "sexo", "gender", "geschlecht", "pohlavi"],
    DocField.EXPIRY_DATE.value: [
        "dateofexpiry", "expiry", "expiration", "expr", "gultig", "gueltig",
        "gutig", "ablauf", "validuntil", "platnost", "dateexpir",
    ],
    DocField.ISSUING_COUNTRY.value: [
        "issuing", "authority", "autorite", "behorde", "uradvydani", "urad",
    ],
}
# Labels we recognize only to AVOID mistaking them for values (not extracted).
_AVOID_LABELS = [
    "issue", "issuy", "delivrance", "vydani", "placeofbirth", "lieu",
    "geburtsort", "misto", "signature", "podpis", "bearer", "titulaire",
    "type", "typ", "code", "authority", "namebirth", "naissance",
]

DATE_RE = re.compile(
    r"\b(\d{1,2})[\s./\-]{0,2}([A-Z]{3}|\d{1,2})[\s./\-]{0,2}(\d{2,4})\b",
    re.IGNORECASE,
)
# A visual document number: 6-9 chars, letters+digits mixed (excludes plain
# words and plain dates); used only as a top-of-page fallback.
DOCNUM_RE = re.compile(r"^[A-Z0-9]{6,9}$")
SEX_RE = re.compile(r"\b([MF]|MALE|FEMALE|MANN|FRAU)\b", re.IGNORECASE)
MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}


def _norm(text: str) -> str:
    """Lowercase, letters-only — for OCR-tolerant label matching."""
    return re.sub(r"[^a-z]", "", text.lower())


def _center(box: list[list[float]]) -> tuple[float, float]:
    if not box:
        return (0.0, 0.0)
    xs = [p[0] for p in box]
    ys = [p[1] for p in box]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _label_field(text: str) -> str | None:
    """Return the field key this line labels, or None. Longest keyword wins so
    'givennames' beats a stray 'name'."""
    n = _norm(text)
    if len(n) < 3:
        return None
    best_field, best_len = None, 0
    for field_key, keywords in LABELS.items():
        for kw in keywords:
            if kw in n and len(kw) > best_len:
                best_field, best_len = field_key, len(kw)
    return best_field


def _is_label(text: str) -> bool:
    if _label_field(text) is not None:
        return True
    n = _norm(text)
    return any(kw in n for kw in _AVOID_LABELS)


def _is_dateish(text: str) -> bool:
    return DATE_RE.search(text.upper()) is not None


def _looks_like_value(text: str, allow_slash: bool = False) -> bool:
    """Is this line plausibly a field VALUE rather than a label?"""
    t = text.strip()
    if len(t) < 2:
        return False
    if _is_dateish(t):
        return True
    if not allow_slash and "/" in t:
        return False  # multilingual labels are slash-separated
    if _is_label(t):
        return False
    letters = [c for c in t if c.isalpha()]
    if letters:
        upper_ratio = sum(c.isupper() for c in letters) / len(letters)
        # Values (names/codes/countries) are predominantly uppercase; labels
        # are mixed/lower case.
        if upper_ratio < 0.6:
            return False
    return True


def _value_near(label: OcrTextLine, lines: list[OcrTextLine], allow_slash: bool = False) -> OcrTextLine | None:
    """Find the value for a label: prefer the nearest value directly BELOW it
    (same column), then the nearest value to the RIGHT on the same row."""
    lx, ly = _center(label.box)

    below: list[tuple[float, OcrTextLine]] = []
    right: list[tuple[float, OcrTextLine]] = []
    for ln in lines:
        if ln is label:
            continue
        cx, cy = _center(ln.box)
        dy, dx = cy - ly, cx - lx
        if 6 < dy < 95 and abs(dx) < 280 and _looks_like_value(ln.text, allow_slash):
            below.append((dy + abs(dx) * 0.3, ln))
        elif abs(dy) < 22 and dx > 0 and _looks_like_value(ln.text, allow_slash):
            right.append((dx, ln))
    if below:
        return min(below, key=lambda c: c[0])[1]
    if right:
        return min(right, key=lambda c: c[0])[1]
    return None


def _normalize_date(text: str) -> str | None:
    m = DATE_RE.search(text.upper())
    if not m:
        return None
    day, mon, year = m.groups()
    mon = MONTHS.get(mon.upper(), mon)
    try:
        d, mo = int(day), int(mon)
    except (ValueError, TypeError):
        return None
    if len(year) == 2:
        year = ("20" if int(year) < 50 else "19") + year
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{int(year):04d}-{mo:02d}-{d:02d}"


def _field(value: str | None, conf: float | None, source_text: str | None) -> ExtractedField:
    if not value:
        return ExtractedField(value=None, confidence=None, status="not_detected")
    status = "detected" if (conf is None or conf >= 0.5) else "low_confidence"
    return ExtractedField(
        value=value.strip(), confidence=conf, status=status,
        source="visual", source_text=source_text,
    )


def _clean_name(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z '\-]", " ", text)).strip().upper()


def extract_fields(ocr: VisualOcrResult) -> VisualOcrResult:
    """Populate ocr.fields (visual-only) from ocr.raw_text. Each field is
    isolated so one anomaly cannot abort the whole extraction."""
    lines = ocr.raw_text
    fields: dict[str, ExtractedField] = {
        f.value: ExtractedField(value=None, confidence=None, status="not_detected")
        for f in DocField
    }
    if not lines:
        ocr.fields = fields
        return ocr

    # Map each label line to the field it names (first occurrence wins).
    label_lines: dict[str, OcrTextLine] = {}
    for ln in lines:
        fk = _label_field(ln.text)
        if fk and fk not in label_lines:
            label_lines[fk] = ln

    def set_from_label(field_key: str, allow_slash: bool = False, transform=None) -> None:
        try:
            label = label_lines.get(field_key)
            if not label:
                return
            vline = _value_near(label, lines, allow_slash)
            if not vline:
                return
            raw = vline.text.strip()
            value = transform(raw) if transform else raw
            if value:
                fields[field_key] = _field(value, vline.confidence, raw)
        except Exception:  # noqa: BLE001 - never let one field abort extraction
            return

    # --- Names --------------------------------------------------------------
    set_from_label(DocField.SURNAME.value, transform=_clean_name)
    set_from_label(DocField.GIVEN_NAMES.value, transform=_clean_name)

    # --- Nationality (values may legitimately contain '/') ------------------
    def _nat(raw: str) -> str | None:
        val = raw.split("/")[0].strip()
        return val or None
    set_from_label(DocField.NATIONALITY.value, allow_slash=True, transform=_nat)

    # --- Dates: chronology is a reliable passport invariant -----------------
    # DOB is the earliest date on the page; expiry is the latest (issue sits
    # between). This is far more robust than matching easily-mangled date
    # labels, and it correctly separates issue-vs-expiry (both often share the
    # same day/month layout on the biodata page).
    try:
        dated: list[tuple[str, OcrTextLine]] = []
        for ln in lines:
            iso = _normalize_date(ln.text)
            if iso:
                dated.append((iso, ln))
        isos = sorted({d[0] for d in dated})

        def _best_line(iso: str) -> OcrTextLine:
            return max((ln for i, ln in dated if i == iso), key=lambda l: l.confidence)

        if len(isos) == 1:
            # A single date: assign to whichever of the birth/expiry labels is
            # vertically nearest, defaulting to date of birth.
            iso = isos[0]
            ln = _best_line(iso)
            _, y = _center(ln.box)
            target = DocField.DATE_OF_BIRTH.value
            exp_label = label_lines.get(DocField.EXPIRY_DATE.value)
            dob_label = label_lines.get(DocField.DATE_OF_BIRTH.value)
            if exp_label and (not dob_label or
                              abs(_center(exp_label.box)[1] - y) < abs(_center(dob_label.box)[1] - y)):
                target = DocField.EXPIRY_DATE.value
            fields[target] = _field(iso, ln.confidence, ln.text)
        elif isos:
            dob_ln, exp_ln = _best_line(isos[0]), _best_line(isos[-1])
            fields[DocField.DATE_OF_BIRTH.value] = _field(isos[0], dob_ln.confidence, dob_ln.text)
            fields[DocField.EXPIRY_DATE.value] = _field(isos[-1], exp_ln.confidence, exp_ln.text)
    except Exception:  # noqa: BLE001
        pass

    # --- Sex: a lone 'M'/'F' cell near the sex label ------------------------
    try:
        label = label_lines.get(DocField.SEX.value)
        if label:
            lx, ly = _center(label.box)
            best, best_d = None, 1e9
            for ln in lines:
                txt = ln.text.strip().upper()
                m = re.fullmatch(r"([MF])", txt) or SEX_RE.search(txt)
                if not m:
                    continue
                cx, cy = _center(ln.box)
                dy, dx = cy - ly, cx - lx
                near_below = 6 < dy < 95 and abs(dx) < 170
                near_right = abs(dy) < 22 and dx > 0 and dx < 260
                if near_below or near_right:
                    d = abs(dy) + abs(dx) * 0.3
                    if d < best_d:
                        tok = m.group(1).upper()
                        best = ("F" if tok in ("F", "FEMALE", "FRAU") else "M", ln)
                        best_d = d
            if best:
                fields[DocField.SEX.value] = _field(best[0], best[1].confidence, best[1].text)
    except Exception:  # noqa: BLE001
        pass

    # --- Document number via label ------------------------------------------
    def _docnum(raw: str) -> str | None:
        cand = re.sub(r"\s", "", raw.upper())
        m = re.search(r"[A-Z0-9]{6,9}", cand)
        if not m:
            return None
        v = m.group(0)
        return v if (any(c.isdigit() for c in v) and any(c.isalpha() for c in v) or v.isdigit()) else None
    set_from_label(DocField.DOCUMENT_NUMBER.value, transform=_docnum)

    # --- Fallback: document number from a top-of-page alphanumeric code ------
    try:
        if fields[DocField.DOCUMENT_NUMBER.value].value is None and lines:
            heights = [max(p[1] for p in ln.box) for ln in lines if ln.box]
            page_h = max(heights) if heights else 1
            best = None
            for ln in lines:
                cand = re.sub(r"\s", "", ln.text.upper())
                cy = _center(ln.box)[1]
                if (
                    DOCNUM_RE.match(cand)
                    and any(c.isdigit() for c in cand)
                    and any(c.isalpha() for c in cand)
                    and not _is_dateish(cand)
                    and cy < page_h * 0.45  # biodata numbers sit high on the page
                ):
                    if best is None or ln.confidence > best.confidence:
                        best = ln
            if best is not None:
                v = re.sub(r"\s", "", best.text.upper())
                fields[DocField.DOCUMENT_NUMBER.value] = _field(v, best.confidence, best.text)
    except Exception:  # noqa: BLE001
        pass

    # --- Derive full name ---------------------------------------------------
    try:
        surname = fields[DocField.SURNAME.value].value
        given = fields[DocField.GIVEN_NAMES.value].value
        if surname or given:
            full = " ".join(p for p in [given, surname] if p)
            confs = [
                c for c in (
                    fields[DocField.SURNAME.value].confidence,
                    fields[DocField.GIVEN_NAMES.value].confidence,
                ) if c is not None
            ]
            fields[DocField.FULL_NAME.value] = _field(full, min(confs) if confs else None, None)
    except Exception:  # noqa: BLE001
        pass

    ocr.fields = fields
    return ocr
