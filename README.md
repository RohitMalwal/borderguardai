# BorderGuard AI

**Explainable, offline-first border document screening prototype.**

Upload a passport biodata page and BorderGuard AI independently analyzes the
document's **visual data** (OCR) and its **machine-readable zone** (MRZ), then
cross-checks them to surface inconsistencies — all processed **locally**, with
no API keys, no cloud AI, and no external services.

> This prototype does **not** access any government database and does **not**
> provide certified forensic analysis. It reports real, sometimes imperfect,
> results — never fabricated ones.

## What runs today

```
DOCUMENT → QUALITY → PREPROCESSING → VISUAL OCR → MRZ EXTRACTION →
MRZ VALIDATION → OCR↔MRZ CONSISTENCY → FACE DETECTION → (experimental forensic)
                                    → STRUCTURED JSON RESULT
```

- **Image quality** (OpenCV): blur, brightness, contrast, resolution, composite score
- **Preprocessing** (OpenCV): resize, denoise, CLAHE, deskew, sharpen — original preserved
- **Visual OCR** (PaddleOCR, local): raw text + heuristic passport-field extraction
- **MRZ** (custom ICAO TD3): detection, parsing, **real check-digit validation**
- **Cross-validation**: field-by-field Visual-OCR ↔ MRZ with per-field status
- **Face detection** (OpenCV Haar): bounding box on the passport photo
- **Forensic** (experimental only): ELA / noise / edge signals — clearly uncertified

Future modules (watchlist, risk fusion, RAG evidence, explanation, officer
decision, offline sync) exist as clean interfaces/placeholders — **not**
implemented, never faked.

## Tech stack

- **Frontend:** React + Vite
- **Backend:** Python + FastAPI
- **Local processing:** OpenCV, PaddleOCR, custom ICAO TD3 validation

## Requirements

- **Python 3.11** (recommended — full OCR + face detection support)
- **Node.js LTS** (18 or 20+)
- Windows 10/11 or macOS. First install needs internet; the demo itself runs offline.

> **Why 3.11?** PaddleOCR/PaddlePaddle publish stable wheels for 3.11, and
> OpenCV pins to 4.x there (OpenCV 5 drops the face-detection module). The app
> still *runs* on other Python versions, but OCR/face stages report themselves
> unavailable honestly instead of faking data.

## Quick start (one command)

From the repo root, after cloning:

**macOS / Linux**
```bash
./start.sh
```

**Windows 10/11**
```bat
start.bat
```

This creates the backend virtualenv, installs backend + frontend dependencies,
and launches both servers. Then open **http://localhost:5173**.

- Backend health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

## Manual start (two terminals)

Prefer manual control? Run the backend first, then the frontend.

### macOS / Linux

```bash
# Terminal 1 — backend (:8000)
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (:5173)
cd frontend
npm install
npm run dev
```

### Windows 10/11 (PowerShell or CMD)

```bat
REM Terminal 1 — backend (:8000)
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

REM Terminal 2 — frontend (:5173)
cd frontend
npm install
npm run dev
```

There are also per-service scripts in [`scripts/`](scripts/): `backend.sh` /
`frontend.sh` (macOS/Linux) and `backend.bat` / `frontend.bat` (Windows).

## Frontend API URL configuration

The frontend reads **`VITE_API_URL`** to decide where to send API calls. Copy
the example and adjust only if needed:

```bash
cd frontend
cp .env.example .env          # Windows: copy .env.example .env
```

- **Leave it empty** for local dev — requests stay same-origin and Vite proxies
  `/api` to the backend automatically (recommended).
- **Set a full origin** to point a built app at a backend directly, e.g. on a
  demo/projector machine or another host on the LAN:
  `VITE_API_URL=http://192.168.1.50:8000`

Nothing is hard-coded to `localhost` in the source.

## Offline demo preparation

The demo runs **fully offline**, but PaddleOCR downloads its models on first
use. Pre-cache them **once while online**:

```bash
cd backend
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m app.preload
```

Models cache locally and persist:
- macOS/Linux: `~/.paddleocr/`
- Windows: `%USERPROFILE%\.paddleocr\`

The Haar face cascade is vendored in the repo
(`backend/app/services/face/models/`), so it needs no download. After preloading
OCR, you can disconnect from the network and the full pipeline still works.

## Tests

```bash
cd backend
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pytest ../tests/backend -q
```

Includes a proof of the ICAO check-digit algorithm against the canonical Doc
9303 specimen, tamper detection, and API contract/error-handling tests.

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| Frontend shows "Cannot reach the analysis backend" | Backend isn't running or `VITE_API_URL` is wrong. Start the backend, check http://localhost:8000/api/health. |
| `/api/health` shows `"ocr": false` | PaddleOCR didn't install/load. Confirm you're on **Python 3.11** and re-run `pip install -r requirements.txt`. OCR-dependent stages degrade honestly until fixed. |
| OCR works with internet but not offline | Run `python -m app.preload` once while online to cache models. |
| `"face_detection": false` | You're on OpenCV 5 (Python ≥3.13). Use **Python 3.11** so OpenCV pins to 4.x, or accept degraded face detection. |
| `pip install` fails building `paddlepaddle` on **Apple Silicon (M1/M2/M3)** | PaddlePaddle's macOS arm64 support is limited. Try `pip install paddlepaddle==2.6.1`; if it still fails, run under an x86_64 (Rosetta) Python 3.11, or proceed with OCR degraded — the rest of the pipeline works. |
| `py -3.11` not found on Windows | Install Python 3.11 from python.org (check *Add to PATH*), or replace `py -3.11` with `python`. |
| Port 8000 or 5173 already in use | Stop the other process, or start the backend on another port (`uvicorn app.main:app --port 8010`) and set `VITE_DEV_PROXY_TARGET`/`VITE_API_URL` accordingly. |
| `npm run dev` fails | Ensure Node.js LTS is installed (`node -v`), delete `frontend/node_modules`, re-run `npm install`. |

## Project structure

```
borderguard-ai/
├── frontend/    React + Vite console (components / features / pages / hooks)
├── backend/     FastAPI + modular services + one screening pipeline
├── storage/     uploads / processed / results (runtime artifacts)
├── knowledge/   reserved offline corpus for future RAG
├── tests/       backend + frontend tests
└── docs/        architecture.md, api-contract.md
```

See [`docs/architecture.md`](docs/architecture.md) and
[`docs/api-contract.md`](docs/api-contract.md).

## Design & data honesty

- Nothing is pre-filled after upload; the uploaded image is actually processed.
- OCR text/confidences are real; MRZ fields and check digits are computed.
- Face similarity is only shown if a real matcher is wired in (none bundled).
- The UI communicates uncertainty (low confidence, not detected, experimental)
  rather than manufacturing a clean-looking result.
