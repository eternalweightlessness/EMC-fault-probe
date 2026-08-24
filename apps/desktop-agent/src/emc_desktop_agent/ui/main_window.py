from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from emc_desktop_agent.api_client import (
    AgentApi,
    AgentEventDto,
    SessionDto,
    SessionSummaryDto,
    format_session_time,
)
from emc_desktop_agent.ui.widgets import (
    AssistantTurnWidget,
    Composer,
    UserMessageWidget,
    WelcomeWidget,
)
from emc_desktop_agent.workers.requests import RequestWorker, StreamWorker


class MainWindow(QMainWindow):
    """EMC Agent 桌面壳；只处理视图状态，业务能力全部来自 AgentApi。"""

    def __init__(
        self,
        *,
        client: AgentApi,
        icon_path: Path | None = None,
        auto_connect: bool = True,
    ) -> None:
        super().__init__()
        self._client = client
        self._current_session_id: str | None = None
        self._active_turn: AssistantTurnWidget | None = None
        self._stream_worker: StreamWorker | None = None
        self._request_workers: list[RequestWorker] = []
        self._session_buttons: dict[str, QPushButton] = {}

        self.setWindowTitle("EMC Fault Probe Agent")
        self.resize(1360, 860)
        self.setMinimumSize(1040, 680)
        if icon_path is not None and icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build_ui()
        self._show_welcome()
        if auto_connect:
            QTimer.singleShot(0, self._load_backend_state)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_chat_area(), 1)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(264)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(10)

        brand_row = QHBoxLayout()
        mark = QLabel("E")
        mark.setObjectName("agentAvatar")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(27, 27)
        brand_row.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("EMC Fault Probe")
        title.setObjectName("brandTitle")
        brand_text.addWidget(title)
        subtitle = QLabel("Local Agent")
        subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(subtitle)
        brand_row.addLayout(brand_text, 1)
        layout.addLayout(brand_row)
        layout.addSpacing(5)

        new_chat = QPushButton("＋  新建对话")
        new_chat.setObjectName("newChatButton")
        new_chat.clicked.connect(self.start_new_session)
        layout.addWidget(new_chat)
        layout.addSpacing(9)
        section = QLabel("最近对话")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)

        session_scroll = QScrollArea()
        session_scroll.setWidgetResizable(True)
        session_scroll.setFrameShape(QFrame.Shape.NoFrame)
        session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        session_scroll.setStyleSheet("background: transparent;")
        session_host = QWidget()
        session_host.setStyleSheet("background: transparent;")
        self.session_layout = QVBoxLayout(session_host)
        self.session_layout.setContentsMargins(0, 0, 0, 0)
        self.session_layout.setSpacing(3)
        self.session_layout.addStretch(1)
        session_scroll.setWidget(session_host)
        layout.addWidget(session_scroll, 1)

        local_row = QHBoxLayout()
        local_dot = QLabel("●")
        local_dot.setStyleSheet("color: #72c69e; font-size: 10px;")
        local_row.addWidget(local_dot)
        local_text = QLabel("本地工作区")
        local_text.setObjectName("muted")
        local_row.addWidget(local_text)
        local_row.addStretch(1)
        layout.addLayout(local_row)
        return sidebar

    def _build_chat_area(self) -> QWidget:
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        self.chat_title = QLabel("新对话")
        self.chat_title.setObjectName("chatTitle")
        header_layout.addWidget(self.chat_title)
        header_layout.addStretch(1)
        self.status_pill = QFrame()
        self.status_pill.setObjectName("statusPill")
        status_layout = QHBoxLayout(self.status_pill)
        status_layout.setContentsMargins(9, 3, 9, 3)
        self.status_text = QLabel("正在连接后端…")
        self.status_text.setObjectName("statusText")
        status_layout.addWidget(self.status_text)
        header_layout.addWidget(self.status_pill)
        model = QLabel("Ollama")
        model.setObjectName("muted")
        header_layout.addWidget(model)
        layout.addWidget(header)

        self.conversation_scroll = QScrollArea()
        self.conversation_scroll.setObjectName("conversationScroll")
        self.conversation_scroll.setWidgetResizable(True)
        self.conversation_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.conversation_host = QWidget()
        self.conversation_host.setObjectName("conversationViewport")
        self.conversation_layout = QVBoxLayout(self.conversation_host)
        self.conversation_layout.setContentsMargins(66, 22, 66, 22)
        self.conversation_layout.setSpacing(2)
        self.conversation_layout.addStretch(1)
        self.conversation_scroll.setWidget(self.conversation_host)
        layout.addWidget(self.conversation_scroll, 1)

        composer_shell = QWidget()
        composer_layout = QVBoxLayout(composer_shell)
        composer_layout.setContentsMargins(66, 8, 66, 14)
        composer_layout.setSpacing(6)
        self.composer = Composer()
        self.composer.send_requested.connect(self._send_message)
        self.composer.stop_requested.connect(self._stop_generation)
        composer_layout.addWidget(self.composer)
        hint = QLabel("回答由本地模型生成，请结合实际测试和适用标准验证。")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        composer_layout.addWidget(hint)
        layout.addWidget(composer_shell)
        return area

    def _load_backend_state(self) -> None:
        self._run_request(self._client.health, self._apply_health, self._show_offline)
        self._run_request(self._client.list_sessions, self.set_sessions, lambda _error: None)

    def _run_request(
        self,
        operation: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_failure: Callable[[str], None],
    ) -> RequestWorker:
        worker = RequestWorker(operation)
        self._request_workers.append(worker)
        worker.succeeded.connect(on_success)
        worker.failed.connect(on_failure)
        worker.finished.connect(lambda: self._forget_request_worker(worker))
        worker.start()
        return worker

    def _forget_request_worker(self, worker: RequestWorker) -> None:
        if worker in self._request_workers:
            self._request_workers.remove(worker)
        worker.deleteLater()

    def _apply_health(self, health: object) -> None:
        payload = health if isinstance(health, dict) else {}
        ollama = payload.get("ollama")
        available = bool(ollama.get("available")) if isinstance(ollama, dict) else bool(ollama)
        self.status_text.setText("本地模型就绪" if available else "后端已连接")

    def _show_offline(self, _error: str) -> None:
        self.status_text.setText("后端离线")
        self.status_pill.setStyleSheet("border-color: #65403d; background: #2c201f;")

    def set_sessions(self, value: object) -> None:
        sessions = value if isinstance(value, list) else []
        while self.session_layout.count() > 1:
            item = self.session_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._session_buttons.clear()
        for summary in sessions:
            if not isinstance(summary, SessionSummaryDto):
                continue
            label = summary.title or "新会话"
            time_text = format_session_time(summary.updated_at)
            button = QPushButton(f"{label}\n{time_text}")
            button.setObjectName("sessionButton")
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, session_id=summary.session_id: self.open_session(
                    session_id
                )
            )
            self.session_layout.insertWidget(self.session_layout.count() - 1, button)
            self._session_buttons[summary.session_id] = button

    def start_new_session(self) -> None:
        if self._stream_worker is not None:
            return
        self._current_session_id = None
        self.chat_title.setText("新对话")
        for button in self._session_buttons.values():
            button.setChecked(False)
        self._show_welcome()
        self.composer.input.setFocus()

    def open_session(self, session_id: str) -> None:
        if self._stream_worker is not None:
            return
        self._current_session_id = session_id
        for current_id, button in self._session_buttons.items():
            button.setChecked(current_id == session_id)
        self._run_request(
            lambda: self._client.get_session(session_id),
            self._render_session,
            self._show_offline,
        )

    def _render_session(self, value: object) -> None:
        if not isinstance(value, SessionDto):
            return
        self._clear_conversation()
        first_user = next((m.content for m in value.messages if m.role == "user"), "会话")
        self.chat_title.setText(self._short_title(first_user))
        for message in value.messages:
            if message.role == "user":
                self._add_conversation_widget(UserMessageWidget(message.content))
            elif message.role == "assistant":
                turn = AssistantTurnWidget()
                if message.thinking:
                    turn.set_thinking(message.thinking)
                turn.set_answer(message.content)
                self._add_conversation_widget(turn)
        self._scroll_to_bottom()

    def _show_welcome(self) -> None:
        self._clear_conversation()
        welcome = WelcomeWidget()
        welcome.prompt_selected.connect(self._use_prompt)
        self._add_conversation_widget(welcome, stretch=1)

    def _use_prompt(self, prompt: str) -> None:
        self.composer.input.setPlainText(prompt)
        self.composer.input.setFocus()

    def _send_message(self, content: str) -> None:
        if self._stream_worker is not None:
            return
        self._clear_welcome_if_present()
        self.chat_title.setText(self._short_title(content))
        self._add_conversation_widget(UserMessageWidget(content))
        self._active_turn = AssistantTurnWidget()
        self._add_conversation_widget(self._active_turn)
        self.composer.set_running(True)

        worker = StreamWorker(
            client=self._client,
            session_id=self._current_session_id,
            content=content,
        )
        self._stream_worker = worker
        worker.session_created.connect(self._set_current_session)
        worker.event_received.connect(self._handle_agent_event)
        worker.failed.connect(self._handle_stream_error)
        # 使用 QThread 自带的 finished 信号。它在线程真正退出后发出，避免窗口
        # 提前 deleteLater() 一个仍在运行的线程对象。
        worker.finished.connect(self._finish_stream)
        worker.start()
        self._scroll_to_bottom()

    def _set_current_session(self, session_id: str) -> None:
        self._current_session_id = session_id

    def _handle_agent_event(self, event: object) -> None:
        if not isinstance(event, AgentEventDto) or self._active_turn is None:
            return
        data = event.data
        if event.type == "assistant.thinking.delta":
            self._active_turn.append_thinking(str(data.get("delta", "")))
        elif event.type == "assistant.content.delta":
            self._active_turn.append_answer(str(data.get("delta", "")))
        elif event.type == "tool.requested":
            arguments = data.get("arguments")
            self._active_turn.add_tool(
                str(data.get("call_id", "")),
                str(data.get("tool_name", "tool")),
                dict(arguments) if isinstance(arguments, dict) else {},
            )
        elif event.type == "tool.completed":
            self._active_turn.complete_tool(
                str(data.get("call_id", "")),
                output=data.get("output"),
                error=data.get("error"),
            )
        elif event.type == "assistant.completed" and not self._active_turn.response.isVisible():
            self._active_turn.set_answer(str(data.get("content", "")))
        elif event.type == "turn.failed" and not self._active_turn.response.isVisible():
            reason = str(data.get("reason", "unknown"))
            message = "*已停止生成。*" if reason == "cancelled" else f"**运行失败**\n\n{reason}"
            self._active_turn.set_answer(message)
        self._scroll_to_bottom()

    def _handle_stream_error(self, error: str) -> None:
        if self._active_turn is not None:
            self._active_turn.set_answer(f"**连接失败**\n\n{error}")
        self._show_offline(error)

    def _finish_stream(self) -> None:
        worker = self._stream_worker
        self._stream_worker = None
        self._active_turn = None
        self.composer.set_running(False)
        if worker is not None:
            worker.deleteLater()
        self._run_request(self._client.list_sessions, self.set_sessions, lambda _error: None)

    def _stop_generation(self) -> None:
        worker = self._stream_worker
        if worker is None:
            return
        worker.requestInterruption()
        session_id = worker.session_id or self._current_session_id
        if session_id:
            self._run_request(lambda: self._client.cancel(session_id), lambda _value: None, lambda _error: None)

    def _clear_welcome_if_present(self) -> None:
        if self.conversation_layout.count() == 2:
            first = self.conversation_layout.itemAt(0).widget()
            if isinstance(first, WelcomeWidget):
                self._clear_conversation()

    def _clear_conversation(self) -> None:
        while self.conversation_layout.count() > 1:
            item = self.conversation_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_conversation_widget(self, widget: QWidget, *, stretch: int = 0) -> None:
        self.conversation_layout.insertWidget(
            self.conversation_layout.count() - 1,
            widget,
            stretch,
        )

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(
            0,
            lambda: self.conversation_scroll.verticalScrollBar().setValue(
                self.conversation_scroll.verticalScrollBar().maximum()
            ),
        )

    @staticmethod
    def _short_title(content: str) -> str:
        normalized = " ".join(content.split())
        return normalized[:34] + ("…" if len(normalized) > 34 else "")

    def seed_preview(self) -> None:
        """填充视觉回归场景；仅由 ``--preview`` 和截图测试调用。"""

        self.status_text.setText("本地模型就绪")
        self.set_sessions(
            [
                SessionSummaryDto("preview-1", "辐射发射超标排查", "2026-08-24T19:30:00+08:00", 2),
                SessionSummaryDto("preview-2", "静电放电导致复位", "2026-08-23T15:10:00+08:00", 3),
                SessionSummaryDto("preview-3", "电源端传导骚扰", "2026-08-21T09:00:00+08:00", 1),
            ]
        )
        self._current_session_id = "preview-1"
        self._session_buttons["preview-1"].setChecked(True)
        self.chat_title.setText("辐射发射超标排查")
        self._clear_conversation()
        self._add_conversation_widget(
            UserMessageWidget("设备在 200 MHz 附近辐射发射超标，请结合案例给出排查方案。")
        )
        turn = AssistantTurnWidget()
        turn.set_thinking(
            "需要先查询与 200 MHz、辐射发射和线缆共模电流相关的案例，再归纳可执行的排查顺序。"
        )
        turn.add_tool("preview-call", "search_cases", {"query": "200MHz 辐射发射超标"})
        turn.complete_tool("preview-call", output=[{}] * 8, error=None)
        turn.set_answer(
            "根据检索到的案例，**200 MHz 附近的窄带超标**通常优先检查时钟谐波与线缆共模辐射。\n\n"
            "### 建议的排查顺序\n\n"
            "1. 用近场探头定位主板上的高频源，核对 25 MHz、50 MHz 等时钟倍频。\n"
            "2. 夹上共模电流探头比较电源线、I/O 线在 200 MHz 的电流峰值。\n"
            "3. 临时加磁环或缩短线缆；若峰值明显下降，优先整改接口滤波与屏蔽搭接。\n\n"
            "建议补充设备类型、测试距离和超标幅度，我可以继续缩小故障路径。"
        )
        self._add_conversation_widget(turn)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if self._stream_worker is not None:
            self._stream_worker.requestInterruption()
            self._stream_worker.wait(2000)
        for worker in self._request_workers:
            worker.requestInterruption()
            worker.wait(2000)
        if event is not None:
            event.accept()
