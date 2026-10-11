# Interrupted taking fade cleanup (PG-6, #93)

This helper patches only `BP_TakingDirector` on PR127 candidate
`42762fcaa07a396f06098131dc1184c468556794`. It preserves the original scheduler,
victim selection, teleport, protection and presentation bodies. The three entry
splices and single fade-call replacement cache the actual local owning
controller before replicated Victim is cleared. Cleanup clears only the fade
this director owns; Hide during the active black interval preserves that fade.

Run only inside the reserved private editor through its worktree/PID-specific
queue. Supply `ROOT`, `QUEUE` and `ARGS.action`. The supported sequence is
`inspect`, reproduce the unmodified failure, stop PIE, `apply`, `audit`, regression
PIE, stop PIE, then `save`. Apply does not save. Save writes only this package.
No authoring builder is imported or executed. Never run against the primary
editor or during PIE.

Mutation requires a fresh queue `mutation-guard.json` with the editor PID,
baseline `head`, verified owned lock (`path`, `id`), `owned_lock_verified: true`,
and current Unix `epoch`. The executor must independently re-fetch PR127 and
verify the reservation before issuing the receipt. This particular reservation
is intentionally pinned in the helper; a later executor must reconcile it.

The native audit fingerprints all original graphs, checks that only the three
named original graphs changed, checks anchored calls, and reads back only the
four new helpers. A complete matching installation is a no-op; partial or
different installations stop. Compile treats warnings as errors. Failed apply
must remain unsaved and be investigated before continuing.

Acceptance evidence distinguishes server scenario fixtures from real owning
Enhanced Input and rendered screenshots. Two-player client and host split checks
do not establish 3/4-player, physical controller, audio listening or natural
route acceptance. See the accompanying validation report for actual results.

`regression.py` reuses the private queue's reviewed `pg_harness`/`common` owning
input harness. It supports `ARGS.case` values `cancel-pre`, `cancel-post` and
`normal`, with unique `run`, `profile` (`joining` or `host_split`), `players: 2`,
`patched: true` and a bounded `timeout`. Cancellation uses authoritative
`FailRound` at `cancel_age` (0.45 or 0.85 seconds). `repeat_cleanup` exercises late
Reset/Finish/Hide after retry. Screenshots and timelines require rendered review;
a state-only `passed` flag is insufficient.

Optional `target_slot` uses an explicit, temporary server survivor fixture:
ApplyDamage on the intended victim, ChooseRemainingPlayer while the other player
is the sole survivor, then ResetHealth before the unchanged scheduler takes the
intended victim. Optional `style` advances the existing NextPresentationStyle
function at most three times before taking. These fixtures do not prove natural
selection, death recovery, user input, or style distribution. The normal check
calls Hide during black, captures the post-teleport black interval, and captures
normal release. It never forces cleanup, fade amounts or cached references.
