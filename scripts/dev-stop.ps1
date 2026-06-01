$ErrorActionPreference = "Continue"
Write-Host "=== Stopping Canopy services ===" -ForegroundColor Cyan

$killed = $false

# Stop background jobs
Get-Job -Name "canopy-backend", "canopy-frontend" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stopping job: $($_.Name)"
    Stop-Job -Job $_ -PassThru | Remove-Job -Force
    $killed = $true
}

# Kill any remaining Python/Node on known ports
foreach ($port in @(8005, 8006, 8007, 8008, 3005)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc -and ($proc.ProcessName -like "*python*" -or $proc.ProcessName -like "*node*")) {
            Write-Host "  Killing port $port (PID $($proc.Id): $($proc.ProcessName))"
            Stop-Process -Id $proc.Id -Force
            $killed = $true
        }
    }
}

if (-not $killed) {
    Write-Host "  No Canopy services found running."
}
Write-Host "=== Done ===" -ForegroundColor Green
