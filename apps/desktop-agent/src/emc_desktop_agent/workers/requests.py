from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from emc_desktop_agent.api_client import AgentApi, AgentEventDto


class RequestWorker(QThread):
    """在线程中执行一次短 HTTP 请求，避免阻塞 Qt 主线程。"""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, operation: Callable[[], Any]) -> None:
        super().__init__()
        self._operation = operation

    def run(self) -> None:
        try:
            self.succeeded.emit(self._operation())
        except Exception as exc:  # noqa: BLE001 - UI 边界统一显示 adapter 错误
            self.failed.emit(str(exc))


class StreamWorker(QThread):
    """消费阻塞式 SSE 流，并通过 Qt signal 把事件安全送回主线程。"""

    session_created = pyqtSignal(str)
    event_received = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        *,
        client: AgentApi,
        session_id: str | None,
        content: str,
    ) -> None:
        super().__init__()
        self._client = client
        self._session_id = session_id
        self._content = content

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def run(self) -> None:
        try:
            if self._session_id is None:
                self._session_id = self._client.create_session().session_id
                self.session_created.emit(self._session_id)
            for event in self._client.stream_chat(self._session_id, self._content):
                if self.isInterruptionRequested():
                    break
                if isinstance(event, AgentEventDto):
                    self.event_received.emit(event)
        except Exception as exc:  # noqa: BLE001 - worker 不能把异常抛进 Qt event loop
            self.failed.emit(str(exc))
