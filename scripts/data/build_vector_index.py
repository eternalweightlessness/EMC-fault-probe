from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from emc_core.persistence.json_case_repository import JsonCaseRepository

from integrations.models.ollama.embeddings import OllamaEmbedder
from integrations.vector_stores.chroma.indexer import ChromaCaseIndexer


async def build_index(
    *,
    data_directory: Path,
    database_path: Path,
    collection_name: str,
    embedding_model: str,
) -> int:
    paths = sorted(data_directory.glob("data_*.json"))
    cases = JsonCaseRepository(paths).list_cases()
    embedder = OllamaEmbedder(model=embedding_model)
    try:
        indexer = ChromaCaseIndexer(
            database_path=database_path,
            collection_name=collection_name,
            embedder=embedder,
        )
        return await indexer.synchronize(cases)
    finally:
        await embedder.close()


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build the formal EMC vector index")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=project_root / "data" / "published" / "v1",
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=project_root / "data" / "runtime" / "vector_store",
    )
    parser.add_argument("--collection", default="emc_faults")
    parser.add_argument("--embedding-model", default="nomic-embed-text")
    args = parser.parse_args()

    count = asyncio.run(
        build_index(
            data_directory=args.data_dir.resolve(),
            database_path=args.database_path.resolve(),
            collection_name=args.collection,
            embedding_model=args.embedding_model,
        )
    )
    print(f"indexed {count} EMC cases into {args.database_path.resolve()}")


if __name__ == "__main__":
    main()
