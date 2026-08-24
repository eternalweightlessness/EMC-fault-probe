from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_STREAM_TIMEOUT_SECONDS = 600.0


@dataclass(frozen=True, slots=True)
class DesktopSettings:
    """桌面端配置；所有值都可由 PyCharm 的环境变量覆盖。"""

    api_base_url: str = DEFAULT_API_BASE_URL
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    stream_timeout_seconds: float = DEFAULT_STREAM_TIMEOUT_SECONDS

    @classmethod
    def from_environment(cls) -> DesktopSettings:
        """从环境变量构建不可变配置，避免 UI 各处直接读取 os.environ。"""

        return cls(
            api_base_url=os.getenv("EMC_BACKEND_URL", DEFAULT_API_BASE_URL).rstrip("/"),
            request_timeout_seconds=float(
                os.getenv(
                    "EMC_DESKTOP_REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT_SECONDS
                )
            ),
            stream_timeout_seconds=float(
                os.getenv("EMC_DESKTOP_STREAM_TIMEOUT", DEFAULT_STREAM_TIMEOUT_SECONDS)
            ),
        )
