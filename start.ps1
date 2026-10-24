<#
.SYNOPSIS
    Starts the Mount Fuji Backend server.
.USAGE
    .\start
    .\start -Prod
#>
param(
    [switch]$Prod
)

# Ensure PyYAML builds pure-python if uv sync triggers on Python 3.15
$env:PYYAML_FORCE_LIBYAML = "0"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  🚀 Starting Mount Fuji Backend Server..." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan

# Ensure local Redis is running
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\scripts\start_redis.ps1"


if ($Prod) {
    Write-Host "Mode: Production" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor DarkGray
    uv run python -m src.server
} else {
    Write-Host "Mode: Development (Hot Reload Enabled)" -ForegroundColor Yellow
    Write-Host "Server : http://localhost:8001" -ForegroundColor Cyan
    Write-Host "Swagger: http://localhost:8001/docs" -ForegroundColor Cyan
    Write-Host "Health : http://localhost:8001/health" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop.`n" -ForegroundColor DarkGray
    uv run uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8001
}
