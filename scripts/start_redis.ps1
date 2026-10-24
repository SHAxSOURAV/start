<#
.SYNOPSIS
    Starts the local Redis Server in background if not already running.
#>
$redisPort = 6379
$conn = Get-NetTCPConnection -LocalPort $redisPort -ErrorAction SilentlyContinue

if ($conn) {
    Write-Host "Redis server is already running on port $redisPort." -ForegroundColor Green
    exit 0
}

$redisDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\taizod1024.redis-windows-fork_Microsoft.Winget.Source_8wekyb3d8bbwe\Redis-8.10.2-Windows-x64-msys2"
$redisExe = "$redisDir\redis-server.exe"

if (-not (Test-Path $redisExe)) {
    Write-Error "Redis binary not found at $redisExe. Please install via winget."
    exit 1
}

Write-Host "Starting Redis server on port $redisPort..." -ForegroundColor Cyan
cmd.exe /c start "Redis Server" /min "$redisExe"
Start-Sleep -Seconds 1

$testPing = & "$redisDir\redis-cli.exe" ping
if ($testPing -match "PONG") {
    Write-Host "Redis Server started successfully! [PONG received]" -ForegroundColor Green
} else {
    Write-Warning "Redis Server launched. Verifying connection..."
}
