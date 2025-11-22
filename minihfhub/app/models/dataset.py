from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DatasetMetadata(SQLModel, table=True):
    id: str = Field(primary_key=True, description="owner/name identifier")
    sha: Optional[str] = Field(default=None, description="Latest known commit hash")
    splits: Optional[str] = Field(default=None, description="JSON array of splits")
    files: Optional[str] = Field(default=None, description="JSON array of files")
    dataset_info: Optional[str] = Field(default=None, description="Cached dataset_info.json content")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
