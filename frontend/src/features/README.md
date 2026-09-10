# Feature modules

Feature-oriented slices of the UI. Each folder groups the components, hooks and
state for one product capability, so the app can grow without turning
`components/` into a dumping ground.

| Folder              | Status      | Purpose                                                        |
|---------------------|-------------|----------------------------------------------------------------|
| `screening/`        | **active**  | Passport upload → analysis flow (currently wired in `pages/Screening.jsx`). |
| `document-analysis/`| active      | OCR / MRZ / consistency result presentation (cards in `components/analysis/`). |
| `intelligence/`     | planned     | Watchlist, risk fusion, evidence graph, recommendation UI.     |
| `officer-review/`   | planned     | Human-in-the-loop decision capture and audit trail.            |

Planned folders are intentionally empty placeholders. Do not add fabricated UI
for unimplemented modules.
