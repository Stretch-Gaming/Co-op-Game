#!/bin/bash
set -e
fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mode="${1:-}"
shift || fail 'Missing launcher mode.'
case "$mode" in
 host) map=/Game/Puzzles/Test/SixRound/L_SixRound_Test ;;
 preview) map=/Game/Maps/L_ConnectedRoomMaze ;;
 *) fail 'Unknown launcher mode.' ;;
esac
dry_run=0
map_given=0
for option in "$@"; do
 if [ "$option" = '--dry-run' ] && [ "$dry_run" -eq 0 ]; then
  dry_run=1
 elif [ "$mode" = host ] && [ "$map_given" -eq 0 ] && [[ "$option" =~ ^/Game/([A-Za-z0-9_]+/)*[A-Za-z0-9_]+$ ]]; then
  map="$option"
  map_given=1
 else
  fail 'Usage: host.command [/Game/Maps/MapName] [--dry-run], or play-connected.command [--dry-run]. Map names allow letters, numbers, underscores and slashes.'
 fi
done
PROJECT="$ROOT/CoopGame.uproject"
[ -f "$PROJECT" ] || fail "Project missing: $PROJECT. Pull the latest project first."
map_file="$ROOT/Content/${map#/Game/}.umap"
[ -f "$map_file" ] || fail "Map missing: $map_file. Pull the latest project and run git lfs pull."
if LC_ALL=C head -c 42 "$map_file" | LC_ALL=C grep -Fqx 'version https://git-lfs.github.com/spec/v1'; then
 fail "Map is a Git LFS pointer: $map_file. Run git lfs pull before playing."
fi
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"
UE_EDITOR="$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
build_version="$UE_ROOT/Engine/Build/Build.version"
[ -x "$UE_EDITOR" ] && [ -f "$build_version" ] || fail "Unreal 5.8.3 not found at $UE_ROOT. Set UE_ROOT to your Unreal installation folder."
read_version() { sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p" "$build_version"; }
installed="$(read_version MajorVersion).$(read_version MinorVersion).$(read_version PatchVersion)"
[ "$installed" = 5.8.3 ] || fail "Unreal $installed found; this project requires 5.8.3. Check UE_ROOT."
map_url="$map"
[ "$mode" != host ] || map_url="$map?listen"
args=("$PROJECT" "$map_url" -game -DisablePython -windowed -ResX=1280 -ResY=720 -log)
commit="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || printf unknown)"
printf 'Launching %s on %s with Unreal %s at commit %s\n' "$mode" "$map" "$installed" "$commit"
if [ "$dry_run" -eq 1 ]; then
 printf 'EXE: %s\n' "$UE_EDITOR"
 printf 'ARG: %s\n' "${args[@]}"
 exit 0
fi
if [ "$mode" = host ]; then
 IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
 printf 'Players join with Tools/join.command %s or Tools\\join.bat %s\n' "${IP:-IP}" "${IP:-IP}"
 echo 'Another player on this Mac: Tools/join.command 127.0.0.1.'
 echo 'If macOS asks whether Unreal Editor may accept incoming connections, choose Allow.'
fi
exec "$UE_EDITOR" "${args[@]}"
