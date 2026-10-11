@echo off
setlocal
rem Host the six-round adventure; clients use Tools\join.bat IP.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch_preview\launch.ps1" host /Game/Puzzles/Test/SixRound/L_SixRound_Test %*
exit /b %errorlevel%
