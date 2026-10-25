<#
.SYNOPSIS
    Starts the local Redis Server in background if not already running.
#>
$redisPort = 6379
$redisDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\taizod1024.redis-windows-fork_Microsoft.Winget.Source_8wekyb3d8bbwe\Redis-8.10.2-Windows-x64-msys2"
$redisExe = "$redisDir\redis-server.exe"
$redisCli = "$redisDir\redis-cli.exe"

if (-not (Test-Path $redisExe)) {
    Write-Error "Redis binary not found at $redisExe. Please install via winget: winget install taizod1024.redis-windows-fork"
    exit 1
}

# Test if Redis is already running and answering PING
if (Test-Path $redisCli) {
    $existingPing = & $redisCli ping 2>$null
    if ($existingPing -match "PONG") {
        Write-Host "Redis server is already running on port $redisPort. [PONG received]" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Starting Redis server on port $redisPort..." -ForegroundColor Cyan
Start-Process -FilePath $redisExe -WindowStyle Hidden
Start-Sleep -Seconds 1

if (Test-Path $redisCli) {
    $testPing = & $redisCli ping 2>$null
    if ($testPing -match "PONG") {
        Write-Host "Redis Server started successfully! [PONG received]" -ForegroundColor Green
        exit 0
    }
}

Write-Warning "Redis Server launched. Verifying connection..."
