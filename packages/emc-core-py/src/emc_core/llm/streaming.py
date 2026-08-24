from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from emc_core.ports.llm import ChatMessage
from emc_core.tools.models import ToolCall, ToolSpec


class ModelStreamEventType(StrEnum):
    """模型适配器对 runtime 暴露的最小流式事件。"""

    THINKING_DELTA = "thinking.delta"
    CONTENT_DELTA = "content.delta"
    TOOL_CALL = "tool.call"


@dataclass(frozen=True, slots=True)
class ModelStreamEvent:
    """一个模型文本增量或完整工具调用。"""

    type: ModelStreamEventType
    text: str = ""
    tool_call: ToolCall | None = None


@runtime_checkable
class StreamingLLM(Protocol):
    """可选流式 LLM 端口；旧的 complete-only 测试替身仍然兼容。"""

    def stream(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolSpec],
    ) -> AsyncIterator[ModelStreamEvent]:
        """逐块产生 thinking、正式回答或工具调用。"""
        ...
