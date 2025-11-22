from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, SQLModel, create_engine, select

from minihfhub.app.models.dataset import DatasetMetadata


def get_engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./data/minihfhub.db")
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def create_db_and_tables(engine=None) -> None:
    engine = engine or get_engine()
    SQLModel.metadata.create_all(engine)


class MetadataCache:
    def __init__(self, engine=None):
        self.engine = engine or get_engine()
        create_db_and_tables(self.engine)

    def get_dataset(self, dataset_id: str) -> Optional[DatasetMetadata]:
        with Session(self.engine) as session:
            statement = select(DatasetMetadata).where(DatasetMetadata.id == dataset_id)
            result = session.exec(statement).first()
            return result

    def list_datasets(self) -> List[DatasetMetadata]:
        with Session(self.engine) as session:
            statement = select(DatasetMetadata)
            return list(session.exec(statement).all())

    def upsert_dataset(
        self, dataset_id: str, sha: Optional[str], splits: List[str], files: List[str], dataset_info: Optional[str]
    ) -> DatasetMetadata:
        encoded_splits = json.dumps(sorted(set(splits))) if splits else None
        encoded_files = json.dumps(sorted(files)) if files else None
        with Session(self.engine) as session:
            dataset = session.get(DatasetMetadata, dataset_id)
            if dataset is None:
                dataset = DatasetMetadata(id=dataset_id)
            dataset.sha = sha
            dataset.splits = encoded_splits
            dataset.files = encoded_files
            dataset.dataset_info = dataset_info
            dataset.updated_at = datetime.utcnow()
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset
