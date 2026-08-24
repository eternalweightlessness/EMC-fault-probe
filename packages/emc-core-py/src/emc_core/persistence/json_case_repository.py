from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from emc_core.domain.fault_case import FaultCase, InvalidFaultCaseError


class DatasetLoadError(RuntimeError):
    """发布数据文件无法被可靠读取。"""


class JsonCaseRepository:
    """从一个或多个发布 JSON 文件加载、校验并去重故障案例。"""

    def __init__(self, paths: Sequence[Path]) -> None:
        if not paths:
            raise ValueError("至少需要一个故障数据文件")
        self._paths = tuple(path.resolve() for path in paths)

    def list_cases(self) -> list[FaultCase]:
        """返回案例；相同完整内容只保留第一次出现的位置。"""

        cases: list[FaultCase] = []
        seen_ids: set[str] = set()
        for path in self._paths:
            for index, raw_case in enumerate(self._read_file(path), start=1):
                if not isinstance(raw_case, dict):
                    raise DatasetLoadError(f"{path} 第 {index} 条必须是 JSON object")
                try:
                    case = FaultCase.from_mapping(raw_case)
                except InvalidFaultCaseError as exc:
                    raise DatasetLoadError(f"{path} 第 {index} 条无效：{exc}") from exc

                if case.case_id not in seen_ids:
                    seen_ids.add(case.case_id)
                    cases.append(case)
        return cases

    @staticmethod
    def _read_file(path: Path) -> list[Any]:
        if not path.is_file():
            raise DatasetLoadError(f"找不到发布数据文件：{path}")
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DatasetLoadError(f"无法读取发布数据文件 {path}：{exc}") from exc

        if not isinstance(raw_data, list):
            raise DatasetLoadError(f"发布数据文件顶层必须是 JSON array：{path}")
        return raw_data
