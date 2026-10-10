@echo off
setlocal
rem Runs the procedural cave using Unreal's built-in empty map.
if not defined UE_ROOT set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "UE_EDITOR=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EDITOR%" (
  echo Unreal Engine not found at: %UE_EDITOR%
  exit /b 1
)
if not exist "%~dp0Binaries\Win64\UnrealEditor-CoopProto.dll" (
  echo Build the prototype first with build_windows.bat.
  exit /b 1
)
start "CoopProto cave" "%UE_EDITOR%" "%~dp0CoopProto.uproject" "/Engine/Maps/Entry?game=/Script/CoopProto.CoopGameMode" -game -DisablePython -windowed -ResX=1600 -ResY=900 -log
exit /b 0
