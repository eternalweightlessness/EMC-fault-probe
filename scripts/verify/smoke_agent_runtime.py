from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from emc_core.application.chat_service import ChatService
from emc_core.domain.events import AgentEventType
from emc_core.persistence.jsonl_store import JsonlSessionStore
from emc_core.tools.registry import ToolRegistry
from emc_core.tools.search_cases import SEARCH_CASES_SPEC, SearchCasesTool
from emc_runtime_local import LocalRuntime
from ollama import AsyncClient

from integrations.models.ollama.client import OllamaLLM
from integrations.models.ollama.embeddings import OllamaEmbedder
from integrations.models.ollama.health import is_ollama_serving
from integrations.vector_stores.chroma.store import ChromaCaseStore, ChromaRetriever


async def run_smoke(
    *,
    project_root: Path,
    query: str,
    model: str,
    embedding_model: str,
) -> None:
    """执行一轮真实本地 Agent，并把全过程写入正式 JSONL store。"""

    if not is_ollama_serving():
        raise RuntimeError("Ollama 未运行，请先启动 ollama serve")

    formal_database = project_root / "data" / "runtime" / "vector_store"
    experiment_database = project_root / "experiments" / "rag" / "emc_vector_db"
    database_path = (
        formal_database if formal_database.exists() else experiment_database
    )

    client = AsyncClient()
    llm = OllamaLLM(model=model, client=client)
    embedder = OllamaEmbedder(model=embedding_model, client=client)
    retriever = ChromaRetriever(
        embedder=embedder,
        store=ChromaCaseStore(
            database_path=database_path,
            collection_name="emc_faults",
        ),
    )
    registry = ToolRegistry()
    registry.register(
        spec=SEARCH_CASES_SPEC,
        handler=SearchCasesTool(retriever),
    )
    runtime = LocalRuntime(llm=llm, registry=registry)
    store = JsonlSessionStore(project_root / "data" / "runtime" / "sessions")
    session = store.create()
    system_prompt = (
        project_root / "packages" / "emc-runtime-local-py" / "prompts" / "system.md"
    ).read_text(encoding="utf-8")
    service = ChatService(
        store=store,
        runtime=runtime,
        system_prompt=system_prompt,
    )

    print(f"session: {session.session_id}")
    thinking_started = False
    try:
        async for event in service.send_message(
            session_id=session.session_id,
            content=query,
        ):
            if event.type is AgentEventType.ASSISTANT_THINKING_DELTA:
                if not thinking_started:
                    print("[thinking]")
                    thinking_started = True
                print(event.data.get("delta", ""), end="", flush=True)
            elif event.type is AgentEventType.TOOL_REQUESTED:
                print(f"\n[tool] {event.data.get('tool_name')} {event.data.get('arguments')}")
            elif event.type is AgentEventType.TOOL_COMPLETED:
                print(f"[tool completed] error={event.data.get('error')}")
            elif event.type is AgentEventType.ASSISTANT_CONTENT_DELTA:
                if thinking_started:
                    print("\n[answer]")
                    thinking_started = False
                print(event.data.get("delta", ""), end="", flush=True)
        print()
    finally:
        # client 由本函数创建，因此必须在退出时关闭。LLM 和 Embedder 共享它，
        # 两个 adapter 都不会擅自关闭外部注入的 client。
        await client.close()


def main() -> None:
    # Windows 终端有时仍使用 GBK，而 Agent 的问题和回答主要是中文。
    # reconfigure() 只调整当前进程的标准输出，不会改变用户的系统设置。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Smoke-test the local EMC Agent runtime")
    parser.add_argument(
        "query",
        nargs="?",
        default="请查询辐射发射超标案例，并给出整改建议。",
    )
    parser.add_argument("--model", default="qwen3.5:9b-q4_K_M")
    parser.add_argument("--embedding-model", default="nomic-embed-text")
    args = parser.parse_args()
    asyncio.run(
        run_smoke(
            project_root=Path(__file__).resolve().parents[2],
            query=args.query,
            model=args.model,
            embedding_model=args.embedding_model,
        )
    )


if __name__ == "__main__":
    main()
