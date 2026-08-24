$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonPathParts = @(
    (Join-Path $ProjectRoot "apps\backend\src"),
    (Join-Path $ProjectRoot "packages\emc-core-py\src"),
    (Join-Path $ProjectRoot "packages\emc-runtime-local-py\src"),
    $ProjectRoot
)

# PYTHONPATH 使用路径分隔符连接多个源码目录，使脚本无需预先执行 editable
# install。分号是 Windows 的路径分隔符；PathSeparator 能保持跨平台语义。
$env:PYTHONPATH = $PythonPathParts -join [IO.Path]::PathSeparator
$env:EMC_PROJECT_ROOT = $ProjectRoot

Set-Location $ProjectRoot
python -m emc_backend.main --reload @args
