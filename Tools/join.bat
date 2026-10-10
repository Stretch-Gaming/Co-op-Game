@echo off
setlocal
rem Joins a playtest. Usage: Tools\join.bat HOST_IP
rem Use 127.0.0.1 for a second client on the host PC.
rem If Unreal isn't in the default folder, first run: set UE_ROOT=D:\Path\To\UE_5.8

set "HOST_IP=%~1"
if "%HOST_IP%"=="" set /p "HOST_IP=Host IP: "
if "%HOST_IP%"=="" goto :no_host

if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "UE_EDITOR=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EDITOR%" goto :no_engine

set "PROJECT="
for %%F in ("%~dp0..\*.uproject") do set "PROJECT=%%~fF"
if not defined PROJECT goto :no_project

set "COMMIT=unknown"
for /f %%H in ('git -C "%~dp0.." rev-parse --short HEAD 2^>nul') do set "COMMIT=%%H"

echo Joining %HOST_IP% from commit %COMMIT%. The host's commit must match.
start "CoopGame client" "%UE_EDITOR%" "%PROJECT%" %HOST_IP% -game -DisablePython -windowed -ResX=1280 -ResY=720 -log
exit /b 0

:no_host
echo No host IP given. Usage: Tools\join.bat HOST_IP
exit /b 1

:no_engine
echo Unreal Editor not found at "%UE_EDITOR%".
echo If Unreal 5.8 is installed elsewhere, first run: set UE_ROOT=D:\Path\To\UE_5.8
exit /b 1

:no_project
echo No .uproject in the repo root. Pull the latest main first.
exit /b 1
