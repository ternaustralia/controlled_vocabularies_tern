"""Lightweight client for interacting with the Research Vocabularies Australia API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Mapping, Tuple

import requests


class RVAClientError(RuntimeError):
    """Raised when the RVA API responds with an error."""


@dataclass(frozen=True)
class RVAEnvironment:
    name: str
    base_url: str


_ENVIRONMENTS: Mapping[str, RVAEnvironment] = {
    "prod": RVAEnvironment("prod", "https://vocabs.ardc.edu.au/registry/api/"),
    "test": RVAEnvironment("test", "https://demo.vocabs.ardc.edu.au/registry/api/"),
}


class RVAClient:
    """HTTP client with the minimal RVA endpoints required for publishing vocabularies."""

    def __init__(
        self,
        environment: str,
        auth: Tuple[str, str],
        *,
        timeout: int = 60,
        session: requests.Session | None = None,
    ) -> None:
        try:
            self._env = _ENVIRONMENTS[environment]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"Unknown RVA environment '{environment}'. Expected one of {sorted(_ENVIRONMENTS)}"
            ) from exc
        self._auth = auth
        self._timeout = timeout
        self._session = session or requests.Session()

    @property
    def base_url(self) -> str:
        return self._env.base_url

    def get_vocabulary(self, vocabulary_id: str | int) -> dict:
        """Return public metadata for the given vocabulary."""
        url = f"{self.base_url}resource/vocabularies/{vocabulary_id}"
        return self._get(url)

    def get_vocabulary_edit(self, vocabulary_id: str | int) -> dict:
        """Return editable metadata for the given vocabulary (requires authentication)."""
        url = f"{self.base_url}resource/vocabularies/{vocabulary_id}/edit"
        return self._get(url, auth=self._auth)

    def create_upload(
        self,
        file_content: bytes | str | Path | BinaryIO,
        filename: str,
        *,
        owner: str,
        file_format: str = "TTL",
    ) -> tuple[str, str]:
        """Upload Turtle data and return the RVA upload ID and sanitized filename."""
        url = f"{self.base_url}resource/uploads"
        params = {"format": file_format, "owner": owner}
        file_tuple, to_close = self._prepare_file_payload(file_content, filename)
        try:
            response = self._request(
                "post",
                url,
                params=params,
                files={"file": file_tuple},
                headers={"accept": "application/json"},
                auth=self._auth,
            )
        finally:
            if to_close is not None:
                to_close.close()
        data = response.json()
        return str(data.get("integerValue")), str(data.get("stringValue"))

    def publish_new_vocabulary_version(
        self,
        vocabulary_id: str | int,
        upload_id: str | int,
        title: str,
        web_page_url: str,
        release_date: str,
    ) -> dict:
        """Mark a new version as current for the vocabulary using the uploaded distribution."""
        metadata = self.get_vocabulary_edit(vocabulary_id)
        versions = metadata.get("version")
        if versions is None:
            versions = []
            metadata["version"] = versions
        for version in versions:
            if version.get("status") == "current":
                version["status"] = "superseded"

        versions.append(
            {
                "browse-flag": ["includeCollections", "mayResolveResources"],
                "access-point": [
                    {
                        "ap-file": {"upload-id": int(upload_id)},
                        "source": "user",
                        "discriminator": "file",
                    },
                    {
                        "ap-web-page": {
                            "url": web_page_url
                        },
                        "source": "user",
                        "discriminator": "webPage",
                    },
                ],
                "status": "current",
                "title": title,
                "release-date": release_date,
                "do-import": True,
                "do-publish": True,
            }
        )

        url = f"{self.base_url}resource/vocabularies/{vocabulary_id}"
        headers = {"accept": "application/json", "content-type": "application/json"}
        response = self._request(
            "put",
            url,
            json=metadata,
            headers=headers,
            auth=self._auth,
        )
        return response.json()

    def _get(self, url: str, *, auth: Tuple[str, str] | None = None) -> dict:
        response = self._request(
            "get", url, headers={"accept": "application/json"}, auth=auth
        )
        return response.json()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        response = self._session.request(method, url, timeout=self._timeout, **kwargs)
        if response.status_code >= 400:
            raise RVAClientError(
                f"RVA request failed: {response.status_code} {response.reason}: {response.text}"
            )
        return response

    @staticmethod
    def _prepare_file_payload(
        file_content: bytes | str | Path | BinaryIO,
        filename: str,
    ) -> tuple[tuple[str, BinaryIO | bytes], BinaryIO | None]:
        if isinstance(file_content, bytes):
            return (filename, file_content), None
        if isinstance(file_content, str):
            return (filename, file_content.encode("utf-8")), None
        if isinstance(file_content, Path):
            handle = file_content.open("rb")
            return (filename, handle), handle
        return (filename, file_content), None
