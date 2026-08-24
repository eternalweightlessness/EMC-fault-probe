from __future__ import annotations

from fastapi import Request

from emc_backend.composition import AppContainer


def get_container(request: Request) -> AppContainer:
    """从当前 FastAPI 应用状态取得依赖容器。"""

    container = getattr(request.app.state, "container", None)
    if not isinstance(container, AppContainer):
        raise RuntimeError("后端依赖容器尚未初始化")
    return container
