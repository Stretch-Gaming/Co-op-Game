# HC-7/HC-8 owned extraction and results slice

Worktree: `C:/Users/Stretch/.codex/worktrees/extraction-results-restart/Co op Game`.
Branch: `codex/extraction-results-restart`, baseline `4be3f85cff446901bbf88bdf918cfb2050d6fa18`.
Bounded tracking: #86, with production acceptance retained in #13 and #14.

## Delivered Blueprint behavior

`BP_MapExit` is a TriggerBox. Its authority-only 0.2-second reevaluation uses the
live GameState PlayerArray and deduplicates PlayerState references. Every required
state must resolve a valid pawn and PlayerController whose PlayerState matches;
the pawn's root position must be inside the box's current world transform and
unscaled extents. This supports translated, rotated and scaled volumes and does
not count overlapping actor components. A pawnless connected state blocks. Zero
required players never completes. The live roster handles joins/departures and
removes disconnected states; an exit commits its local latch before delegation.
No health/downed dependency was added because that system is absent at this
baseline and revive work is outside this approved slice.

Before the completion latch, leaving the volume cancels readiness, a disconnected
PlayerState is removed from the requirement, and a newly admitted PlayerState must
acquire its own valid pawn and enter the volume. After the latch, departures and
new joins do not cancel completion or recapture the snapshot. A player admitted
to the results world receives the current replicated snapshot and its own results
widget when its local player is ready. Admission/routing for a connection arriving
during non-seamless travel remains with Core and requires actual travel acceptance.

`BP_RunCoordinator` is an authority-owned, replicated, always-relevant actor.
It must be a singleton: missing/ambiguous coordinators fail safely in the exit,
results lifecycle and the coordinator's own capture/restore/restart guards.
`CaptureSnapshot() -> Accepted` copies BOTH GameState totals into the existing
GameInstance fields, and sets the capture latch before any travel call.
`TryCommitExtraction() -> Accepted` captures once then delegates to the existing
`BP_CoopGameMode.CompleteMap()`. It creates no alternate travel path and never
writes the round phase itself.

`RestoreResults() -> Accepted` runs only on authority in a level whose exact short
name is `L_Site02`, on a fresh uncommitted coordinator. It copies BOTH GI totals
back to GameState and to its replicated snapshot, marks `ResultsActive`, and asks
the GameMode to set MapComplete. Repeated restoration returns false. Capturing on
the outgoing map does not activate results or authorize restart.

`RequestRestart(RequestingController) -> Accepted` requires authority, singleton,
committed AND active results, no prior accepted restart, a valid controller found
in this world's live controller actors and GameState roster, and the native
IsLocalController + IsPrimaryPlayer checks. It does not accept a client-supplied
host boolean or perform a player-index-zero lookup. Remote and secondary local
controllers are denied. A dedicated server has no local primary host and waits
for an explicit team policy. Acceptance sets RestartInProgress, resets BOTH GI
totals to zero, then delegates to existing GameMode.CompleteMap. Duplicate requests
cannot issue another completion call. The old displayed snapshot remains visible
with RESTARTING while the transition is pending.

`AC_RunResults` belongs on a PlayerController. It resolves exactly one active
coordinator and owns only its own `WBP_RunResults`. It waits for a valid local
player controller and Enhanced Input local-player subsystem before creation,
validates the returned widget, and retries after a failed AddToPlayerScreen.
It uses AddToPlayerScreen with that controller. Repeated refreshes reuse the
widget and rebind its coordinator; absent, ambiguous, inactive or destroyed
coordinators clear the widget AND stored coordinator. EndPlay removes only the
owned results widget/timer. Existing HUD widgets and input contexts are untouched.
`RequestLocalRestart()` obtains the component's actual controller owner and
passes it to the coordinator; it defines no RPC and cannot mutate a client proxy.

`WBP_RunResults` renders the replicated collected/available snapshot and shows
PRESS R TO START A NEW RUN only for an authority primary owner; others see
WAITING FOR HOST. All owners see RESTARTING after an accepted restart.

## Required Core integration boundary

No Core assets, production maps, existing input assets or settings were edited.
This slice is not a production full-run/travel acceptance.

1. GameMode must create exactly one RunCoordinator on authority per world, after
   its shared initialization. Do not save cross-sublevel actor hard references.
   Put/resolve the exit in the approved HC map ownership/lock context. It refuses
   to travel when the coordinator is missing or ambiguous.
2. Route all production extraction and direct/debug completion entry points
   through the coordinator's accepted commit path, then keep GameMode.CompleteMap
   as the existing final travel function. The baseline F4 still calls CompleteMap
   directly and bypasses capture until its Core owner wires this hook. Avoid
   recursively calling CaptureSnapshot from CompleteMap after the coordinator has
   already latched it; duplicate transition entry points need the same global gate.
3. On the actual results-world startup, validate a completed-run GI marker/policy,
   create the fresh coordinator and call RestoreResults AFTER GameMode initializes
   GameState. GI currently exposes only two totals; adding a valid-run marker, run
   ID, or equivalent remains Core work so a manually opened Site02 cannot imply a
   completed run. Preserve valid zero/zero completed snapshots.
4. Prevent Core's periodic RefreshRelicTotals from overwriting restored totals in
   results. Actual Site02 currently has no relevant fixture relics, so the baseline
   refresh would reset its available total. The owned coordinator snapshot remains
   stable, but that alone is not GameState travel-persistence acceptance.
5. Attach/reuse exactly one AC_RunResults per controller, including all valid local
   owners after travel. Add the production R action to the controller's established
   per-local-player Enhanced Input lifecycle and invoke RequestLocalRestart. Do not
   duplicate HUD/input setup or ClearAllMappings. No production IA/IMC is authored
   by this slice. If Core adds client RPC forwarding, use the actual owning PC and
   retain the server provenance guard; local event rejection is not RPC proof.
6. After accepted restart, existing GameMode travel must construct fresh map/puzzle
   state and restore the established HUD/input lifecycle. The fixture's GI reset
   does not prove a fresh production map or two consecutive traveled runs.

## Native Windows fixture evidence

Engine/project/PID/port evidence is `Tools/unreal/hc_run_ending/editor-identity.json`:
Unreal 5.8.3 CL58210709, dedicated PID43812 on localhost MCP8017. It proves the
isolated project before mutations. D3D11 and disabled ray tracing are launch-only
renderer overrides. All calls use this dedicated editor; other editors are untouched.

Owned fixture package `/Game/Puzzles/Test/HC_RunEnding/L_Site02` deliberately shares
only the short results-map name with production. Its fixture GameMode is a child
of Core. It overrides CompleteMap as an EVENT to count calls and set MapComplete
through inherited GameMode behavior; it contains NO travel implementation. Two
exit volumes share one coordinator. A placed unchanged BP_Relic, Value19 and
MinPlayers2, supplies the denominator; GameMode.AddRelics(7) seeds collected value.
FixtureSpawnCoordinator and FixtureClearTotals are test-only native Blueprint
helpers, invoked from editor Python for setup. No production method or RPC is
claimed as network proof from Python call_method.

| Gate | Evidence | Result |
| --- | --- | --- |
| 2/3/4 native Play As Client | `clients-2.json`, `clients-3.json`, `clients-4.json` | Occupancy, departure, pawnless block, shared two-exit once-only7/19 capture, hidden outgoing results, restore idempotence, replicated7/19 and owning widgets, actual remote action event rejection, destruction cleanup |
| Listen host and host-local split pair | `host-split.json` | Native late local join must enter; native removal changes roster; late results local owner receives snapshot; actual second-local action event denied; actual primary-host action accepted once; GI0/0 and replicated restart state; repeat action denied; stable distinct widgets |
| Deliberately cleared-state restore | `restore-cleared-state.json` | Authority GI7/19, fixture GS0/0 before restore, GS7/19 immediately and all PIE worlds7/19 after delay |
| Compile/native graph audit | `final-audit.json` | Six touched Blueprints compile with warnings_as_errors; readable graph DSL plus native setter target/link types distinguish GI/GS fields |
| Log intervals | `*-log.json` | Byte ranges of dedicated Saved/Logs/CoopGame.log; passing gates have no errors, Blueprint Runtime Error or Accessed None |
| Owning split results render | `host-split-results00000.png`, `results-view-ready.json` | Actual Shot SHOWUI pixels inspected: both7/19, top primary R prompt, bottom waiting prompt; existing two HCA3 HUDs retained |

The fixture's existing shared HUD displays Round0/3 because no production round
run is staged; that shared HUD was not edited. Screenshot capture stalled the
engine about37s and emitted long-tick warnings, not gameplay errors. The previous
CaptureViewport image is preserved as `host-split-attempt1.png` and is NOT results
visual evidence. Failed/partial fixture harness attempts and the first late-local
lifecycle failure are preserved separately; they are not passing gates. The
lifecycle defect was corrected before the final affected client and host gates.

Input verification injects the owned fixture Enhanced Input action into the actual
owning subsystem, traversing its Blueprint event and component/server-local guard.
`RestartInputEvents` proves that the event occurred. This does not prove physical
keyboard R, hardware gamepad mapping, or a client-to-server restart RPC. State and
widget snapshot replication use actual PIE network worlds.

## Reproduction and remaining acceptance

Use bundled engine Python at
`C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe`.
Launch the exact worktree editor hidden with the owned editor_loop.py, unique port
8017 and the owned fixture. Preserve recorded reports before a rerun. Only stopped
PIE may author/compile. Authoring order: scaffold.py, build.py, build_results.py,
fixtures.py, build_fixture.py, seed_fixture.py, fixture_spawn.py, fixture_clear.py.
Run `run_test.py 2`, `run_test.py 3`, `run_test.py 4`, `run_test.py 2 host`, and
`run_restore.py`; then StopPIE and run audit.py. No production travel command is
introduced by any of these files.

Core hooks/locks and real Site01->Site02->Site01 travel remain pending, including
persistent GI validity, totals protected from refresh, HUD/input once after travel,
no duplicated local players/widgets, and two consecutive traveled runs. Dedicated
server host policy, physical R/gamepad, Mac/network machine acceptance and final
production exit placement remain pending. #13/#14 must remain open for these gates.

`artifact-hashes.json` records SHA256 for the owned delivery assets and evidence.
No commit, push, issue edit or original-checkout edit was made by this worker.

## Primary independent verification

The primary agent independently inspected the implementation, readable and native
Blueprint graphs, owning split-screen pixels, and the worker's evidence. A new
native listen-server scenario (`primary-native.json`) used three initial players
and a fourth host-local player. It verified that the fourth player blocks
extraction while outside, and removing that only missing player triggers exactly
one completion. It also restored deliberately cleared GameState totals from 0/0
to 7/19, checked late local results with exactly one active results widget and one
results component per owner, rejected null/remote/foreign-world/secondary
controller arguments, rejected ambiguous coordinators, recovered widget ownership
when singleton placement was restored, and traversed the actual owning input
event for one accepted restart and a rejected repeated restart.

Direct server argument checks are authority-unit evidence, not client RPC proof.
The independent scenario had a clean recorded log interval in
`primary-native-log.json`. Native owned graphs matched the worker's audited
implementation; six owned packages were compiled with warnings treated as errors
and saved individually (`primary-save-review.json`). The protected Core
controller graphs matched baseline. Editor inspection left that Core package
dirty in memory; it was never saved, and its on-disk fingerprint is checked
against the original protected baseline. Original editor test settings were
restored and PIE stopped (`primary-editor-cleanup.json`).

`primary-final-review.json` records scope, protected file fingerprints, native
artifact fingerprints, script syntax, and independently rescanned log intervals.
The final `artifact-hashes.json` covers the delivered files after primary review;
`worker-artifact-hashes.json` preserves the worker's original manifest.

Production integration and all acceptance listed above remain pending. No full
#13 or #14 completion is claimed by this bounded fixture delivery.

After the final owned compile/save, serialized fingerprints changed for
AC_RunResults and the fixture controller while their native graphs matched the
audited implementation. The primary reopened the saved project in a fresh,
identity-checked Unreal 5.8.3 editor (PID21996, owned MCP8017) and repeated the
independent scenario (`primary-native-fresh.json`). All nine checks and its
recorded log interval pass. Unreal refreshed and saved the owned BP_MapExit during
fresh startup at 14:53:35 UTC, before the acceptance scenario began. No gameplay
graph changes were introduced; the final manifest records those saved bytes.
Settings were restored, PIE stopped, and both dedicated editors were closed after
identity checks; unsaved Core state was discarded. Original and fresh raw logs
are preserved to support the recorded byte intervals.

The owned tooling attributes preserve raw evidence bytes across Git checkouts so
log interval offsets and recorded hashes remain reviewable.
