"""Collection registry helper for SKOS Collection workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "collections.yaml"


@dataclass
class CollectionEntry:
    identifier: str
    endpoint: str
    collection: str
    validators: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to collections registry (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--collection",
        help="Identifier or Collection IRI to return. If omitted, list all registered collections.",
    )
    parser.add_argument(
        "--endpoint",
        help="Fallback endpoint when --collection is supplied but missing from the registry.",
    )
    parser.add_argument(
        "--format",
        choices={"plain"},
        default="plain",
        help="Output format. Only 'plain' (pipe-delimited rows) is currently supported.",
    )
    return parser.parse_args()


def load_registry(path: Path) -> Sequence[CollectionEntry]:
    if not path.exists():
        return []
    content = yaml.safe_load(path.read_text()) or {}
    collections: list[CollectionEntry] = []
    for entry in content.get("collections", []):
        endpoint = entry.get("endpoint")
        collection = entry.get("collection")
        if not endpoint or not collection:
            continue
        identifier = str(entry.get("id") or collection)
        validators = [str(v) for v in entry.get("validators", [])]
        collections.append(
            CollectionEntry(
                identifier=identifier,
                endpoint=str(endpoint),
                collection=str(collection),
                validators=validators,
            )
        )
    return collections


def select_collections(
    registry: Sequence[CollectionEntry],
    requested: str | None,
    endpoint_override: str | None,
) -> Iterable[CollectionEntry]:
    if requested is None:
        return registry

    for collection in registry:
        if requested in {collection.identifier, collection.collection}:
            return [collection]

    if endpoint_override is None:
        raise SystemExit(
            "Collection not found in registry and --endpoint not provided for override."
        )

    return [
        CollectionEntry(
            identifier=requested,
            endpoint=endpoint_override,
            collection=requested,
            validators=[],
        )
    ]


def emit_plain(collections: Iterable[CollectionEntry]) -> int:
    count = 0
    for collection in collections:
        validators = " ".join(collection.validators)
        print(
            "|".join(
                [
                    collection.identifier,
                    collection.endpoint,
                    collection.collection,
                    validators,
                ]
            )
        )
        count += 1
    return count


def main() -> int:
    args = parse_args()
    registry = load_registry(args.config)
    collections = list(select_collections(registry, args.collection, args.endpoint))

    if not collections:
        raise SystemExit(
            "No collections available. Check the registry or provide --collection."
        )

    emitted = emit_plain(collections)
    if emitted == 0:
        raise SystemExit("No collections emitted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
