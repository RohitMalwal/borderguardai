"""Shared enums and constants used across the screening pipeline.

Keeping these in one place lets every module (and the API contract) speak the
same vocabulary of statuses. The frontend mirrors these strings.
"""
from __future__ import annotations

from enum import Enum


class StageStatus(str, Enum):
    """Lifecycle status for any pipeline stage."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class FieldStatus(str, Enum):
    """Status of a single extracted/validated field or a comparison."""

    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_AVAILABLE = "not_available"
    LOW_CONFIDENCE = "low_confidence"
    NOT_DETECTED = "not_detected"
    VALID = "valid"
    INVALID = "invalid"


class MrzStatus(str, Enum):
    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    LOW_CONFIDENCE = "low_confidence"
    INVALID = "invalid"
    VALID = "valid"


class QualityStatus(str, Enum):
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


# --- Pipeline stage identifiers (order matters for the UI) -----------------
class PipelineStage(str, Enum):
    DOCUMENT = "document"
    QUALITY = "quality"
    PREPROCESSING = "preprocessing"
    OCR = "ocr"
    MRZ = "mrz"
    VALIDATION = "validation"
    CONSISTENCY = "consistency"
    FACE = "face"
    FORENSIC = "forensic"


# Canonical field keys used everywhere so OCR, MRZ and consistency align.
class DocField(str, Enum):
    SURNAME = "surname"
    GIVEN_NAMES = "given_names"
    FULL_NAME = "full_name"
    DOCUMENT_NUMBER = "document_number"
    NATIONALITY = "nationality"
    DATE_OF_BIRTH = "date_of_birth"
    SEX = "sex"
    EXPIRY_DATE = "expiry_date"
    ISSUING_COUNTRY = "issuing_country"
    DOCUMENT_TYPE = "document_type"


# ICAO TD3 (passport) geometry.
TD3_LINE_LENGTH = 44
TD3_LINE_COUNT = 2

# Check-digit weighting pattern per ICAO Doc 9303.
CHECK_DIGIT_WEIGHTS = (7, 3, 1)
