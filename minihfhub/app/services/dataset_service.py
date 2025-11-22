from __future__ import annotations

import json
from typing import Dict, List, Optional

from minihfhub.app.services.gitea_client import GiteaClient
from minihfhub.app.services.metadata_cache import MetadataCache


class DatasetService:
    def __init__(self, cache: MetadataCache, client: Optional[GiteaClient] = None):
        self.cache = cache
        self.client = client or GiteaClient()

    async def refresh_dataset(
        self, owner: str, dataset: str, revision: str, token: Optional[str]
    ) -> Dict[str, Optional[str]]:
        dataset_id = f"{owner}/{dataset}"
        tree = await self.client.get_tree(owner, dataset, revision, token)
        files = [entry["path"] for entry in tree.get("tree", []) if entry.get("type") != "tree"]
        sha = tree.get("sha")

        splits: List[str] = []
        for path in files:
            if "/" in path:
                split = path.split("/", 1)[0]
                if split not in (".git", "lfs"):
                    splits.append(split)

        dataset_info_content = await self.client.get_file_content(
            owner, dataset, "dataset_info.json", revision, token
        )

        record = self.cache.upsert_dataset(dataset_id, sha, splits, files, dataset_info_content)
        return {
            "id": dataset_id,
            "sha": record.sha,
            "splits": json.loads(record.splits or "[]"),
            "files": json.loads(record.files or "[]"),
            "dataset_info": dataset_info_content,
        }

    def get_cached_dataset(self, owner: str, dataset: str) -> Optional[Dict[str, Optional[str]]]:
        dataset_id = f"{owner}/{dataset}"
        record = self.cache.get_dataset(dataset_id)
        if not record:
            return None
        return {
            "id": dataset_id,
            "sha": record.sha,
            "splits": json.loads(record.splits or "[]"),
            "files": json.loads(record.files or "[]"),
            "dataset_info": record.dataset_info,
            "updated_at": record.updated_at.isoformat(),
        }
