from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from emc_core.ports.llm import ChatMessage, LLMOutput
from emc_core.tools.models import ToolSpec
from emc_runtime_local.parser import parse_prompt_tool_call
from ollama import AsyncClient, ChatResponse


class PromptProtocolOllamaLLM:
    """不支持 native tools 的模型所用的 Prompt JSON 协议兼容适配器。"""

    def __init__(
        self,
        *,
        model: str,
        client: AsyncClient | None = None,
        options: Mapping[str, object] | None = None,
    ) -> None:
        self._model = model
        self._owns_client = client is None
        self._client = client or AsyncClient()
        self._options = dict(options or {})

    async def close(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def complete(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
    ) -> LLMOutput:
        tool_manual = json.dumps(
            [
                {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                }
                for spec in tools
            ],
            ensure_ascii=False,
        )
        protocol_message = {
            "role": "system",
            "content": (
                "需要使用工具时，只输出 JSON："
                '{"name":"工具名","arguments":{参数}}。'
                "可以直接回答时输出普通文本。\n可用工具："
                f"{tool_manual}"
            ),
        }
        ollama_messages = [protocol_message, *[dict(message) for message in messages]]
        response = await self._client.chat(
            model=self._model,
            messages=ollama_messages,
            stream=False,
            options=self._options,
        )
        if not isinstance(response, ChatResponse):
            raise TypeError("Ollama stream=False 时应返回 ChatResponse。")
        content = response.message.content or ""
        return parse_prompt_tool_call(content) or content
