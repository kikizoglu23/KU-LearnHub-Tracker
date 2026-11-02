@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\start_windows.ps1"
if errorlevel 1 pause
endlocal
