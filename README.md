# controlled_vocabularies_tern

This repository manages TERN controlled vocabularies, including pulling vocabs, validating them against SHACL shapes, and publishing validated vocabs.

## Repository layout
- `data/snapshots` — copies of fetched vocabularies, versioned by timestamp.
- `shapes/` — SHACL shape graphs (e.g. baseline SKOS constraints) used during validation.
- `src/validation/` — validation tooling and helpers for running SHACL or related checks.
- `src/publish/` — code responsible for preparing and publishing validated vocabularies to external targets.
- `src/ingest/` — scripts that retrieve vocabularies from remote endpoints and stage them locally.
- `tests/` — automated tests covering ingestion, validation, and publication behaviour.

## Running workflows

Install dependencies if you have not already:

```
pip install -r requirements.txt
```

The main entry point is `src/workflow.py`, which also backs the Make targets:

- Full pipeline (pull → normalize → validate → report) for all registered schemes:
  ```
  make pipeline VIOLATIONS_DIR=downloads/violations
  ```
  Optional flags: `SCHEME=<scheme-id-or-iri>`, `ENDPOINT=<override>`, and custom runner flags via `PIPELINE_FLAGS` (e.g. `PIPELINE_FLAGS="--pyshacl pyshacl --ontotools ontotools"`).

- Full pipeline (pull → normalize → validate → report) for all registered collections:
  ```
  make collection-pipeline VIOLATIONS_DIR=downloads/violations
  ```
  Optional flags: `COLLECTION=<collection-id-or-iri>`, `ENDPOINT=<override>`, `MAX_DEPTH=<n>` (default 3), and custom runner flags via `COLLECTION_PIPELINE_FLAGS` (e.g. `COLLECTION_PIPELINE_FLAGS="--pyshacl pyshacl --ontotools ontotools"`).

- Pull snapshots only:
  ```
  make pull
  ```
  Supports the same `SCHEME`/`ENDPOINT` selection as the pipeline.

- Pull collection snapshots only:
  ```
  make collection-pull
  ```
  Supports the same `COLLECTION`/`ENDPOINT`/`MAX_DEPTH` selection as the collection pipeline (default depth 3).

- Validate an existing snapshot and export violations:
  ```
  make validate SNAPSHOT=data/snapshots/example.ttl VIOLATIONS_DIR=downloads/violations
  ```
  Pass extra pyshacl flags using `VALIDATE_FLAGS`, or list additional SHACL files via `VALIDATE_FLAGS="--schemes shapes/custom.ttl"`.

- Normalize an existing snapshot in place:
  ```
  make normalize SNAPSHOT=data/snapshots/example.ttl
  ```

You can also invoke the runner directly, e.g. `python src/workflow.py pipeline --violations-dir downloads/violations`. See `python src/workflow.py --help` for full options. Schemes and their validator files are maintained in `config/schemes.yaml`, and collections live in `config/collections.yaml`.

Baseline validator files are `shapes/scheme-basics.ttl` for ConceptSchemes and `shapes/collection-basics.ttl` for Collections.
