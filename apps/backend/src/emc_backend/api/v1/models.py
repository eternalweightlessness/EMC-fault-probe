from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from emc_backend.composition import AppContainer
from emc_backend.dependencies import get_container
from integrations.models.ollama.health import is_ollama_model_installed

router = APIRouter(tags=["models"])


class ModelInfo(BaseModel):
    """一个模型在当前 Agent 配置中的用途和安装状态。"""

    model_config = ConfigDict(extra="forbid")

    name: str
    role: str
    installed: bool


class ModelsResponse(BaseModel):
    """模型列表接口响应。"""

    model_config = ConfigDict(extra="forbid")

    ollama_available: bool
    configured: list[ModelInfo]
    installed: list[str]


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    container: Annotated[AppContainer, Depends(get_container)],
) -> ModelsResponse:
    """返回桌面端模型选择器和状态栏需要的模型信息。"""

    status = await container.ollama_status()
    installed = list(status["models"])
    return ModelsResponse(
        ollama_available=bool(status["available"]),
        configured=[
            ModelInfo(
                name=container.settings.chat_model,
                role="chat",
                installed=is_ollama_model_installed(
                    container.settings.chat_model,
                    installed,
                ),
            ),
            ModelInfo(
                name=container.settings.embedding_model,
                role="embedding",
                installed=is_ollama_model_installed(
                    container.settings.embedding_model,
                    installed,
                ),
            ),
        ],
        installed=installed,
    )
