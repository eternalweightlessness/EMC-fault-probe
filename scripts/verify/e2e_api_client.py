from __future__ import annotations

import argparse
import sys

from emc_desktop_agent.api_client import BackendApiClient
from emc_desktop_agent.settings import DesktopSettings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify desktop → API → Agent → RAG")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument(
        "query",
        nargs="?",
        default="请检索静电放电导致设备复位的案例，并给出三点整改建议。",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    client = BackendApiClient(DesktopSettings(api_base_url=args.base_url))
    health = client.health()
    print(f"health: {health.get('status')}, ollama={health.get('ollama')}")
    session = client.create_session()
    print(f"session: {session.session_id}")

    event_types: list[str] = []
    answer_parts: list[str] = []
    failure_reason: str | None = None
    for event in client.stream_chat(session.session_id, args.query):
        event_types.append(event.type)
        if event.type == "tool.requested":
            print(
                "tool:",
                event.data.get("tool_name"),
                event.data.get("arguments"),
            )
        elif event.type == "assistant.content.delta":
            delta = str(event.data.get("delta", ""))
            answer_parts.append(delta)
            print(delta, end="", flush=True)
        elif event.type == "turn.failed":
            failure_reason = str(event.data.get("reason", "unknown error"))
    print()

    if failure_reason is not None:
        raise RuntimeError(f"Agent 回合失败：{failure_reason}")
    if "tool.requested" not in event_types:
        raise RuntimeError("模型没有通过 API 触发 RAG 工具")
    if not answer_parts:
        raise RuntimeError("API 没有返回流式回答")
    restored = client.get_session(session.session_id)
    if len(restored.messages) != 2:
        raise RuntimeError("会话没有持久化一问一答")
    print(f"verified events={len(event_types)}, messages={len(restored.messages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
