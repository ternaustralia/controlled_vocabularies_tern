SHELL := /bin/bash

PYTHON ?= python3
WORKFLOW := src/workflow.py
CONFIG ?= config/schemes.yaml
COLLECTIONS_CONFIG ?= config/collections.yaml
VIOLATIONS_DIR ?=
MAX_DEPTH ?= 3

PIPELINE_FLAGS ?=
COLLECTION_PIPELINE_FLAGS ?=
PULL_FLAGS ?=
COLLECTION_PULL_FLAGS ?=
VALIDATE_FLAGS ?=
NORMALIZE_FLAGS ?=

.PHONY: pipeline
pipeline:
	@if [ -z "$(VIOLATIONS_DIR)" ]; then \
		echo "VIOLATIONS_DIR is required. Usage: make pipeline VIOLATIONS_DIR=<path-to-store-violations>"; \
		exit 1; \
	fi
	$(PYTHON) $(WORKFLOW) pipeline --config "$(CONFIG)" --violations-dir "$(VIOLATIONS_DIR)" $(PIPELINE_FLAGS) $(if $(SCHEME),--scheme "$(SCHEME)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)")

.PHONY: collection-pipeline
collection-pipeline:
	@if [ -z "$(VIOLATIONS_DIR)" ]; then \
		echo "VIOLATIONS_DIR is required. Usage: make collection-pipeline VIOLATIONS_DIR=<path-to-store-violations>"; \
		exit 1; \
	fi
	$(PYTHON) $(WORKFLOW) collection-pipeline --config "$(COLLECTIONS_CONFIG)" --violations-dir "$(VIOLATIONS_DIR)" $(COLLECTION_PIPELINE_FLAGS) $(if $(COLLECTION),--collection "$(COLLECTION)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)") --max-depth "$(MAX_DEPTH)"

.PHONY: pull
pull:
	$(PYTHON) $(WORKFLOW) pull --config "$(CONFIG)" $(PULL_FLAGS) $(if $(SCHEME),--scheme "$(SCHEME)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)")

.PHONY: collection-pull
collection-pull:
	$(PYTHON) $(WORKFLOW) collection-pull --config "$(COLLECTIONS_CONFIG)" $(COLLECTION_PULL_FLAGS) $(if $(COLLECTION),--collection "$(COLLECTION)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)") --max-depth "$(MAX_DEPTH)"

.PHONY: validate
validate:
	@if [ -z "$(SNAPSHOT)" ]; then \
		echo "SNAPSHOT is required. Usage: make validate SNAPSHOT=<path> VIOLATIONS_DIR=<dir>"; \
		exit 1; \
	fi
	@if [ -z "$(VIOLATIONS_DIR)" ]; then \
		echo "VIOLATIONS_DIR is required. Usage: make validate SNAPSHOT=<path> VIOLATIONS_DIR=<dir>"; \
		exit 1; \
	fi
	$(PYTHON) $(WORKFLOW) validate "$(SNAPSHOT)" --violations-dir "$(VIOLATIONS_DIR)" $(VALIDATE_FLAGS)

.PHONY: normalize
normalize:
	@if [ -z "$(SNAPSHOT)" ]; then \
		echo "SNAPSHOT is required. Usage: make normalize SNAPSHOT=<path>"; \
		exit 1; \
	fi
	$(PYTHON) $(WORKFLOW) normalize "$(SNAPSHOT)" $(NORMALIZE_FLAGS)
