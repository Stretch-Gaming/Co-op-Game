# Ghost backoff regression and target qualification

Flare repulsion replaced `BackoffUntil` with `now + 0.2`, shortening a longer
headlamp or contact-damage backoff. The repair makes that deadline
`Max(BackoffUntil, now + 0.2)` in `BP_Ghost.RefreshFlareRepulsion` only.
It splices two pure nodes into the existing data connection; original nodes,
execution links, events and other graphs remain intact. The existing target
validity guard and named speed/damage scaling repair are preserved.

Source: [chase authoring](../../six_round/player/chase.py),
[headlamp backoff](../../playable_game/build_headlamp_ghosts.py),
[named scaling repair](../../pg8_tools/fix_scaling.py), and the
[shared contracts](../../../../docs/sprints.md#shared-contracts).

## Recorded bounded result

The actual two-client native Q/F baseline reproduced the defect: the deadline
fell from `18.478` to `18.211`. The final version passed the same three checks.
The completed matrix passed **18/18 cases, 47 check entries, zero native log
errors**: five cases for each actual 2/3/4-client roster, plus death retarget,
flare safety and overlapping backoff on a four-player host-split topology.

[Compact native evidence](evidence/summary.json) records the baseline/final
assertions, topology and log checks, raw receipt hashes and the saved Ghost
fingerprint. [Owner's matrix receipt](evidence/matrix-summary.json) retains the
case outcomes. The patch audited 12 graphs: all 24 original repulsion nodes,
original execution links and 11 other graphs were preserved; two pure nodes
replace only the deadline data edge. Ghost alone compiled with warnings as
errors and was saved. The existing target guard stayed intact.

The editor owner executed the scratch helpers. The portable versions here
change import/checkout guards, output locations and platform metadata; they
have static validation, not a second native matrix. Raw megabyte graph dumps
and frame snapshots are omitted. This is bounded qualification, with the
remaining acceptance below still open.

## Portable helpers

| File | Purpose |
| --- | --- |
| `context.py` | Resolve the repository root and verify the live editor project and raw output path. |
| `inspect_ghost_targets.py` | Read graph DSL, native pin wiring and scaling rows without changing assets. |
| `patch_ghost_backoff.py` | Validate the original deadline wiring, splice the Max, audit preservation, compile with warnings as errors and save only Ghost; report errors and rollback. |
| `test_ghost_targets.py` | Run the bounded ghost/light/death/target regression against actual network owners. |
| `ghost_runtime_support.py` | Shared runtime queries, owning input and disclosed test-fixture support. |
| `collect_evidence.py` | Extract compact actual report/log evidence into `evidence/summary.json`. |

Only the parent may execute editor scripts. Serialize all editor calls;
stop PIE before patching, and never run a full legacy builder.
These helpers use a repository-root guard rather than a machine-specific
Windows path. Existing Windows-guarded authoring helpers are not rewritten.
Runtime output and default `args.json` live in `Saved/PlayableState/Ghosts/`.
Provide an `ARGS` dictionary or use that arguments file. Keep logs and failed
reports alongside successful runs; a queued callback is not a passed gate.

## Required acceptance matrix

Start each independent runtime case in a fresh Lobby of the assembled
six-round test map, with settled ownership and actual replicated rosters:
2, 3 and 4 joining clients, then 4 players comprising two host-local owners
and two joining clients. Report each topology separately; changing a scaling
row on a two-player fixture does not prove a larger roster.

Q and F use native owning Enhanced Input and their normal server path.
Disclose ghost spawning, initial positioning, damage and destroyed-pawn
fixtures separately from those inputs. Destroying a pawn is not a real
disconnect or GameMode `Logout` test. Observe target validity/death handling,
flare safety and expiry, headlamp backoff, replication, owner isolation and
deadline preservation while light sources overlap. Review the Output Log.

The recorded host-split subset omits all-dead and destroyed-target cases.
Continuous cave-to-maze-to-results traversal, carrier-first
chase/contact damage, real logout/rejoin, packet emulation, physical devices
and rendered/audio acceptance remain unproven by this focused workflow.

## Reproduce a runtime case

Open `/Game/Puzzles/Test/SixRound/L_SixRound_Test` in the matching checkout.
For joining tests, use Play As Client, 2/3/4 players, and Run Under One Process.
For the four-player split test, use a listen host with two joining clients and
add the second host-local owner through F5 while still in Lobby. Wait until
all owners are possessed and their input contexts and ColorSlots agree.

Write `Saved/PlayableState/Ghosts/args.json`, for example:

```json
{"players":4,"profile":"host_split","owner_ordinal":0,"case":"flare_backoff"}
```

Execute `test_ghost_targets.py` through the editor's Python command box. Wait
for `Saved/PlayableState/Ghosts/ghost-CASE-PROFILE-N.json`; verify `passed`,
cleanup, topology and the matching native Output Log interval. Stop PIE after
each case: lethal/deleted-pawn fixtures are intentionally not resurrected.
The cases are `retarget_death`, `all_dead`, `flare_all_safe`,
`destroyed_target` and `flare_backoff`. Do not run another callback concurrently.

## Collect durable evidence

The collector runs in ordinary Python, never in the editor. Supply the native
patch receipt, baseline failure, completed runtime directory and optional native
inventory. It retains source hashes and compact log/check summaries, and omits
full graph dumps and frame snapshots. Raw output belongs in ignored `Saved/` or
scratch storage. Do not claim the newly portable scripts were executed when the
matrix used their scratch versions; record those actual script receipts.

```sh
python3 Tools/unreal/playable_state/ghosts/collect_evidence.py \
  --patch-report <raw>/ghost-backoff-patch-report.json \
  --baseline-report <raw>/baseline-flare-backoff-joining-2.json \
  --runtime-dir <raw>/runtime-evidence \
  --inventory-report <raw>/ghost-target-pin-report.json \
  --executed-script <raw>/test_ghost_targets.py \
  --executed-script <raw>/ghost_runtime_support.py \
  --complete --host-split-case retarget_death \
  --host-split-case flare_all_safe --host-split-case flare_backoff
```

`--complete` requires all 15 joining cases and the named host subset to exist;
it preserves failed and unknown-log states. Missing receipts never become passes.


The later warning-free final compile/save rewrote serialized package bytes. The historical matrix/patch hashes remain unchanged in this packet. The [final read-only graph proof](../evidence/final-graph-proof.json) reloaded the final saved Ghost and matched all 12 graphs exactly to the native-tested patch snapshot. No package was saved by that proof; its final fingerprint identifies the published binary.
