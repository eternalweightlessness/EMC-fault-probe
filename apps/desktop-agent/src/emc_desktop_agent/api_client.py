from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from emc_desktop_agent.settings import DesktopSettings


class AgentApiError(RuntimeError):
    """后端不可用或返回了无法解析的响应。"""


@dataclass(frozen=True, slots=True)
class SessionSummaryDto:
    session_id: str
    title: str
    updated_at: str = ""
    turns: int = 0


@dataclass(frozen=True, slots=True)
class SessionMessageDto:
    role: str
    content: str
    thinking: str | None = None


@dataclass(frozen=True, slots=True)
class SessionDto:
    session_id: str
    messages: tuple[SessionMessageDto, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentEventDto:
    type: str
    session_id: str
    step: int = 0
    data: dict[str, Any] = field(default_factory=dict)


class AgentApi(Protocol):
    """主窗口所需的最小后端接口，测试可注入内存替身。"""

    def health(self) -> dict[str, Any]: ...

    def list_sessions(self) -> list[SessionSummaryDto]: ...

    def create_session(self) -> SessionDto: ...

    def get_session(self, session_id: str) -> SessionDto: ...

    def stream_chat(self, session_id: str, content: str) -> Iterator[AgentEventDto]: ...

    def cancel(self, session_id: str) -> bool: ...


def parse_sse_events(lines: Iterable[bytes | str]) -> Iterator[dict[str, Any]]:
    """把 SSE 字节行转换成 JSON。

    SSE 用空行分隔事件，一个事件可以包含多个 ``data:`` 行。这里不把 HTTP
    逻辑混入解析器，因此它可以用普通列表做离线单元测试。
    """

    data_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        line = line.rstrip("\r\n")
        if not line:
            if data_lines:
                payload = "\n".join(data_lines)
                decoded = json.loads(payload)
                if isinstance(decoded, dict):
                    yield decoded
                data_lines.clear()
            continue
        if line.startswith(":"):
            # 以冒号开头的是 SSE keep-alive 注释，不属于业务事件。
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())

    if data_lines:
        decoded = json.loads("\n".join(data_lines))
        if isinstance(decoded, dict):
            yield decoded


class BackendApiClient:
    """仅使用 Python 标准库的同步 HTTP/SSE client。

    方法是同步的，但主窗口始终在 ``QThread`` 中调用它们，所以网络等待不会
    卡住 Qt 事件循环。这样也避免桌面包额外引入另一套异步 HTTP 运行时。
    """

    def __init__(self, settings: DesktopSettings) -> None:
        self._base_url = settings.api_base_url
        self._request_timeout = settings.request_timeout_seconds
        self._stream_timeout = settings.stream_timeout_seconds

    def health(self) -> dict[str, Any]:
        value = self._request_json("GET", "/health")
        return value if isinstance(value, dict) else {}

    def list_sessions(self) -> list[SessionSummaryDto]:
        payload = self._request_json("GET", "/sessions")
        records = payload.get("items", []) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise AgentApiError("会话列表响应格式无效")
        return [self._summary_from_json(item) for item in records if isinstance(item, dict)]

    def create_session(self) -> SessionDto:
        payload = self._request_json("POST", "/sessions", {})
        if not isinstance(payload, dict):
            raise AgentApiError("新建会话响应格式无效")
        return self._session_from_json(payload)

    def get_session(self, session_id: str) -> SessionDto:
        payload = self._request_json("GET", f"/sessions/{quote(session_id, safe='')}")
        if not isinstance(payload, dict):
            raise AgentApiError("会话响应格式无效")
        return self._session_from_json(payload)

    def stream_chat(self, session_id: str, content: str) -> Iterator[AgentEventDto]:
        request = self._request(
            "POST",
            f"/sessions/{quote(session_id, safe='')}/messages",
            {"content": content},
            accept="text/event-stream",
        )
        try:
            with urlopen(request, timeout=self._stream_timeout) as response:
                for payload in parse_sse_events(response):
                    yield AgentEventDto(
                        type=str(payload.get("type", "")),
                        session_id=str(payload.get("session_id", session_id)),
                        step=int(payload.get("step", 0)),
                        data=(
                            dict(payload["data"])
                            if isinstance(payload.get("data"), dict)
                            else {}
                        ),
                    )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise AgentApiError(f"流式对话请求失败：{exc}") from exc

    def cancel(self, session_id: str) -> bool:
        payload = self._request_json(
            "POST", f"/sessions/{quote(session_id, safe='')}/cancel", {}
        )
        return bool(payload.get("cancelled")) if isinstance(payload, dict) else False

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        request = self._request(method, path, body, accept="application/json")
        try:
            with urlopen(request, timeout=self._request_timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AgentApiError(f"后端请求失败：{exc}") from exc

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        *,
        accept: str,
    ) -> Request:
        encoded = None
        headers = {"Accept": accept}
        if body is not None:
            encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        return Request(
            f"{self._base_url}{path}",
            data=encoded,
            headers=headers,
            method=method,
        )

    @staticmethod
    def _summary_from_json(payload: dict[str, Any]) -> SessionSummaryDto:
        return SessionSummaryDto(
            session_id=str(payload.get("session_id", "")),
            title=str(payload.get("title", "新会话")),
            updated_at=str(payload.get("updated_at", "")),
            turns=int(payload.get("turns", 0)),
        )

    @staticmethod
    def _session_from_json(payload: dict[str, Any]) -> SessionDto:
        raw_messages = payload.get("messages", [])
        messages = tuple(
            SessionMessageDto(
                role=str(item.get("role", "assistant")),
                content=str(item.get("content", "")),
                thinking=(str(item["thinking"]) if item.get("thinking") else None),
            )
            for item in raw_messages
            if isinstance(item, dict)
        )
        return SessionDto(session_id=str(payload.get("session_id", "")), messages=messages)


def format_session_time(value: str) -> str:
    """把 ISO 时间转成侧栏使用的简短本地时间；解析失败时保持原值。"""

    if not value:
        return "刚刚"
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%m-%d %H:%M")
    except ValueError:
        return value
