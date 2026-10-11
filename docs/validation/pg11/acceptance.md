# PG-11 view acceptance preparation

Issue [#30](https://github.com/Stretch-Gaming/Co-op-Game/issues/30), related
[#23](https://github.com/Stretch-Gaming/Co-op-Game/issues/23),
[#24](https://github.com/Stretch-Gaming/Co-op-Game/issues/24) and
[#93](https://github.com/Stretch-Gaming/Co-op-Game/issues/93).
Prepared October 11, 2026 by PK, lane PG, Mac 1, thread `thr_47qsqyxjpw`.

**Status: offline source/evidence audit and prepared scenarios. No new native
runtime pass, visual acceptance, asset repair or issue closure is claimed.**
The tools worker owns the first editor slot. Native checks require its explicit
handoff after verified editor closure and settings restoration.

## Exact baseline and ownership

Clean worktree started at current `origin/main`
`fea4e5115b1e6ceffa142cd696adfb2c4b977bb9`. PR127 landed at
`073defcb77c39e5209daf229b93604358049e2aa`; subsequent main includes PR120 and
PR121. The accompanying [source manifest](source-audit.json) records baseline
asset fingerprints and read-only source inputs. A future test must pin its own
exact saved head, rather than call this baseline an executed candidate.

The existing PG camera and spectator package is
`Content/Player/AC_PlayerView.uasset` (`/Game/Player/AC_PlayerView`). There is no
separate spectator component in the inspected tracked Player inventory.
Potential new fixtures belong only under
`Content/Player/Test/ViewAcceptance/`; none were created for this report.

Core owns `BP_CoopCharacter`, `BP_CoopPlayerController`, GameMode, GameState,
GameInstance, input contexts and travel/restart. HUD packages are HC-owned under
`Content/Puzzles/UI/`. `BPFL_SplitScreen` is PG-owned but outside this task's
binary write scope. All are read-only for this worker. The explicit child task
authorizes "your assigned PG packages plus your narrow text/evidence files" and
asks to publish a "source audit or read-only evidence report first". These two
PG-11 evidence files use that narrow authorization; no cross-lane binary edits
or locks are included. No Tools, Config, maps, shared assets, traversal,
ghosts, tools or TakingDirector edits are included.

The black-screen cancellation repair is already saved in main's
`BP_TakingDirector`: LFS SHA-256
`ce5d9f9063d41a8d53dc865affeea01e87d08c47b9752318a8022bcc916529f3`.
Preserve that package and its owning-camera cleanup. Do not replay authoring
scripts to rebuild delivered systems.

## Source reconciliation

These are source observations, not fresh native saved-graph validation:

- `Tools/unreal/pg1_player_view/README.md` describes an earlier delivery that
  was held back under locks. Its 0.25-second blend, component RPC and 40/64/94
  Mac assertions do not establish the current production graph or its rendered
  behavior.
- `Tools/unreal/playable_game/align_delivered_view_contract.py` describes the
  later production alignment: first possession snaps; subsequent arm changes
  move toward 0/380 cm at 1266.6667 cm/s on a 0.05-second refresh; FOV is 90/75;
  socket Y is 0/45 and Z is 65. Facing mode is applied on every peer; camera/body
  visibility is applied on the owning pawn. Confirm actual saved values before
  using these as runtime expectations.
- `Tools/unreal/six_round/player/spectator.py` writes the existing PG view
  component. It chooses living teammates by ColorSlot 0–3, excludes its owner,
  advances/wraps the selection, validates the target every 0.05 seconds, refreshes
  its replicated mode/aim locally, and blends only its owning controller's
  ViewTarget over 0.2 seconds. When alive again, it clears the selection and
  restores the owner's pawn. Missing/invalid targets are guarded.
- The Core hook sends dead Interact to the owner's `CycleSpectator`, before
  gameplay interaction. This hook, health and GameMode recovery remain HC/HZ
  dependencies, not reasons to edit their assets here.
- `presentation_hooks.py` adds a timed headlamp visual blackout to PlayerView;
  its broad authoring also touches Taking/Ghosts and must not be executed by this
  task. Camera fade cancellation is the separately delivered TakingDirector
  repair documented in `player/fade_cleanup/VALIDATION.md`.
- `player/generated-dsl.json` contains older null-comparison spectator bodies,
  while `spectator.py` uses validity helpers. Neither source file alone proves
  which nodes are saved today. Native bounded readback must resolve that before
  diagnosing a defect.

## Historical evidence and its limits

| Evidence | Candidate / platform | Actual coverage | Does not establish |
| --- | --- | --- | --- |
| PR127 `Tools/unreal/six_round/VALIDATION.md` | Windows candidate based on `9dc0fab`; see PR127 for delivery | 2/3/4 owning controls, four-player host split, second-keyboard bridge; host + joining client two transaction runs/results/restart | Current exact-head Mac checks, physical devices, complete route, both split owners across travel; Windows used D3D11 after reset |
| [Mac smoke comment](https://github.com/Stretch-Gaming/Co-op-Game/pull/127#issuecomment-6103548634) | `42762fcaa07a396f06098131dc1184c468556794`, Mac Metal | Two actual joining clients and a separate host split pair: owning view/lamp/control isolation; rendered pair observed | Death/spectator, joining peer with the split pair, travel, complete HUD or physical-device acceptance |
| `Tools/unreal/six_round/player/fade_cleanup/VALIDATION.md` | Repair branch `pg/pg6-taking-fade-cleanup`, baseline `42762fc`; local fixed-head report identifies `2cdfe396` | Rendered interrupted/uninterrupted taking for both local panes; two joining clients; legacy `L_Site01` view/control gates | Fresh combined-head runtime, complete route, physical input, 3/4-player fade acceptance; whole historical log includes failed Python harness runs |
| Local `/tmp/pg127-batch/functional-count-acceptance.md` | `42762fc`, Mac | Three-client and host + two-client roster prerequisites; partial controls | Completed 3/4-owner or death checks; sustained pressure caused stop |
| Local `/tmp/pg127-batch/post-merge-validation.md` | `f064dc7b1aba38234714d1036ef0be3bb4f06b81`, Mac | Saved loads; two warnings-as-errors compiles (TakingDirector/AdventureTrap); world creation | **No fresh gameplay gate passed**: null PlayerStates/readiness timeout occurred before fixtures/input; 9% free-memory observation, long net ticks and audio underruns |

Local historical artifacts are context, not shared runnable evidence links.
The combined report states its tree matched the PR127 landing tree; equality
does not turn an earlier runtime result into a new runtime pass. The current
main baseline is later again. No issue acceptance box can be ticked from this
audit alone.

## Prepared exact-owner scenario matrix

For every executed slice record commit, map, engine/changelist, resource samples,
wall-clock start/end, topology, each LocalPlayer's controller, PlayerId and
ColorSlot, owning Enhanced Input subsystem, pawn, HUD and ViewTarget. Compare
replicated peers within their own worlds. Never select a gameplay owner by
player/controller/pawn index zero. Wait for complete non-null PlayerStates,
matching roster/slots and installed input contexts; stop at a bounded readiness
deadline rather than inject into an incomplete roster.

| Gate | Topology / steps | Expected observations / evidence |
| --- | --- | --- |
| V1: fresh owner state | Candidate `/Game/Puzzles/Test/SixRound/L_SixRound_Test`; host creates secondary through its existing owning add-player action | Both panes have distinct owner controllers, own pawns/ViewTargets, own HUD/prompt and first-person camera. Read FOV/arm/mesh visibility and capture the actual two-pane window |
| V2: independent switches | Primary V press/release through its subsystem; wait for arm settle; repeat secondary; restore both | Only intended ViewMode changes; arm converges and FOV matches native saved contract; remote peers agree on facing; review glide/body visibility in both panes |
| V3: tight passage/climb | Existing safe passage and climb fixture, each owner in third person, then first | Arm collision retracts without entering walls/body; owning prompt remains in its half; inspect climbing transition and interruption. Approach teleport, aim or traversal setup is disclosed separately from physical route traversal |
| V4: each dead pane | Stable R2/R4 after taking protection ends; authoritative lethal ApplyDamage fixture for one chosen host owner at a time | Dead owner follows a living teammate; other owner retains its own camera/HUD. Dead Interact action cycles bounded living slots; target's mode/aim is applied. With one survivor, selection remains that survivor; this does not prove multi-target cycling |
| V5: recovery/invalid target | Existing GameMode recovery fixture; later distributed 3/4-player target death/disconnect | Regroup/retry restores own pawn camera/HUD without lingering fade or old SpectatedPawn. GameMode-only restart/clear calls are disclosed scripted transactions, not natural regroup/route completion; destroyed/dead targets must be rejected |
| V6: results and return | Repeat V1/V2/V4 before travel; use existing CompleteMap/host restart path with HC, record actual destination then return | Track both local owners across new worlds/controllers/pawns, not UObject identity across travel. HUD belongs to correct controller, remains in correct half, removes stale instances; repeat fresh view toggles, death/cycle/recovery after return. Report native default vs preserved view mode explicitly |
| V7: joining-owner isolation | First bounded Play As Client with 2 players on candidate; then host pair + 1 joining client only if safe | Real NM_Client owners exercise Blueprint input/RPC path; joining client's HUD/view/spectator is independent of both local panes. Separate client-only and pair-only tests cannot certify this combined topology |
| V8: required legacy smoke | `/Game/Maps/L_Site01`, Play As Client with at least 2; separate host pair | Exact-head owner camera/input and logs; distinguish legacy evidence from production candidate evidence |

Action injection is synthetic input through each actual local-player Enhanced
Input subsystem; it is not keyboard mapping or physical gamepad acceptance.
Direct Python RPC invocation is not input/network proof. Lethal damage, safe
approach teleport, CompleteMap and GameMode restart/clear are named fixtures;
none proves continuous route, natural hazard death or full mission acceptance.
No fixture should force ViewTarget, FOV, spectator selection, fade amount or HUD
ownership to make assertions pass.

## Resource budget and distributed handoff

Preflight disk was 8.1 GiB free. Do not package: the 30 GiB prerequisite is
unsatisfied. Do not remove another worker's caches/files or open another editor.
Use one private PID/project guard and sequential editor calls after the tools
worker's explicit closure handoff; never attach to port 8000. Snapshot own and
affected global transient INIs before launch, disable autosave transiently,
restore original settings/bytes/absence after zero PIE and normal private exit.

Prior count slices stopped after pressure above baseline level 1 sustained ten
seconds. Use that conservative stop again, plus bounded roster/scenario deadlines;
capture stop state and cleanup rather than escalating to more worlds. Start with
the host pair. A joining-only two-client slice is separate. The combined pair +
joining client is conditional, and 4-player single-Mac escalation is not planned.
Keep gameplay/network/physics settings unchanged; disclose any render reduction.

If native checks are blocked, retain exact unmet prerequisites and publish the
partial result. PK/HC should coordinate a common saved commit on Windows host
(two physical local gamepads) plus Mac 1 and Mac 2 joining for four owners;
also run 2 and 3 owners on that same head. Check both panes' HUD, FOV, collision,
climbing/glide, dead cycling/recovery before results travel and after return.
Preserve per-machine logs and screenshots, controller/slot inventory and physical
device identities. Windows normal graphics, actual network delay/disconnect and
the complete physical route remain separate unexecuted gates until measured.

Only reproduced view defects confined to the existing PG component justify a
repair here. Compile any changed Blueprint with no errors, test owning client
and split regressions on its exact saved head, inspect errors/Accessed None and
verify no other packages saved. Hand HUD/input/travel/recovery contract defects
to HC with before/after owner evidence. PK/root retains merge ownership and
[#30](https://github.com/Stretch-Gaming/Co-op-Game/issues/30) stays open until the
complete Done-when passes.
