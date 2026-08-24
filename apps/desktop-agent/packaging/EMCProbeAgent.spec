from pathlib import Path

import PyQt6
from PyInstaller.utils.hooks import collect_all, collect_submodules

project_root = Path(SPECPATH).resolve().parents[2]
desktop_root = project_root / "apps" / "desktop-agent"

datas = [
    (
        str(project_root / "packages" / "emc-runtime-local-py" / "prompts"),
        "packages/emc-runtime-local-py/prompts",
    ),
    (str(desktop_root / "resources" / "icons"), "apps/desktop-agent/resources/icons"),
    (str(project_root / "data" / "runtime" / "vector_store"), "data/runtime/vector_store"),
]
binaries = []
hiddenimports = []
for package_name in ("chromadb", "onnxruntime", "uvicorn"):
    package_datas, package_binaries, package_hidden = collect_all(package_name)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden
hiddenimports += collect_submodules("emc_backend")
hiddenimports += collect_submodules("emc_core")
hiddenimports += collect_submodules("emc_runtime_local")
hiddenimports += collect_submodules("integrations")

# Conda 提供的 Qt 6 使用较新的 MSVC runtime。PyInstaller 的 PyQt hook 在某些
# 环境只收集基础三个 DLL，Qt6Core 因缺少 atomic/thread 辅助库而无法加载。
qt_bin = Path(PyQt6.__file__).resolve().parent / "Qt6" / "bin"
for runtime_name in (
    "concrt140.dll",
    "msvcp140_atomic_wait.dll",
    "msvcp140_codecvt_ids.dll",
    "vcruntime140_threads.dll",
    "d3dcompiler_47.dll",
):
    runtime_path = qt_bin / runtime_name
    if runtime_path.is_file():
        binaries.append((str(runtime_path), "PyQt6/Qt6/bin"))

a = Analysis(
    [str(desktop_root / "src" / "emc_desktop_agent" / "main.py")],
    pathex=[
        str(desktop_root / "src"),
        str(project_root / "apps" / "backend" / "src"),
        str(project_root / "packages" / "emc-core-py" / "src"),
        str(project_root / "packages" / "emc-runtime-local-py" / "src"),
        str(project_root),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pandas", "openpyxl"],
    noarchive=False,
)

# Anaconda base 目录里的 ICU 73 使用带版本后缀的导出符号，但此 PyQt6 构建链接
# 的是 Windows 系统 ICU（未加后缀）。若把 Anaconda ICU 放进 onedir 根目录，
# 它会遮蔽 System32/icuuc.dll，导致 QtCore.pyd 报 WinError 127。
excluded_runtime_names = {"icuuc.dll", "icudt73.dll"}
a.binaries = [
    entry
    for entry in a.binaries
    if Path(entry[0]).name.lower() not in excluded_runtime_names
]

# 同一 Conda 环境可能从其他包收集到旧的 MSVC runtime。先删除同名条目，再把
# PyQt6 随附的匹配版本同时放到 onedir 根目录和 Qt bin 目录，保证 DLL 搜索顺序
# 不会选择到 ABI 不兼容的版本。
qt_runtime_names = {
    "msvcp140.dll",
    "msvcp140_1.dll",
    "msvcp140_2.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
}
a.binaries = [
    entry for entry in a.binaries if Path(entry[0]).name.lower() not in qt_runtime_names
]
for runtime_name in sorted(qt_runtime_names):
    source = qt_bin / runtime_name
    if source.is_file():
        a.binaries.append((runtime_name, str(source), "BINARY"))
        a.binaries.append((f"PyQt6/Qt6/bin/{runtime_name}", str(source), "BINARY"))
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EMCProbeAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(desktop_root / "resources" / "icons" / "emc_fault_probe.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="EMCProbeAgent",
)
