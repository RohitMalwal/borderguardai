# BorderGuard AI — Architecture

## Principles

1. **One connected application.** Structure follows *technical responsibility*,
   never team members. Frontend and backend are cleanly separated but share one
   result contract.
2. **Local-first & offline.** No API keys, no cloud AI, no external services.
   Everything runs on a laptop for the demo.
3. **Modular services behind one pipeline.** Each processing concern is an
   independently improvable module; a single orchestrator composes them.
4. **Honest data.** Every result is computed from the uploaded image. When a
   capability is unavailable, the system says so instead of fabricating.
5. **Extensible.** Future modules (watchlist, risk fusion, RAG, officer
   decision) attach to the same `ScreeningResult` without redesigning the
   document-analysis pipeline.

## System flow

```
React Frontend  ──(multipart upload)──▶  FastAPI  ──▶  Screening Pipeline
      ▲                                                      │
      └───────────────  Structured JSON (ScreeningResult) ◀──┘
```

## Backend pipeline (implemented)

```
run_screening(passport, [traveller])
  DOCUMENT        decode + validate + persist original
  QUALITY         OpenCV: blur / brightness / contrast / resolution
  PREPROCESSING   OpenCV: resize → denoise → CLAHE → deskew → sharpen
  OCR             PaddleOCR (guarded) → heuristic field extraction
  MRZ             detect TD3 candidates → parse structure
  VALIDATION      ICAO check digits (doc no / DOB / expiry / composite)
  CONSISTENCY     Visual OCR ↔ MRZ, normalized, field-by-field
  FACE            Haar-cascade detection (matcher interface, not bundled)
  FORENSIC        experimental ELA/noise/edge signals (NOT certified)
  ──▶ one ScreeningResult (+ reserved keys for future modules)
```

Each stage is isolated: a failure degrades to `warning`/`error` for that stage
and never crashes the request. The stage timeline (with timings) is returned so
the UI reflects *real* progress.

## Backend layout

```
backend/app/
  main.py                 FastAPI app + CORS
  core/                   config, constants/enums (shared vocabulary)
  api/routes/             health, screening
  models/                 API request/response envelopes
  schemas/                pydantic result contract (document/analysis/screening)
  services/
    document/  decode + quality + preprocessing
    ocr/       paddle_service (guarded) + field_extractor
    mrz/       detector + parser + validator (ICAO TD3)
    consistency/ comparison (normalization + per-field status)
    face/      detector (Haar) + matcher (interface only)
    forensic/  tamper (experimental) + localization (interface)
    intelligence/  FUTURE: risk, watchlist, evidence, recommendation
    rag/       FUTURE: knowledge_base, retrieval, explanation
  orchestrator/           screening_pipeline.run_screening()
```

## Frontend layout

```
frontend/src/
  api/client.js           fetch wrapper (health, analyze) + ApiError
  hooks/useScreening.js    request lifecycle + derived per-stage state
  pages/                  Screening (operational), Dashboard (overview)
  components/
    layout/               Header (live capability indicators)
    document/             UploadPanel, DocumentPreview (dims + face overlay)
    pipeline/             PipelineTimeline
    analysis/             Quality / Ocr / Mrz / Consistency / Face / Forensic cards
    common/               Card, StatusBadge, EmptyState
  features/               screening, document-analysis (active);
                          intelligence, officer-review (planned placeholders)
  utils/                  status → tone mapping, formatting
  data/                   pipeline stage definitions
```

## Extension points (deliberately not implemented)

| Future module        | Seam                                             |
|----------------------|--------------------------------------------------|
| Watchlist screening  | `services/intelligence/watchlist.py`             |
| Risk fusion          | `services/intelligence/risk.py`                  |
| Evidence graph       | `services/intelligence/evidence.py`              |
| Recommendation       | `services/intelligence/recommendation.py`        |
| RAG retrieval        | `services/rag/{knowledge_base,retrieval}.py`     |
| Explanation          | `services/rag/explanation.py`                    |
| Officer decision     | `ScreeningResult.officer_decision` (reserved)    |
| Offline queue / sync | `api/dependencies.py` (request seam)             |

All are stubs that raise `NotImplementedError` and are surfaced in the UI as
`planned` — never with fabricated output.

## Environment notes

- **Python 3.11** is the target. `requirements.txt` uses environment markers so
  that on Python ≤3.12 it installs OpenCV **4.x**, NumPy **<2**, and PaddleOCR /
  PaddlePaddle **2.x** (the API this project's OCR service targets); on newer
  Python it stays installable but OCR/face degrade honestly.
- PaddleOCR downloads models on first use and caches them (`~/.paddleocr` /
  `%USERPROFILE%\.paddleocr`). `python -m app.preload` pre-caches them for
  offline demos. The engine is constructed defensively so minor version
  differences don't crash startup.
- The frontal-face Haar cascade is vendored at
  `backend/app/services/face/models/` (loaded via `pathlib`, no absolute paths)
  because OpenCV 5 wheels no longer bundle `cv2.data` cascades. On OpenCV 4.x
  (Python 3.11) it also works via `cv2.data`.
- All runtime paths (storage/uploads/processed/results, vendored models) derive
  from `pathlib.Path` relative to the repo, so they work on Windows and macOS.
```
