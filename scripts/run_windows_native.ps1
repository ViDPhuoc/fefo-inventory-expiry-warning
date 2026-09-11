$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$FrontendIndex = Join-Path $FrontendDir "dist\index.html"
$Requirements = Join-Path $BackendDir "requirements.txt"
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$EnvFile = Join-Path $ProjectRoot ".env"
$DatabaseName = "canhbao_hethan_demo"
$DatabaseHost = "127.0.0.1"
$DatabasePort = "5432"

function Stop-WithMessage {
    param([string]$Message)
    Write-Host ""
    Write-Host "LOI: $Message" -ForegroundColor Red
    Write-Host "Khong mo localhost luc nay. Kiem tra thong bao loi o phia tren." -ForegroundColor Yellow
    Read-Host "Nhan Enter de dong"
    exit 1
}

function Test-DemoWebsite {
    try {
        $Health = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2
        return $Health.status -eq "ok"
    }
    catch {
        return $false
    }
}

try {
    if (Test-DemoWebsite) {
        Write-Host "Website dang chay. Dang mo http://localhost:8000" -ForegroundColor Green
        Start-Process "http://localhost:8000"
        exit 0
    }

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        Stop-WithMessage "Khong tim thay Python trong PATH. May nay can Python 3.11 tro len."
    }
    $PythonVersion = (& $PythonCommand.Source --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $PythonVersion -notmatch '^Python 3\.\d+') {
        Stop-WithMessage "Khong doc duoc phien ban Python: $PythonVersion"
    }
    $PythonMinor = [int]([regex]::Match($PythonVersion, '^Python 3\.(\d+)').Groups[1].Value)
    if ($PythonMinor -lt 11) {
        Stop-WithMessage "Can Python 3.11 tro len; dang tim thay $PythonVersion."
    }
    Write-Host "[1/7] Python hop le: $PythonVersion" -ForegroundColor Cyan

    $PsqlCommand = Get-Command psql -ErrorAction SilentlyContinue
    if (-not $PsqlCommand) {
        Stop-WithMessage "Khong tim thay psql. Can PostgreSQL 16 va psql trong PATH."
    }
    $PsqlVersion = (& $PsqlCommand.Source --version 2>&1 | Out-String).Trim()
    Write-Host "[2/7] PostgreSQL client: $PsqlVersion" -ForegroundColor Cyan

    $DatabaseUser = Read-Host "Nhap PostgreSQL user (Enter de dung postgres)"
    if ([string]::IsNullOrWhiteSpace($DatabaseUser)) {
        $DatabaseUser = "postgres"
    }
    $SecurePassword = Read-Host "Nhap mat khau PostgreSQL cua user $DatabaseUser" -AsSecureString
    $Credential = New-Object System.Management.Automation.PSCredential($DatabaseUser, $SecurePassword)
    $PlainPassword = $Credential.GetNetworkCredential().Password
    $env:PGPASSWORD = $PlainPassword
    $env:PGCLIENTENCODING = "UTF8"

    $ConnectionCheck = (& $PsqlCommand.Source -X -w -h $DatabaseHost -p $DatabasePort -U $DatabaseUser -d postgres -tAc "SELECT 1" 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $ConnectionCheck -notmatch '1') {
        Stop-WithMessage "Khong ket noi duoc PostgreSQL localhost:5432. Chi tiet: $ConnectionCheck"
    }
    Write-Host "[3/7] Da ket noi PostgreSQL." -ForegroundColor Cyan

    $DatabaseExists = (& $PsqlCommand.Source -X -w -h $DatabaseHost -p $DatabasePort -U $DatabaseUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DatabaseName'" 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Khong kiem tra duoc database: $DatabaseExists"
    }
    if ($DatabaseExists -ne "1") {
        $CreateResult = (& $PsqlCommand.Source -X -w -h $DatabaseHost -p $DatabasePort -U $DatabaseUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $DatabaseName" 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Khong tao duoc database $DatabaseName. Chi tiet: $CreateResult"
        }
        Write-Host "Da tao database $DatabaseName." -ForegroundColor Green
    }
    else {
        Write-Host "Database $DatabaseName da co; giu nguyen." -ForegroundColor Green
    }

    if (-not (Test-Path $FrontendIndex)) {
        $NpmCommand = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $NpmCommand) {
            Stop-WithMessage "Chua co frontend build va khong tim thay npm. Hay cai Node.js 22 roi chay lai."
        }
        Write-Host "[4/7] Dang cai thu vien va build frontend..." -ForegroundColor Cyan
        Push-Location $FrontendDir
        try {
            & $NpmCommand.Source ci
            if ($LASTEXITCODE -ne 0) {
                Stop-WithMessage "npm ci that bai. Kiem tra Node.js va Internet."
            }
            & $NpmCommand.Source run build
            if ($LASTEXITCODE -ne 0) {
                Stop-WithMessage "Build frontend that bai. Kiem tra loi Vite o phia tren."
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "[4/7] Frontend da san sang." -ForegroundColor Cyan
    }

    $EncodedUser = [System.Uri]::EscapeDataString($DatabaseUser)
    $EncodedPassword = [System.Uri]::EscapeDataString($PlainPassword)
    $EnvironmentText = @(
        "DATABASE_URL=postgresql://$EncodedUser`:$EncodedPassword@$DatabaseHost`:$DatabasePort/$DatabaseName",
        "APP_TODAY=",
        "CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173"
    ) -join [Environment]::NewLine
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($EnvFile, $EnvironmentText, $Utf8NoBom)

    if (-not (Test-Path $VenvPython)) {
        Write-Host "[5/7] Dang tao moi truong Python .venv..." -ForegroundColor Cyan
        & $PythonCommand.Source -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Khong tao duoc .venv."
        }
    }

    $RequirementHash = (Get-FileHash $Requirements -Algorithm SHA256).Hash
    $RequirementMarker = Join-Path $VenvDir "requirements.sha256"
    $InstalledHash = if (Test-Path $RequirementMarker) {
        (Get-Content $RequirementMarker -Raw).Trim()
    }
    else {
        ""
    }
    if ($InstalledHash -ne $RequirementHash) {
        Write-Host "[5/7] Dang cai thu vien Python. Lan dau co the mat vai phut..." -ForegroundColor Cyan
        & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Cai thu vien Python that bai. Kiem tra Internet va phan loi pip o tren."
        }
        [System.IO.File]::WriteAllText($RequirementMarker, $RequirementHash, $Utf8NoBom)
    }
    else {
        Write-Host "[5/7] Thu vien Python da san sang." -ForegroundColor Cyan
    }

    Write-Host "[6/7] Dang tao bang va chi nap du lieu neu database trong..." -ForegroundColor Cyan
    Push-Location $BackendDir
    try {
        & $VenvPython -m app.cli ensure-demo
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Tao bang/nap du lieu that bai. Xem chi tiet o tren."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "[7/7] Dang khoi dong FastAPI..." -ForegroundColor Cyan
    $ServerScript = Join-Path $PSScriptRoot "start_server_windows.ps1"
    $ServerArguments = "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$ServerScript`""
    Start-Process powershell.exe -WorkingDirectory $BackendDir -ArgumentList $ServerArguments | Out-Null

    $Ready = $false
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        Start-Sleep -Seconds 2
        if (Test-DemoWebsite) {
            $Ready = $true
            break
        }
    }
    if (-not $Ready) {
        Stop-WithMessage "FastAPI khong san sang sau 60 giay. Xem loi trong cua so PowerShell server moi."
    }

    Write-Host "" 
    Write-Host "THANH CONG: http://localhost:8000" -ForegroundColor Green
    Write-Host "Manager: manager1 / Demo@2026"
    Write-Host "Staff:   staff1   / Demo@2026"
    Write-Host "Giu cua so server moi dang mo. Ctrl+C trong cua so do de dung web."
    Start-Process "http://localhost:8000"
    Start-Sleep -Seconds 2
    exit 0
}
catch {
    Stop-WithMessage $_.Exception.Message
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
