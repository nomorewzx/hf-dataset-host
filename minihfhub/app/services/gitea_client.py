from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional, Tuple

import httpx


class GiteaClient:
    def __init__(self, api_base: Optional[str] = None, raw_base: Optional[str] = None):
        self.api_base = (api_base or os.getenv("GITEA_API_BASE", "http://gitea:3000/api/v1")).rstrip("/")
        self.raw_base = (raw_base or os.getenv("GITEA_RAW_BASE", "http://gitea:3000")).rstrip("/")

    def _headers(self, token: Optional[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    async def get_tree(self, owner: str, repo: str, revision: str, token: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/{revision}"
        params = {"recursive": 1}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self._headers(token), timeout=30.0)
            response.raise_for_status()
            return response.json()

    async def get_file_content(
        self, owner: str, repo: str, path: str, revision: str, token: Optional[str] = None
    ) -> Optional[str]:
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": revision}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self._headers(token), timeout=30.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            payload = response.json()
            content = payload.get("content")
            if content:
                try:
                    decoded = base64.b64decode(content).decode("utf-8")
                    return decoded
                except Exception:
                    return None
            return None

    async def stream_file(
        self, owner: str, repo: str, path: str, revision: str, token: Optional[str], range_header: Optional[str]
    ) -> Tuple[httpx.Response, httpx.AsyncClient]:
        raw_url = f"{self.raw_base}/{owner}/{repo}/raw/{revision}/{path}"
        headers = self._headers(token)
        if range_header:
            headers["Range"] = range_header
        client = httpx.AsyncClient(follow_redirects=True)
        response = await client.stream("GET", raw_url, headers=headers, timeout=60.0)
        return response, client
