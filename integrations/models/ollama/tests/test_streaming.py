from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from emc_core.llm.streaming import ModelStreamEventType
from ollama import ChatResponse

from integrations.models.ollama.client import OllamaLLM
from integrations.models.ollama.prompt_client import PromptProtocolOllamaLLM


class FakeStreamingClient:
    async def chat(self, **kwargs: Any) -> AsyncIterator[ChatResponse]:
        assert kwargs["stream"] is True

        async def chunks() -> AsyncIterator[ChatResponse]:
            yield ChatResponse(message={"role": "assistant", "thinking": "思考"})
            yield ChatResponse(message={"role": "assistant", "content": "回答"})

        return chunks()


class FakePromptClient:
    async def chat(self, **kwargs: Any) -> ChatResponse:
        assert kwargs["stream"] is False
        return ChatResponse(
            message={
                "role": "assistant",
                "content": '{"name":"search_cases","arguments":{"top_k":"3"}}',
            }
        )


async def _collect(llm: OllamaLLM):
    return [event async for event in llm.stream([], [])]


def test_ollama_stream_separates_thinking_and_content() -> None:
    llm = OllamaLLM(
        model="fake",
        client=FakeStreamingClient(),  # type: ignore[arg-type]
    )

    events = asyncio.run(_collect(llm))

    assert [event.type for event in events] == [
        ModelStreamEventType.THINKING_DELTA,
        ModelStreamEventType.CONTENT_DELTA,
    ]
    assert [event.text for event in events] == ["思考", "回答"]


def test_prompt_protocol_adapter_returns_unified_tool_call() -> None:
    llm = PromptProtocolOllamaLLM(
        model="fake",
        client=FakePromptClient(),  # type: ignore[arg-type]
    )

    output = asyncio.run(llm.complete([], []))

    assert not isinstance(output, str)
    assert output.name == "search_cases"
    assert output.arguments == {"top_k": "3"}
