from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from emc_backend.composition import AppContainer
from emc_backend.dependencies import get_container

router = APIRouter(tags=["health"])


class OllamaStatus(BaseModel):
    """Ollama 服务、配置模型和本地安装状态。"""

    model_config = ConfigDict(extra="forbid")

    available: bool
    host: str
    models: list[str]
    chat_model: str
    embedding_model: str
    chat_model_installed: bool
    embedding_model_installed: bool


class HealthResponse(BaseModel):
    """后端健康检查响应。"""

    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    environment: str
    runtime: str
    ollama: OllamaStatus


@router.get("/health", response_model=HealthResponse)
async def health(
    container: Annotated[AppContainer, Depends(get_container)],
) -> HealthResponse:
    """报告后端自身和本地 Ollama 的状态。

    即使 Ollama 不可用，HTTP 状态仍为 200：后端本身可以工作，桌面端可以据此
    显示离线提示，而不是把“模型未启动”误判成“整个后端崩溃”。
    """

    ollama_status = await container.ollama_status()
    return HealthResponse(
        status="ok",
        service="emc-backend",
        environment=container.settings.environment,
        runtime=type(container.runtime).__name__,
        ollama=OllamaStatus.model_validate(ollama_status),
    )
