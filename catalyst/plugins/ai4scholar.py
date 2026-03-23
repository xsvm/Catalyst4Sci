from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from catalyst.models.plugin import PluginMetadata
from catalyst.plugins.base import PluginResponse


DEFAULT_BASE_URL = "https://ai4scholar.net/graph/v1"
DEFAULT_SEARCH_FIELDS = "paperId,title,abstract,authors,year,citationCount"
DEFAULT_DETAIL_FIELDS = "paperId,title,abstract,authors,year,citationCount,references,citations"


class Ai4ScholarPlugin:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("AI4SCHOLAR_API_KEY", "")
        self.base_url = (base_url or os.getenv("AI4SCHOLAR_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ai4scholar",
            description="Academic paper search and metadata lookup via Ai4Scholar Graph API.",
            configured=bool(self.api_key),
            capabilities=["search-papers", "get-paper", "batch-get-papers"],
        )

    def status(self) -> PluginResponse:
        return PluginResponse(
            plugin="ai4scholar",
            operation="status",
            payload={
                "configured": bool(self.api_key),
                "base_url": self.base_url,
                "capabilities": self.metadata().capabilities,
                "auth_env": "AI4SCHOLAR_API_KEY",
            },
        )

    def search_papers(
        self,
        query: str,
        limit: int = 10,
        fields: str = DEFAULT_SEARCH_FIELDS,
    ) -> PluginResponse:
        payload = self._request_json(
            method="GET",
            path="/paper/search",
            params={"query": query, "limit": limit, "fields": fields},
        )
        return PluginResponse(
            plugin="ai4scholar",
            operation="search-papers",
            payload=payload,
        )

    def get_paper(
        self,
        paper_id: str,
        fields: str = DEFAULT_DETAIL_FIELDS,
    ) -> PluginResponse:
        payload = self._request_json(
            method="GET",
            path=f"/paper/{paper_id}",
            params={"fields": fields},
        )
        return PluginResponse(
            plugin="ai4scholar",
            operation="get-paper",
            payload=payload,
        )

    def batch_get_papers(self, ids: list[str]) -> PluginResponse:
        payload = self._request_json(
            method="POST",
            path="/paper/batch",
            body={"ids": ids},
        )
        return PluginResponse(
            plugin="ai4scholar",
            operation="batch-get-papers",
            payload=payload,
        )

    def _request_json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("AI4SCHOLAR_API_KEY is not configured.")
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            url=f"{self.base_url}{path}{query}",
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(body).encode("utf-8") if body is not None else None,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                remaining = response.headers.get("X-Credits-Remaining")
                if remaining is not None:
                    payload["_credits_remaining"] = remaining
                return payload
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ai4Scholar HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Ai4Scholar request failed: {exc.reason}") from exc

    @staticmethod
    def serialize(response: PluginResponse) -> dict[str, Any]:
        return asdict(response)
