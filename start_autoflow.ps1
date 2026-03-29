# AutoFlow: Pro-Grade Master Launcher
# 🛠️ Ensures a zero-conflict environment, linked Chrome, and active AI brain.

Write-Host ">>> PHASE 1: System Sanitation..." -ForegroundColor Yellow
$apps = "python", "node", "electron", "chrome"
foreach ($app in $apps) { Stop-Process -Name $app -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

# Force clear Port 9222 and 8000
$ports = 9222, 8000
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue 
    if ($conn) {
        Write-Host ">>> Port $port busy. Evicted." -ForegroundColor Red
        $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
}

Write-Host ">>> PHASE 2: AI Brain Check (Ollama)..." -ForegroundColor Cyan
try {
    $ollama = ollama list
    Write-Host ">>> Ollama is ONLINE." -ForegroundColor Green
} catch {
    Write-Host ">>> WARNING: Ollama is OFFLINE. Starting Ollama..." -ForegroundColor Red
    Start-Process "ollama" -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 5
}

Write-Host ">>> PHASE 3: Launching Linked Chrome session..." -ForegroundColor Blue
$CHROME_EXE = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $CHROME_EXE)) { $CHROME_EXE = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" }
Start-Process $CHROME_EXE -ArgumentList "--remote-debugging-port=9222", "--restore-last-session"
Start-Sleep -Seconds 5

Write-Host ">>> PHASE 4: Initializing AutoFlow Intelligence..." -ForegroundColor Magenta
if (!(Test-Path "outputs")) { New-Item -ItemType Directory "outputs" }
# Start backend in background with consolidated log redirection
$backendLog = "outputs/backend.log"
Start-Process ".\venv\Scripts\python.exe" -ArgumentList "main.py" -NoNewWindow -RedirectStandardOutput $backendLog -RedirectStandardError "outputs/error.log"

# Wait for Backend Ping
Write-Host ">>> Waiting for Backend..." -NoNewline
for ($i=0; $i -lt 15; $i++) {
    try {
        $check = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get -TimeoutSec 1
        if ($check.status -eq "online") { Write-Host " ONLINE." -ForegroundColor Green; break }
    } catch { Write-Host "." -NoNewline; Start-Sleep -Seconds 1 }
}

Write-Host ">>> PHASE 5: Launching Pro UI Context..." -ForegroundColor Green
Set-Location ui
# Auto-open the browser to the UI once vite is ready
Start-Process "http://localhost:5173"
npm run dev
