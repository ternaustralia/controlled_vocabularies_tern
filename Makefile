PYTHON ?= python
SCRIPT := src/ingest/pull_skos_scheme.py
ONTOTOOLS ?= ontotools
PYSHACL ?= pyshacl
SHAPES ?= shapes/skos-basics.ttl
FORMAT ?= text/turtle

# Optional passthrough flags
EXTRA_PULL_ARGS ?= 
ONTO_ARGS ?=
PYSHACL_ARGS ?=

.PHONY: snapshot
snapshot:
	@if [ -z "$(ENDPOINT)" ]; then \
		echo "ENDPOINT is required. Usage: make snapshot ENDPOINT=<sparql-endpoint> SCHEME=<concept-scheme-iri>"; \
		exit 1; \
	fi
	@if [ -z "$(SCHEME)" ]; then \
		echo "SCHEME is required. Usage: make snapshot ENDPOINT=<sparql-endpoint> SCHEME=<concept-scheme-iri>"; \
		exit 1; \
	fi
	@set -euo pipefail; \
		SNAPSHOT_OUTPUT=$$($(PYTHON) $(SCRIPT) $(ENDPOINT) $(SCHEME) --format $(FORMAT) $(EXTRA_PULL_ARGS)); \
		SNAPSHOT_PATH=$$(printf '%s\n' "$$SNAPSHOT_OUTPUT" | tail -n1 | sed -E 's/^Wrote snapshot to //'); \
		if [ -z "$$SNAPSHOT_PATH" ]; then \
			echo "Unable to determine snapshot path from script output:"; \
			printf '%s\n' "$$SNAPSHOT_OUTPUT"; \
			exit 1; \
		fi; \
		printf '%s\n' "$$SNAPSHOT_OUTPUT"; \
		echo "Normalizing snapshot $$SNAPSHOT_PATH"; \
		$(ONTOTOOLS) file normalize $(ONTO_ARGS) $$SNAPSHOT_PATH; \
		echo "Validating snapshot $$SNAPSHOT_PATH against $(SHAPES)"; \
		$(PYSHACL) -s $(SHAPES) -d $$SNAPSHOT_PATH $(PYSHACL_ARGS)
