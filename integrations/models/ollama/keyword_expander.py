from __future__ import annotations

from collections.abc import Sequence

from emc_core.retrieval.keyword import extract_keyword_array
from ollama import AsyncClient, ChatResponse


class OllamaKeywordExpander:
    """使用 Ollama 迁移旧桌面程序的模糊检索关键词扩展。"""

    def __init__(self, *, model: str, client: AsyncClient | None = None) -> None:
        self._model = model
        self._owns_client = client is None
        self._client = client or AsyncClient()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def expand(self, query: str) -> Sequence[str]:
        response = await self._client.chat(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "请根据用户输入的电磁兼容故障描述生成用于模糊搜索的关键词。"
                        "只返回 JSON 字符串数组，不要解释。\n\n"
                        f"用户输入：{query}"
                    ),
                }
            ],
            stream=False,
        )
        if not isinstance(response, ChatResponse):
            raise TypeError("Ollama stream=False 时应返回 ChatResponse")
        return extract_keyword_array(response.message.content or "", query)[1:]
