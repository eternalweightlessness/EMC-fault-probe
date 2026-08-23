from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AgentEventType(StrEnum):
    """定义事件类型。
    包含对话轮次开始、工具请求、工具请求结束、助手回复结束、对话轮次结束和对话轮次失败。
    """
    TURN_STARTED = "turn.started"
    TOOL_REQUESTED = "tool.requested"
    TOOL_COMPLETED = "tool.completed"
    ASSISTANT_COMPLETED = "assistant.completed"
    TURN_COMPLETED = "turn.completed"
    TURN_FAILED = "turn.failed"


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """Agent Runtime 对外产生的统一事件。"""
    type: AgentEventType
    session_id: str
    step: int
    data: dict[str, Any] = field(default_factory=dict)
