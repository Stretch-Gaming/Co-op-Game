# Packaged play

In BB, use **`/package-play`** to rebuild and play the current Blueprint game as
a native Development app. Use the [repo PR template](../.github/pull_request_template.md)
and [team handoff guide](../docs/pull-requests.md) to describe the delivery.
Project skills live in `.bb/skills/`; fresh BB threads discover them after pull.
These workflows are shared by HC, PG and HZ and do not change lane ownership.
The default map follows `GameDefaultMap` in `Config/DefaultEngine.ini`. Main
currently opens `/Game/Puzzles/Test/SixRound/L_SixRound_Test`, the combined
six-round candidate; full team acceptance is still open. Specify `--map` to
select a different saved map. An existing package defaults to its receipt's map.

From a terminal in the repository:

```sh
# Mac: rebuild, cook, package, launch
bash Tools/package-play.command
# Inspect the plan without building, launching or writing files
bash Tools/package-play.command --dry-run
# Host the adventure, or just package it
bash Tools/package-play.command --mode host
bash Tools/package-play.command --build-only
# Connected environment preview (different map from the production adventure)
bash Tools/package-play.command --map /Game/Maps/L_ConnectedRoomMaze
```

On Windows, use `Tools\package-play.bat` with the same arguments. Both wrappers
call `Tools/package_game.py`, requiring Python **3.9+**, Unreal **5.8.3**, hydrated
Git LFS content and at least **30 GiB free** (the existing Mac setup budget).
Set `UE_ROOT` or pass `--engine-root` if Unreal is installed elsewhere. Packaging
also needs the engine's platform SDK/toolchain; UAT reports missing prerequisites.
Build Mac packages on Mac and Windows packages on Windows.

Save your intended asset changes first. Packaging reads disk; it cannot include
unsaved editor graphs or placements. The workflow invokes AutomationTool
`BuildCookRun` to build, cook all main-project content (including traveled maps
and dynamically loaded assets), stage, pak/IoStore, package and archive. It uses
a headless Unreal commandlet internally for cooking; no GUI editor is opened.
The result runs its own native executable. The older `host`/`join` and
`play-connected` launchers use the engine's `-game` mode.

Each build uses a new archive under `Builds/PackagedPlay/<platform>/<run>/` and
stage/log directory under `Saved/PackagedPlay/<run>/`. Normal builds refresh the
build and cook through UAT while reusing engine/shader caches. They never select
a previous archive automatically. Generated files stay ignored. A failed build
retains its `build.log` and `build-receipt.json` and does not launch anything.
The receipt records the full Git commit, local-change status, engine version,
platform, arguments, archive and UAT exit code. `game.log` and a separate launch
receipt record each actual run. Dirty work is explicitly qualified; it is not
an exact reproduction of the named Git commit.

To run another instance without rebuilding, use the successful receipt printed
by the build:

```sh
bash Tools/package-play.command --launch-only Saved/PackagedPlay/RUN/build-receipt.json --mode host
bash Tools/package-play.command --launch-only Saved/PackagedPlay/RUN/build-receipt.json --mode join --address 127.0.0.1
```

Joining also supports DNS/Tailscale names and an optional `:7777` port. Each
instance prints its packaged commit; match the same clean commit and settings
across the team. Use packages on every peer. The project's existing rule is to
avoid mixing packaged peers with engine `-game` peers. Mac and Windows each run
their native build; a Windows executable does not run on Mac. This workflow
packages a listen-host/client game, not a dedicated server target.

Close the game window to end the terminal session. Do not treat successful
packaging or process launch as visual, controller or network acceptance. Those
checks still need actual 2/3/4-player and owning split-screen runs. Link receipts,
logs and images in the [team PR format](../docs/pull-requests.md), publishing
reviewer-accessible evidence when creating a GitHub PR.

Focused script verification (synthetic fixtures; no engine launch):

```sh
python3 -m unittest discover -s Tools/tests -p 'test_package_game.py'
```
