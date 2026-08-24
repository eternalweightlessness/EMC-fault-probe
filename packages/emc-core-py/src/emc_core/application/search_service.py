from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from emc_core.domain.fault_case import FaultCase
from emc_core.ports.case_repository import CaseRepository
from emc_core.ports.keyword_expander import KeywordExpander
from emc_core.ports.retriever import Retriever
from emc_core.retrieval.keyword import normalize_keywords


class SearchSource(StrEnum):
    KEYWORD = "keyword"
    VECTOR = "vector"


@dataclass(frozen=True, slots=True)
class CaseSearchHit:
    """适合 API 与 UI 使用的结构化搜索命中。"""

    case: FaultCase
    source: SearchSource
    score: float | None = None
    matched_keywords: tuple[str, ...] = ()


class CaseSearchService:
    """统一关键词和向量搜索，同时保留 Ollama 不可用时的降级路径。"""

    def __init__(
        self,
        *,
        repository: CaseRepository,
        retriever: Retriever | None = None,
        keyword_expander: KeywordExpander | None = None,
    ) -> None:
        self._repository = repository
        self._retriever = retriever
        self._keyword_expander = keyword_expander

    async def keyword_search(
        self,
        query: str,
        *,
        limit: int = 50,
        target_field: str | None = None,
        expand: bool = False,
    ) -> list[CaseSearchHit]:
        normalized_query = self._validate_query_and_limit(query, limit)
        if target_field is not None and target_field not in FaultCase.FIELD_MAP:
            raise ValueError(f"未知故障字段：{target_field}")

        generated: Sequence[str] = ()
        if expand and self._keyword_expander is not None:
            try:
                generated = await self._keyword_expander.expand(normalized_query)
            except Exception:  # noqa: BLE001 - 模型扩展失败必须降级到原始关键词
                generated = ()
        keywords = normalize_keywords(normalized_query, generated)

        hits: list[CaseSearchHit] = []
        for case in self._repository.list_cases():
            mapping = case.to_mapping()
            values = (
                [mapping[target_field]]
                if target_field is not None
                else list(mapping.values())
            )
            matched = tuple(
                keyword
                for keyword in keywords
                if any(keyword.casefold() in value.casefold() for value in values)
            )
            if matched:
                hits.append(
                    CaseSearchHit(
                        case=case,
                        source=SearchSource.KEYWORD,
                        matched_keywords=matched,
                    )
                )
            if len(hits) >= limit:
                break
        return hits

    async def vector_search(self, query: str, *, limit: int = 10) -> list[CaseSearchHit]:
        normalized_query = self._validate_query_and_limit(query, limit)
        if self._retriever is None:
            raise RuntimeError("当前应用没有配置向量检索器")

        results = await self._retriever.retrieve(normalized_query, limit)
        return [
            CaseSearchHit(
                case=FaultCase.from_mapping(result.metadata),
                source=SearchSource.VECTOR,
                score=result.score,
            )
            for result in results
        ]

    @staticmethod
    def _validate_query_and_limit(query: str, limit: int) -> str:
        normalized = query.strip()
        if not normalized:
            raise ValueError("query 不能为空")
        if limit < 1:
            raise ValueError("limit 必须大于 0")
        return normalized
