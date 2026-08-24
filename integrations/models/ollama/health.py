from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DEFAULT_HOST = "http://127.0.0.1:11434"


def list_ollama_models(
    *,
    host: str = DEFAULT_HOST,
    timeout_seconds: float = 2.0,
) -> list[str]:
    """通过 Ollama ``/api/tags`` 返回已安装模型名称。

    该函数只负责协议适配，不读取应用配置。网络或响应格式错误会返回空列表，
    健康接口因此仍能稳定响应并把模型标记为未安装。
    """

    tags_url = f"{host.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=timeout_seconds) as response:
            payload = json.load(response)
    except (OSError, json.JSONDecodeError):
        return []

    raw_models = payload.get("models", []) if isinstance(payload, dict) else []
    names = {
        str(model["name"])
        for model in raw_models
        if isinstance(model, dict) and model.get("name")
    }
    return sorted(names)


def is_ollama_model_installed(
    model: str,
    installed_models: list[str],
) -> bool:
    """判断配置模型是否出现在 Ollama 模型列表中。

    Ollama 允许调用方省略默认的 ``:latest`` 标签，但 ``/api/tags`` 通常返回
    完整名称。集合推导式在这里把两种写法都标准化为无 ``:latest`` 的名称，
    从而避免健康接口误报。
    """

    def without_latest(name: str) -> str:
        return name.removesuffix(":latest")

    normalized_installed = {without_latest(name) for name in installed_models}
    return without_latest(model) in normalized_installed


def is_ollama_serving(
    *,
    host: str = DEFAULT_HOST,
    timeout_seconds: float = 2.0,
) -> bool:
    """通过 Ollama tags 接口判断服务是否可用。"""

    health_url = f"{host.rstrip('/')}/api/tags"

    try:
        with urllib.request.urlopen(
            health_url,
            timeout=timeout_seconds,
        ) as response:
            return response.status == 200
    except OSError:
        return False


def ensure_ollama_running(
    *,
    host: str = DEFAULT_HOST,
    log_path: Path,
    wait_seconds: float = 15.0,
) -> subprocess.Popen[bytes] | None:
    """
    确保 Ollama 服务已经运行。

    返回 None 表示服务原本就在运行；返回 Popen 表示本函数启动了一个新
    进程，调用方结束时应通过 stop_ollama_process() 关闭它。
    """

    if is_ollama_serving(host=host):
        return None

    ollama_command = shutil.which("ollama")
    if ollama_command is None:
        raise FileNotFoundError("找不到 ollama 命令，请先安装 Ollama 并加入 PATH。")

    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Windows 下隐藏后台服务窗口；其他平台的 creationflags 使用 0。
    creation_flags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    )

    with log_path.open("ab") as log_file:
        process = subprocess.Popen(
            [ollama_command, "serve"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"ollama serve 提前退出，请检查日志：{log_path.resolve()}"
            )

        if is_ollama_serving(host=host):
            return process

        time.sleep(0.5)

    stop_ollama_process(process)
    raise TimeoutError(
        f"等待 Ollama 服务超过 {wait_seconds:.0f} 秒，请检查：{log_path.resolve()}"
    )


def stop_ollama_process(process: subprocess.Popen[bytes]) -> None:
    """关闭由 ensure_ollama_running() 启动的 Ollama 子进程。"""

    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
