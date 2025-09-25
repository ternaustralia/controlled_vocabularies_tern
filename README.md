# controlled_vocabularies_tern

This repository manages TERN controlled vocabularies, including pulling vocabs, validating them against SHACL shapes, and publishing validated vocabs.

## Repository layout
- `data/snapshots` — copies of fetched vocabularies, versioned by timestamp.
- `shapes/` — SHACL shape graphs (e.g. baseline SKOS constraints) used during validation.
- `src/validation/` — validation tooling and helpers for running SHACL or related checks.
- `src/publish/` — code responsible for preparing and publishing validated vocabularies to external targets.
- `src/ingest/` — scripts that retrieve vocabularies from remote endpoints and stage them locally.
- `tests/` — automated tests covering ingestion, validation, and publication behaviour.
