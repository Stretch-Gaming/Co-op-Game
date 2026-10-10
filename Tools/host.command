#!/bin/bash
# Hosts a playtest from this Mac: runs CoopGame as a listen server on L_Site01.
# Usage: Tools/host.command, or double-click it in Finder.
# If Unreal isn't in the default folder: UE_ROOT=/path/to/UE_5.8 Tools/host.command

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
UE_EDITOR="$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"

if [ ! -x "$UE_EDITOR" ]; then
  echo "Unreal Editor not found at: $UE_EDITOR"
  echo "If Unreal 5.8 is installed elsewhere, run: UE_ROOT=/path/to/UE_5.8 $0"
  exit 1
fi

PROJECT="$(find "$ROOT" -maxdepth 1 -name '*.uproject' | head -n 1)"
if [ -z "$PROJECT" ]; then
  echo "No .uproject in $ROOT. Pull the latest main first."
  exit 1
fi

IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)"
[ -n "$IP" ] || IP="<this Mac's IP>"
echo "Hosting $(basename "$PROJECT") at commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "Players join with:  Tools/join.command $IP  or  Tools\\join.bat $IP"
echo "If macOS asks whether Unreal Editor may accept incoming connections, choose Allow."
exec "$UE_EDITOR" "$PROJECT" "/Game/Maps/L_Site01?listen" -game -DisablePython -windowed -ResX=1280 -ResY=720 -log
