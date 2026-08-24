param(
    [string]$Python = "python"
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$watcher = Join-Path $projectRoot "scripts\dev\watch_desktop.py"

# 使用当前解释器运行 watcher。watcher 会给桌面子进程补充 src 路径，因此在
# PyCharm 中无需临时修改项目代码，也可以直接获得保存后自动重启的效果。
& $Python $watcher
exit $LASTEXITCODE
