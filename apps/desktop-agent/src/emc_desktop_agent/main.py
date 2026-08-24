from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from emc_desktop_agent.composition import build_main_window
from emc_desktop_agent.runtime.paths import prepare_packaged_environment
from emc_desktop_agent.settings import DesktopSettings
from emc_desktop_agent.ui.theme import APP_STYLESHEET, configure_application_font


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EMC Fault Probe desktop Agent")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="显示带示例对话的 UI 预览，不连接后端",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        help="把预览窗口保存为 PNG 后退出，用于视觉回归",
    )
    parser.add_argument(
        "--embedded-backend",
        action="store_true",
        help="在当前桌面进程的后台线程启动 FastAPI；打包版默认启用",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prepare_packaged_environment()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("EMC Fault Probe Agent")
    app.setStyle("Fusion")
    configure_application_font(app)
    app.setStyleSheet(APP_STYLESHEET)

    preview = args.preview or args.screenshot is not None
    use_embedded_backend = args.embedded_backend or getattr(sys, "frozen", False)
    backend_server = None
    backend_startup_error: str | None = None
    if use_embedded_backend and not preview:
        try:
            # 延迟导入已经由 runtime helper 封装；Settings 此时能读到打包路径设置。
            from emc_backend.config import Settings

            from emc_desktop_agent.runtime.backend_server import EmbeddedBackendServer

            backend_server = EmbeddedBackendServer(Settings.from_env())
            app.aboutToQuit.connect(backend_server.stop)
        except Exception as exc:  # noqa: BLE001 - packaged GUI 必须把启动异常落盘
            backend_startup_error = (
                f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            )
    window = build_main_window(
        DesktopSettings.from_environment(),
        auto_connect=not preview,
    )
    if preview:
        window.seed_preview()
    window.show()

    def report_backend_error(message: str) -> None:
        window.show_backend_error(message)
        runtime_root = Path(os.environ.get("EMC_RUNTIME_ROOT", Path.cwd()))
        log_directory = runtime_root / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        (log_directory / "backend-error.log").write_text(
            message,
            encoding="utf-8",
        )

    if backend_startup_error is not None:
        report_backend_error(backend_startup_error)
    if backend_server is not None:
        backend_server.failed.connect(report_backend_error)
        backend_server.start()
        # 后端线程启动需要短暂时间。窗口先可见，再自动刷新两次状态和会话；
        # 普通开发模式仍由独立热重载后端提供服务。
        QTimer.singleShot(700, window.reconnect_backend)
        QTimer.singleShot(1800, window.reconnect_backend)

    if args.screenshot is not None:
        destination = args.screenshot.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        def save_screenshot() -> None:
            if not window.grab().save(str(destination), "PNG"):
                raise RuntimeError(f"无法保存截图：{destination}")
            app.quit()

        # 等待布局和字体完成首次绘制，否则截图尺寸可能还是初始值。
        QTimer.singleShot(500, save_screenshot)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
