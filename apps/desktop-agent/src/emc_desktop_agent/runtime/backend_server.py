from __future__ import annotations

import asyncio
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from emc_backend.config import Settings
from emc_backend.main import create_app
from PyQt6.QtCore import QThread, pyqtSignal


class EmbeddedBackendServer(QThread):
    """在打包进程的独立线程中运行后端，同时保持 HTTP 架构边界。

    桌面 widget 仍然只访问 ``BackendApiClient``，不会直接调用 ChatService。
    这里嵌入 Uvicorn 是为了让 Windows 用户双击一个 exe 即可启动完整本地应用。
    """

    failed = pyqtSignal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._server: uvicorn.Server | None = None

    def run(self) -> None:
        try:
            self._log("backend thread entered")
            config = uvicorn.Config(
                create_app(settings=self._settings),
                host=self._settings.host,
                port=self._settings.port,
                log_level="warning",
                access_log=False,
                # ``console=False`` 的 PyInstaller GUI 没有 sys.stdout。
                # Uvicorn 默认 formatter 会调用 stdout.isatty()，因此发布版
                # 显式关闭默认 logging 配置，异常由本类写入运行目录的日志。
                log_config=None,
            )
            self._log("uvicorn config created")
            self._server = uvicorn.Server(config)
            self._log("uvicorn serve starting")
            asyncio.run(self._server.serve())
            self._log("uvicorn serve stopped")
        except Exception as exc:  # noqa: BLE001 - 线程边界必须转成 UI 可显示错误
            # GUI 发布版没有控制台，完整 traceback 会写入运行目录，便于用户反馈。
            message = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            self._log(message)
            self.failed.emit(message)

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        self.requestInterruption()
        self.wait(5000)

    @staticmethod
    def _log(message: str) -> None:
        runtime_root = Path(os.environ.get("EMC_RUNTIME_ROOT", Path.cwd()))
        log_directory = runtime_root / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()
        with (log_directory / "embedded-backend.log").open(
            "a",
            encoding="utf-8",
        ) as stream:
            stream.write(f"{timestamp} {message}\n")
