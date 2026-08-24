from __future__ import annotations

from emc_desktop_agent.api_client import format_session_time, parse_sse_events


def test_parse_sse_events_ignores_comments_and_supports_multiple_data_lines() -> None:
    events = list(
        parse_sse_events(
            [
                b": keep-alive\n",
                b"\n",
                b'data: {"type":\n',
                b'data: "turn.started", "data": {}}\n',
                b"\n",
            ]
        )
    )

    assert events == [{"type": "turn.started", "data": {}}]


def test_format_session_time_handles_empty_and_iso_values() -> None:
    assert format_session_time("") == "刚刚"
    assert format_session_time("not-a-date") == "not-a-date"
    assert len(format_session_time("2026-08-24T19:30:00+08:00")) == 11
