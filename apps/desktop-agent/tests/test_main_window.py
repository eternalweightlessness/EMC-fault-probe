from __future__ import annotations

import time
from collections.abc import Iterator

from emc_desktop_agent.api_client import (
    AgentEventDto,
    SessionDto,
    SessionSummaryDto,
)
from emc_desktop_agent.ui.main_window import MainWindow
from emc_desktop_agent.ui.widgets import ToolCallCard
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QTableView, QTextBrowser


class FakeAgentApi:
    def health(self) -> dict[str, object]:
        return {"ollama": {"available": True}}

    def list_sessions(self) -> list[SessionSummaryDto]:
        return []

    def create_session(self) -> SessionDto:
        return SessionDto("test-session")

    def get_session(self, session_id: str) -> SessionDto:
        return SessionDto(session_id)

    def stream_chat(self, session_id: str, content: str) -> Iterator[AgentEventDto]:
        yield AgentEventDto("turn.started", session_id)
        yield AgentEventDto(
            "assistant.thinking.delta",
            session_id,
            1,
            {"delta": "先查询案例。"},
        )
        yield AgentEventDto(
            "tool.requested",
            session_id,
            1,
            {
                "call_id": "call-1",
                "tool_name": "search_cases",
                "arguments": {"query": content},
            },
        )
        yield AgentEventDto(
            "tool.completed",
            session_id,
            1,
            {"call_id": "call-1", "output": [{"case": 1}], "error": None},
        )
        yield AgentEventDto(
            "assistant.content.delta",
            session_id,
            2,
            {"delta": "建议检查屏蔽搭接。"},
        )
        yield AgentEventDto(
            "assistant.completed",
            session_id,
            2,
            {"content": "建议检查屏蔽搭接。"},
        )

    def cancel(self, session_id: str) -> bool:
        return True


def test_preview_renders_conversational_agent_without_legacy_table() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(client=FakeAgentApi(), auto_connect=False)

    window.seed_preview()
    window.show()
    app.processEvents()

    visible_text = " ".join(
        widget.text()
        for widget in [
            *window.findChildren(QLabel),
            *window.findChildren(QPushButton),
        ]
    ) + " ".join(browser.toPlainText() for browser in window.findChildren(QTextBrowser))
    assert "辐射发射超标排查" in visible_text
    assert "已检索 EMC 案例" in visible_text
    assert window.findChildren(ToolCallCard)
    assert not window.findChildren(QTableView)
    assert "Excel" not in visible_text

    window.close()


def test_window_consumes_stream_in_worker_and_renders_tool_trace() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(client=FakeAgentApi(), auto_connect=False)
    window.show()

    window.composer.send_requested.emit("辐射发射怎么整改？")
    deadline = time.monotonic() + 2
    while window._stream_worker is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()

    answer_text = " ".join(
        browser.toPlainText() for browser in window.findChildren(QTextBrowser)
    )
    card_text = " ".join(label.text() for label in window.findChildren(QLabel))
    assert "建议检查屏蔽搭接" in answer_text
    assert "已检索 EMC 案例" in card_text
    assert window._current_session_id == "test-session"
    assert window.composer.send_button.isVisible()

    window.close()
