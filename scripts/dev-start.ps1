param(
    [int]$BackendPort = 8005,
    [int]$FrontendPort = 3005
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "=== Canopy Dev Starter ===" -ForegroundColor Cyan
Write-Host "Backend port: $BackendPort | Frontend port: $FrontendPort"

# ── Kill existing processes on target ports ──
Write-Host "`n[1/3] Killing old processes..." -ForegroundColor Yellow

$killed = $false
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "  Killing backend on port $BackendPort (PID $($proc.Id): $($proc.ProcessName))"
        Stop-Process -Id $proc.Id -Force
        $killed = $true
    }
}
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -like "*node*") {
        Write-Host "  Killing frontend on port $FrontendPort (PID $($proc.Id): $($proc.ProcessName))"
        Stop-Process -Id $proc.Id -Force
        $killed = $true
    }
}
if (-not $killed) {
    Write-Host "  No old processes found on ports $BackendPort/$FrontendPort"
}

# ── Start Backend ──
Write-Host "`n[2/3] Starting backend..." -ForegroundColor Yellow

$backendDir = Join-Path $root "apps\backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "  ERROR: Virtual env not found at $venvPython" -ForegroundColor Red
    Write-Host "  Run: cd apps\backend && python -m venv .venv && .venv\Scripts\activate && pip install -e `".[dev]`"" -ForegroundColor Red
    exit 1
}

$backendLog = Join-Path $root "backend-$BackendPort.out.log"
$backendErrLog = Join-Path $root "backend-$BackendPort.err.log"

Start-Process `
    -FilePath $venvPython `
    -WorkingDirectory $backendDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError $backendErrLog `
    -ArgumentList @(
        "-m", "uvicorn",
        "app:app",
        "--host", "127.0.0.1",
        "--port", "$BackendPort",
        "--reload",
        "--reload-exclude", "tests"
    ) | Out-Null

Write-Host "  Backend starting on http://127.0.0.1:$BackendPort"
Write-Host "  Logs: $backendLog"
Write-Host "  Reload watcher ignores: tests/*"

# ── Start Frontend ──
Write-Host "`n[3/3] Starting frontend..." -ForegroundColor Yellow

$frontendDir = Join-Path $root "apps\frontend"
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) {
    $npmCmd = (Get-Command npm -ErrorAction SilentlyContinue).Source
}
if (-not $npmCmd) {
    Write-Host "  ERROR: npm not found in PATH" -ForegroundColor Red
    exit 1
}

$frontendLog = Join-Path $root "frontend-$FrontendPort.out.log"
$frontendErrLog = Join-Path $root "frontend-$FrontendPort.err.log"

$env:NODE_OPTIONS = "--max-old-space-size=2048"
Start-Process `
    -FilePath "cmd.exe" `
    -WorkingDirectory $frontendDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError $frontendErrLog `
    -ArgumentList @("/c", "npm", "run", "dev", "--", "--port", "$FrontendPort") | Out-Null

Write-Host "  Frontend starting on http://localhost:$FrontendPort"
Write-Host "  Logs: $frontendLog"
Write-Host "  Memory limit: 2GB"

# ── Summary ──
Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "  Backend:  http://127.0.0.1:${BackendPort}/api/health"
Write-Host "  Frontend: http://localhost:${FrontendPort}"
Write-Host ""
Write-Host "  To stop: powershell -File scripts\dev-stop.ps1"
Write-Host ""
Write-Host "  Type 'exit' to close this window (services keep running in background)"
Write-Host "  Notes: services are detached processes (not PowerShell jobs)"
