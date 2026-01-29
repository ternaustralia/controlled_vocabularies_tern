"""Tests for workflow helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, SKOS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workflow import WorkflowError, strip_deprecated_concepts_from_snapshot  # noqa: E402


def _write_graph(graph: Graph, destination: Path) -> None:
    serialized = graph.serialize(format="turtle")
    destination.write_text(serialized, encoding="utf-8")


def test_strip_deprecated_concepts_updates_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "scheme.ttl"
    graph = Graph()
    scheme = URIRef("http://example.com/scheme")
    deprecated = URIRef("http://example.com/concept/deprecated")
    active = URIRef("http://example.com/concept/active")

    graph.add((scheme, SKOS.prefLabel, Literal("Example Scheme")))
    graph.add((scheme, SKOS.hasTopConcept, deprecated))
    graph.add((deprecated, SKOS.inScheme, scheme))
    graph.add((deprecated, SKOS.prefLabel, Literal("Deprecated Concept")))
    graph.add((deprecated, OWL.deprecated, Literal(True)))
    graph.add((active, SKOS.inScheme, scheme))
    graph.add((active, SKOS.prefLabel, Literal("Active Concept", lang="en")))

    _write_graph(graph, snapshot)

    removed = strip_deprecated_concepts_from_snapshot(snapshot)

    assert removed == 1

    updated = Graph()
    updated.parse(str(snapshot))
    assert list(updated.triples((deprecated, None, None))) == []
    assert list(updated.triples((None, None, deprecated))) == []
    assert (active, SKOS.prefLabel, Literal("Active Concept", lang="en")) in updated


def test_strip_deprecated_concepts_raises_for_invalid_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "broken.ttl"
    snapshot.write_text("this is not valid turtle", encoding="utf-8")

    with pytest.raises(WorkflowError):
        strip_deprecated_concepts_from_snapshot(snapshot)
