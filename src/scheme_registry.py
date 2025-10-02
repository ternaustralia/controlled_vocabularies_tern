"""Scheme registry helper for ConceptScheme workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "schemes.yaml"


@dataclass
class Scheme:
    identifier: str
    endpoint: str
    concept_scheme: str
    validators: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to schemes registry (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--scheme",
        help="Identifier or ConceptScheme IRI to return. If omitted, list all registered schemes.",
    )
    parser.add_argument(
        "--endpoint",
        help="Fallback endpoint when --scheme is supplied but missing from the registry.",
    )
    parser.add_argument(
        "--format",
        choices={"plain"},
        default="plain",
        help="Output format. Only 'plain' (pipe-delimited rows) is currently supported.",
    )
    return parser.parse_args()


def load_registry(path: Path) -> Sequence[Scheme]:
    if not path.exists():
        return []
    content = yaml.safe_load(path.read_text()) or {}
    schemes: list[Scheme] = []
    for entry in content.get("schemes", []):
        endpoint = entry.get("endpoint")
        concept_scheme = entry.get("concept_scheme")
        if not endpoint or not concept_scheme:
            continue
        identifier = str(entry.get("id") or concept_scheme)
        validators = [str(v) for v in entry.get("validators", [])]
        schemes.append(
            Scheme(
                identifier=identifier,
                endpoint=str(endpoint),
                concept_scheme=str(concept_scheme),
                validators=validators,
            )
        )
    return schemes


def select_schemes(
    registry: Sequence[Scheme],
    requested: str | None,
    endpoint_override: str | None,
) -> Iterable[Scheme]:
    if requested is None:
        return registry

    for scheme in registry:
        if requested in {scheme.identifier, scheme.concept_scheme}:
            return [scheme]

    if endpoint_override is None:
        raise SystemExit(
            "Scheme not found in registry and --endpoint not provided for override."
        )

    return [
        Scheme(
            identifier=requested,
            endpoint=endpoint_override,
            concept_scheme=requested,
            validators=[],
        )
    ]


def emit_plain(schemes: Iterable[Scheme]) -> int:
    count = 0
    for scheme in schemes:
        validators = " ".join(scheme.validators)
        print(
            "|".join(
                [
                    scheme.identifier,
                    scheme.endpoint,
                    scheme.concept_scheme,
                    validators,
                ]
            )
        )
        count += 1
    return count


def main() -> int:
    args = parse_args()
    registry = load_registry(args.config)
    schemes = list(select_schemes(registry, args.scheme, args.endpoint))

    if not schemes:
        raise SystemExit("No schemes available. Check the registry or provide --scheme.")

    emitted = emit_plain(schemes)
    if emitted == 0:
        raise SystemExit("No schemes emitted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
