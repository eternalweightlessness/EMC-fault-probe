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
    print(
        f"validated {stats['cases']} cases from {stats['files']} files "
        f"({stats['severity_kinds']} severity values, "
        f"{stats['unknown_values']} blank fields normalized to 未知)"
    )


if __name__ == "__main__":
    main()
