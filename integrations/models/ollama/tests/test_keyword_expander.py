from __future__ import annotations

import asyncio
from typing import Any

from ollama import ChatResponse

from integrations.models.ollama.keyword_expander import OllamaKeywordExpander


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def chat(self, **kwargs: Any) -> ChatResponse:
        self.calls.append(kwargs)
        return ChatResponse(
            message={
                "role": "assistant",
                "content": '["辐射发射", "发射超标"]',
            }
        )


def test_ollama_keyword_expander_parses_json_array() -> None:
    client = FakeClient()
    expander = OllamaKeywordExpander(
        model="test-model",
        client=client,  # type: ignore[arg-type]
    )

    keywords = asyncio.run(expander.expand("辐射问题"))

    assert list(keywords) == ["辐射发射", "发射超标"]
    assert client.calls[0]["stream"] is False
