from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from emc_core.domain.events import AgentEvent
from emc_core.domain.session import MessageRole, Session, SessionMessage, SessionSummary


class SessionStore(Protocol):
    """会话持久化端口。当前 JSONL 和未来数据库实现共享此接口。"""

    def create(self) -> Session:
        ...

    def load(self, session_id: str) -> Session:
        ...

    def list_summaries(self) -> Sequence[SessionSummary]:
        ...

    def append_message(
        self,
        session_id: str,
        *,
        role: MessageRole,
        content: str,
        thinking: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessage:
        ...

    def append_event(self, session_id: str, event: AgentEvent) -> None:
        ...
