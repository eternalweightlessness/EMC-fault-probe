from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from emc_core.agent.state import AgentState
from emc_core.domain.events import AgentEvent, AgentEventType
from emc_core.domain.session import MessageRole
from emc_core.ports.agent_runtime import AgentRuntime
from emc_core.ports.session_store import SessionStore


class SessionBusyError(RuntimeError):
    """同一会话已有一轮 Agent 正在运行。"""


class ChatService:
    """连接持久化会话与可替换 AgentRuntime 的应用编排服务。"""

    def __init__(
        self,
        *,
        store: SessionStore,
        runtime: AgentRuntime,
        system_prompt: str,
    ) -> None:
        self._store = store
        self._runtime = runtime
        self._system_prompt = system_prompt.strip()
        self._locks: dict[str, asyncio.Lock] = {}
        self._active_states: dict[str, AgentState] = {}

    async def send_message(
        self,
        *,
        session_id: str,
        content: str,
    ) -> AsyncIterator[AgentEvent]:
        normalized = content.strip()
        if not normalized:
            raise ValueError("消息内容不能为空")

        lock = self._locks.setdefault(session_id, asyncio.Lock())
        if lock.locked():
            raise SessionBusyError(f"会话正在运行：{session_id}")

        await lock.acquire()
        try:
            session = await asyncio.to_thread(self._store.load, session_id)
            await asyncio.to_thread(
                self._store.append_message,
                session_id,
                role=MessageRole.USER,
                content=normalized,
            )

            messages: list[dict[str, str]] = []
            if self._system_prompt:
                messages.append({"role": "system", "content": self._system_prompt})
            messages.extend(message.to_llm_message() for message in session.messages)
            messages.append({"role": "user", "content": normalized})

            state = AgentState(session_id=session_id, messages=messages)
            self._active_states[session_id] = state
            thinking_parts: list[str] = []

            async for event in self._runtime.run(state=state):
                await asyncio.to_thread(self._store.append_event, session_id, event)
                if event.type is AgentEventType.ASSISTANT_THINKING_DELTA:
                    thinking_parts.append(str(event.data.get("delta", "")))
                elif event.type is AgentEventType.ASSISTANT_COMPLETED:
                    await asyncio.to_thread(
                        self._store.append_message,
                        session_id,
                        role=MessageRole.ASSISTANT,
                        content=str(event.data.get("content", "")),
                        thinking="".join(thinking_parts) or None,
                    )
                yield event
        finally:
            self._active_states.pop(session_id, None)
            lock.release()

    def cancel(self, session_id: str) -> bool:
        """标记正在运行的状态为取消；不存在活动轮次时返回 False。"""

        state = self._active_states.get(session_id)
        if state is None:
            return False
        state.cancelled = True
        return True
