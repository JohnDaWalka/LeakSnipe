# Start LeakSnipe MCP + public tunnel for Grok chat connectors (grok.com).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\start-grok-mcp.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ServerPy = Join-Path $RepoRoot "mcp_grok_server.py"
$Cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$Port = 8001
$LogDir = Join-Path $env:TEMP "leaksnipe-grok-mcp"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $VenvPython)) { throw "Missing: $VenvPython" }
if (-not (Test-Path $ServerPy)) { throw "Missing: $ServerPy" }

function Stop-Port([int]$p) {
    Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Stop-Port $Port
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'serveo|localhost.run' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

$env:LEAKSNIPE_ROOT = $RepoRoot
$env:SQLITE_DB_PATH = (Join-Path $RepoRoot "poker_hands.db")
$mcp = Start-Process -FilePath $VenvPython -ArgumentList @($ServerPy) `
    -WorkingDirectory $RepoRoot -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $LogDir "mcp.out.log") `
    -RedirectStandardError (Join-Path $LogDir "mcp.err.log") -PassThru

$initPath = Join-Path $LogDir "init.json"
[System.IO.File]::WriteAllText($initPath,
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"Grok","version":"1"}}}')

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 400
    $code = & curl.exe -sS -o NUL -w "%{http_code}" --max-time 2 -X POST "http://127.0.0.1:$Port/mcp" `
        -H "Content-Type: application/json" -H "Accept: application/json" --data-binary "@$initPath" 2>$null
    if ($code -eq "200") { $ready = $true; break }
}
if (-not $ready) { throw "Local MCP failed. See $($LogDir)\mcp.err.log" }
Write-Host "Local MCP OK  http://127.0.0.1:$Port/mcp  (PID $($mcp.Id))"

# Prefer Cloudflare quick tunnel
if (-not (Test-Path $Cloudflared)) { throw "cloudflared missing: $Cloudflared" }
$cfErr = Join-Path $LogDir "cloudflared.err.log"
Remove-Item $cfErr -ErrorAction SilentlyContinue
$cf = Start-Process -FilePath $Cloudflared -ArgumentList @(
    "tunnel", "--url", "http://127.0.0.1:$Port", "--no-autoupdate", "--protocol", "http2"
) -WindowStyle Hidden -RedirectStandardError $cfErr -PassThru

$base = $null
for ($i = 0; $i -lt 50; $i++) {
    Start-Sleep -Milliseconds 400
    if (Test-Path $cfErr) {
        $m = Select-String -Path $cfErr -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -Last 1
        if ($m -and $m.Line -match '(https://[a-z0-9-]+\.trycloudflare\.com)') {
            $base = $Matches[1]
            break
        }
    }
}
if (-not $base) { throw "No tunnel URL. See $cfErr" }

$url = "$base/mcp"
Set-Content (Join-Path $LogDir "public-url.txt") $url -Encoding utf8

for ($i = 0; $i -lt 25; $i++) {
    $code = & curl.exe -sS -o NUL -w "%{http_code}" --max-time 12 -X POST $url `
        -H "Content-Type: application/json" -H "Accept: application/json" --data-binary "@$initPath" 2>$null
    if ($code -eq "200") { break }
    Start-Sleep -Seconds 2
}
if ($code -ne "200") { throw "Public URL not ready: $url (HTTP $code)" }

if (Get-Command grok -ErrorAction SilentlyContinue) {
    try {
        & grok mcp remove leak-snipe 2>$null
        & grok mcp add --transport http leak-snipe $url 2>$null
    } catch {}
}

Write-Host ""
Write-Host "============================================"
Write-Host " PASTE THIS INTO GROK CONNECTORS:"
Write-Host " $url"
Write-Host "============================================"
Write-Host ""
Write-Host "1) Open https://grok.com/connectors"
Write-Host "2) Remove any old LeakSnipe / custom MCP connector"
Write-Host "3) New Connector -> Custom -> paste URL above (must end with /mcp)"
Write-Host "4) New chat -> enable connector"
Write-Host "5) Ask: list my poker databases and hands for Gboss101 and JohnDaWalka"
Write-Host ""
Write-Host "Keep this PC awake. Tunnel PID $($cf.Id)  MCP PID $($mcp.Id)"
Write-Host "URL also in: $LogDir\public-url.txt"
