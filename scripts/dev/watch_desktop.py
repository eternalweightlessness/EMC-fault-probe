from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

WATCHED_SUFFIXES = {".py", ".svg", ".ui"}


def snapshot(directory: Path) -> dict[Path, int]:
    """记录源码修改时间；字典让新增、删除和修改都能通过一次比较发现。"""

    return {
        path: path.stat().st_mtime_ns
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in WATCHED_SUFFIXES
    }


def stop_child(process: subprocess.Popen[bytes]) -> None:
    """只停止本 watcher 创建的桌面子进程。"""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


def start_child(project_root: Path, environment: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [sys.executable, "-m", "emc_desktop_agent.main"],
        cwd=project_root,
        env=environment,
    )


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    source_root = project_root / "apps" / "desktop-agent" / "src"
    environment = os.environ.copy()
    previous_pythonpath = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(source_root), previous_pythonpath) if value
    )

    state = snapshot(source_root)
    child = start_child(project_root, environment)
    print("Desktop hot reload is running. Press Ctrl+C to stop.", flush=True)
    try:
        while True:
            time.sleep(0.5)
            new_state = snapshot(source_root)
            if new_state == state:
                continue
            state = new_state
            print("Desktop source changed; restarting UI...", flush=True)
            stop_child(child)
            child = start_child(project_root, environment)
    except KeyboardInterrupt:
        print("Stopping desktop hot reload...", flush=True)
    finally:
        stop_child(child)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
