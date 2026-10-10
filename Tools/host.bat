@echo off
setlocal
rem Hosts a playtest: runs CoopGame as a listen server on L_Site01.
rem Usage: Tools\host.bat
rem If Unreal isn't in the default folder, first run: set UE_ROOT=D:\Path\To\UE_5.8

if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "UE_EDITOR=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EDITOR%" goto :no_engine

set "PROJECT="
for %%F in ("%~dp0..\*.uproject") do set "PROJECT=%%~fF"
if not defined PROJECT goto :no_project

set "COMMIT=unknown"
for /f %%H in ('git -C "%~dp0.." rev-parse --short HEAD 2^>nul') do set "COMMIT=%%H"

echo Hosting %PROJECT% at commit %COMMIT%
echo.
echo Players join with:  Tools\join.bat IP  or  Tools/join.command IP
echo A 4th player here:  Tools\join.bat 127.0.0.1
echo.
echo This PC's addresses:
ipconfig | findstr /c:"IPv4"
echo.
echo If the Macs can't connect, allow Unreal Editor through Windows Firewall on private networks.

start "CoopGame host" "%UE_EDITOR%" "%PROJECT%" "/Game/Maps/L_Site01?listen" -game -DisablePython -windowed -ResX=1280 -ResY=720 -log
exit /b 0

:no_engine
echo Unreal Editor not found at "%UE_EDITOR%".
echo If Unreal 5.8 is installed elsewhere, first run: set UE_ROOT=D:\Path\To\UE_5.8
exit /b 1

:no_project
echo No .uproject in the repo root. Pull the latest main first.
exit /b 1
