# Frontend tests

Placeholder for frontend tests (e.g. Vitest + React Testing Library). Not set up
in this prototype — the current verification focus is the backend pipeline and
the real OCR/MRZ/consistency behavior.

Suggested first tests when added:
- `utils/status.js` tone mapping is exhaustive over backend statuses.
- `useScreening` never marks a stage `complete` before the backend reports it.
- Result cards render honest empty/`not_detected`/`unavailable` states.
