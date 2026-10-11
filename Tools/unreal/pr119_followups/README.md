# PR #119 follow-ups: cave traps and the maze rebake

Editor scripts for two follow-ups to the HC-INT2 checkpoint (PR #119, issue #93), run on PK's Mac on Oct 10, 2026. Every asset change went through the Unreal editor; nothing here edits a `.uasset` or `.umap` on disk.

## Running them

The scripts run inside a second editor opened on this checkout, so they never touch an editor that's open on another checkout:

    open -n -a UnrealEditor.app --args "$PWD/CoopGame.uproject" -ExecCmds="ModelContextProtocol.StartServer 8001,py $PWD/Tools/unreal/pr119_followups/loop.py"

`loop.py` watches `Saved/PR119/command.json`. `request.py <script> '<json args>'` submits one script and prints its `RESULT`; add `"_during_pie": true` for scripts that inspect a running PIE session, and `"_timeout"` for long ones. Scripts can also be from `../playable_game/`. `mcp.py` calls an Unreal MCP tool on port 8001, such as `CaptureViewport`.

## Cave traps (`L_Site01_HZ`)

The adopted HZ cave lost its traps in the integration.

1. `place_cave_traps.py` puts back the nine traps and the cave fall volume from `../playable_game/place_adventure_threats.py`, at the same positions, in `L_Site01_HZ` only. Every trap position has cave floor at Z 0 (`floor_probe.py`).
2. `fix_trap_server_timer.py` fixes `BP_AdventureTrap.BeginTrap`. The integrated graph started the `RefreshTrap` timer only on clients, so on the server no trap ever damaged anyone or read its `DT_HazardScaling` row. The timer now starts on every machine, and the server still sets the replicated `StartTime`.
3. `run_trap_matrix.sh 2 3 4` runs `test_cave_traps.py` as Play As Client at each player count. Results are in `evidence/cave-traps-*.json`.

The fall volume stays where the original script put it, at Z −3300 under the chasm. The adopted cave's chasm floor is at Z −2000, and the map exit and the zipline landing are on that floor, so the volume only catches players who fall out of the world. A volume that kills fallers into the chasm, as the layout doc describes, is HZ's call, because it would also cover the exit.

## The maze rebake (`L_Maze_HZ`, `Content/Puzzles/Art/MazeIntegration`)

1. Build `Prototypes/CoopCave` with `build_mac.sh`, then export headless:

       UnrealEditor Prototypes/CoopCave/CoopProto.uproject /Engine/Maps/Entry -game -nullrhi -unattended -ExecCmds="coop.ExportCave,quit"

   The prototype writes `Saved/CaveTransfer/cave.json`. It's re-serialized as compact JSON and gzipped (level 9, mtime 0) into `SourceArt/HC/MazeIntegration/scene.json.gz`, and `provenance.json` records the source commit and hashes.
2. `clear_maze_bake.py` removes the old `PlayableMazeScene` actors from `L_Maze_HZ` and the `SM_Maze_*` meshes they used, after checking that nothing else references them.
3. `../playable_game/bake_maze_assets.py` and `../playable_game/place_maze_scene.py`, each run in two index ranges, bake and place the new scene.
4. `verify_maze_bake.py` checks the level against the scene file and deletes any tint material nothing references.
5. `fix_maze_grade_bounds.py` turns off collision on the maze's colour-grade box. The exporter writes every `UBoxComponent` as a blocker, including `MazeGradeBounds`, which ignores every channel in the prototype. `place_maze_scene.py` places blockers as hidden `BlockAll` cubes, so that box enclosed the whole maze in an invisible solid. The old bake had the same box, as `MazeScene_909`. A player-sized capsule anywhere inside the maze started in penetration (`probe_capsule.py`). The exporter should skip boxes without blocking collision, so the next rebake won't need this step.
6. `test_maze.py` and `test_maze_walk.py` check the maze as Play As Client. Results are in `evidence/maze-*.json`.
