# First-room mining in the six-round adventure

HC/HZ integration for [HC-6](https://github.com/Stretch-Gaming/Co-op-Game/issues/12)
and the [playable adventure](https://github.com/Stretch-Gaming/Co-op-Game/issues/93),
based on main `56bbb93`. The merged mining delivery remains read-only in
`Content/Hazards/FirstRoom/` and the original `L_Site01_HZ`.

This packet preserves the actual authoring/test scripts under `executed/`, their
hashes in `source-manifest.json`, and bounded native readback evidence. It is not
a complete mission acceptance report. Root owns the serialized editor, exact
LFS locks, compile/save, runtime checks and publication.

## Scope

- Reserved HZ derivative `Content/Hazards/Test/SixRound/L_WorldRoute_Test.umap`:
  11 linked mining instances (one puzzle/cart/pickaxe, four deposits/plates).
- HC `Content/Puzzles/Test/SixRound/L_SixRound_HC_Test.umap`: retire only the old
  `Six_PlatePuzzle` and four `Six_Plate_0..3`; preserve the sole start pad,
  north connection door, checkpoints, altar, meeting locks and route.
- Reserved `Content/Core/BP_CoopGameMode.uasset`: replace only old Round 1
  statue feasibility, add mining-resource recovery and guarded retry reset.
- Reserved `Content/Core/BP_CoopCharacter.uasset`: allow its authoritative carried item past the final eye-to-hand visibility check; preserve all preceding use gates.
- HC cave copy `Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap`: remove only the eleven baked decorative cart pieces (source manifest indices 305–315) that overlap the functional cart; retain rails and all other scenery.
- HC round HUD and test connection door: change their Round 1 instruction
  literals. No source mining Blueprint, input, persistent map, cave source meshes,
  Player asset, project setting or runtime C++ change belongs to this slice.

The resource guard requires valid loose/held rocks plus spawnable rocks to
cover the remaining cart quota and `max(0, active plates - living players)`.
Loaded or lost rocks do not count. Unbroken deposits also require a valid
pickaxe. This allows viable survivors to continue and routes overfill/lost
resources through the existing three-second round retry. Round 3 flare and
Round 5 lever rules remain the source builder's behavior.

The native retry inventory proves this order: recover the roster, dispatch the
shared reset, then StartRound. The existing retry snapshot remains true until
`RestockAfterCheckpointRetry` clears it. A guarded Core hook resets cart,
deposits and inherited pickaxe state only during a Round 1 checkpoint retry.
The bounded Core hook explicitly covers native cart/deposit/pickaxe reset functions rather than relying on every mining piece being reached by the global reset dispatch.

## Recorded placement gate

Native batch duplication initially scrambled the puzzle's deposit array.
`clone-diff.json` identifies that exact mismatch; all other instance fields and
links matched. The revised placement explicitly maps the original typed array
through source-to-clone identities before full property validation. A UDP
transport editor crash discarded the first unsaved attempt; its finalizer did
not execute. After a clean relaunch, the revised initial stage passed and saved
only the two derivative maps. `placement.json` records all 11 exact remapped
instance-property proofs, preserved unrelated actors and protected source bytes.

Loading/inspecting Blueprints can mark packages dirty in memory. Readback is
not permission to save protected packages. Every mutation stage has partial
and error receipts; do not repeat a failed stage over unknown editor state.

## Reproduction

`replay.py` adapts only the original scripts' project/output path guards for the
current project. It does not rewrite their gameplay expressions. Execute it in
the root-controlled editor with an `ARGS` dictionary, a stopped PIE for authoring,
and the exact own lock snapshot in `Saved/PlayableState/Mining/leases.json`.

Stages: `inventory`, `retry_inventory`, `rpc_inventory`, `place`, `prepare_core`, `patch_core`,
`trigger_pickaxe`, `transaction`. Fresh authoring requires the original baseline
state. Placement refuses existing mining actors; Core refuses an already-added
retry function or different native baseline. Never run old full scene builders.

`trigger_pickaxe` checks the complete-team pad through owning movement, selected
owner pickup, swing-context isolation and Drop cleanup. Its physical-E mode
observes the key supplied to the correct PIE window; action injection is
separately labelled. `transaction` supports completion, wipe and lost-rock
cases, with owning swing/pickup/load/push input and explicit approach/released-
rock settling or damage/loss fixtures. Host split uses 3/4 total players with
a remote peer; this Runtime does not qualify a pure two-local-only topology.

Root must record actual head, topology, input method, log intervals, compile
and saved readback. Continuous maze/climb/chase, full results/restart, physical
controllers and broader Mac/Windows acceptance remain separate gates.

The first two-player completion run stopped at the first rock pickup because
the harness immediately compared server/client actor names and carry fields.
`evidence/diagnostic-first-completion-joining-2-owner0.json` preserves that
failure and `diagnostic-first-completion-source.py` preserves its exact source.
Dynamic actor names do not identify replicated rocks across worlds; the peer
owner's replicated `CarriedItem` reference does. The corrected native run proves
server rock `C_0` is client 1's held `C_1`, and server `C_1` is client 1's `C_0`.
All first-deposit hold checks converged on the first poll. The old name match
would inspect a free sibling; this was a harness defect.

The next trigger run proved the mining instruction on all three GameStates and
both owning HUDs. Its parent driver intentionally stopped PIE after 60 seconds
while the gate awaited Drop; the resulting roster/cleanup errors invalidate the
overall gate. The receipt, exact source and parent-confirmed classification are
preserved as `evidence/diagnostic-trigger-objective-*`. The subsequent pulse
change records actual first positive injection, releases relative to that
clock, clears actions at phase changes and settles results after release.
The two-player trigger now passes all four checks, including live objective
data on both owning HUDs. The completion attempt passes eight checks: actual
three-swing first-deposit break, three owning rock loads, and plate reveal.
It then records zero hits for the first swing at deposit slot 1. That failure
and its exact source are preserved as `diagnostic-second-deposit-swing-*`.
The focused read-only trace/input diagnostic is recorded below. These harness
corrections changed no gameplay Blueprint; full mining completion/retry and
the remaining player/topology matrix were still unaccepted at that point.

The trace diagnostic then hit the intended slot 1 boulder with correct carrier,
attachment and swing mapping. Client swing time advanced while authoritative
swing time stayed at the first deposit. `diagnostic-swing-trace-*` preserves
that run and the exact queued source. Native `rpc-inventory.json` shows the
owning character's RPC forwards Target to `BeginUse`, which calls `UseAllowed`.
The latter validates distance/state and a separate eye-to-pickaxe-origin line
trace. The successful boulder trace does not establish that validation ray.
The frozen `swing_probe` skips rock processing and reproduces rejection with
distance 26.3 cm, permitted holder, and no blocked/Downed state. `UseAllowed`
returns false because its eye-to-held-pickaxe ray hits copied scenery
`Cave_procedural_320`; the boulder swing ray remains correct. The confirmed
predicate and exact frozen source are preserved as `diagnostic-held-los-*`.
An additional root-held Character lock reserves a narrow Boolean-return
splice that allows the authoritative carried item after the original gates.
The four-pure-node patch is now compiled with warnings treated as errors and saved under the additional Character lock. `held-use-summary.json` records 51 original nodes and all 69 other graphs preserved, no new execution wiring, functions or variables. Native contextual operator creation removed four original Target fan-outs; the strict audit prevented saving, and the bounded continuation restored exactly those four links before repeating the full proof and saving only Character. The original v2 and continuation sources and their receipts are preserved. Authoring requires the original recorded baseline; do not rerun node creation over an unknown or already patched graph. Runtime regression is recorded separately below.

## Copied cart obstruction

The focused native probe moved the loaded cart 13 cm before its eye-to-cart validation and focus ray hit `Cave_static_310` in the HC cave copy. Source manifest indices 305–315 identify the eleven overlapping decorative cart pieces (four wheels, floor, four walls and two rims). `remove_copied_cart.py` checked every exact mesh/transform against that source, retired only those eleven static actors through the editor, proved all other 1,699 actor snapshots unchanged, and saved only the HC cave-copy map. All 54 other protected source-package hashes remain unchanged. The original HZ cave, rails and mesh assets remain intact. This additional map scope supersedes the initial read-only cave-copy baseline; the old baseline is retained in historical receipts.


## Latest transaction reproduction

`transaction` selects `executed/acceptance_transaction_v6.py`; the earlier frozen diagnostic stays intact. The latest helper also parks the held-pickaxe miner after each broken boulder so its capsule does not obstruct the collecting player’s approach. It uses actual owning inputs, bounded replication of each owner’s CarriedItem reference, one-time relocation of each ghost outside the room, approach/aim fixtures and settling of the free pickaxe after native Drop. It accepts only an unprocessed rock from the current deposit when physics chooses a valid sibling. Cart arrival requires the replicated Arrived flag and actual track-end position, rather than mirroring its internal distance accumulator. These fixtures isolate mining transactions; they do not qualify continuous traversal or chase survival.

The external serial task bridge avoids console autocomplete during PIE. This test session temporarily uses screen percentage 25 and hardware occlusion queries disabled after a Metal/editor stall before readiness. Neither setting changes saved project configuration. Rendering, performance and audio are not qualified by these transactions. The interrupted start and the preceding replication deadline failure are retained separately.


The original three-player pad fixture kept the final owner walking during the three-second team hold and timed out. The v2 trigger stops that owner on native overlap, records the overlap/positions and passes without changing the StartPad Blueprint. A four-player v5 rock pickup later timed out with the held-pickaxe miner standing between the collecting pawn and the free rock. That receipt is retained; capsule occlusion is the fixture hypothesis, not a demonstrated gameplay fault. The v6 transaction parks the miner after native boulder break before rock collection.

The final scoped compile/save rewrote package bytes. Historical patch receipts and hashes remain unchanged. [Final graph proof](../evidence/final-graph-proof.json) independently reloaded and matched all 12 Ghost graphs to the tested native patch, the final UseAllowed graph to its preserved splice and all 69 other Character graphs to their original baseline. All 55 protected package fingerprints (including the explicitly retired decorative-cart copy) match. The readback saved no package.


## Qualified native transaction matrix

The [terminal matrix](evidence/matrix-summary.json) passes **six fresh-PIE cases, 24 trigger checks and 119 transaction checks, with zero scanned native errors**. Room completion passes at joining 2/3/4 and four-player host split (two host locals plus two joining clients). The split mining owner is independently verified as the non-primary host-local controller. Two-player wipe and minimal lost-rock cases naturally retry once after three seconds and restore all peer health/checkpoints/cart/deposits/pickaxe state.

The actual room checks are 20 at two players, 21 at three, and 26 for each four-player topology. Earlier failures and exact versions remain separate evidence. The v5 helper was executed at 2/3; v6 parks the miner during collection and was executed at both four-player topologies. v2 trigger stops the final player inside the pad for the required hold. Portable path adaptation remains syntax checked only.

These are mining transactions with the fixtures listed above, not full-mission acceptance. Larger-roster recovery, uninterrupted maze/climb/carrier return, live threats, results/restart, Windows and physical input remain open. The HUD instruction is qualified as owning data; its rendered overlay remains an independently recorded blocker.
