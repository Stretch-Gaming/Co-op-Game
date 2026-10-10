# HC-6 altar tools

Pinned checkout: `C:/Users/Stretch/.codex/worktrees/altar-challenge/Co op Game`, MCP 8042, PIE 17792. Never use port 8000. Launch/run helpers validate the exact project and process. Calls are sequential. No gameplay runs in Python: production behavior is entirely BP_Altar and existing Blueprint contracts.

`launch_editor.ps1` starts only this editor. The script pump uses ignored `Saved/HC6Altar/`. `run_editor.ps1 SCRIPT.py` checks process/project identity. `slate.ps1` routes native editor calls to 8042 with the same identity check.

`build.py` is an authoring factory for owned BP_Altar only. It duplicates the interface-bearing StaticMeshActor template through the editor, removes all copied carrying functions/variables, and creates the altar graphs. Do not replay casually against reviewed assets. `fixtures.py` creates the owned standalone map and input probe and refuses to replace an existing map. Art and production carrying/Core are read-only.

For a native matrix, write `{"clients":2}` (or 3/4) to `Saved/HC6Altar/options.json`, run `configure.py`, call StartPIE with options `{bSimulate:false,playMode:"PlayMode_InEditorFloating",warmupSeconds:2}`, then run `begin_matrix.py` to wait for native network ownership before the matrix. Wait for `clients-N.json`. The runner injects IA_Interact/IA_Drop into each owning local player's subsystem, waits for actual native FocusedTarget, and observes server/client state. It never calls a positive altar transaction/RPC directly. Python positions and aims fixture actors and calls StartRound/reset contracts for setup. Static fixture collision/gravity overrides prevent test actors obstructing each other; they are not production movement acceptance.

`test_latejoin.py` reconnects a real client to 17792, proves distinct new world/pawn identities, observes the placed key, then resets and picks a key through native input. `test_stale.py` destroys that runtime carried key and verifies native altar rejection. `test_authority.py` calls accept/reset directly on clients only as negative authority checks. `verify_evidence.py` independently checks captured world snapshots and hashes owned binaries.

Temporary PIE settings are restored by `restore.py`; no project config is saved. Compile auditing requires stopped PIE. All binary asset saves occur through Unreal; no raw uasset/umap edits.

