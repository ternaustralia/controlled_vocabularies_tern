"""Command-line workflow runner for SKOS ConceptScheme processing."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from rdflib import Graph
from rdflib.util import guess_format

from publish.filters import remove_deprecated_concepts
from scheme_registry import DEFAULT_CONFIG, load_registry, select_schemes
from validation.export_validation_report import export_rows, load_violations


PROJECT_ROOT = Path(__file__).resolve().parent
PULL_SCRIPT = PROJECT_ROOT / "ingest" / "pull_skos_scheme.py"


class WorkflowError(Exception):
    """Domain-specific runtime error."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to scheme registry (default: {DEFAULT_CONFIG})",
    )
    common.add_argument(
        "--scheme",
        help="Run a specific scheme (registry id or concept scheme IRI)."
        " If omitted, run all registered schemes.",
    )
    common.add_argument(
        "--endpoint",
        help="Endpoint override when --scheme is provided but missing from the registry.",
    )
    common.add_argument(
        "--format",
        default="text/turtle",
        help="Serialization format to request from the endpoint (default: text/turtle).",
    )
    common.add_argument("--pull-args", default="", help="Extra arguments for the pull script.")

    pipeline = subparsers.add_parser("pipeline", parents=[common])
    pipeline.add_argument(
        "--violations-dir",
        required=True,
        type=Path,
        help="Directory where validation XLSX reports should be written.",
    )
    pipeline.add_argument(
        "--ontotools",
        default="ontotools",
        help="ontotools executable (default: ontotools).",
    )
    pipeline.add_argument(
        "--ontotools-args",
        default="",
        help="Extra ontotools arguments (quoted string).",
    )
    pipeline.add_argument("--pyshacl", default="pyshacl", help="pyshacl executable name.")
    pipeline.add_argument("--pyshacl-args", default="", help="Extra pyshacl arguments.")
    pipeline.add_argument(
        "--base-shape",
        default="shapes/skos-basics.ttl",
        help="Baseline SHACL shapes file (auto-added for every validation run).",
    )

    pull = subparsers.add_parser("pull", parents=[common])

    validate = subparsers.add_parser("validate")
    validate.add_argument("snapshot", type=Path, help="Path to snapshot file")
    validate.add_argument(
        "--schemes",
        nargs="*",
        default=[],
        help="Optional list of validator files in addition to the baseline shape.",
    )
    validate.add_argument(
        "--violations-dir",
        required=True,
        type=Path,
        help="Directory where validation XLSX reports should be written.",
    )
    validate.add_argument(
        "--scheme-slug",
        help="Slug for naming the validation report. Default derived from snapshot filename.",
    )
    validate.add_argument("--pyshacl", default="pyshacl")
    validate.add_argument("--pyshacl-args", default="")
    validate.add_argument(
        "--base-shape",
        default="shapes/skos-basics.ttl",
        help="Baseline validator applied to every run.",
    )

    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("snapshot", type=Path, help="Snapshot to normalize in place")
    normalize.add_argument("--ontotools", default="ontotools")
    normalize.add_argument("--ontotools-args", default="")

    return parser


def _shlex_split(args: str) -> list[str]:
    return shlex.split(args) if args else []


def _run_subprocess(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, check=True, text=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        raise WorkflowError(
            f"Command failed ({' '.join(cmd)}): {exc.stderr.strip() or exc.stdout.strip()}"
        ) from exc


def _parse_pull_output(stdout: str) -> tuple[Path, str]:
    snapshot_path: Path | None = None
    slug: str | None = None
    for line in stdout.splitlines():
        if line.startswith("SNAPSHOT_PATH="):
            snapshot_path = Path(line.split("=", 1)[1].strip())
        elif line.startswith("SCHEME_SLUG="):
            slug = line.split("=", 1)[1].strip()
    if snapshot_path is None or slug is None:
        raise WorkflowError("Pull script did not emit SNAPSHOT_PATH and SCHEME_SLUG metadata.")
    return snapshot_path, slug


def strip_deprecated_concepts_from_snapshot(snapshot: Path) -> int:
    """Remove deprecated concepts from a serialized graph on disk."""

    graph = Graph()
    try:
        graph.parse(str(snapshot))
    except Exception as exc:  # pragma: no cover - rdflib provides detailed errors
        raise WorkflowError(
            f"Failed to parse snapshot {snapshot} while stripping deprecated concepts: {exc}"
        ) from exc

    removed = remove_deprecated_concepts(graph)
    if not removed:
        return 0

    suffix = snapshot.suffix.lower().lstrip(".")
    format_hint = guess_format(suffix) or "turtle"
    serialized = graph.serialize(format=format_hint)
    snapshot.write_text(serialized, encoding="utf-8")
    return removed


def _normalize_snapshot(snapshot: Path, ontotools: str, extra_args: str) -> None:
    cmd = [ontotools, "file", "normalize"] + _shlex_split(extra_args) + [str(snapshot)]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ttl", mode="w+") as tmp:
        tmp_path = Path(tmp.name)
        completed = subprocess.run(cmd, stdout=tmp, stderr=subprocess.PIPE, text=True)
    try:
        if completed.returncode != 0:
            raise WorkflowError(
                f"Normalization failed for {snapshot}: {completed.stderr.strip() if completed.stderr else 'unknown error'}"
            )
        if tmp_path.stat().st_size == 0:
            print(
                f"Normalization produced no output for {snapshot}; leaving snapshot unchanged."
            )
            return
        snapshot.write_text(tmp_path.read_text())
    finally:
        tmp_path.unlink(missing_ok=True)


def _run_pyshacl(
    snapshot: Path,
    validators: Iterable[Path | str],
    pyshacl_exe: str,
    extra_args: str,
) -> Path:
    validators_list = [str(Path(v)) for v in validators]
    cmd = [pyshacl_exe]
    for validator in validators_list:
        cmd.extend(["-s", validator])
    cmd.extend(["-d", str(snapshot)])
    cmd.extend(_shlex_split(extra_args))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        report_path = Path(tmp.name)
    cmd.extend(["-f", "json-ld", "-o", str(report_path)])
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode not in (0, 1):
        raise WorkflowError(
            f"pyshacl failed for {snapshot}: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    return report_path


def _export_report(report_path: Path, slug: str, output_dir: Path) -> None:
    rows = load_violations(report_path)
    report_path.unlink(missing_ok=True)
    if rows:
        destination = export_rows(rows, slug, output_dir.expanduser())
        print(
            f"Validation detected {len(rows)} violation(s). Report saved to {destination}")
    else:
        print("No SHACL violations detected; all good and ready for publication.")


def _run_pull(endpoint: str, concept_scheme: str, request_format: str, extra: str) -> tuple[Path, str]:
    cmd = [
        sys.executable,
        str(PULL_SCRIPT),
        endpoint,
        concept_scheme,
        "--format",
        request_format,
    ] + _shlex_split(extra)
    completed = _run_subprocess(cmd)
    if completed.stdout:
        print(completed.stdout.strip())
    return _parse_pull_output(completed.stdout)


def _unique_validators(base_shape: Path, extras: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in [base_shape, *extras]:
        normalized = str(Path(path))
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def do_pipeline(args: argparse.Namespace) -> int:
    registry = load_registry(args.config)
    schemes = list(select_schemes(registry, args.scheme, args.endpoint))
    if not schemes:
        raise WorkflowError("No schemes to process.")

    overall_status = 0
    for scheme in schemes:
        print(f"\n=== Processing {scheme.identifier} ===")
        try:
            snapshot_path, slug = _run_pull(
                endpoint=scheme.endpoint,
                concept_scheme=scheme.concept_scheme,
                request_format=args.format,
                extra=args.pull_args,
            )
            removed = strip_deprecated_concepts_from_snapshot(snapshot_path)
            if removed:
                print(f"Removed {removed} deprecated concept(s) before validation.")
            _normalize_snapshot(snapshot_path, args.ontotools, args.ontotools_args)
            validators = _unique_validators(Path(args.base_shape), scheme.validators)
            print("Using validators:")
            for validator in validators:
                print(f"  - {validator}")
            report_path = _run_pyshacl(
                snapshot=snapshot_path,
                validators=validators,
                pyshacl_exe=args.pyshacl,
                extra_args=args.pyshacl_args,
            )
            _export_report(report_path, slug, args.violations_dir)
        except WorkflowError as exc:
            overall_status = 1
            print(f"Error: {exc}", file=sys.stderr)
    return overall_status


def do_pull(args: argparse.Namespace) -> int:
    registry = load_registry(args.config)
    schemes = list(select_schemes(registry, args.scheme, args.endpoint))
    if not schemes:
        raise WorkflowError("No schemes to process.")
    for scheme in schemes:
        print(f"\n=== Pulling {scheme.identifier} ===")
        _run_pull(
            endpoint=scheme.endpoint,
            concept_scheme=scheme.concept_scheme,
            request_format=args.format,
            extra=args.pull_args,
        )
    return 0


def do_validate(args: argparse.Namespace) -> int:
    snapshot_path = args.snapshot
    if not snapshot_path.exists():
        raise WorkflowError(f"Snapshot {snapshot_path} not found")
    removed = strip_deprecated_concepts_from_snapshot(snapshot_path)
    if removed:
        print(f"Removed {removed} deprecated concept(s) before validation.")
    slug = args.scheme_slug or snapshot_path.stem.split("_", 1)[0]
    validators = _unique_validators(Path(args.base_shape), args.schemes)
    report_path = _run_pyshacl(
        snapshot=snapshot_path,
        validators=validators,
        pyshacl_exe=args.pyshacl,
        extra_args=args.pyshacl_args,
    )
    _export_report(report_path, slug, args.violations_dir)
    return 0


def do_normalize(args: argparse.Namespace) -> int:
    snapshot_path = args.snapshot
    if not snapshot_path.exists():
        raise WorkflowError(f"Snapshot {snapshot_path} not found")
    _normalize_snapshot(snapshot_path, args.ontotools, args.ontotools_args)
    print(f"Normalized {snapshot_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "pipeline": do_pipeline,
        "pull": do_pull,
        "validate": do_validate,
        "normalize": do_normalize,
    }

    handler = handlers[args.command]
    try:
        return handler(args)
    except WorkflowError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
