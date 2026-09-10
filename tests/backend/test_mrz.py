"""Tests for ICAO TD3 MRZ parsing and check-digit validation.

Uses the canonical example from ICAO Doc 9303 Part 4, which has known-valid
check digits — proving the algorithm, not a hard-coded expectation.
"""
from app.services.mrz.parser import parse_td3, yymmdd_to_iso
from app.services.mrz.validator import compute_check_digit, validate_mrz

# Canonical ICAO Doc 9303 TD3 specimen.
LINE1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
LINE2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def test_check_digit_algorithm():
    # Document number field 'L898902C3' has published check digit 6.
    assert compute_check_digit("L898902C3") == 6
    # DOB 740812 -> check 2; expiry 120415 -> check 9.
    assert compute_check_digit("740812") == 2
    assert compute_check_digit("120415") == 9


def test_parse_and_validate_valid_specimen():
    parsed = parse_td3([LINE1, LINE2])
    assert parsed.surname == "ERIKSSON"
    assert parsed.given_names == "ANNA MARIA"
    assert parsed.document_number == "L898902C3"
    assert parsed.nationality == "UTO"

    result = validate_mrz(parsed, detection_confidence=0.99)
    assert result.detected is True
    assert result.validation.document_number is True
    assert result.validation.date_of_birth is True
    assert result.validation.expiry_date is True
    assert result.validation.composite is True
    assert result.status == "valid"
    assert result.fields["date_of_birth"] == "1974-08-12"
    assert result.fields["expiry_date"] == "2012-04-15"


def test_detects_tampered_document_number():
    # Flip a digit in the document number so its check digit no longer matches.
    bad_line2 = "L899902C36UTO7408122F1204159ZE184226B<<<<<10"
    parsed = parse_td3([LINE1, bad_line2])
    result = validate_mrz(parsed, 0.99)
    assert result.validation.document_number is False
    assert result.status == "invalid"


def test_date_conversion_century_rules():
    assert yymmdd_to_iso("990101", expiry=False) == "1999-01-01"
    assert yymmdd_to_iso("250101", expiry=False) == "2025-01-01"
    assert yymmdd_to_iso("300101", expiry=True) == "2030-01-01"
    assert yymmdd_to_iso("bad", expiry=False) is None
