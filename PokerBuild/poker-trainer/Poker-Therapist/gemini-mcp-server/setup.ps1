#!/usr/bin/env pwsh
# Quick setup script for Gemini MCP Server

Write-Host "🚀 Gemini MCP Server - Quick Setup" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js version..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Choose authentication method:" -ForegroundColor Yellow
Write-Host "1. Use Google AI API Key (Recommended - Simpler)"
Write-Host "2. Use Google Cloud Application Default Credentials"
Write-Host ""

$choice = Read-Host "Enter choice (1 or 2)"

$envFile = "C:\Users\mfane\gemini-mcp-server\.env"
$configFile = "C:\Users\mfane\AppData\Roaming\github-copilot\config.json"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "📋 Steps to get API key:" -ForegroundColor Cyan
    Write-Host "1. Visit https://aistudio.google.com/apikey"
    Write-Host "2. Sign in with Google"
    Write-Host "3. Click 'Create API Key'"
    Write-Host "4. Copy the key"
    Write-Host ""
    
    $apiKey = Read-Host "Paste your Google AI API key here"
    
    # Update .env
    @"
# Google AI API Key
GOOGLE_API_KEY=$apiKey

# MCP Server Configuration
LOG_LEVEL=info
"@ | Set-Content $envFile
    
    # Update config.json
    @"
{
  "mcpServers": {
    "gemini": {
      "command": "node",
      "args": ["C:\\Users\\mfane\\gemini-mcp-server\\src\\index.js"],
      "env": {
        "GOOGLE_API_KEY": "$apiKey"
      }
    }
  }
}
"@ | Set-Content $configFile
    
    Write-Host "✅ Configuration updated with API key" -ForegroundColor Green
    
} else {
    Write-Host ""
    Write-Host "Using Google Cloud credentials..." -ForegroundColor Yellow
    Write-Host "⚠️  Make sure to enable the Generative Language API:" -ForegroundColor Yellow
    Write-Host "   https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=gen-lang-client-0928153103"
    Write-Host ""
    
    # .env already set up for ADC
    Write-Host "✅ Configuration set for Application Default Credentials" -ForegroundColor Green
}

Write-Host ""
Write-Host "Testing server..." -ForegroundColor Yellow
Write-Host ""

Set-Location "C:\Users\mfane\gemini-mcp-server"

$process = Start-Process -FilePath "node" -ArgumentList "src\index.js" -PassThru -NoNewWindow -RedirectStandardError "test-output.log"
Start-Sleep -Seconds 3

if (!$process.HasExited) {
    Stop-Process -Id $process.Id -Force
    $output = Get-Content "test-output.log" -Raw
    
    if ($output -match "Server running") {
        Write-Host "✅ Server test successful!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Server started but check logs:" -ForegroundColor Yellow
        Write-Host $output
    }
    
    Remove-Item "test-output.log" -ErrorAction SilentlyContinue
} else {
    Write-Host "❌ Server failed to start. Check configuration." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Close and reopen your terminal"
Write-Host "2. The Gemini models will be available through MCP tools"
Write-Host "3. For iPhone: Install GitHub Copilot app and sign in"
Write-Host ""
Write-Host "Documentation: C:\Users\mfane\gemini-mcp-server\README.md" -ForegroundColor Gray
