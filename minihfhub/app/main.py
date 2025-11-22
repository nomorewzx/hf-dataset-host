from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from minihfhub.app.routers import datasets
from minihfhub.app.utils.auth import get_bearer_token

app = FastAPI(title="MiniHFHub", version="0.1.0")
app.include_router(datasets.router)

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

metadata_cache = datasets.metadata_cache
dataset_service = datasets.dataset_service


@app.get("/", response_class=HTMLResponse)
async def list_datasets(request: Request):
    datasets_cached = metadata_cache.list_datasets()
    return templates.TemplateResponse(
        "dataset_list.html", {"request": request, "datasets": datasets_cached}
    )


@app.get("/datasets/{owner}/{dataset}", response_class=HTMLResponse)
async def dataset_detail(owner: str, dataset: str, request: Request, token: str | None = Depends(get_bearer_token)):
    cached = dataset_service.get_cached_dataset(owner, dataset)
    if cached is None:
        try:
            cached = await dataset_service.refresh_dataset(owner, dataset, "main", token)
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return templates.TemplateResponse("dataset_detail.html", {"request": request, "dataset": cached})


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
