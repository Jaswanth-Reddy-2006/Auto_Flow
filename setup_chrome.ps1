# AutoFlow Chrome Setup Utility
# This script helps link your Chrome browser to the AutoFlow Assistant.

$CHROME_EXE = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $CHROME_EXE)) {
    $CHROME_EXE = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   AutoFlow Browser Setup Utility" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Choose how you want to link your browser:"
Write-Host "1. [DEFAULT] Create a dedicated AutoFlow Profile (Safe, remembers logins)"
Write-Host "2. [ADVANCED] Link your main Chrome profile (Requires restarting Chrome)"
Write-Host "3. Check current status"
Write-Host ""

$choice = Read-Host "Select an option (1-3)"

if ($choice -eq "1") {
    Write-Host ">>> Creating dedicated profile directory..." -ForegroundColor Green
    $profilePath = Join-Path (Get-Location) "autoflow_chrome_profile"
    if (-not (Test-Path $profilePath)) { New-Item -ItemType Directory -Path $profilePath }
    
    Write-Host ">>> Launching AutoFlow Browser. Please login to YouTube/WhatsApp here." -ForegroundColor Yellow
    Write-Host "NOTE: This browser will remember your logins forever." -ForegroundColor Gray
    Start-Process $CHROME_EXE -ArgumentList "--user-data-dir='$profilePath'", "--remote-debugging-port=9222", "--no-first-run"
}
elseif ($choice -eq "2") {
    Write-Host "!!! This will close and restart your main Chrome with Debugging enabled. !!!" -ForegroundColor Red
    $confirm = Read-Host "Proceed? (y/n)"
    if ($confirm -eq "y") {
        Write-Host "Closing Chrome..." -ForegroundColor Yellow
        Stop-Process -Name "chrome" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        Write-Host ">>> Restarting your main Chrome with Automation Link..." -ForegroundColor Green
        Start-Process $CHROME_EXE -ArgumentList "--remote-debugging-port=9222", "--restore-last-session"
        Write-Host "DONE! Your primary browser is now linked to AutoFlow." -ForegroundColor Green
    }
}
elseif ($choice -eq "3") {
    Write-Host "Checking for Chrome debugging port (9222)..."
    $portCheck = Test-NetConnection -ComputerName localhost -Port 9222 -InformationLevel Quiet
    if ($portCheck) {
        Write-Host "✅ SUCCESS: Chrome is READY for AutoFlow." -ForegroundColor Green
    } else {
        Write-Host "❌ NOT LINKED: Run option 1 or 2 to link your browser." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Setup complete. You can now use AutoFlow to play music and automate tasks!" -ForegroundColor Cyan
