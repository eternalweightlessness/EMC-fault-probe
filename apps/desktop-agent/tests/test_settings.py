from __future__ import annotations

from emc_desktop_agent.settings import DesktopSettings


def test_settings_read_backend_url_and_strip_trailing_slash(monkeypatch) -> None:
    monkeypatch.setenv("EMC_BACKEND_URL", "http://localhost:9000/api/v1/")

    settings = DesktopSettings.from_environment()

    assert settings.api_base_url == "http://localhost:9000/api/v1"
