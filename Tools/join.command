#!/bin/bash
# Joins a playtest. Usage: Tools/join.command HOST_IP
# Double-click it in Finder to be asked for the IP instead.
# If Unreal isn't in the default folder: UE_ROOT=/path/to/UE_5.8 Tools/join.command HOST_IP

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
UE_EDITOR="$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"

HOST_IP="$1"
if [ -z "$HOST_IP" ]; then
  read -r -p "Host IP: " HOST_IP
fi
if [ -z "$HOST_IP" ]; then
  echo "No host IP given. Usage: Tools/join.command HOST_IP"
  exit 1
fi

if [ ! -x "$UE_EDITOR" ]; then
  echo "Unreal Editor not found at: $UE_EDITOR"
  echo "If Unreal 5.8 is installed elsewhere, run: UE_ROOT=/path/to/UE_5.8 $0 $HOST_IP"
  exit 1
fi

PROJECT="$(find "$ROOT" -maxdepth 1 -name '*.uproject' | head -n 1)"
if [ -z "$PROJECT" ]; then
  echo "No .uproject in $ROOT. Pull the latest main first."
  exit 1
fi

echo "Joining $HOST_IP from commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown). The host's commit must match."
exec "$UE_EDITOR" "$PROJECT" "$HOST_IP" -game -windowed -ResX=1280 -ResY=720 -log
