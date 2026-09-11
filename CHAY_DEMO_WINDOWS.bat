@echo off
setlocal
cd /d "%~dp0"
title Canh bao het han - Chay truc tiep tren Windows

echo ======================================================
echo   CANH BAO HET HAN - KHONG DOCKER, KHONG WSL
echo ======================================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run_windows_native.ps1"
if errorlevel 1 (
  echo.
  echo Chua khoi dong duoc. Doc loi phia tren hoac gui anh cua so nay.
  pause
)
