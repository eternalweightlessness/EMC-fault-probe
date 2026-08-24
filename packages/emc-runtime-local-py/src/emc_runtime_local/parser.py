from __future__ import annotations

import json
from collections.abc import Mapping
from uuid import uuid4

from emc_core.tools.models import ToolCall


def parse_prompt_tool_call(reply: str) -> ToolCall | None:
    """提取 Prompt 协议回复中最后一个合法工具调用 JSON object。"""

    decoder = json.JSONDecoder()
    result: ToolCall | None = None
    for index, character in enumerate(reply):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(reply[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, Mapping):
            continue
        name = candidate.get("name")
        arguments = candidate.get("arguments")
        if isinstance(name, str) and isinstance(arguments, Mapping):
            result = ToolCall(
                name=name,
                arguments=dict(arguments),
                call_id=f"prompt-{uuid4().hex}",
            )
    return result
