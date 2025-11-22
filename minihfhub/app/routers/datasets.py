from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from minihfhub.app.services.dataset_service import DatasetService
from minihfhub.app.services.gitea_client import GiteaClient
from minihfhub.app.services.metadata_cache import MetadataCache
from minihfhub.app.utils.auth import get_bearer_token

router = APIRouter(prefix="/datasets", tags=["datasets"])

metadata_cache = MetadataCache()
gitea_client = GiteaClient()
dataset_service = DatasetService(metadata_cache, gitea_client)


@router.get("/{owner}/{dataset}/info")
async def dataset_info(
    owner: str,
    dataset: str,
    request: Request,
    revision: str = "main",
    token: str | None = Depends(get_bearer_token),
):
    try:
        meta = await dataset_service.refresh_dataset(owner, dataset, revision, token)
    except httpx.HTTPStatusError as exc:
        cached = dataset_service.get_cached_dataset(owner, dataset)
        if cached:
            return cached
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc)) from exc
    return meta


@router.get("/{owner}/{dataset}/tree/{revision}")
async def dataset_tree(owner: str, dataset: str, revision: str, token: str | None = Depends(get_bearer_token)):
    try:
        tree = await gitea_client.get_tree(owner, dataset, revision, token)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc)) from exc
    return {"id": f"{owner}/{dataset}", "revision": revision, "tree": tree.get("tree", [])}


@router.get("/{owner}/{dataset}/resolve/{revision}/{file_path:path}")
async def resolve_file(
    owner: str,
    dataset: str,
    revision: str,
    file_path: str,
    token: str | None = Depends(get_bearer_token),
    request: Request | None = None,
):
    range_header = request.headers.get("range") if request else None
    response, client = await gitea_client.stream_file(owner, dataset, file_path, revision, token, range_header)

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        await response.aclose()
        await client.aclose()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    headers = {}
    passthrough_headers = [
        "content-length",
        "content-type",
        "content-range",
        "accept-ranges",
        "last-modified",
        "etag",
    ]
    for key in passthrough_headers:
        if key in response.headers:
            headers[key] = response.headers[key]

    async def iterator():
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        iterator(),
        status_code=response.status_code,
        headers=headers,
        media_type=headers.get("content-type", "application/octet-stream"),
    )
