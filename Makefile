PYTHON ?= python
SCRIPT := src/ingest/pull_skos_scheme.py
ONTOTOOLS ?= ontotools
PYSHACL ?= pyshacl
SHAPES ?= shapes/skos-basics.ttl
FORMAT ?= text/turtle
VIOLATIONS_DIR ?=

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
	@if [ -z "$(VIOLATIONS_DIR)" ]; then \
		echo "VIOLATIONS_DIR is required. Usage: make snapshot ENDPOINT=<sparql-endpoint> SCHEME=<concept-scheme-iri> VIOLATIONS_DIR=<path-to-store-violations>"; \
		exit 1; \
	fi
	@set -euo pipefail; \
		SNAPSHOT_OUTPUT=$$($(PYTHON) $(SCRIPT) $(ENDPOINT) $(SCHEME) --format $(FORMAT) $(EXTRA_PULL_ARGS)); \
		SNAPSHOT_PATH=$$(printf '%s\n' "$$SNAPSHOT_OUTPUT" | sed -n 's/^SNAPSHOT_PATH=//p'); \
		SCHEME_SLUG=$$(printf '%s\n' "$$SNAPSHOT_OUTPUT" | sed -n 's/^SCHEME_SLUG=//p'); \
		if [ -z "$$SNAPSHOT_PATH" ]; then \
			echo "Unable to determine snapshot path from script output:"; \
			printf '%s\n' "$$SNAPSHOT_OUTPUT"; \
			exit 1; \
		fi; \
		if [ -z "$$SCHEME_SLUG" ]; then \
			echo "Unable to determine scheme slug from script output:"; \
			printf '%s\n' "$$SNAPSHOT_OUTPUT"; \
			exit 1; \
		fi; \
		printf '%s\n' "$$SNAPSHOT_OUTPUT"; \
		echo "Normalizing snapshot $$SNAPSHOT_PATH"; \
		$(ONTOTOOLS) file normalize $(ONTO_ARGS) $$SNAPSHOT_PATH; \
		echo "Validating snapshot $$SNAPSHOT_PATH against $(SHAPES)"; \
		REPORT_JSON=$$(mktemp "$(PWD)/pyshacl_report.XXXXXX.json"); \
		set +e; \
		$(PYSHACL) -s $(SHAPES) -d $$SNAPSHOT_PATH -f json-ld -o $$REPORT_JSON $(PYSHACL_ARGS); \
		VALIDATION_STATUS=$$?; \
		set -e; \
		$(PYTHON) src/validation/export_validation_report.py "$$REPORT_JSON" "$$SCHEME_SLUG" "$(VIOLATIONS_DIR)"; \
		rm -f $$REPORT_JSON; \
		if [ $$VALIDATION_STATUS -ne 0 ]; then \
			exit $$VALIDATION_STATUS; \
		fi
