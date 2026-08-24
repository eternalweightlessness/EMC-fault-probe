from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from emc_core.domain.fault_case import FaultCase
from emc_core.ports.retriever import TextEmbedder


class ChromaCaseIndexer:
    """将发布案例可重复地同步到 cosine Chroma collection。"""

    def __init__(
        self,
        *,
        database_path: Path,
        collection_name: str,
        embedder: TextEmbedder,
    ) -> None:
        self._database_path = database_path.resolve()
        self._collection_name = collection_name
        self._embedder = embedder

    def _collection(self) -> Collection:
        self._database_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self._database_path))
        return client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def synchronize(self, cases: Sequence[FaultCase]) -> int:
        """upsert 当前案例并删除已不在发布数据中的旧 ID。"""

        collection = self._collection()
        current_ids: list[str] = []
        for case in cases:
            case_id = case.case_id
            embedding = await self._embedder.embed(case.searchable_text())
            collection.upsert(
                ids=[case_id],
                embeddings=[list(embedding)],
                documents=[case.searchable_text()],
                metadatas=[case.to_mapping()],
            )
            current_ids.append(case_id)

        existing_ids = set(collection.get(include=[])["ids"])
        stale_ids = sorted(existing_ids - set(current_ids))
        if stale_ids:
            collection.delete(ids=stale_ids)
        return len(current_ids)
