# HC Round 3 gauntlet integration milestone

This slice adds an HC coordinator, entrance control and far-side objective. It
uses the delivered PG continuous levers and gate without changing PG packages.
Production completion is blocked until PG supplies a persistent gate-latch
adapter. The test bridge is explicitly a simulation: the real PG gate closes
after `ClearRound()` cancels its holders. Passing fixture completion does not
mean the cave's haunted gauntlet is complete.

## Ownership and provenance

The isolated checkout is
`C:/Users/Stretch/.codex/worktrees/haunted-gauntlet-integration/Co op Game`,
branch `codex/haunted-gauntlet-integration`, based on published HC-2
`4be3f85cff446901bbf88bdf918cfb2050d6fa18`. The primary independently verified
the dedicated Unreal 5.8.3 build 58210709 editor and loopback MCP port 8045.
The behavior session uses NullRHI. This supplies native behavior evidence,
not rendered appearance or physical gamepad acceptance.

Only `Content/Puzzles/Gauntlet/`, `Content/Puzzles/Test/HC_Gauntlet/`,
`Tools/unreal/hc_gauntlet/` and this document are written. Blueprint assets and
the owned test map are authored and saved through the editor. No Core, PG,
HZ, carrying, Round 1, existing map, HUD, art, material, project settings or
plugin package is saved. No commit or push is made by the worker.

The owned actor copies use read-only `BP_Carryable` solely because its native
`StaticMeshActor` parent implements both `BPI_Interactable` and
`BPI_RoundReset`. All carrying variables, functions and event chains are
removed from the copies. The coordinator and bridge have blank meshes,
no collision, gravity or physics, and a unit root scale. The initial inherited
0.5 root scale caused the first native entry test to fail; its failure evidence
is retained, and `root-defaults.json` records the correction.

## Gameplay contract

`BP_HCGauntletStart` is an instant entrance interaction. A valid current player
may request `StartRound(3)` only while Round 2 is `Cleared` and a unique
coordinator, tagged real gate and supporting bridge are ready. It does not
write round state. Before accepting the server request, it synchronously refreshes
coordinator state and runtime dependencies, closing the readiness-cache race.
`BP_HCGauntletObjective` is the instant far-side interaction;
its normal inherited HC input/RPC path runs `UseAllowed`, including range,
line of sight and current interaction/downed-tag checks, on the server.

`BP_HCGauntletCoordinator` polls current GameState state on the server. It
does not rely on receiving a dispatcher event. Its replicated snapshot includes
`CurrentAttempt`, `RoundPlaying`, `Completed`, `CrossedPawns`, readiness and a
completion counter. It fails closed when multiple coordinators exist.

Progress belongs to a live `BP_CoopCharacter` whose current controller owns
that pawn, whose controller and pawn share a PlayerState, and whose
PlayerState is in the current GameState roster. A server-observed entry within
the route bounds records the pawn for the current attempt. Crossing the
far-side plane records it only while the real PG gate reports all required
levers held, replicated open state and sufficient physical lift. Holders do
not receive the crossing token unless they actually cross. Tokens reset on a
new attempt, interruption or round change, including when notifications were
missed. The actual `BPI_RoundReset` event also clears them.

Planes and bounds use the coordinator's actor-local transform, forward +X:
`EntryX=-200`, entry band 300 cm deep, `CrossX=250`, crossing band 600 cm deep,
`HalfWidth=800`, `HalfHeight=500`. The production coordinator root is unit
scale. These are route checks, not a replacement for cave walls, traps,
health, checkpoints or anti-bypass enclosure.

Completion revalidates current Round 3 `Playing`, matching attempt, current
pawn membership, unique coordinator and progress. It asks the unique runtime
bridge to `RequestLatch(3, Attempt)` and then requires
`QueryLatch(3, Attempt)` to acknowledge that same attempt. It sets its
completion flag before calling the existing GameMode `ClearRound()` so a
second request cannot clear again. GameMode remains the only phase writer.

## PG bridge and placement handoff

Production discovery uses exactly one actor tagged `HC_GauntletGate`, cast
to the delivered `BP_GauntletGate`, and exactly one actor tagged
`HC_GauntletBridge`, cast to `BP_HCGauntletGateBridge` or its child. Missing,
wrong-class or ambiguous tagged actors fail closed. No placed cross-sublevel
references are saved by the owned gameplay actors.

The base bridge returns false for `SupportsLatch()`, `RequestLatch(Index,
Attempt)` and `QueryLatch(Index, Attempt)`. PG should implement a child bridge
in its own folder/sublevel. `SupportsLatch()` must report actual runtime
readiness; it must not latch the gate as a readiness probe. `RequestLatch`
must persistently latch PG's gate on the server for the exact active attempt.
`QueryLatch` must confirm that persistent state. Reset must unlatch for the new
attempt. The bridge must not clear the round itself; the coordinator owns
that completion request. Setting `bOpen` once is insufficient: the delivered PG `UpdateGate`
overwrites it every authority tick from held levers or safety overlap.

The labeled `BP_FixtureLatchBridge` child returns support and simulates the
attempt handshake. The coordinator's `AllowFixtureBridge` defaults false;
only the owned test map opts in. The simulation never writes PG gate state.
PG's published gate has no confirmed latch API or round-phase guard, and
its current `GetLeverCount` uses the maximum of locked scaling row and live
roster. A late fourth join can increase the required count mid-attempt.
PG/Core must agree on roster restart policy before that production case passes.

For placement after the owning cave/PG gate passes: make `L_Site01_HC` current
for the HC actors; place entrance control at X11700 cm, coordinator at the
gate plane X12500 cm facing +X, and objective beyond the traps at the far-side
lever position X17000/Y600 cm. Preserve unit coordinator scale and tune
route bounds against the actual enclosed hall. HC's checkpoint is at
X11800 cm and needs Core's eventual checkpoint/recovery hookup. PG places
its levers, gate and child bridge in `L_Site01_PG`; PG binds the required
levers at runtime or within its own sublevel. Never save actor references
between those placed HC and PG actors.

## External dependencies

- Core must broadcast `BPI_RoundReset(Index, Attempt)` on restart, implement
  everyone-down recovery/checkpoints, and restart a playing round on roster
  departure with a newly sampled scaling row. Current inspected `StartRound`
  and `FailRound` cancel active uses and change state; a reset broadcast is
  not present in those inspected graphs. Owned polling cleanup does not
  replace Core's framework.
- PG owns persistent latch behavior/adapter, the exit lever's final presentation,
  ghost spawner/lifecycle and lever-holder targeting, headlamp and production
  split-screen controls. `dependency-inspection.json` records actual delivered
  `BP_Ghost`: replicated Pawn and movement, nearest-player targeting from
  GameState's PlayerArray, authority-only chase and overlap `Apply Damage`
  with a timed backoff. `ApplyScaling()` is empty, `IsPlayerDowned()` returns
  false, and the class does not implement `BPI_RoundReset`. Its inspected
  event graph has no round-phase lifecycle or lever-holder priority. PG must
  gate round-3 ghosts to Index 3/Playing, spawn counts from the locked row
  (1 at 2/3 players, 2 at 4), apply speed/damage scaling, prefer valid lever
  holders, and despawn/reset when the attempt ends or changes. Resolve
  lever holders at runtime through valid tagged PG lever actors, rather
  than saving cross-sublevel references. Health/downed filtering must use
  HZ's eventual real component. None of these missing ghost systems is
  replaced by this milestone.
- HZ owns real health/downed state, damage/revive, traps, dark cave enclosure
  and the route's safety/anti-bypass placement. The owned objective currently
  respects Core interaction blocking and the `Downed` tag; missing HZ health
  binding must be completed against the real component contract.

Native dependency queries confirm `BP_GhostSpawner`, `AC_PlayerView`,
`BPFL_SplitScreen`, `BP_ExitLever`, `AC_Health`, and the documented spike,
dart and swinging trap classes are absent from this checkout. The complete
Hazards asset listing in the evidence contains cave art/sublevels, without
gameplay trap Blueprints. There are no ghost, damage, trap or cave simulations
in the owned input map; those are explicit integration dependencies.

GitHub remains the tracker. PG issue #28 stays open. Creating the bounded HC
issue under epic #1/Sprint 6 was rejected with HTTP 403 by the connector; no
new issue number is assigned and no alternate tracker is created.

## Evidence and remaining checks

`contract-inspection.json` contains actual protected graph reads;
`interfaces.json` records native interface proof. `authored-graphs.json` and
`dsl/` provide owned graph readback/source. The native input fixture uses real
PG levers/gate and actual owning Enhanced Input injection through inherited HC
character RPCs. Python positioning/bootstrap/restart and native local-player
creation are labeled fixture setup. Positive traversal uses `IA_Move` through
the open real gate with collision enabled. The owning probe resolves an input
subsystem by controller, including distinct subsystems for the host's two
local owners in one world.

The native matrix and affected primary checks passed with no Blueprint errors,
`Accessed None` or log errors in their archived successful intervals:

| Report | Native evidence |
| --- | --- |
| `input-clients-2.json` | Primary rerun of the final source after the startup correction: two Play As Client players, actual traversal/completion, exact matching server pawn, duplicate/stale denial, renewed traversal and replicated reset/unlatch across all three worlds. |
| `input-clients-3.json` | Three Play As Client players plus a distinct fresh network client reconnect: current completed attempt/fixture latch snapshot, owned prompt/input after reconnect, matching server-pawn stale denial, renewed real hold and traversal, actual interface reset on the server. |
| `input-clients-4.json` | Four Play As Client players: two-lever scaling including closed with one holder, all gameplay checks, fixture latch replicated true before actual BPI reset, then tokens/holders/real gate/fixture unlatch cleared across all five worlds. |
| `input-host-3.json` | Host plus two remote worlds, adding a second host-local fixture player for four total. Both host-local owners hold separate PG levers through distinct owning input subsystems in the same world; all final movement and replicated reset checks pass. |

The primary independently reviewed source and emitted graphs, then corrected
startup to refresh live coordinator/dependency state before accepting the
request. `primary-review.json` compiles all six owned Blueprints with warnings
treated as errors and proves real interfaces, replication/default flags,
unit coordinator scale, no carrying/probe behavior, no player-index gameplay
nodes and no direct phase/state writes. The base bridge's support/latch calls
remain false and production fixture opt-in defaults false.

`primary-boundaries-clients-2.json`, `-clients-3.json`,
`-clients-4.json` and `-host-3.json` each pass ten independent boundary
checks. Actual owning client input cannot start when fixture support is
forbidden or coordinators/bridges are ambiguous. A labeled synchronous server
fixture request immediately after bridge ambiguity appears proves revalidation
before the polling timer can run. Valid input starts Round 3 after ambiguity
is removed. The host check uses the second local owner's input subsystem.
These intervals include PIE stop and have no log errors.

The independent final two-client full-suite rerun includes the stronger
replicated reset checks; three-client evidence includes the fresh-world
reconnect and immediate server interface reset, while four-client/host evidence
also observes reset replication. Production changes affect only the startup
guard; the focused corrected-start matrix covers every tested roster. Native
test-only spawn helpers added to the labeled fixture bridge exercise duplicate
actors; they neither change production actors nor write PG state.

Protected Core/Player/Hazards/Maps/Config/project/MCP files match the original
116-file SHA256 row aggregate
`84f8971484df119342b549a75358e19b4a408a33e48bf9f178b6cf8b451b15b3`.
Git status contains only the four authorized scopes, and the original checkout
retains its initial untracked RPC probe. Final source/evidence/binary hashes
are recorded in `artifact-hashes.json`; operational session authorization
and inbox files are excluded. The work remains uncommitted in the attached
branch; no pull request, merge or issue closure is claimed.

Each acceptance runner stops its own PIE and restores unsaved Play/performance
preferences in `finally`; it never saves configuration. Compile audits run
with PIE stopped. The initial slow graph inspection and authoring-client
timeout are not inferred passes; matching native command results and saved
compile readback provide the actual completion evidence.

Production persistent latch, ghost/health/trap/cave integration, rendered
split-screen appearance, physical controller routing, Mac clients and the
full `L_Site01` run remain external acceptance. Windows PIE fixture results
do not close those dependencies.
