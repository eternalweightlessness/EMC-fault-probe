from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from emc_desktop_agent.composition import build_main_window
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("EMC Fault Probe Agent")
    app.setStyle("Fusion")
    configure_application_font(app)
    app.setStyleSheet(APP_STYLESHEET)

    preview = args.preview or args.screenshot is not None
    window = build_main_window(
        DesktopSettings.from_environment(),
        auto_connect=not preview,
    )
    if preview:
        window.seed_preview()
    window.show()

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
