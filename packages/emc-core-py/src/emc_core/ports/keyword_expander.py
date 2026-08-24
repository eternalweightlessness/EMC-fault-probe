from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class KeywordExpander(Protocol):
    """把用户原始查询扩展成同义关键词的可选模型端口。"""

    async def expand(self, query: str) -> Sequence[str]:
        """返回模型建议的关键词；调用方始终自行保留原始查询。"""
        ...
