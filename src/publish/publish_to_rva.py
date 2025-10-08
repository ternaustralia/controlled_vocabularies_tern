"""CLI utility to publish controlled vocabularies to Research Vocabularies Australia."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from rdflib import Graph

from .filters import FilterResults, apply_publish_filters
from .rva_client import RVAClient, RVAClientError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the Turtle file containing the vocabulary to upload.",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="RVA username. Falls back to RVA_USERNAME environment variable if omitted.",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="RVA password. Falls back to RVA_PASSWORD environment variable if omitted.",
    )
    parser.add_argument(
        "--vocabulary-id",
        dest="vocabulary_id",
        default=None,
        help="RVA vocabulary identifier. Falls back to RVA_VOCABULARY_ID environment variable if omitted.",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Version string for the new publication. Falls back to RVA_VERSION environment variable if omitted.",
    )
    parser.add_argument(
        "--environment",
        choices=("prod", "test"),
        default=os.getenv("RVA_ENV", "test"),
        help="RVA environment to target (prod or test). Defaults to RVA_ENV or 'test'.",
    )
    parser.add_argument(
        "--upload-filename",
        default=os.getenv("RVA_UPLOAD_FILENAME", "upload.ttl"),
        help="Filename to associate with the upload. Defaults to RVA_UPLOAD_FILENAME or 'upload.ttl'.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("RVA_TIMEOUT", "60")),
        help="HTTP timeout in seconds. Defaults to RVA_TIMEOUT or 60.",
    )
    return parser


def resolve_required(value: str | None, env_var: str, *, display: str) -> str:
    if value:
        return value
    env_value = os.getenv(env_var)
    if env_value:
        return env_value
    raise SystemExit(f"{display} is required. Provide via CLI flag or {env_var} environment variable.")


def assemble_payload(path: Path) -> tuple[bytes, FilterResults]:
    if not path.exists():
        raise SystemExit(f"Input path '{path}' does not exist.")
    if path.is_dir():
        raise SystemExit("Publishing currently supports a single Turtle file. A directory was provided.")

    graph = Graph()
    try:
        graph.parse(path, format="turtle")
    except Exception as exc:  # pragma: no cover - rdflib raises many custom exceptions
        raise SystemExit(f"Failed to parse Turtle data from {path}: {exc}") from exc

    filter_results = apply_publish_filters(graph)

    serialized = graph.serialize(format="turtle", encoding="utf-8")
    if isinstance(serialized, str):  # pragma: no cover - rdflib returns str when encoding omitted
        serialized = serialized.encode("utf-8")
    return serialized, filter_results


def publish(args: argparse.Namespace) -> int:
    username = resolve_required(args.username, "RVA_USERNAME", display="RVA username")
    password = resolve_required(args.password, "RVA_PASSWORD", display="RVA password")
    vocabulary_id = resolve_required(
        args.vocabulary_id, "RVA_VOCABULARY_ID", display="RVA vocabulary id"
    )
    version = resolve_required(args.version, "RVA_VERSION", display="Vocabulary version")

    payload, filter_results = assemble_payload(args.path)

    if filter_results.deprecated_concepts_removed:
        print(
            f"Filtered out {filter_results.deprecated_concepts_removed} deprecated concept(s) "
            "from upload."
        )
    if filter_results.broad_matches_removed:
        print(
            f"Removed {filter_results.broad_matches_removed} skos:broadMatch triple(s) before upload."
        )
    if filter_results.invalid_hierarchy_links_removed:
        print(
            "Removed "
            f"{filter_results.invalid_hierarchy_links_removed} skos:broader/skos:narrower triple(s) "
            "with non-concept targets."
        )

    client = RVAClient(args.environment, (username, password), timeout=args.timeout)

    print(f"Fetching vocabulary {vocabulary_id} metadata from RVA ({args.environment}).")
    try:
        vocab_metadata = client.get_vocabulary(vocabulary_id)
    except RVAClientError as exc:
        raise SystemExit(f"Failed to fetch vocabulary metadata: {exc}") from exc

    owner = vocab_metadata.get("owner")
    if not owner:
        raise SystemExit(
            "RVA response did not include an owner attribute; publishing cannot proceed."
        )

    print("Creating upload in RVA.")
    try:
        upload_id, sanitized_filename = client.create_upload(
            payload, args.upload_filename, owner=owner
        )
    except RVAClientError as exc:
        raise SystemExit(f"Upload to RVA failed: {exc}") from exc

    release_date = date.today().isoformat()

    print(
        f"Publishing new version {version} (upload {upload_id}, file '{sanitized_filename}') "
        f"with release date {release_date}."
    )
    try:
        client.publish_new_vocabulary_version(vocabulary_id, upload_id, version, release_date)
    except RVAClientError as exc:
        raise SystemExit(f"Failed to publish new vocabulary version: {exc}") from exc

    base_url = (
        "https://demo.vocabs.ardc.edu.au/" if args.environment == "test" else "https://vocabs.ardc.edu.au/"
    )
    print("Vocabulary published successfully.")
    print(f"View at {base_url}viewById/{vocabulary_id}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return publish(args)


if __name__ == "__main__":
    sys.exit(main())
