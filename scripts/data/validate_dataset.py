from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from emc_core.persistence.json_case_repository import JsonCaseRepository


def validate(data_directory: Path) -> dict[str, int]:
    """校验发布文件并返回适合 CI 输出的统计信息。"""

    paths = sorted(data_directory.glob("data_*.json"))
    repository = JsonCaseRepository(paths)
    cases = repository.list_cases()
    severities = Counter(case.severity for case in cases)
    unknown_values = sum(
        value == case.UNKNOWN_VALUE
        for case in cases
        for value in case.to_mapping().values()
    )
    return {
        "files": len(paths),
        "cases": len(cases),
        "severity_kinds": len(severities),
        "unknown_values": unknown_values,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate published EMC dataset")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "published" / "v1",
    )
    args = parser.parse_args()
    stats = validate(args.data_dir.resolve())

    # CI 摘要只使用 ASCII 字符。Windows runner 的标准输出可能仍采用
    # cp1252 等本地代码页；即使数据文件本身是 UTF-8，直接打印中文也会
    # 在编码阶段触发 UnicodeEncodeError。这里保留相同语义，同时让脚本
    # 能在 GitHub Actions、传统 PowerShell 和 PyCharm 终端中稳定运行。
    print(
        f"validated {stats['cases']} cases from {stats['files']} files "
        f"({stats['severity_kinds']} severity values, "
        f"{stats['unknown_values']} blank fields normalized to unknown)"
    )


if __name__ == "__main__":
    main()
