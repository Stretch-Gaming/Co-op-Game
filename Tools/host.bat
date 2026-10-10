@echo off
setlocal
rem Usage: Tools\host.bat [/Game/Maps/MapName] [--dry-run]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_preview\launch.ps1" host %*
exit /b %errorlevel%
