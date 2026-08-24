from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from integrations.models.ollama.health import (
    is_ollama_model_installed,
    list_ollama_models,
)


class FakeResponse(BytesIO):
    """提供 urlopen 上下文管理器所需的最小文件接口。"""

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def test_list_ollama_models_returns_sorted_unique_names(monkeypatch) -> None:
    payload = {
        "models": [
            {"name": "nomic-embed-text"},
            {"name": "qwen3.5:9b-q4_K_M"},
            {"name": "nomic-embed-text"},
            {"missing": "name"},
        ]
    }
    response = FakeResponse(json.dumps(payload).encode())
    monkeypatch.setattr(
        "integrations.models.ollama.health.urllib.request.urlopen",
        lambda *_args, **_kwargs: response,
    )

    assert list_ollama_models() == ["nomic-embed-text", "qwen3.5:9b-q4_K_M"]


def test_list_ollama_models_handles_unavailable_service(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise OSError("offline")

    monkeypatch.setattr(
        "integrations.models.ollama.health.urllib.request.urlopen",
        fail,
    )

    assert list_ollama_models() == []


def test_model_installation_accepts_implicit_latest_tag() -> None:
    installed = ["nomic-embed-text:latest", "qwen3.5:9b-q4_K_M"]

    assert is_ollama_model_installed("nomic-embed-text", installed) is True
    assert is_ollama_model_installed("qwen3.5:9b-q4_K_M", installed) is True
    assert is_ollama_model_installed("missing-model", installed) is False
