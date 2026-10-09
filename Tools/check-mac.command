#!/bin/bash
# Checks that this Mac is ready for a Co-op Game session.
# Usage: Tools/check-mac.command, or double-click it in Finder.
# If Unreal isn't in the default folder: UE_ROOT=/path/to/UE_5.8 Tools/check-mac.command

ENGINE_VERSION="5.8.3"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UE_ROOT="${UE_ROOT:-/Users/Shared/Epic Games/UE_5.8}"

problems=0
ok()   { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
fix()  { printf '  \033[31mFIX\033[0m   %s\n' "$1"; [ -n "$2" ] && printf '        %s\n' "$2"; problems=$((problems + 1)); }
note() { printf '  \033[33mNOTE\033[0m  %s\n' "$1"; [ -n "$2" ] && printf '        %s\n' "$2"; }

echo "Co-op Game setup check for this Mac"
echo

# macOS: Unreal 5.8 needs 14.5 or later.
os="$(sw_vers -productVersion)"
os_major="${os%%.*}"
os_rest="${os#*.}"
os_minor="${os_rest%%.*}"
[ "$os_rest" = "$os" ] && os_minor=0
if [ "$os_major" -gt 14 ] || { [ "$os_major" -eq 14 ] && [ "$os_minor" -ge 5 ]; }; then
  ok "macOS $os"
else
  fix "macOS $os" "Unreal 5.8 needs macOS 14.5 or later."
fi

if [ "$(uname -m)" = "arm64" ]; then
  ok "Apple Silicon ($(sysctl -n machdep.cpu.brand_string))"
else
  note "Intel Mac" "Unreal 5.8 runs much better on Apple Silicon."
fi

# Unreal Engine, pinned to one exact version for the whole team.
build_version="$UE_ROOT/Engine/Build/Build.version"
engine_installed=0
if [ -f "$build_version" ]; then
  engine_installed=1
  v_major="$(sed -n 's/.*"MajorVersion": *\([0-9]*\).*/\1/p' "$build_version")"
  v_minor="$(sed -n 's/.*"MinorVersion": *\([0-9]*\).*/\1/p' "$build_version")"
  v_patch="$(sed -n 's/.*"PatchVersion": *\([0-9]*\).*/\1/p' "$build_version")"
  installed="$v_major.$v_minor.$v_patch"
  if [ "$installed" = "$ENGINE_VERSION" ]; then
    ok "Unreal Engine $installed"
  else
    fix "Unreal Engine $installed is installed, but the team is pinned to $ENGINE_VERSION" "Update it in the Epic Games Launcher (Unreal Engine > Library)."
  fi
else
  fix "Unreal Engine $ENGINE_VERSION not found in $UE_ROOT" "Install it from the Epic Games Launcher (Unreal Engine > Library > +). If it's somewhere else, run: UE_ROOT=/path/to/UE_5.8 $0"
fi

# Disk: the engine needs a lot of room; after it's installed, the project and shader cache still need some.
free_gb="$(df -g / | awk 'NR == 2 { print $4 }')"
if [ "$engine_installed" -eq 1 ]; then needed_gb=30; else needed_gb=100; fi
if [ "$free_gb" -ge "$needed_gb" ]; then
  ok "$free_gb GB free on disk"
else
  fix "Only $free_gb GB free on disk" "Free up space until about $needed_gb GB is free."
fi

# Xcode: Epic lists 26.0 as the minimum and 26.1.1 as recommended, and says 26.4 is not compatible with Unreal 5.8.
if xcode_line="$(xcodebuild -version 2>/dev/null | head -n 1)" && [ -n "$xcode_line" ]; then
  xv="${xcode_line#Xcode }"
  x_major="${xv%%.*}"
  x_rest="${xv#*.}"
  x_minor="${x_rest%%.*}"
  [ "$x_rest" = "$xv" ] && x_minor=0
  if [ "$x_major" -eq 26 ] && [ "$x_minor" -le 3 ]; then
    ok "Xcode $xv"
  elif [ "$x_major" -eq 26 ] && [ "$x_minor" -eq 4 ]; then
    fix "Xcode $xv" "Epic lists Xcode 26.4 as incompatible with Unreal 5.8. Install 26.1.1 (recommended) to 26.3."
  elif [ "$x_major" -lt 26 ]; then
    fix "Xcode $xv" "Unreal 5.8 needs Xcode 26.0 or later. Install 26.1.1 (recommended) to 26.3."
  else
    note "Xcode $xv" "Epic hasn't listed this version for Unreal 5.8. If shaders fail to compile, switch to 26.1.1 to 26.3."
  fi
elif [ -d /Applications/Xcode.app ]; then
  fix "Xcode is installed but not selected" "Run: sudo xcode-select -s /Applications/Xcode.app && sudo xcodebuild -license accept"
else
  fix "Xcode not found" "Install Xcode 26.1.1 (recommended) to 26.3 from developer.apple.com/download, and open it once."
fi

# Metal toolchain: Unreal compiles Mac shaders with it, and Xcode 26 no longer installs it by default.
if xcrun -sdk macosx metal --version >/dev/null 2>&1; then
  ok "Metal toolchain"
else
  fix "Metal toolchain missing" "Run: xcodebuild -downloadComponent MetalToolchain"
fi

# Git LFS
if git lfs version >/dev/null 2>&1; then
  if git config --get filter.lfs.process >/dev/null 2>&1; then
    ok "Git LFS $(git lfs version | sed -n 's|^git-lfs/\([^ ]*\).*|\1|p')"
  else
    fix "Git LFS is installed but not set up" "Run: git lfs install"
  fi
else
  fix "Git LFS not installed" "Run: brew install git-lfs && git lfs install"
fi

# Claude Code drives the editor through Unreal MCP.
if command -v claude >/dev/null 2>&1; then
  ok "Claude Code"
else
  note "Claude Code not found" "You need it, or another MCP client, to drive the editor. See docs/mcp.md."
fi

# The repo itself.
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
  GIT_TERMINAL_PROMPT=0 git -C "$ROOT" fetch --quiet origin main 2>/dev/null
  behind="$(git -C "$ROOT" rev-list --count HEAD..origin/main 2>/dev/null)"
  if [ "$branch" = "main" ] && [ "$behind" = "0" ]; then
    ok "Repo on main and up to date"
  else
    note "Repo on $branch, ${behind:-?} commits behind origin/main" "Run: git checkout main && git pull --rebase"
  fi
  if [ -z "$(find "$ROOT" -maxdepth 1 -name '*.uproject')" ]; then
    note "No Unreal project in the repo yet" "Windows creates it at the start of Sprint 0 (HC-0)."
  fi
else
  fix "$ROOT is not a Git repo" "Clone it: git clone https://github.com/StretchGaming/Co-op-Game"
fi

echo
if [ "$problems" -eq 0 ]; then
  echo "Ready for Sprint 0."
else
  echo "$problems thing(s) to fix before Sprint 0."
fi
[ "$problems" -eq 0 ]
