param(
    [string]$Python = "python",
    [switch]$SkipIndexBuild
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$indexPath = Join-Path $projectRoot "data\runtime\vector_store\chroma.sqlite3"
$specPath = Join-Path $projectRoot "apps\desktop-agent\packaging\EMCProbeAgent.spec"
$distPath = Join-Path $projectRoot "artifacts\dist"
$workPath = Join-Path $projectRoot "artifacts\build\desktop-agent"

if ($env:OS -ne "Windows_NT") {
    throw "EMCProbeAgent.exe must be built on Windows."
}

if (-not $SkipIndexBuild) {
    & $Python (Join-Path $projectRoot "scripts\data\build_vector_index.py")
    if ($LASTEXITCODE -ne 0) {
        throw "Vector index build failed. Ensure Ollama and nomic-embed-text are ready."
    }
}

if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
    throw "Formal vector index not found: $indexPath"
}

& $Python -m PyInstaller --clean --noconfirm --distpath $distPath --workpath $workPath $specPath
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Output "Windows application: $distPath\EMCProbeAgent\EMCProbeAgent.exe"
