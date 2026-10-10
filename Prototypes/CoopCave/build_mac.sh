#!/bin/bash
# Compiles the CoopProto editor module on a Mac.
# Usage: open Terminal in this folder and run:  bash build_mac.sh
# If it fails, copy the FIRST error line(s) and paste them to Claude.

PROJECT="$(cd "$(dirname "$0")" && pwd)/CoopProto.uproject"

is_engine() { [ -n "$1" ] && [ -f "$1/Engine/Build/BatchFiles/Mac/Build.sh" ]; }

# 1. Use UE_ROOT if it was set and is valid. Otherwise try the usual install spots.
if ! is_engine "$UE_ROOT"; then
  UE_ROOT=""
  for candidate in "$HOME/Documents/UE_5.8" "/Users/Shared/Epic Games/UE_5.8" "$HOME/Epic Games/UE_5.8" "/Applications/Epic Games/UE_5.8"; do
    if is_engine "$candidate"; then UE_ROOT="$candidate"; break; fi
  done
fi

# 2. Look one and two folders deep inside Documents (e.g. Documents/UE_5.8 or
#    Documents/Epic Games/UE_5.8), preferring a 5.8 install.
if [ -z "$UE_ROOT" ]; then
  FALLBACK=""
  for candidate in "$HOME"/Documents/*/ "$HOME"/Documents/*/*/; do
    candidate="${candidate%/}"
    if is_engine "$candidate"; then
      case "$candidate" in
        *5.8*) UE_ROOT="$candidate"; break ;;
        *) [ -z "$FALLBACK" ] && FALLBACK="$candidate" ;;
      esac
    fi
  done
  [ -z "$UE_ROOT" ] && UE_ROOT="$FALLBACK"
fi

# 3. Still not found: ask Spotlight where Unreal Editor is installed (prefers a 5.8 install).
if [ -z "$UE_ROOT" ]; then
  FOUND="$(mdfind -name UnrealEditor.app 2>/dev/null | grep '/Engine/Binaries/Mac/UnrealEditor.app$' | sed 's|/Engine/Binaries/Mac/UnrealEditor.app$||')"
  UE_ROOT="$(echo "$FOUND" | grep -m1 '5\.8')"
  [ -z "$UE_ROOT" ] && UE_ROOT="$(echo "$FOUND" | head -1)"
fi

if ! is_engine "$UE_ROOT"; then
  echo "Couldn't find Unreal Engine 5.8 on this Mac."
  echo "If you know the folder it's installed in, run:  UE_ROOT=\"/that/folder\" bash build_mac.sh"
  exit 1
fi

echo "Using Unreal Engine at: $UE_ROOT"
bash "$UE_ROOT/Engine/Build/BatchFiles/Mac/Build.sh" CoopProtoEditor Mac Development -project="$PROJECT" -waitmutex
