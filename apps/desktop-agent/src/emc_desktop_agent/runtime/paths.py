from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def prepare_packaged_environment() -> None:
    """为 PyInstaller 版本准备只读资源和可写运行目录。

    ``sys._MEIPASS`` 是 PyInstaller 提供的解包资源根目录。向量库首次运行时复制到
    LOCALAPPDATA，之后复用用户自己的副本；会话也写到这里，升级 exe 不会丢失。
    """

    if not getattr(sys, "frozen", False):
        return

    bundle_root = Path(sys._MEIPASS).resolve()
    local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    runtime_root = local_app_data / "EMC Fault Probe" / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)

    bundled_index = bundle_root / "data" / "runtime" / "vector_store"
    installed_index = runtime_root / "vector_store"
    if not installed_index.exists():
        if not bundled_index.is_dir():
            raise FileNotFoundError("安装包中缺少 EMC 向量索引")
        shutil.copytree(bundled_index, installed_index)

    os.environ.setdefault("EMC_PROJECT_ROOT", str(bundle_root))
    os.environ.setdefault("EMC_RUNTIME_ROOT", str(runtime_root))
    # 双击 exe 时没有单独启动后端或 Ollama 的步骤。只在发布版设置默认值；
    # 高级用户仍可事先用环境变量 ``false`` 禁用自动启动。
    os.environ.setdefault("EMC_AUTO_START_OLLAMA", "true")
