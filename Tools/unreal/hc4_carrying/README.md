# HC-4 carrying tools

Runtime logic is in the Blueprint assets, not Python. These scripts author or inspect assets through Unreal's editor APIs, drive isolated PIE fixtures, and verify captured evidence.

The authoring session is intentionally pinned to `C:/Users/Stretch/.codex/worktrees/hc4-carrying/Co op Game/CoopGame.uproject`. Its MCP port is 8024; PIE uses 17774. Do not point these tools at another editor or chat. The queue lives in ignored `Saved/HC4/`; the MCP client never uses the repository's port-8000 connection.

`launch_editor.ps1` starts the dedicated editor. `editor_loop.py` checks the active project before every queued script. `run_editor.ps1` additionally verifies the process command line and atomically submits one request; wait for its response before submitting another. A timeout means the editor command may still be running. Do not enqueue a duplicate. `slate.ps1` verifies the project again before dedicated MCP UI/PIE calls.

Example:

```powershell
./Tools/unreal/hc4_carrying/launch_editor.ps1
./Tools/unreal/hc4_carrying/run_editor.ps1 verify_assets.py
./Tools/unreal/hc4_carrying/matrix.ps1 -Players 4
```

`matrix.ps1` uses the saved HC4 fixture map and subclasses. It waits for network PlayerStates, arranges actors on the server, aims the fixture camera, and injects input per local player. Short pulses guarantee at least three input frames so slow multi-window PIE does not silently skip a press. Positive tests never invoke a server RPC directly through Python. `runtime_action.py` also supports reconnect, split-screen and movement sampling through `action.ps1`; observations are saved under `evidence/`.

```powershell
./Tools/unreal/hc4_carrying/action.ps1 '{"command":"input","action":"/Game/Core/Input/IA_Drop","subsystems":[0],"duration":0.3}'
./Tools/unreal/hc4_carrying/action.ps1 '{"command":"snapshot","label":"inspection"}'
```

`verify_evidence.py` is an offline independent assertion pass over snapshots and motion samples. `verify_assets.py` reads saved class contracts and action connections. `final_report.json` and `artifact_hashes.json` identify the final acceptance evidence and files. The detailed production handoff is in [docs/hc4-verification.md](../../../docs/hc4-verification.md).

The factory scripts (`scaffold.py`, `build_logic.py`, `build_fixtures.py`, with `authoring.py`) are **authoring tools**, not runtime dependencies. They replace owned graphs and refuse to recreate an existing fixture map. Do not replay them against reviewed assets casually. For a fresh generation, Blueprint editor UI steps are required: add `BPI_RoundReset` in BP_Carryable Class Settings, and set the three fixture `Server_HC4…` events to reliable **Run on Server**. The engine does not expose those settings through the Python graph API. The delivered binary assets already contain them.

All saves are scoped to the authorized carrying assets and HC4 fixtures. Engine basic geometry is used until the separate reviewed art deliveries are integrated. No imported art, Core, production input/HUD, shared materials or cave map is authored by these tools.
