@echo off
setlocal
rem Usage: Tools\play-connected.bat [--dry-run]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_preview\launch.ps1" preview %*
exit /b %errorlevel%
