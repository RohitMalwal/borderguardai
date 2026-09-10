"""ICAO TD3 MRZ parser.

TD3 (passport) MRZ layout — two lines of 44 characters:

Line 1:
  pos  1     document type ('P')
  pos  2     document subtype
  pos  3-5   issuing state (ISO-3166-1 alpha-3, MRZ variant)
  pos  6-44  name field: PRIMARY<<SECONDARY (surname<<given names)

Line 2:
  pos  1-9   passport number
  pos 10     passport number check digit
  pos 11-13  nationality
  pos 14-19  date of birth (YYMMDD)
  pos 20     date of birth check digit
  pos 21     sex (M/F/<)
  pos 22-27  expiry date (YYMMDD)
  pos 28     expiry check digit
  pos 29-42  optional personal number
  pos 43     optional data check digit
  pos 44     composite check digit

This module only parses structure into raw fields. Validation lives in
validator.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import TD3_LINE_LENGTH


@dataclass
class ParsedMrz:
    ok: bool
    document_type: str = ""
    issuing_country: str = ""
    surname: str = ""
    given_names: str = ""
    document_number: str = ""
    document_number_check: str = ""
    nationality: str = ""
    date_of_birth: str = ""  # raw YYMMDD
    date_of_birth_check: str = ""
    sex: str = ""
    expiry_date: str = ""  # raw YYMMDD
    expiry_date_check: str = ""
    optional_data: str = ""
    optional_data_check: str = ""
    composite_check: str = ""
    line1: str = ""
    line2: str = ""
    errors: list[str] = field(default_factory=list)


def _clean_name(part: str) -> str:
    return part.replace("<", " ").strip()


def parse_td3(lines: list[str]) -> ParsedMrz:
    if len(lines) < 2:
        return ParsedMrz(ok=False, errors=["Fewer than two MRZ lines available."])

    line1, line2 = lines[0], lines[1]
    errors: list[str] = []
    if len(line1) != TD3_LINE_LENGTH:
        errors.append(f"Line 1 length is {len(line1)}, expected {TD3_LINE_LENGTH}.")
    if len(line2) != TD3_LINE_LENGTH:
        errors.append(f"Line 2 length is {len(line2)}, expected {TD3_LINE_LENGTH}.")

    # Pad defensively so slicing never raises; validation flags real issues.
    l1 = line1.ljust(TD3_LINE_LENGTH, "<")
    l2 = line2.ljust(TD3_LINE_LENGTH, "<")

    document_type = l1[0:2].replace("<", "").strip()
    issuing_country = l1[2:5].replace("<", "")
    name_field = l1[5:44]
    if "<<" in name_field:
        primary, secondary = name_field.split("<<", 1)
    else:
        primary, secondary = name_field, ""

    parsed = ParsedMrz(
        ok=len(errors) == 0,
        document_type=document_type,
        issuing_country=issuing_country,
        surname=_clean_name(primary),
        given_names=_clean_name(secondary),
        document_number=l2[0:9].replace("<", ""),
        document_number_check=l2[9:10],
        nationality=l2[10:13].replace("<", ""),
        date_of_birth=l2[13:19],
        date_of_birth_check=l2[19:20],
        sex=l2[20:21].replace("<", ""),
        expiry_date=l2[21:27],
        expiry_date_check=l2[27:28],
        optional_data=l2[28:42].replace("<", ""),
        optional_data_check=l2[42:43],
        composite_check=l2[43:44],
        line1=l1,
        line2=l2,
        errors=errors,
    )
    return parsed


def yymmdd_to_iso(raw: str, expiry: bool = False) -> str | None:
    """Convert a 6-digit YYMMDD MRZ date to ISO YYYY-MM-DD.

    Century inference: births assume 19xx/20xx around a 30-year window from
    'now-ish'; expiry dates are always in the 20xx-21xx range.
    """
    if len(raw) != 6 or not raw.isdigit():
        return None
    yy, mm, dd = int(raw[0:2]), int(raw[2:4]), int(raw[4:6])
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None
    if expiry:
        century = 2000
    else:
        # Simple heuristic: 00-30 -> 2000s, else 1900s.
        century = 2000 if yy <= 30 else 1900
    return f"{century + yy:04d}-{mm:02d}-{dd:02d}"
