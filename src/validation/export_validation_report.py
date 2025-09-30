"""Export SHACL validation violations into an XLSX report."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from rdflib import Graph, Namespace, RDF
from zoneinfo import ZoneInfo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to the JSON-LD validation report")
    parser.add_argument("scheme_slug", help="Slug to include in the output filename")
    parser.add_argument(
        "violations_dir",
        type=Path,
        help="Directory in which the XLSX report should be written",
    )
    return parser


def load_violations(report_path: Path) -> list[tuple[str, str, str]]:
    graph = Graph()
    graph.parse(report_path, format="json-ld")

    sh = Namespace("http://www.w3.org/ns/shacl#")
    rows: list[tuple[str, str, str]] = []
    for result in graph.subjects(RDF.type, sh.ValidationResult):
        focus = graph.value(result, sh.focusNode)
        path = graph.value(result, sh.resultPath)
        message = graph.value(result, sh.resultMessage)
        rows.append(
            (
                str(focus) if focus is not None else "",
                str(path) if path is not None else "",
                str(message) if message is not None else "",
            )
        )
    return rows


def export_rows(rows: list[tuple[str, str, str]], scheme_slug: str, output_dir: Path) -> Path:
    brisbane_now = datetime.now(ZoneInfo("Australia/Brisbane"))
    timestamp = brisbane_now.strftime("%Y%m%dT%H%M%S%z")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{scheme_slug}_validation_report_{timestamp}.xlsx"

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Violations"
    sheet.append(["ConceptIRI", "Predicate", "Violation"])
    for row in rows:
        sheet.append(row)
    workbook.save(destination)
    return destination


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        rows = load_violations(args.report)
    except Exception as exc:  # pragma: no cover - defensive logging
        parser.error(f"Failed to load validation report {args.report}: {exc}")

    scheme_slug = args.scheme_slug.strip()
    if not scheme_slug:
        parser.error("Scheme slug must not be empty")

    if rows:
        destination = export_rows(rows, scheme_slug, args.violations_dir)
        print(
            f"Validation detected {len(rows)} violation(s). "
            f"Report saved to {destination}"
        )
    else:
        print("No SHACL violations detected; all good and ready for publication.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
