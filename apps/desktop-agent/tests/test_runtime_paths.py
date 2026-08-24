from __future__ import annotations

import os
import sys
from pathlib import Path

from emc_desktop_agent.runtime.paths import prepare_packaged_environment


def test_packaged_environment_copies_index_to_local_app_data(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundle_root = tmp_path / "bundle"
    bundled_index = bundle_root / "data" / "runtime" / "vector_store"
    bundled_index.mkdir(parents=True)
    (bundled_index / "chroma.sqlite3").write_bytes(b"index")
    local_app_data = tmp_path / "local"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("EMC_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("EMC_RUNTIME_ROOT", raising=False)
    monkeypatch.delenv("EMC_AUTO_START_OLLAMA", raising=False)

    prepare_packaged_environment()

    runtime_root = local_app_data / "EMC Fault Probe" / "runtime"
    assert (runtime_root / "vector_store" / "chroma.sqlite3").read_bytes() == b"index"
    assert Path(os.environ["EMC_PROJECT_ROOT"]) == bundle_root
    assert Path(os.environ["EMC_RUNTIME_ROOT"]) == runtime_root
    assert os.environ["EMC_AUTO_START_OLLAMA"] == "true"
