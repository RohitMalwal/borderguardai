# Knowledge base (offline corpus) — reserved

This folder will hold the **local**, offline knowledge corpus used by the future
RAG evidence + explanation modules:

- ICAO Doc 9303 rules and MRZ specifications
- Issuing-state notes and document specimens
- Security-feature references

Nothing here is loaded by the current prototype. The retrieval and explanation
services (`backend/app/services/rag/`) are interface stubs today; they will
index this corpus locally (no external API) when implemented.

No live government or law-enforcement data is stored or accessed by this system.
