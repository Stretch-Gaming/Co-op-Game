# Owned HC gauntlet workflow

This checkout's gauntlet assets are already authored. Normal verification
does not run authoring scripts. Operate only the primary-verified dedicated
UE5.8.3 CL58210709 session on loopback8045; never use the configured8000 tools
or another chat's editor. The primary owns launch, shutdown, authority and
independent verification.

`editor_loop.py` validates the exact isolated project path and build, publishes
PID/session in ignored `ready.json`, and registers a sequential inbox. Its
startup does not modify gameplay. The primary verifies process/project/port
identity and writes matching ignored `authorization.json` before mutation.
Every request carries the verified session. Authoring/compile/fixture scripts
refuse active PIE. A client timeout does not cancel a native operation; confirm
the matching command-result before submitting another request.

Bundled Windows Python:

    C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe

From this exact worktree, using that executable:

    python -B Tools/unreal/hc_gauntlet/run_input.py clients 2
    python -B Tools/unreal/hc_gauntlet/run_input.py clients 3
    python -B Tools/unreal/hc_gauntlet/run_input.py clients 4
    python -B Tools/unreal/hc_gauntlet/run_input.py host 3

The host command starts the host plus two remote worlds, then adds one local
host fixture player: four total, including the two local owners in one world.
It uses the per-controller input probe, not a subsystem lookup by world.
The three-client command performs a fresh network client reconnect after
completion. Positive crossing uses IA_Move with collision enabled. Python
positions/bootstrap/restart and native CreatePlayer are labeled fixture setup.
The final reset test earns fresh progress through movement, seeds only the
fixture bridge's acknowledged latch through its public test contract, and
dispatches the actual BPI_RoundReset message before waiting for replication.

`run_input.py` archives current-session log intervals and always stops its PIE
and restores unsaved preferences in finally. It does not SaveConfig.
`inspect_contracts.py`, `inspect_interfaces.py` and `inspect_dependencies.py`
are read-only evidence scripts. `dsl/` plus `authored-graphs.json` provide
implementation source/readback. Failed reports retain explicit failure names.

Authoring recipes are `author_scaffold.py`, `author_logic.py`,
`fixture_level.py` and `author_reset_probe.py`, used in that order only for an
explicit new owned build. The fixture script refuses to replace an existing
map. `author_defaults.py` records the initial root-scale repair and should
not be rerun merely to verify. All binary writes go through the editor;
only owned packages are saved. All gameplay remains Blueprint-only.

The production base bridge fails closed; fixture opt-in defaults false.
Fixture completion does not supply persistent PG latch, ghost lifecycle,
health/traps/cave integration, production split-screen controls, rendered
appearance, physical gamepads or Mac acceptance. See
`docs/hc-gauntlet-verification.md` for exact handoffs and evidence limits.

## Primary verification

The final Start server request refreshes live dependencies before validation.
Its source is in `author_logic.py`; `author_primary_correction.py` records
the focused editor correction. `author_primary_fixture_spawns.py` adds only
test-bridge spawn helpers needed by the primary boundary suite.

With PIE stopped, run `request.py audit_primary.py`. Run
`run_primary.py clients 2`, `clients 3`, `clients 4`, and `host 3`
sequentially for independent startup/ambiguity/race gates. The host gate creates
and uses the second host-local owner. `run_input.py clients 2` is the primary's
final full behavior rerun. All runners restore preferences in finally.

`collect_evidence.py` hashes all owned delivery source, evidence and binaries,
excluding its manifest and ignored operational session files. No source tool
edits a binary on disk. Production latch, threats, cave placement, rendered
split-screen and physical controllers remain owner integration acceptance.
