SHELL := /bin/bash

PYTHON ?= python3
WORKFLOW := src/workflow.py
CONFIG ?= config/schemes.yaml
VIOLATIONS_DIR ?=

PIPELINE_FLAGS ?=
PULL_FLAGS ?=
VALIDATE_FLAGS ?=
NORMALIZE_FLAGS ?=

.PHONY: pipeline
pipeline:
	@if [ -z "$(VIOLATIONS_DIR)" ]; then \
		echo "VIOLATIONS_DIR is required. Usage: make pipeline VIOLATIONS_DIR=<path-to-store-violations>"; \
		exit 1; \
	fi
	$(PYTHON) $(WORKFLOW) pipeline --config "$(CONFIG)" --violations-dir "$(VIOLATIONS_DIR)" $(PIPELINE_FLAGS) $(if $(SCHEME),--scheme "$(SCHEME)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)")

.PHONY: pull
pull:
	$(PYTHON) $(WORKFLOW) pull --config "$(CONFIG)" $(PULL_FLAGS) $(if $(SCHEME),--scheme "$(SCHEME)") $(if $(ENDPOINT),--endpoint "$(ENDPOINT)")

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
