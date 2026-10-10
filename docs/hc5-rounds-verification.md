# HC-5 round progression and checkpoint slice

Worktree: `C:/Users/Stretch/.codex/worktrees/round-progression/Co op Game`.
Branch: `codex/round-progression-next`, baseline HC-2 PR #81 at
`4be3f85cff446901bbf88bdf918cfb2050d6fa18`. No commits or pushes made by the slice author.

The human cancelled revives during this slice. No revive interface, production
health component, downed interaction, health recovery, or death policy was added.
The older HC-3/HC-5 issue text still mentions these; its full acceptance is not
claimed here. Issue #11 remains open.

## Authored behavior

`BP_RoundDirector` runs on the server. It accepts a possessed pawn present in
GameState.PlayerArray and only the next entrance: Lobby/0 -> 1, Cleared/1 -> 2,
and Cleared/2 -> 3. It rejects duplicate, skipped and Playing-phase starts and
requires exactly one checkpoint matching the requested round. It calls the
existing GameMode.StartRound; it never sets RoundState or its phase itself.

The director observes Failed and schedules one non-looping three-second retry.
It captures Index and Attempt, checks that they still match at expiry, transports
existing possessed pawns to their checkpoint spots, dispatches the existing
BPI_RoundReset.ResetForRound(Index, Attempt + 1) on server actors, and calls
GameMode.StartRound exactly once. StartRound owns the Attempt increment and
samples fresh roster scaling. A roster decrease during Playing first calls
GameMode.FailRound and follows the same retry path. A changed index or attempt
invalidates an old timer. Client-local director calls cannot alter server state.

`BP_Checkpoint` has four separate SceneComponents, Spot0 through Spot3, and an
instance-editable RoundIndex. The director uses the existing unique ColorSlot
0-3 to choose a spot. Its CurrentCheckpoint is a runtime reference with a null
class default; no placed cross-sublevel reference is saved. The checkpoint
selector refuses ambiguous duplicate checkpoints. Missing/unpossessed pawns
block transport and retry; the empty PreparePlayerForCheckpoint override is
reserved for the primary owner's future death/respawn policy. It currently
changes no pawn health or life state.

`BP_RoundStart` is a TriggerBox. Its server overlap path resolves the director at
runtime and supplies the actual overlapping pawn. RoundIndex defaults to 1 and
is editable per placement. Duplicate directors disable progression, rather than
running competing timers. All authored gameplay is Blueprint-only.

## Placement and primary-owned hooks

Place exactly one BP_RoundDirector in L_Site01_HC after making that sublevel
current. Place one BP_Checkpoint for the spawn cavern (RoundIndex 0) and one at
each round entrance (1, 2, 3). Adjust all four spots to safe, separate supported
positions. Place BP_RoundStart at each chamber entrance with matching 1/2/3
indices. The assets resolve each other at runtime; do not assign actor hard
references in saved packages. This slice makes no cave or persistent-map edits.

Existing GameMode StartRound/ClearRound/FailRound remain the only phase writers.
The primary owner must connect any future death/failure detector to FailRound
while Playing and define behavior in other phases. If pawn replacement or life
state reset is required, implement it in PreparePlayerForCheckpoint (or replace
the orchestration hook under the appropriate ownership lock), then verify that
all remaining PlayerStates have valid possessed pawns before transport. No
health API is assumed. Do not add another Attempt increment or another reset
broadcast in Core.

Round 1 actor delivery, chamber gates and start pad are separate owners/slices.
The reset fixture verifies the existing interface, not every future production
puzzle/ghost actor. Full issue #11 acceptance requires their integration and the
team's cave/client tests.

## Validation

Editor authoring and automated
behavior tests use UE 5.8.3 with NullRHI at port 8041. This accurately defers
rendering, physical gamepad routing, cave placement and Mac/team acceptance.
For strict handling of a player leaving and another joining between the 0.2-second
polls, the primary-owned GameMode Logout path must additionally call FailRound
when the current phase is Playing, then resolve the sole director at runtime
and call ScheduleRetry. Preserve the existing logout/interaction cleanup.
The director's count observer is a fallback; the tests below exercise an actual
native local-player removal and the count-driven path. This slice does not edit
or claim acceptance of a production Logout hook.

The final behavior gates passed:

| Gate | Recorded checks | Result |
| --- | --- | --- |
| Play As Client, 2 players | 17 | Passed; clean log |
| Play As Client, 3 players | 17 | Passed; clean log |
| Play As Client, 4 players | 17 | Passed; clean log |
| Native local split-player departure, initial 2 | 5 | Passed; remaining roster 1, scaling row 2 |
| Native local split-player departure, initial 3 | 5 | Passed; remaining roster 2, scaling row 2 |
| Native local split-player departure, initial 4 | 5 | Passed; remaining roster 3, scaling row 3 |
| Native client IA_Move through the real entrance trigger | 2 | Passed; all worlds Round 1 / Playing / Attempt 1 |

Client gates inject IA_Interact through the unchanged owning-character input and
reliable server RPC, then clearly labelled fixture commands call the actual
round actor methods or the existing GameMode functions. They prove competing
entrances cannot start twice, skipped/earlier/Playing entrances are refused,
rounds advance 1 -> 2 -> 3, failure cannot increment Attempt early, the three-second
retry increments once, every fixture receives one server reset with the next
Attempt and observes it replicated, and 2/3/4 pawns land on distinct checkpoint
spots. The separate native IA_Move test proves ReceiveActorBeginOverlap itself.
Native CreatePlayer/RemovePlayer are fixture setup, not production PG split-screen
or physical gamepad acceptance. Neither test route calls an RPC directly through
editor Python as proof of networking.

Each final behavior log interval contains no errors, Blueprint Runtime Error or
Accessed None. The movement fixture initially failed before input because an
editor Python helper used an unavailable movement accessor; that helper was
corrected, and only the failed gate was rerun. Earlier graph/fixture authoring
failures are outside final behavior log intervals and were corrected before the
reported final gates. The LFS-pointer startup was also resolved before authoring.

Evidence is under Tools/unreal/hc5_rounds: clients-2/3/4.json and their log JSONs,
roster-2/3/4.json and their log JSONs, entrance-overlap.json and its log JSON,
audit.json, settings-restored.json, acceptance-summary.json and
artifact-sha256.json. Audit exports all owned graphs, checks null saved actor
references and absence of player-index getter nodes, and compiles all six authored
Blueprints with warnings treated as errors. The SHA-256 manifest covers the
owned delivery files; baseline tracked files remain unchanged.

The editor remains at localhost port 8041, PID 26672, with PIE stopped for primary
independent review. Original checkout assets and unrelated editors were untouched.
Transient play/performance settings were restored. NullRHI validation does not
prove appearance, physical gamepad routing, cave placement, actual death/respawn,
Mac interoperability or full issue #11 acceptance.

The owned-package save audit also found `/Game/Core/BP_CoopGameMode` dirty in the
editor session. It was left unsaved because this slice has no Core ownership.
The Core file's disk SHA-256 matches its baseline LFS OID
`33eace87e28cb9e2481aa16989c1aa2455b1a8e24ddbf7105d10a6930ea4a07b`,
and `git diff` is empty for all baseline tracked files. The primary reviewer
should use fresh baseline Core packages or its own locked integration editor;
do not run a global Save All in this authoring session.
