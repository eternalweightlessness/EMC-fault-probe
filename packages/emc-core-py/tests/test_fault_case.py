from __future__ import annotations

import pytest
from emc_core.domain.fault_case import FaultCase, InvalidFaultCaseError


def _raw_case() -> dict[str, str]:
    return {
        "故障对象": "测试设备",
        "故障现象": "辐射发射超标",
        "故障原因": "屏蔽不连续",
        "解决方案": "改善屏蔽搭接",
        "故障等级": "严重",
        "发生频率": "偶发",
    }


def test_fault_case_round_trip_and_stable_id() -> None:
    first = FaultCase.from_mapping(_raw_case())
    second = FaultCase.from_mapping(dict(reversed(list(_raw_case().items()))))

    assert first.to_mapping() == _raw_case()
    assert first.case_id == second.case_id
    assert "故障现象：辐射发射超标" in first.searchable_text()


def test_fault_case_normalizes_empty_published_field() -> None:
    raw = _raw_case()
    raw["故障原因"] = "  "

    assert FaultCase.from_mapping(raw).cause == "未知"


def test_fault_case_rejects_non_string_field() -> None:
    raw = _raw_case()
    raw["故障原因"] = None  # type: ignore[assignment]

    with pytest.raises(InvalidFaultCaseError, match="故障原因必须是字符串"):
        FaultCase.from_mapping(raw)
