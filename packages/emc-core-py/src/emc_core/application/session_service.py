from __future__ import annotations

import asyncio
from collections.abc import Sequence

from emc_core.domain.session import Session, SessionSummary
from emc_core.ports.session_store import SessionStore


class SessionService:
    """供 HTTP、桌面和未来 Web 端共同调用的异步会话服务。"""

    def __init__(self, store: SessionStore) -> None:
        self._store = store

    async def create(self) -> Session:
        return await asyncio.to_thread(self._store.create)

    async def get(self, session_id: str) -> Session:
        return await asyncio.to_thread(self._store.load, session_id)

    async def list(self) -> Sequence[SessionSummary]:
        return await asyncio.to_thread(self._store.list_summaries)
