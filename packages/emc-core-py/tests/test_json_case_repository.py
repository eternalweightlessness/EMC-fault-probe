from __future__ import annotations

import json
from pathlib import Path

import pytest
from emc_core.persistence.json_case_repository import (
    DatasetLoadError,
    JsonCaseRepository,
)


def _case(phenomenon: str = "辐射发射超标") -> dict[str, str]:
    return {
        "故障对象": "测试设备",
        "故障现象": phenomenon,
        "故障原因": "屏蔽不连续",
        "解决方案": "改善屏蔽搭接",
        "故障等级": "严重",
        "发生频率": "偶发",
    }


def _write(path: Path, rows: object) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def test_repository_merges_files_and_deduplicates_complete_cases(tmp_path: Path) -> None:
    first = tmp_path / "data_1.json"
    second = tmp_path / "data_2.json"
    _write(first, [_case()])
    _write(second, [_case(), _case("传导发射超标")])

    cases = JsonCaseRepository([first, second]).list_cases()

    assert [case.phenomenon for case in cases] == ["辐射发射超标", "传导发射超标"]


def test_repository_reports_file_and_row_for_invalid_case(tmp_path: Path) -> None:
    data_file = tmp_path / "data_1.json"
    raw = _case()
    del raw["解决方案"]
    _write(data_file, [raw])

    with pytest.raises(DatasetLoadError, match=r"data_1\.json 第 1 条"):
        JsonCaseRepository([data_file]).list_cases()
