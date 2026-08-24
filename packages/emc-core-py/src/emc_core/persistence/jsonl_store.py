from __future__ import annotations

import json
import re
import secrets
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from emc_core.domain.events import AgentEvent, AgentEventType
from emc_core.domain.session import MessageRole, Session, SessionMessage, SessionSummary

SESSION_ID_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$")


class SessionNotFoundError(FileNotFoundError):
    """请求的会话不存在。"""


class JsonlSessionStore:
    """追加写 JSONL 会话存储，迁移 persistent_session.py 的可靠性行为。"""

    def __init__(self, directory: Path) -> None:
        self._directory = directory.resolve()

    def create(self) -> Session:
        self._directory.mkdir(parents=True, exist_ok=True)
        for _ in range(10):
            created_at = datetime.now(UTC)
            session_id = created_at.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
            path = self._path(session_id)
            try:
                # mode="x" 是原子式新建：文件已存在会失败，而不是覆盖历史会话。
                with path.open("x", encoding="utf-8") as stream:
                    self._write_line(
                        stream,
                        {
                            "type": "session",
                            "session_id": session_id,
                            "created_at": created_at.isoformat(),
                        },
                    )
                return Session(session_id=session_id, created_at=created_at)
            except FileExistsError:
                continue
        raise RuntimeError("连续生成会话 ID 冲突，请重试")

    def load(self, session_id: str) -> Session:
        path = self._path(session_id)
        if not path.is_file():
            raise SessionNotFoundError(f"找不到会话：{session_id}")

        session: Session | None = None
        for record in self._records(path):
            record_type = record.get("type")
            try:
                if record_type == "session" and session is None:
                    session = Session(
                        session_id=str(record["session_id"]),
                        created_at=datetime.fromisoformat(str(record["created_at"])),
                    )
                elif record_type == "message" and session is not None:
                    session.messages.append(self._message_from_record(record))
                elif record_type == "agent_event" and session is not None:
                    session.events.append(self._event_from_record(record, session.session_id))
            except (KeyError, TypeError, ValueError):
                # 与实验保持一致：崩溃残留或旧版本坏行被跳过，其余历史仍可恢复。
                continue

        if session is None:
            raise SessionNotFoundError(f"会话文件缺少有效 header：{session_id}")
        return session

    def list_summaries(self) -> list[SessionSummary]:
        if not self._directory.exists():
            return []
        summaries: list[SessionSummary] = []
        for path in self._directory.glob("*.jsonl"):
            try:
                summaries.append(self.load(path.stem).summary)
            except SessionNotFoundError:
                continue
        return sorted(summaries, key=lambda item: item.updated_at, reverse=True)

    def append_message(
        self,
        session_id: str,
        *,
        role: MessageRole,
        content: str,
        thinking: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessage:
        normalized = content.strip()
        if not normalized:
            raise ValueError("消息内容不能为空")
        message = SessionMessage(
            role=role,
            content=normalized,
            thinking=thinking or None,
            metadata=dict(metadata or {}),
        )
        self._append(
            session_id,
            {
                "type": "message",
                "message_id": message.message_id,
                "role": message.role.value,
                "content": message.content,
                "thinking": message.thinking,
                "metadata": message.metadata,
                "created_at": message.created_at.isoformat(),
            },
        )
        return message

    def append_event(self, session_id: str, event: AgentEvent) -> None:
        self._append(
            session_id,
            {
                "type": "agent_event",
                "event_type": event.type.value,
                "step": event.step,
                "data": event.data,
                "recorded_at": datetime.now(UTC).isoformat(),
            },
        )

    def _append(self, session_id: str, record: dict[str, Any]) -> None:
        path = self._path(session_id)
        if not path.is_file():
            raise SessionNotFoundError(f"找不到会话：{session_id}")
        with path.open("a", encoding="utf-8") as stream:
            self._write_line(stream, record)
            stream.flush()

    def _path(self, session_id: str) -> Path:
        if not SESSION_ID_PATTERN.fullmatch(session_id):
            raise ValueError("session_id 格式无效")
        return self._directory / f"{session_id}.jsonl"

    @staticmethod
    def _write_line(stream: TextIO, record: dict[str, Any]) -> None:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _records(path: Path) -> Iterator[dict[str, Any]]:
        with path.open(encoding="utf-8") as stream:
            for raw_line in stream:
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    yield record

    @staticmethod
    def _message_from_record(record: dict[str, Any]) -> SessionMessage:
        metadata = record.get("metadata")
        return SessionMessage(
            message_id=str(record["message_id"]),
            role=MessageRole(str(record["role"])),
            content=str(record["content"]),
            thinking=(str(record["thinking"]) if record.get("thinking") else None),
            metadata=dict(metadata) if isinstance(metadata, dict) else {},
            created_at=datetime.fromisoformat(str(record["created_at"])),
        )

    @staticmethod
    def _event_from_record(record: dict[str, Any], session_id: str) -> AgentEvent:
        data = record.get("data")
        return AgentEvent(
            type=AgentEventType(str(record["event_type"])),
            session_id=session_id,
            step=int(record["step"]),
            data=dict(data) if isinstance(data, dict) else {},
        )
