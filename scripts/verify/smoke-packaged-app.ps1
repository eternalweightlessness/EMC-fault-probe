param(
    [string]$Executable = "artifacts\dist\EMCProbeAgent\EMCProbeAgent.exe",
    [int]$Port = 8000,
    [switch]$RunAgentTurn,
    [switch]$DisableThinking,
    [string]$Python = "python",
    [string]$Query = "Search local cases for ESD-induced resets and give one concise remedy."
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$resolvedExecutable = (Resolve-Path (Join-Path $projectRoot $Executable)).Path
$env:LOCALAPPDATA = Join-Path $projectRoot "artifacts\package-embedded-smoke"
$env:QT_QPA_PLATFORM = "offscreen"
if ($DisableThinking) {
    $env:EMC_OLLAMA_THINK = "false"
}
$baseUrl = "http://127.0.0.1:$Port/api/v1"

# Keep the exact process returned by Start-Process. The finally block only stops
# this owned process and never scans for unrelated user processes by name.
$process = Start-Process -FilePath $resolvedExecutable -WindowStyle Hidden -PassThru
try {
    $health = $null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
            break
        }
        catch {
            # Embedded Uvicorn and Chroma need a short bounded warm-up period.
        }
    }
    if ($null -eq $health) {
        $process.Refresh()
        throw (
            "Packaged backend did not become ready. Exited={0}; Window={1}" -f `
                $process.HasExited, $process.MainWindowTitle
        )
    }

    $session = Invoke-RestMethod `
        -Method Post `
        -Uri "$baseUrl/sessions" `
        -ContentType "application/json" `
        -Body "{}"
    Write-Output (
        "Packaged backend: {0}, runtime={1}, session={2}" -f `
            $health.status, $health.runtime, $session.session_id
    )

    if ($RunAgentTurn) {
        & $Python `
            (Join-Path $projectRoot "scripts\verify\e2e_api_client.py") `
            --base-url $baseUrl `
            $Query
        if ($LASTEXITCODE -ne 0) {
            throw "Packaged Agent end-to-end turn failed."
        }
    }
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
}

Write-Output "Packaged process stopped: $($process.HasExited)"
