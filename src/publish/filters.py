"""Utility functions to clean vocab graphs before publication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rdflib import Graph
from rdflib.namespace import OWL, RDF, SKOS
from rdflib.term import Literal


@dataclass(frozen=True)
class FilterResults:
    deprecated_concepts_removed: int = 0
    broad_matches_removed: int = 0
    invalid_hierarchy_links_removed: int = 0


def _literal_is_true(values: Iterable[object]) -> bool:
    for value in values:
        if isinstance(value, Literal):
            python_value = value.toPython()
            if isinstance(python_value, bool) and python_value:
                return True
    return False


def remove_deprecated_concepts(graph: Graph) -> int:
    """Remove deprecated concepts and references to them."""

    deprecated = {
        subject
        for subject in graph.subjects(OWL.deprecated, None)
        if _literal_is_true(graph.objects(subject, OWL.deprecated))
    }

    if not deprecated:
        return 0

    to_remove = set()
    for concept in deprecated:
        to_remove.update(graph.triples((concept, None, None)))

    to_remove.update(
        triple for triple in graph.triples((None, None, None)) if triple[2] in deprecated
    )

    for triple in to_remove:
        graph.remove(triple)

    return len(deprecated)


def remove_broad_matches(graph: Graph) -> int:
    """Remove all skos:broadMatch triples."""

    triples = list(graph.triples((None, SKOS.broadMatch, None)))
    for triple in triples:
        graph.remove(triple)
    return len(triples)


def remove_invalid_hierarchy_links(graph: Graph) -> int:
    """Remove skos:broader/narrower triples whose object is not a skos:Concept."""

    concept_nodes = {subject for subject in graph.subjects(RDF.type, SKOS.Concept)}
    removed = 0
    for predicate in (SKOS.broader, SKOS.narrower):
        for triple in list(graph.triples((None, predicate, None))):
            if triple[2] not in concept_nodes:
                graph.remove(triple)
                removed += 1
    return removed


def apply_publish_filters(graph: Graph) -> FilterResults:
    """Apply all publish-time filters and return their impact summary."""

    deprecated_removed = remove_deprecated_concepts(graph)
    broad_removed = remove_broad_matches(graph)
    hierarchy_removed = remove_invalid_hierarchy_links(graph)

    return FilterResults(
        deprecated_concepts_removed=deprecated_removed,
        broad_matches_removed=broad_removed,
        invalid_hierarchy_links_removed=hierarchy_removed,
    )
