# BorderGuard AI — Backend

FastAPI service running the local, offline document-screening pipeline.

## Requirements

- Python **3.10–3.12 recommended** (for PaddleOCR wheels). The API still runs
  on newer Python without PaddleOCR — OCR-dependent stages report
  `engine_unavailable` honestly instead of faking data.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If PaddleOCR fails to install on your Python version, the app still boots;
install it later under a 3.10–3.12 environment to enable real OCR.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Key endpoints

| Method | Path                     | Purpose                                   |
|--------|--------------------------|-------------------------------------------|
| GET    | `/api/health`            | Status + real capability flags            |
| POST   | `/api/screening/analyze` | Upload passport (+optional traveller) → JSON |
| GET    | `/api/screening/config`  | Upload limits for the frontend            |

`POST /api/screening/analyze` accepts `multipart/form-data`:
- `passport` (required): JPG/JPEG/PNG biodata page
- `traveller` (optional): live photo for future face comparison

## Architecture

```
app/
  api/          FastAPI routes + dependencies
  core/         config + shared constants/enums
  models/       API request/response envelopes
  schemas/      pydantic result contract (document / analysis / screening)
  services/     modular processing units:
    document/   decode, quality (OpenCV), preprocessing (OpenCV)
    ocr/        PaddleOCR (guarded) + heuristic field extraction
    mrz/        TD3 detector, parser, ICAO check-digit validator
    consistency/ visual-OCR ↔ MRZ field comparison
    face/       Haar-cascade detection (+ matcher interface, not bundled)
    forensic/   experimental tamper signals (NOT certified)
    intelligence/ FUTURE: watchlist, risk fusion, evidence, recommendation
    rag/        FUTURE: knowledge base, retrieval, explanation
  orchestrator/ run_screening() — the single pipeline
```

See `../docs/architecture.md` and `../docs/api-contract.md`.
