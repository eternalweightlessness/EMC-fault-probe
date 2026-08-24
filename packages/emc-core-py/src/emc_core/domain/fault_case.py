from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar


class InvalidFaultCaseError(ValueError):
    """输入记录不是完整 EMC 故障案例。"""


@dataclass(frozen=True, slots=True)
class FaultCase:
    """一条经过校验的 EMC 故障案例。

    Python 属性使用英文，保证业务代码容易输入和静态检查；文件/API 边界仍使用
    数据集已有的六个中文字段，避免破坏现有数据兼容性。
    """

    object_name: str
    phenomenon: str
    cause: str
    solution: str
    severity: str
    frequency: str

    FIELD_MAP: ClassVar[dict[str, str]] = {
        "故障对象": "object_name",
        "故障现象": "phenomenon",
        "故障原因": "cause",
        "解决方案": "solution",
        "故障等级": "severity",
        "发生频率": "frequency",
    }
    UNKNOWN_VALUE: ClassVar[str] = "未知"

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> FaultCase:
        """从 JSON object 创建案例，并拒绝缺失、非字符串或空字段。"""

        values: dict[str, str] = {}
        errors: list[str] = []
        for source_name, attribute_name in cls.FIELD_MAP.items():
            value = raw.get(source_name)
            if not isinstance(value, str):
                errors.append(f"{source_name}必须是字符串")
                continue

            # 现有 151 条发布数据中有少量空字段。正式模型用“未知”显式表示
            # 缺失知识，既保留全部历史案例，也避免 UI 把空字符串误认为渲染错误。
            normalized = value.strip() or cls.UNKNOWN_VALUE
            values[attribute_name] = normalized

        if errors:
            raise InvalidFaultCaseError("；".join(errors))
        return cls(**values)

    def to_mapping(self) -> dict[str, str]:
        """转换回发布数据使用的中文字段字典。"""

        return {
            source_name: getattr(self, attribute_name)
            for source_name, attribute_name in self.FIELD_MAP.items()
        }

    @property
    def case_id(self) -> str:
        """返回由完整内容决定的稳定 ID，用于去重和向量索引 upsert。"""

        canonical_json = json.dumps(
            self.to_mapping(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def searchable_text(self) -> str:
        """生成嵌入和人工调试共用的结构化文本。"""

        return "\n".join(
            f"{field_name}：{value}"
            for field_name, value in self.to_mapping().items()
        )
