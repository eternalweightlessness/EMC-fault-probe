from __future__ import annotations

from pathlib import Path

from emc_desktop_agent.api_client import BackendApiClient
from emc_desktop_agent.settings import DesktopSettings
from emc_desktop_agent.ui.main_window import MainWindow


def build_main_window(
    settings: DesktopSettings,
    *,
    auto_connect: bool = True,
) -> MainWindow:
    """集中组装 adapter 和窗口，避免 UI 类自行创建网络依赖。"""

    app_root = Path(__file__).resolve().parents[2]
    return MainWindow(
        client=BackendApiClient(settings),
        icon_path=app_root / "resources" / "icons" / "emc_fault_probe.ico",
        auto_connect=auto_connect,
    )
