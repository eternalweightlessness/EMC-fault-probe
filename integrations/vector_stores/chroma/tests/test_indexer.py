from __future__ import annotations

import asyncio
from pathlib import Path

import chromadb
from emc_core.domain.fault_case import FaultCase

from integrations.vector_stores.chroma.indexer import ChromaCaseIndexer


class FakeEmbedder:
    async def embed(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]


def _case(name: str) -> FaultCase:
    return FaultCase(
        object_name=name,
        phenomenon="发射超标",
        cause="原因",
        solution="方案",
        severity="一般",
        frequency="偶发",
    )


def test_indexer_upserts_current_cases_and_removes_stale_ids(tmp_path: Path) -> None:
    indexer = ChromaCaseIndexer(
        database_path=tmp_path / "chroma",
        collection_name="test_cases",
        embedder=FakeEmbedder(),
    )
    first = _case("设备一")
    second = _case("设备二")

    assert asyncio.run(indexer.synchronize([first, second])) == 2
    assert asyncio.run(indexer.synchronize([second])) == 1

    collection = chromadb.PersistentClient(path=str(tmp_path / "chroma")).get_collection(
        "test_cases"
    )
    assert collection.get(include=[])["ids"] == [second.case_id]
