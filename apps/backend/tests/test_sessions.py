from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from emc_backend.composition import AppContainer
from emc_backend.config import Settings
from emc_backend.main import create_app
from emc_core.agent.state import AgentState
from emc_core.application.chat_service import ChatService
from emc_core.application.session_service import SessionService
from emc_core.domain.events import AgentEvent, AgentEventType
from emc_core.persistence.jsonl_store import JsonlSessionStore
from emc_core.ports.agent_runtime import AgentRuntime
from fastapi.testclient import TestClient


class FakeRuntime:
    async def run(self, *, state: AgentState) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(AgentEventType.TURN_STARTED, state.session_id, 0)
        yield AgentEvent(
            AgentEventType.ASSISTANT_THINKING_DELTA,
            state.session_id,
            1,
            {"delta": "先检索本地案例。"},
        )
        yield AgentEvent(
            AgentEventType.TOOL_REQUESTED,
            state.session_id,
            1,
            {
                "tool_name": "search_cases",
                "call_id": "call-test",
                "arguments": {"query": "辐射发射"},
            },
        )
        yield AgentEvent(
            AgentEventType.TOOL_COMPLETED,
            state.session_id,
            1,
            {
                "tool_name": "search_cases",
                "call_id": "call-test",
                "output": "找到 3 条案例",
                "error": None,
            },
        )
        answer = "建议依次检查时钟谐波、线缆共模电流和屏蔽搭接。"
        yield AgentEvent(
            AgentEventType.ASSISTANT_CONTENT_DELTA,
            state.session_id,
            2,
            {"delta": answer},
        )
        yield AgentEvent(
            AgentEventType.ASSISTANT_COMPLETED,
            state.session_id,
            2,
            {"content": answer},
        )
        yield AgentEvent(
            AgentEventType.TURN_COMPLETED,
            state.session_id,
            2,
            {"content": answer},
        )


class FailingRuntime:
    async def run(self, *, state: AgentState) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(AgentEventType.TURN_STARTED, state.session_id, 0)
        raise ConnectionError("Ollama stream closed")


class SessionApiContainer(AppContainer):
    def __init__(
        self,
        settings: Settings,
        session_directory: Path,
        runtime: AgentRuntime | None = None,
    ) -> None:
        self.settings = settings
        self.runtime = runtime or FakeRuntime()
        store = JsonlSessionStore(session_directory)
        self.session_service = SessionService(store)
        self.chat_service = ChatService(
            store=store,
            runtime=self.runtime,
            system_prompt="你是 EMC Agent。",
        )

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None


def test_session_api_streams_agent_events_and_restores_messages(tmp_path: Path) -> None:
    settings = Settings(project_root=Path.cwd())
    container = SessionApiContainer(settings, tmp_path / "sessions")
    application = create_app(
        settings=settings,
        container_factory=lambda _settings: container,
    )

    with TestClient(application) as client:
        created = client.post("/api/v1/sessions")
        assert created.status_code == 201
        session_id = created.json()["session_id"]

        with client.stream(
            "POST",
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "辐射发射超标怎么整改？"},
        ) as response:
            stream_text = "".join(response.iter_text())

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '"type": "tool.requested"' in stream_text
        assert '"type": "assistant.content.delta"' in stream_text

        restored = client.get(f"/api/v1/sessions/{session_id}").json()
        summaries = client.get("/api/v1/sessions").json()

    assert [message["role"] for message in restored["messages"]] == [
        "user",
        "assistant",
    ]
    assert restored["messages"][1]["thinking"] == "先检索本地案例。"
    assert summaries[0]["turns"] == 1


def test_session_api_reports_missing_session_and_inactive_cancel(tmp_path: Path) -> None:
    settings = Settings(project_root=Path.cwd())
    container = SessionApiContainer(settings, tmp_path / "sessions")
    application = create_app(
        settings=settings,
        container_factory=lambda _settings: container,
    )

    with TestClient(application) as client:
        missing = client.get("/api/v1/sessions/20260824-000000-abcd")
        created = client.post("/api/v1/sessions").json()
        cancelled = client.post(
            f"/api/v1/sessions/{created['session_id']}/cancel"
        )

    assert missing.status_code == 404
    assert cancelled.json() == {"cancelled": False}


def test_session_api_converts_runtime_exception_to_failed_event(tmp_path: Path) -> None:
    settings = Settings(project_root=Path.cwd())
    container = SessionApiContainer(
        settings,
        tmp_path / "sessions",
        runtime=FailingRuntime(),
    )
    application = create_app(
        settings=settings,
        container_factory=lambda _settings: container,
    )

    with TestClient(application) as client:
        session_id = client.post("/api/v1/sessions").json()["session_id"]
        response = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"content": "触发模型异常"},
        )

    assert response.status_code == 200
    assert '"type": "turn.failed"' in response.text
    assert "ConnectionError: Ollama stream closed" in response.text
