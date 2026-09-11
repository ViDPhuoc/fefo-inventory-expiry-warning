$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $BackendDir
Write-Host "FastAPI dang chay tai http://localhost:8000" -ForegroundColor Green
Write-Host "Giu cua so nay trong luc demo. Nhan Ctrl+C de dung." -ForegroundColor Yellow
Write-Host ""
& $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Server da dung do loi. Kiem tra log o phia tren." -ForegroundColor Red
}
