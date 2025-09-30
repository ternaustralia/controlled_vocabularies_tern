#!/usr/bin/env python3
"""Pull a SKOS ConceptScheme from a SPARQL endpoint and store a snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from string import Template

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

PREFIXES = f"PREFIX skos: <{SKOS}>\n"
CONSTRUCT_BODY_TEMPLATE = Template(
    """CONSTRUCT {
  <$scheme> ?scheme_p ?scheme_o .
  ?concept ?concept_p ?concept_o .
}
WHERE {
  BIND(<$scheme> AS ?scheme)
  {
    ?scheme ?scheme_p ?scheme_o .
  } UNION {
    ?concept skos:inScheme ?scheme .
    ?concept ?concept_p ?concept_o .
  }
}
"""
)

FORMAT_MAP = {
    "text/turtle": "turtle",
    "application/ld+json": "json-ld",
    "application/rdf+xml": "xml",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a SKOS ConceptScheme and write it to data/snapshots."
    )
    parser.add_argument("endpoint", help="URL of the SPARQL endpoint")
    parser.add_argument("scheme", help="IRI of the SKOS ConceptScheme to fetch")
    parser.add_argument(
        "--format",
        default="text/turtle",
        choices=list(FORMAT_MAP.keys()),
        help="Serialization format to request from the endpoint",
    )
    args = parser.parse_args()

    snapshots_dir = Path(__file__).resolve().parents[2] / "data" / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    query = PREFIXES + CONSTRUCT_BODY_TEMPLATE.substitute(scheme=args.scheme)
    try:
        response = requests.post(
            args.endpoint,
            data={"query": query},
            headers={"Accept": args.format},
            timeout=120,
        )
        response.raise_for_status()
    except requests.HTTPError as err:
        sys.stderr.write(f"Failed to fetch ConceptScheme: {err}\n")
        raise SystemExit(1) from err

    graph = Graph()
    graph.parse(data=response.text, format=FORMAT_MAP[args.format])

    scheme_ref = URIRef(args.scheme)
    label = None
    fallback = None
    for candidate in graph.objects(scheme_ref, SKOS.prefLabel):
        text = str(candidate).strip()
        if not text:
            continue
        if getattr(candidate, "language", None) in (None, "", "en"):
            label = text
            break
        if fallback is None:
            fallback = text
    label_text = label or fallback or "concept_scheme"
    slug = re.sub(r"[^0-9A-Za-z]+", "_", label_text).strip("_") or "concept_scheme"

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    extension = {
        "text/turtle": "ttl",
        "application/ld+json": "jsonld",
        "application/rdf+xml": "rdf",
    }[args.format]
    destination = snapshots_dir / f"{slug}_{timestamp}.{extension}"

    graph.serialize(destination, format=FORMAT_MAP[args.format])
    print(f"Wrote snapshot to {destination}")


if __name__ == "__main__":
    main()
