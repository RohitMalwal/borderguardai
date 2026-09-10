"""End-to-end tests for the API and pipeline honesty/error handling."""
import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _png_bytes(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def _synthetic_biodata() -> np.ndarray:
    img = np.full((600, 900, 3), 235, np.uint8)
    cv2.rectangle(img, (40, 120), (240, 380), (200, 200, 200), -1)
    cv2.circle(img, (140, 230), 60, (150, 140, 130), -1)
    return img


def test_health_reports_capabilities():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert set(["ocr", "face_detection", "mrz_validation"]).issubset(body["capabilities"])


def test_analyze_returns_structured_contract():
    r = client.post(
        "/api/screening/analyze",
        files={"passport": ("t.png", _png_bytes(_synthetic_biodata()), "image/png")},
    )
    assert r.status_code == 200
    d = r.json()
    # Contract keys must always be present (even future/reserved ones).
    for key in [
        "screening_id", "schema_version", "document", "quality", "preprocessing",
        "visual_ocr", "mrz", "consistency", "face", "forensic", "stages",
        "intelligence", "explanation", "officer_decision",
    ]:
        assert key in d, f"missing key: {key}"
    # Reserved future modules must be null (not fabricated).
    assert d["intelligence"] is None
    assert d["explanation"] is None
    assert d["officer_decision"] is None
    # Quality must be really computed.
    assert 0 <= d["quality"]["quality_score"] <= 100


def test_rejects_unsupported_format():
    r = client.post(
        "/api/screening/analyze",
        files={"passport": ("x.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400
    assert r.json()["code"] == "unsupported_format"


def test_rejects_corrupt_image():
    r = client.post(
        "/api/screening/analyze",
        files={"passport": ("x.png", b"\x89PNG-not-real", "image/png")},
    )
    assert r.status_code == 400
    assert r.json()["code"] == "corrupt_image"


def test_no_fabricated_ocr_when_engine_missing():
    d = client.post(
        "/api/screening/analyze",
        files={"passport": ("t.png", _png_bytes(_synthetic_biodata()), "image/png")},
    ).json()
    ocr = d["visual_ocr"]
    if ocr["engine"] == "unavailable":
        # When no engine, there must be zero fabricated field values.
        assert ocr["raw_text"] == []
        assert all(f["value"] is None for f in ocr["fields"].values()) or ocr["fields"] == {}
