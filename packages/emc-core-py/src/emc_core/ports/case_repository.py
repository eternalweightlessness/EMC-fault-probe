from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from emc_core.domain.fault_case import FaultCase


class CaseRepository(Protocol):
    """故障案例读取端口；JSON、数据库或远程 API 都可以实现。"""

    def list_cases(self) -> Sequence[FaultCase]:
        """按数据源中的稳定顺序返回去重后的全部案例。"""
        ...
