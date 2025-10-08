from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.publish import publish_to_rva
from src.publish.filters import FilterResults


class DummyClient:
    def __init__(self, environment: str, auth: tuple[str, str], *, timeout: int):
        self.environment = environment
        self.auth = auth
        self.timeout = timeout
        self.uploads: list[tuple[bytes, str, str]] = []

    def get_vocabulary(self, vocabulary_id: str | int) -> dict:
        self.last_vocabulary_id = vocabulary_id
        return {"owner": "owner-123"}

    def create_upload(self, payload: bytes, filename: str, *, owner: str) -> tuple[str, str]:
        self.uploads.append((payload, filename, owner))
        return "456", filename

    def publish_new_vocabulary_version(
        self, vocabulary_id: str | int, upload_id: str | int, title: str, release_date: str
    ) -> dict:
        self.published = {
            "vocabulary_id": vocabulary_id,
            "upload_id": upload_id,
            "title": title,
            "release_date": release_date,
        }
        return {"status": "ok"}


def test_resolve_required_prefers_cli(monkeypatch):
    monkeypatch.setenv("RVA_USERNAME", "env-user")
    assert publish_to_rva.resolve_required("cli-user", "RVA_USERNAME", display="user") == "cli-user"


def test_resolve_required_reads_env(monkeypatch):
    monkeypatch.setenv("RVA_PASSWORD", "env-pass")
    assert publish_to_rva.resolve_required(None, "RVA_PASSWORD", display="password") == "env-pass"


def test_resolve_required_missing_errors(monkeypatch):
    monkeypatch.delenv("RVA_VERSION", raising=False)
    with pytest.raises(SystemExit):
        publish_to_rva.resolve_required(None, "RVA_VERSION", display="version")


def test_assemble_payload_loads_turtle(tmp_path):
    turtle_path = tmp_path / "vocab.ttl"
    turtle_path.write_text("""@prefix ex: <http://example.com/> . ex:a ex:b ex:c .""")

    payload, stats = publish_to_rva.assemble_payload(turtle_path)
    assert isinstance(payload, (bytes, bytearray))
    assert b"ex:a" in payload
    assert stats == FilterResults()


def test_assemble_payload_rejects_directory(tmp_path):
    directory = tmp_path / "dir"
    directory.mkdir()
    with pytest.raises(SystemExit):
        publish_to_rva.assemble_payload(directory)


def test_publish_happy_path(monkeypatch, capsys):
    dummy_client = DummyClient("test", ("user", "pass"), timeout=60)
    monkeypatch.setattr(publish_to_rva, "RVAClient", lambda *a, **kw: dummy_client)
    monkeypatch.setattr(
        publish_to_rva,
        "assemble_payload",
        lambda path: (
            b"ttl-bytes",
            FilterResults(
                deprecated_concepts_removed=1,
                broad_matches_removed=2,
                invalid_hierarchy_links_removed=3,
            ),
        ),
    )

    args = argparse.Namespace(
        path=Path("/tmp/vocab.ttl"),
        username="user",
        password="pass",
        vocabulary_id="123",
        version="1.2.3",
        environment="test",
        upload_filename="upload.ttl",
        timeout=60,
    )

    exit_code = publish_to_rva.publish(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Vocabulary published successfully." in captured.out
    assert "viewById/123" in captured.out
    assert "Filtered out 1 deprecated concept" in captured.out
    assert "Removed 2 skos:broadMatch" in captured.out
    assert "Removed 3 skos:broader/skos:narrower" in captured.out
    assert dummy_client.uploads[0][0] == b"ttl-bytes"
    assert dummy_client.published["title"] == "1.2.3"


def test_publish_requires_owner(monkeypatch):
    class NoOwnerClient(DummyClient):
        def get_vocabulary(self, vocabulary_id: str | int) -> dict:  # type: ignore[override]
            return {}

    monkeypatch.setattr(publish_to_rva, "RVAClient", lambda *a, **kw: NoOwnerClient("test", ("u", "p"), timeout=60))
    monkeypatch.setattr(
        publish_to_rva,
        "assemble_payload",
        lambda path: (b"ttl", FilterResults()),
    )

    args = argparse.Namespace(
        path=Path("/tmp/vocab.ttl"),
        username="user",
        password="pass",
        vocabulary_id="123",
        version="1.0.0",
        environment="test",
        upload_filename="upload.ttl",
        timeout=60,
    )

    with pytest.raises(SystemExit) as exc:
        publish_to_rva.publish(args)
    assert "did not include an owner" in str(exc.value)
