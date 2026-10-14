#!/usr/bin/env python3
"""Pull a SKOS Collection from a SPARQL endpoint and store a snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from string import Template

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SKOS
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from publish.filters import remove_deprecated_concepts

PREFIXES = f"PREFIX skos: <{SKOS}>\nPREFIX rdf: <{RDF}>\n"

DIRECT_QUERY_TEMPLATE = Template(
    """CONSTRUCT {
  ?collection ?collection_p ?collection_o .
  ?collection skos:member ?member .
  ?collection skos:memberList ?list .
  ?list ?list_p ?list_o .
  ?member ?member_p ?member_o .
}
WHERE {
  VALUES ?collection { $collections }
  {
    ?collection ?collection_p ?collection_o .
  } UNION {
    ?collection skos:member ?member .
    ?member ?member_p ?member_o .
  } UNION {
    ?collection skos:memberList ?list .
    ?list ?list_p ?list_o .
  } UNION {
    ?collection skos:memberList ?list .
    ?list rdf:rest*/rdf:first ?member .
    ?member ?member_p ?member_o .
  }
}
"""
)

FORMAT_MAP = {
    "text/turtle": "turtle",
    "application/ld+json": "json-ld",
    "application/rdf+xml": "xml",
}


def _post_query(endpoint: str, query: str, accept: str) -> str:
    response = requests.post(
        endpoint,
        data={"query": query},
        headers={"Accept": accept},
        timeout=120,
    )
    response.raise_for_status()
    return response.text


def _fetch_direct(
    endpoint: str, collections: list[str], request_format: str
) -> Graph:
    values = " ".join(f"<{value}>" for value in collections)
    query = PREFIXES + DIRECT_QUERY_TEMPLATE.substitute(collections=values)
    data = _post_query(endpoint, query, request_format)
    graph = Graph()
    graph.parse(data=data, format=FORMAT_MAP[request_format])
    return graph


def _expand_with_max_depth(
    endpoint: str,
    collection: str,
    request_format: str,
    max_depth: int,
) -> Graph:
    graph = Graph()
    seen: set[str] = {collection}
    current = [collection]
    depth = 0

    while current:
        batch = _fetch_direct(endpoint, current, request_format)
        graph += batch
        if depth >= max_depth:
            break

        next_collections: set[str] = set()
        for member in batch.objects(None, SKOS.member):
            if (member, RDF.type, SKOS.Collection) in batch or (
                member,
                RDF.type,
                SKOS.OrderedCollection,
            ) in batch:
                next_collections.add(str(member))
        for member in batch.objects(None, RDF.first):
            if (member, RDF.type, SKOS.Collection) in batch or (
                member,
                RDF.type,
                SKOS.OrderedCollection,
            ) in batch:
                next_collections.add(str(member))

        next_collections = {value for value in next_collections if value not in seen}
        seen.update(next_collections)
        current = sorted(next_collections)
        depth += 1

    return graph


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a SKOS Collection and write it to data/snapshots."
    )
    parser.add_argument("endpoint", help="URL of the SPARQL endpoint")
    parser.add_argument("collection", help="IRI of the SKOS Collection to fetch")
    parser.add_argument(
        "--format",
        default="text/turtle",
        choices=list(FORMAT_MAP.keys()),
        help="Serialization format to request from the endpoint",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        required=True,
        help="Maximum nesting depth of collection members to pull",
    )
    args = parser.parse_args()

    if args.max_depth < 0:
        parser.error("--max-depth must be >= 0")

    snapshots_dir = Path(__file__).resolve().parents[2] / "data" / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    try:
        graph = _expand_with_max_depth(
            args.endpoint, args.collection, args.format, args.max_depth
        )
    except requests.HTTPError as err:
        sys.stderr.write(f"Failed to fetch Collection: {err}\n")
        raise SystemExit(1) from err

    removed = remove_deprecated_concepts(graph)
    if removed:
        print(f"Filtered out {removed} deprecated concept(s) prior to snapshot serialization.")

    collection_ref = URIRef(args.collection)
    label = None
    fallback = None
    for candidate in graph.objects(collection_ref, SKOS.prefLabel):
        text = str(candidate).strip()
        if not text:
            continue
        if getattr(candidate, "language", None) in (None, "", "en"):
            label = text
            break
        if fallback is None:
            fallback = text
    label_text = label or fallback or "collection"
    slug = re.sub(r"[^0-9A-Za-z]+", "_", label_text).strip("_") or "collection"

    brisbane_now = dt.datetime.now(ZoneInfo("Australia/Brisbane"))
    timestamp = brisbane_now.strftime("%Y%m%dT%H%M%S%z")
    extension = {
        "text/turtle": "ttl",
        "application/ld+json": "jsonld",
        "application/rdf+xml": "rdf",
    }[args.format]
    destination = snapshots_dir / f"{slug}_{timestamp}.{extension}"

    graph.serialize(destination, format=FORMAT_MAP[args.format])
    print(f"Wrote snapshot to {destination}")
    print(f"SNAPSHOT_PATH={destination}")
    print(f"COLLECTION_SLUG={slug}")


if __name__ == "__main__":
    main()
