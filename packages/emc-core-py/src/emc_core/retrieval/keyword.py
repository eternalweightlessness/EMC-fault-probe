from __future__ import annotations

import json
from collections.abc import Iterable


def normalize_keywords(original: str, generated: Iterable[object]) -> list[str]:
    """保留原始查询，并按出现顺序移除空白和重复关键词。"""

    keywords: list[str] = []
    seen: set[str] = set()
    for candidate in (original, *generated):
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            keywords.append(normalized)
    return keywords


def extract_keyword_array(content: str, original: str) -> list[str]:
    """从模型文本中提取最后一个有效字符串 JSON 数组。

    推理模型可能先在思考文本中输出示例数组。``JSONDecoder.raw_decode`` 可以从
    任意 ``[`` 位置尝试解析，而选择最后一个有效数组能与旧实验行为保持一致。
    """

    decoder = json.JSONDecoder()
    generated: list[str] = []
    for index, character in enumerate(content):
        if character != "[":
            continue
        try:
            candidate, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, list) and all(
            isinstance(item, str) for item in candidate
        ):
            generated = candidate
    return normalize_keywords(original, generated)
