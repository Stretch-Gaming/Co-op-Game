# HC-5 isolated round authoring and validation

Run only from the assigned `round-progression/Co op Game` worktree, with UE 5.8.3.
The editor command loop asserts the full project path. `rpc.py` targets only
localhost port 8041 and verifies a project-specific startup log marker before
calling a tool. Never point it at the default 8000 editor.

Authoring sequence: `scaffold.py`, then `build.py`, then `fixtures.py`, requested
through `request.py`. `build.py` may target named functions for a bounded repair;
all graph authoring is editor-only and ownership guarded. Do not run authoring
while PIE is active. `fixtures.py` preserves an existing fixture map.

Tests: `run_clients.py 2`, `3`, `4` use Play As Client with native owning-player
IA_Interact and the unchanged production interaction RPC. The command/reset
actors are clearly labelled HC fixtures. `run_overlap.py` injects native IA_Move
and tests the real entrance overlap event. `run_roster.py 2`, `3`, `4` add and
remove a native local split player from a listen fixture and test the production
director's roster restart. Fixture transforms and Create/RemovePlayer are setup,
never evidence of production split-screen/gamepad or death integration.

After stopped PIE, `audit.py` compiles every owned Blueprint with warnings treated
as errors and exports graphs. `restore.py` restores transient editor preferences.
`artifact-sha256.json` records delivery files, and `acceptance-summary.json` records
the final gates. NullRHI behavior tests defer rendering acceptance explicitly.

No health/death tests, new production health, revive interactions, Core changes,
cave placement, commits or pushes belong to this slice. See
`docs/hc5-rounds-verification.md` for the primary owner's integration hooks.
