Set-Location "C:\PokerBuild\poker-trainer"
Write-Host "Starting build at $(Get-Date)" -ForegroundColor Cyan
Write-Host "Command: npx electron-builder --win portable" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

try {
    & npx electron-builder --win portable 2>&1
    Write-Host "`n=========================================" -ForegroundColor Cyan
    Write-Host "Build completed at $(Get-Date)" -ForegroundColor Green
}
catch {
    Write-Host "`n=========================================" -ForegroundColor Red
    Write-Host "Build failed at $(Get-Date)" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

# Find the latest executable
Write-Host "`nLooking for output executables..." -ForegroundColor Cyan
Get-ChildItem -Path "C:\PokerBuild\poker-trainer" -Recurse -Filter "Poker*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | ForEach-Object {
    Write-Host "Found: $($_.FullName)" -ForegroundColor Yellow
    Write-Host "  Size: $([math]::Round($_.Length/1MB,2)) MB" -ForegroundColor Yellow
    Write-Host "  Modified: $($_.LastWriteTime)" -ForegroundColor Yellow
}
