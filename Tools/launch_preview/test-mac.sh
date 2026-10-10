#!/bin/bash
# Uses synthetic fixtures and dry-run only; works on macOS and Git Bash.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
fixture="$(mktemp -d "${TMPDIR:-/tmp}/Co op launcher test.XXXXXX")"
trap 'rm -rf -- "$fixture"' EXIT
mkdir -p "$fixture/Tools/launch_preview" "$fixture/Content/Maps" "$fixture/Engine install with spaces/Engine/Build" "$fixture/Engine install with spaces/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS"
cp "$HERE/launch.sh" "$fixture/Tools/launch_preview/"
cp "$HERE/../host.command" "$HERE/../play-connected.command" "$fixture/Tools/"
printf '{}\n' > "$fixture/CoopGame.uproject"
printf 'synthetic map fixture\n' > "$fixture/Content/Maps/L_Site01.umap"
printf 'synthetic map fixture\n' > "$fixture/Content/Maps/L_ConnectedRoomMaze.umap"
export UE_ROOT="$fixture/Engine install with spaces"
build="$UE_ROOT/Engine/Build/Build.version"
printf '{"MajorVersion":5,"MinorVersion":8,"PatchVersion":3}\n' > "$build"
editor="$UE_ROOT/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor"
printf '#!/bin/bash\nexit 99\n' > "$editor"
chmod +x "$editor"
tests=0
check() {
 local expected="$1" needle="$2" script="$3" result output
 shift 3
 result=0
 output="$(bash "$fixture/Tools/$script" "$@" 2>&1)" || result=$?
 [ "$result" -eq "$expected" ] || { printf 'FAIL exit: %s\n' "$output"; exit 1; }
 [[ "$output" == *"$needle"* ]] || { printf 'FAIL output: %s\n' "$output"; exit 1; }
 tests=$((tests+1))
}
check 0 '/Game/Maps/L_ConnectedRoomMaze' play-connected.command --dry-run
check 0 "ARG: $fixture/CoopGame.uproject" play-connected.command --dry-run
check 0 'ARG: -DisablePython' play-connected.command --dry-run
check 0 'at commit unknown' play-connected.command --dry-run
check 0 '/Game/Maps/L_Site01?listen' host.command --dry-run
check 0 '/Game/Maps/L_ConnectedRoomMaze?listen' host.command /Game/Maps/L_ConnectedRoomMaze --dry-run
check 0 '/Game/Maps/L_ConnectedRoomMaze?listen' host.command --dry-run /Game/Maps/L_ConnectedRoomMaze
check 1 'Map missing:' host.command /Game/Maps/Missing --dry-run
check 1 'Usage:' host.command /Game/../Maps/L_Site01 --dry-run
check 1 'Usage:' host.command '/Game/Maps/L_Site01?listen' --dry-run
check 1 'Usage:' play-connected.command /Game/Maps/L_Site01 --dry-run
printf 'version https://git-lfs.github.com/spec/v1\noid sha256:fixture\nsize 0\n' > "$fixture/Content/Maps/L_ConnectedRoomMaze.umap"
check 1 'Git LFS pointer:' play-connected.command --dry-run
printf '{"MajorVersion":5,"MinorVersion":8,"PatchVersion":2}\n' > "$build"
check 1 'requires 5.8.3' host.command --dry-run
export UE_ROOT="$fixture/Missing engine"
check 1 'Unreal 5.8.3 not found' host.command --dry-run
printf 'PASS: %s Mac launcher checks; no engine launched.\n' "$tests"
