from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.publish.rva_client import RVAClient, RVAClientError


def make_response(status_code: int, payload: dict) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(payload).encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    response.url = "https://example.test/api"
    response.reason = "OK" if status_code < 400 else "Bad Request"
    return response


def test_invalid_environment():
    with pytest.raises(ValueError):
        RVAClient("invalid", ("user", "pass"))


def test_get_vocabulary_uses_session():
    session = MagicMock()
    session.request.return_value = make_response(200, {"owner": "owner"})
    client = RVAClient("test", ("user", "pass"), session=session)

    metadata = client.get_vocabulary(123)

    expected_url = "https://demo.vocabs.ardc.edu.au/registry/api/resource/vocabularies/123"
    session.request.assert_called_once_with(
        "get",
        expected_url,
        timeout=60,
        auth=None,
        headers={"accept": "application/json"},
    )
    assert metadata["owner"] == "owner"


def test_create_upload_returns_identifiers(tmp_path):
    payload_path = tmp_path / "data.ttl"
    payload_path.write_text("""@prefix ex: <http://example.com/> . ex:a ex:b ex:c .""")

    session = MagicMock()
    session.request.return_value = make_response(201, {"integerValue": 42, "stringValue": "data.ttl"})

    client = RVAClient("prod", ("user", "pass"), session=session)
    upload_id, filename = client.create_upload(payload_path, "upload.ttl", owner="owner")

    expected_url = "https://vocabs.ardc.edu.au/registry/api/resource/uploads"
    args, kwargs = session.request.call_args
    assert args == ("post", expected_url)
    assert kwargs["params"] == {"format": "TTL", "owner": "owner"}
    assert kwargs["headers"] == {"accept": "application/json"}
    assert kwargs["files"]["file"][0] == "upload.ttl"
    assert upload_id == "42"
    assert filename == "data.ttl"


def test_request_error_raises_exception():
    session = MagicMock()
    session.request.return_value = make_response(400, {"error": "bad"})

    client = RVAClient("test", ("user", "pass"), session=session)

    with pytest.raises(RVAClientError):
        client.get_vocabulary(123)


def test_prepare_file_payload_handles_bytes():
    client = RVAClient("test", ("user", "pass"))
    file_tuple, to_close = client._prepare_file_payload(b"data", "upload.ttl")

    assert file_tuple == ("upload.ttl", b"data")
    assert to_close is None


def test_prepare_file_payload_opens_path(tmp_path):
    client = RVAClient("test", ("user", "pass"))
    payload = tmp_path / "file.ttl"
    payload.write_text("data")

    file_tuple, to_close = client._prepare_file_payload(payload, "upload.ttl")
    assert file_tuple[0] == "upload.ttl"
    assert file_tuple[1].read() == b"data"
    to_close.close()
