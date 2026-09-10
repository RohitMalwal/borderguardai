# BorderGuard AI — API Contract

Version: `schema_version = "1.0"`. This contract is stable and modular: future
modules (watchlist, risk fusion, RAG, officer decision) consume the same object
without depending on any frontend state. Statuses are enumerated strings, not
presentation text.

Base URL (dev): `http://localhost:8000`, prefix `/api`. Vite proxies `/api`.

---

## GET `/api/health`

Returns service status and **real** capability flags (computed at call time).

```json
{
  "status": "ok",
  "app": "BorderGuard AI",
  "version": "0.1.0",
  "capabilities": {
    "ocr": false,
    "face_detection": true,
    "mrz_validation": true,
    "quality_analysis": true,
    "forensic_experimental": true
  }
}
```

`capabilities.ocr` is `false` when PaddleOCR cannot be loaded in the current
environment — the pipeline then reports OCR as `engine_unavailable` rather than
fabricating text.

---

## GET `/api/screening/config`

```json
{ "allowed_extensions": [".jpeg", ".jpg", ".png"], "max_upload_bytes": 15728640 }
```

---

## POST `/api/screening/analyze`

`multipart/form-data`:

| field       | required | notes                                   |
|-------------|----------|-----------------------------------------|
| `passport`  | yes      | JPG / JPEG / PNG biodata page           |
| `traveller` | no       | Live photo (for future face comparison) |

### 200 — `ScreeningResult`

```jsonc
{
  "screening_id": "a1b2c3d4e5f6",
  "schema_version": "1.0",
  "created_at": "2026-09-10T12:00:00+00:00",
  "status": "complete",              // complete | partial | error

  "document": {
    "filename": "passport.jpg",
    "content_type": "image/jpeg",
    "size_bytes": 482113,
    "width": 1280, "height": 850, "channels": 3
  },

  "quality": {
    "status": "good",                // good | acceptable | poor
    "quality_score": 78.4,           // 0-100 composite
    "blur_score": 142.7,             // variance of Laplacian
    "brightness_score": 138.2,       // mean luminance 0-255
    "contrast_score": 54.1,          // std-dev of luminance
    "resolution": { "width": 1280, "height": 850, "megapixels": 1.09 },
    "warnings": []
  },

  "preprocessing": {
    "steps": [ { "name": "denoise", "applied": true, "detail": "..." } ],
    "original_artifact": "processed/<id>/original.png",
    "primary_artifact": "processed/<id>/primary.png",
    "notes": []
  },

  "visual_ocr": {
    "engine": "paddleocr",           // paddleocr | unavailable
    "status": "complete",            // complete | low_confidence | failed | engine_unavailable
    "raw_text": [ { "text": "...", "confidence": 0.97, "box": [[x,y],...] } ],
    "fields": {
      "full_name":       { "value": "JOHN DOE", "confidence": 0.95, "status": "detected" },
      "surname":         { "value": "DOE",  "confidence": 0.96, "status": "detected" },
      "given_names":     { "value": "JOHN", "confidence": 0.94, "status": "detected" },
      "document_number": { "value": null, "confidence": null, "status": "not_detected" },
      "nationality":     { "value": null, "confidence": null, "status": "not_detected" },
      "date_of_birth":   { "value": "2002-01-12", "confidence": 0.9, "status": "detected" },
      "sex":             { "value": "M", "confidence": 0.9, "status": "detected" },
      "expiry_date":     { "value": null, "confidence": null, "status": "not_detected" }
    },
    "mean_confidence": 0.93,
    "message": null
  },

  "mrz": {
    "detected": true,
    "status": "valid",               // detected | not_detected | low_confidence | invalid | valid
    "raw_lines": ["P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
                  "L898902C36UTO7408122F1204159ZE184226B<<<<<10"],
    "confidence": 0.9,
    "fields": {
      "document_type": "P", "issuing_country": "UTO",
      "surname": "ERIKSSON", "given_names": "ANNA MARIA", "full_name": "ANNA MARIA ERIKSSON",
      "document_number": "L898902C3", "nationality": "UTO",
      "date_of_birth": "1974-08-12", "sex": "F", "expiry_date": "2012-04-15"
    },
    "validation": {
      "document_number": true, "date_of_birth": true, "expiry_date": true,
      "composite": true, "line_lengths_ok": true
    },
    "errors": [],
    "message": null
  },

  "consistency": {
    "overall_status": "partial",     // match | partial | mismatch | not_available
    "match_count": 2, "comparable_count": 3,
    "fields": {
      "full_name":       { "visual": "JOHN DOE", "mrz": "JOHN DOE", "status": "match" },
      "date_of_birth":   { "visual": "2002-01-12", "mrz": "2003-01-12", "status": "mismatch",
                           "detail": "Normalized values differ." },
      "document_number": { "visual": null, "mrz": "L898902C3", "status": "not_available" }
    }
  },

  "face": {
    "detected": true,
    "status": "detected",            // detected | not_detected | multiple_detected | unavailable
    "faces": [ { "x": 40, "y": 120, "width": 200, "height": 260, "confidence": null } ],
    "primary_face": { "x": 40, "y": 120, "width": 200, "height": 260 },
    "comparison_available": false,   // true only if a real matcher is wired in
    "similarity": null,              // never fabricated
    "match_status": null,
    "message": null
  },

  "forensic": {
    "label": "Experimental Prototype Signal",
    "status": "analyzed",            // analyzed | unavailable
    "signals": { "ela_mean": 1.2, "ela_max": 44, "noise_std": 3.1, "edge_density": 0.06 },
    "suspicious_regions": [],
    "disclaimer": "Experimental image-anomaly signal only. NOT certified forensic analysis."
  },

  "stages": [
    { "stage": "document", "status": "complete", "duration_ms": 3.1, "message": null },
    { "stage": "quality",  "status": "warning",  "duration_ms": 12.4, "message": "Low contrast..." }
    // ... one per pipeline stage: document, quality, preprocessing, ocr, mrz,
    // validation, consistency, face, forensic
  ],

  "intelligence": null,              // RESERVED: watchlist / risk fusion / evidence / recommendation
  "explanation": null,               // RESERVED: RAG-backed narrative
  "officer_decision": null,          // RESERVED: human-in-the-loop decision
  "warnings": ["..."]
}
```

### Error responses (`400` / `500`)

```json
{ "status": "error", "code": "unsupported_format", "message": "…", "detail": null }
```

Known `code` values: `unsupported_format`, `empty_file`, `file_too_large`,
`corrupt_image`, `read_failed`, `processing_error`.

---

## Status vocabularies

| Group            | Values                                                        |
|------------------|---------------------------------------------------------------|
| Stage status     | `pending` `processing` `complete` `warning` `error` `skipped` |
| Field/comparison | `match` `mismatch` `not_available` `low_confidence` `detected` `not_detected` `valid` `invalid` |
| MRZ status       | `detected` `not_detected` `low_confidence` `invalid` `valid`  |
| Quality status   | `good` `acceptable` `poor`                                    |
| Consistency      | `match` `partial` `mismatch` `not_available`                  |

## Data-honesty guarantees

- OCR text and confidences come from the actual engine; when unavailable,
  `raw_text` is `[]` and all `fields[*].value` are `null`.
- MRZ fields and check digits are parsed/computed from the detected lines.
- Face `similarity` is `null` unless a real matcher backend is present.
- Forensic signals are labelled experimental and are never presented as
  certified. No government-database access is claimed anywhere.
