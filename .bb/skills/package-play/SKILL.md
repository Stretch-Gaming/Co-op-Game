---
name: package-play
description: Build, cook, package and run this Co-op-Game checkout as a native Mac or Windows app. Use /package-play when asked to rebuild and play a packaged game, host or join packaged playtests, or inspect a packaging plan.
---

# Package and play Co-op-Game

Read root `AGENTS.md` and `Tools/packaged-play.md`. This command operates on
the current checkout's Blueprint-only `CoopGame.uproject`; its default map comes
from `Config/DefaultEngine.ini`'s `GameDefaultMap`. Main currently selects the
six-round candidate `/Game/Puzzles/Test/SixRound/L_SixRound_Test`; it is an
isolated combined assembly with team acceptance still open. The separate `Prototypes/CoopCave` project has different
rules and is outside this command's scope. For a connected environment preview,
use `--map /Game/Maps/L_ConnectedRoomMaze` and label the result as a preview.

An invocation authorizes the requested local build and game launch. Run the
workflow through `Tools/package_game.py`, using Python 3.9+ on the target
machine. With no arguments, build and launch a Development package. Map requests
to `--build-only`, `--dry-run`, `--mode host`, or `--mode join --address HOST`.
Use `--launch-only <build-receipt.json>` when the user wants another instance of
an existing package; print that package's recorded commit, which may be older
than the checkout. Pass arguments as an argv array, never interpolate them into
a shell command.

Run long builds in a visible persistent BB terminal, scoped to the current
thread: `bb terminal create --thread <current-thread-id> --title "Packaged game"
-- python3 Tools/package_game.py <options>` (Windows: `py -3`). Inspect bounded
terminal output and report meaningful build progress. A normal invocation must
continue from packaging into launch; a dry run is sufficient only when requested
or when a concrete prerequisite blocks execution.

Before starting, identify the checkout/commit, save-dependent inputs and other
active work. Ask the editor owner to save only if unsaved content is known to be
required; do not close or save another person's editor. UAT cooks saved assets
with an internal headless commandlet and launches the archived game executable.
It opens no GUI editor. Preserve the main project's Blueprint-only contract:
UAT may generate temporary targets in `Intermediate/Source`, but do not add
gameplay C++, root `Source/`, plugins or Config changes to make packaging pass.

Use the script's exact 5.8.3, map, LFS and disk checks. If blocked, diagnose the
first actionable failure and give the precise remedy. Never silently fall back
to `UnrealEditor -game` or an earlier build. Do not delete another thread's cache
or packages to free disk. Packaging doesn't publish, commit, push, merge, update
issues, or prove multiplayer acceptance.

Report the packaged app, full commit and dirty-input qualification, platform,
build/launch receipts and logs with clickable links. Distinguish package success,
process launch, rendered startup and actual tested gameplay. Network play uses
packages built on each native platform from the same clean commit and settings;
follow the repo's rule against mixing packaged and `-game` instances. This local
run does not replace the lane's client, split-screen or full-route acceptance.
