from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, SKOS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.publish.filters import (
    FilterResults,
    apply_publish_filters,
    remove_broad_matches,
    remove_deprecated_concepts,
    remove_invalid_hierarchy_links,
)


def test_remove_deprecated_concepts_removes_subject_and_references():
    graph = Graph()
    active = URIRef("http://example.com/concept/active")
    deprecated = URIRef("http://example.com/concept/deprecated")
    scheme = URIRef("http://example.com/scheme")

    graph.add((active, SKOS.narrower, deprecated))
    graph.add((deprecated, SKOS.prefLabel, Literal("Deprecated")))
    graph.add((deprecated, OWL.deprecated, Literal(True)))
    graph.add((scheme, SKOS.hasTopConcept, deprecated))

    removed = remove_deprecated_concepts(graph)

    assert removed == 1
    assert list(graph.triples((deprecated, None, None))) == []
    assert list(graph.triples((None, None, deprecated))) == []


def test_remove_broad_matches_removes_triples_only():
    graph = Graph()
    concept = URIRef("http://example.com/concept")
    external = URIRef("http://external.example.com/concept")

    graph.add((concept, SKOS.prefLabel, Literal("Concept")))
    graph.add((concept, SKOS.broadMatch, external))
    graph.add((external, SKOS.prefLabel, Literal("External")))

    removed = remove_broad_matches(graph)

    assert removed == 1
    assert list(graph.triples((concept, SKOS.broadMatch, external))) == []
    assert list(graph.triples((external, None, None)))  # untouched triples remain


def test_remove_invalid_hierarchy_links_only_targets_without_type():
    graph = Graph()
    concept = URIRef("http://example.com/concept")
    valid_target = URIRef("http://example.com/valid")
    invalid_target = URIRef("http://example.com/invalid")

    graph.add((concept, RDF.type, SKOS.Concept))
    graph.add((valid_target, RDF.type, SKOS.Concept))

    graph.add((concept, SKOS.narrower, valid_target))
    graph.add((concept, SKOS.broader, invalid_target))

    removed = remove_invalid_hierarchy_links(graph)

    assert removed == 1
    assert list(graph.triples((concept, SKOS.broader, invalid_target))) == []
    assert list(graph.triples((concept, SKOS.narrower, valid_target)))


def test_apply_publish_filters_combines_results():
    graph = Graph()
    deprecated = URIRef("http://example.com/deprecated")
    graph.add((deprecated, OWL.deprecated, Literal(True)))
    graph.add((URIRef("http://example.com/a"), SKOS.broadMatch, URIRef("http://example.com/b")))
    graph.add((URIRef("http://example.com/a"), SKOS.broader, URIRef("http://example.com/missing")))

    results = apply_publish_filters(graph)

    assert isinstance(results, FilterResults)
    assert results.deprecated_concepts_removed == 1
    assert results.broad_matches_removed == 1
    assert results.invalid_hierarchy_links_removed == 1
