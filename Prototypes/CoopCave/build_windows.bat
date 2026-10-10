@echo off
REM Compiles the CoopProto editor module on Windows.
REM Usage: double-click, or run from a terminal in this folder.
REM If it fails, copy the FIRST error line(s) and paste them to Claude.

if "%UE_ROOT%"=="" set UE_ROOT=C:\Program Files\Epic Games\UE_5.8

if not exist "%UE_ROOT%\Engine\Build\BatchFiles\Build.bat" (
  echo Unreal Engine not found at: %UE_ROOT%
  echo Install UE 5.8 from the Epic Games Launcher, or set UE_ROOT to your install folder.
  pause
  exit /b 1
)

call "%UE_ROOT%\Engine\Build\BatchFiles\Build.bat" CoopProtoEditor Win64 Development -Project="%~dp0CoopProto.uproject" -WaitMutex
pause
