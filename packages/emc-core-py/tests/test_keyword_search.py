from __future__ import annotations

import asyncio
from collections.abc import Sequence

from emc_core.application.search_service import CaseSearchService, SearchSource
from emc_core.domain.fault_case import FaultCase
from emc_core.retrieval.keyword import extract_keyword_array, normalize_keywords


def _case(phenomenon: str, cause: str) -> FaultCase:
    return FaultCase(
        object_name="测试设备",
        phenomenon=phenomenon,
        cause=cause,
        solution="整改",
        severity="一般",
        frequency="偶发",
    )


class FakeRepository:
    def list_cases(self) -> Sequence[FaultCase]:
        return [
            _case("辐射发射超标", "屏蔽不连续"),
            _case("传导发射超标", "滤波不足"),
        ]


class FakeExpander:
    async def expand(self, query: str) -> Sequence[str]:
        assert query == "发射问题"
        return ["辐射发射", "传导发射", "辐射发射"]


class FailingExpander:
    async def expand(self, query: str) -> Sequence[str]:
        raise RuntimeError(query)


def test_keyword_helpers_preserve_original_and_last_valid_array() -> None:
    content = '思考示例 ["错误"] 最终输出 ["辐射发射", "传导发射"]'

    assert extract_keyword_array(content, "发射问题") == [
        "发射问题",
        "辐射发射",
        "传导发射",
    ]
    assert normalize_keywords("原始", [" 原始 ", "", 42, "扩展"]) == ["原始", "扩展"]


def test_keyword_search_supports_expansion_and_field_filter() -> None:
    service = CaseSearchService(
        repository=FakeRepository(),
        keyword_expander=FakeExpander(),
    )

    hits = asyncio.run(service.keyword_search("发射问题", expand=True))
    filtered = asyncio.run(
        service.keyword_search("滤波", target_field="故障原因")
    )

    assert [hit.case.phenomenon for hit in hits] == ["辐射发射超标", "传导发射超标"]
    assert hits[0].source is SearchSource.KEYWORD
    assert filtered[0].case.phenomenon == "传导发射超标"


def test_keyword_expansion_failure_falls_back_to_original_query() -> None:
    service = CaseSearchService(
        repository=FakeRepository(),
        keyword_expander=FailingExpander(),
    )

    hits = asyncio.run(service.keyword_search("辐射发射", expand=True))

    assert len(hits) == 1
    assert hits[0].matched_keywords == ("辐射发射",)
