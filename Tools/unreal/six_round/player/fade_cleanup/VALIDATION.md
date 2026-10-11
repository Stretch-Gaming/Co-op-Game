# PG-6 taking fade cleanup validation — PR127 dependent candidate

Baseline: `42762fcaa07a396f06098131dc1184c468556794` on
`codex/six-round-adventure`, based on `9dc0fab`. Fix branch:
`pg/pg6-taking-fade-cleanup`. Mac Unreal 5.8.3, one private editor PID 77354,
port 8001. Parker's production integration remains authoritative. #93 remains
open; this is a draft repair, not full game acceptance.

## Reproduced defect and change

An unmodified two-client R2 taking interrupted by the server FailRound fixture
at age **0.473 s** left the actual victim's client window black through failure
and same-index retry. The witness rendered normally. State-only harness success
did not establish rendered success. Screenshot
`cancel-pre-joining-auto-auto-retry-w3.png` reproduces the black victim.

Only BP_TakingDirector is saved. PlayTakingVisual, FinishTaking and
HideTakingPresentation receive entry splices; the existing manual fade call
becomes an owning fade helper. Four local, nonreplicated cache fields retain the
actual victim pawn/controller and schedule before Victim clears. Cleanup checks
cached local controller and its own camera manager, releases the fade this
director owns, then clears the cache on every path. Reconciliation preserves the
existing 0.35–1.15 s active blackout. The replacement preserves original amount,
color and audio inputs. Original scheduler, protection, teleport, audio and other
presentation bodies remain intact. No indexed controller/pawn/camera lookup is
introduced.

Native compilation passed with warnings treated as errors. Native graph audit
verified 23 original graphs unchanged, only three original graphs modified,
every retained original node's type/pin/default contract preserved, and owning
camera-property getters. Only four new helpers were read back as DSL. Repeated
complete apply was a no-op. Explicit package-only save succeeded after audit.
No other package or settings asset was saved.

## Runtime results

All rows use the candidate L_SixRound_Test unless stated otherwise. Rendered
screens were reviewed separately from machine state assertions.

| Gate | Result / exact bound |
| --- | --- |
| Dedicated server + two actual joining clients, cancel before teleport | Pass: age 0.478, style 0, owner slot 0; victim black before cancellation, both scenes restored on failure/retry, cache/protection cleared without death |
| Two clients, cancel after teleport | Pass: age 0.890, style 0, Teleported true; rendered scene restored; own controller ViewTarget retained |
| Host split secondary owner cancellation | Pass before 0.475 / after 0.887 s, style 0; owning cached controller and rendered restoration, both local panes visible afterward |
| Host split primary owner cancellation | Pass before 0.471 s/style 2 and after 0.856 s/style 1; explicit survivor/style fixture disclosed below |
| Host split uninterrupted taking + active Hide | Pass styles 0, 1 and 2; screenshots at about 0.8 s show victim pane still black after Hide, witness pane visible; completion restores scene and clears cache |
| Late repeated cleanup | Pass ResetTaking(2,2), FinishTaking and each owner-world Hide after retry; cleared cache stays clear, no camera blackening |
| Retry replay | No taking replay observed for six seconds on each completed cancellation run; same R2 attempt 2, alive/unprotected players and own ViewTargets |
| **Legacy L_Site01**, Play As Client, two players | Pass: dedicated server + two NM_Client worlds; each actual owning Enhanced Input subsystem drives view/headlamp, move/sprint/release and flare; replicated readbacks and other-owner isolation |
| **Legacy L_Site01**, host split pair | Pass: actual primary F5 action creates second local player; both owners independently exercise the same controls, releases and flare ownership; split screenshot captured |

Inputs above are synthetic Started/release events through actual owning local
Enhanced Input subsystems and ordinary Blueprint input/RPC paths. They are not
physical device acceptance. Taking cancellation is an authoritative scenario
fixture, not user-input network proof. Split has one listen-server world with
two owning local controllers; it does not prove a remote RPC by itself.

The optional primary/secondary selection fixture applies lethal damage to the
intended victim, calls the existing ChooseRemainingPlayer while only the other
player survives, then calls that victim's existing AC_Health.ResetHealth before
the unchanged scheduler starts taking. The optional style fixture advances the
existing NextPresentationStyle at most three calls so the subsequent native take
uses the specified style. These operate only in PIE and do not prove natural
survivor recovery, victim/style distribution, or route completion. Hide and late
Reset/Finish are explicitly recorded presentation fixtures. No fixture forces
fade amount or cache cleanup.

## Logs, setup failures and limits

There are **zero Accessed None warnings, zero non-Python engine/Blueprint error
lines and no fatal/assertion crash**. Each completed fade case's exact timeline
has zero error lines. L_Site01 client/split runtime also has zero error lines.
The editor exited normally via QUIT_EDITOR.

The **whole session log is not clean**: it contains **7,163 Python error lines**
from the executor stopping an asynchronous post-cancel run before its report
completed. Its callback then referenced a destroyed PIE world. The callback was
explicitly removed; a guarded host-side driver waits for report completion,
and the exact post-cancel run was repeated successfully. Failed evidence is
preserved. The regression helper now unregisters through its original cleanup
even when finish-time evidence capture fails.

Other harness/preflight failures were corrected without saving bad graphs:
truthy empty native pin wrappers, unexposed NodeComment reflection, Unreal Array
JSON conversion, a null object template default setter, and a cleanup flow whose
reset initially reached only the false branch. Both incomplete graph transactions
were undone and baseline inventory verified before corrected compile/audit.
Instance-edit-disabled selection setters and an editor-rejected console setter
were removed; successful fixtures use existing runtime functions above. None of
these setup failures is reported as a new candidate runtime defect.

65 bounded resource samples recorded 15–29% free memory, maximum used swap
7,100.25 MiB, and 35 pressure-level-2 samples. First pressure2 was during the
joining post-cancel check at 00:33:11 UTC (20% free, 6,588.69 MiB swap). PIE was
stopped between gates; the host pair was prioritized. **3/4-player fade regression
was not run**, and no OOM/near-crash claim is made. Closure pressure was level1,
76% free. Joining-client uninterrupted styles 1/2, physical keyboard/gamepad, ears listening/audio one-shot counts, actual
packet delay/reordering, disconnect/invalid-controller expiry, full physical
route and complete team acceptance remain pending.

## Scope and closure

Original baseline branch/worktrees were preserved. Exact own LFS reservation
56118904 covered only `Content/Player/Taking/BP_TakingDirector.uasset`; no world
lock or forced unlock. The editor was closed before pull/rebase or push, zero PIE
and no dirty packages verified, native play/performance preferences restored,
all seven existing INIs byte-verified and generated INIs archived/removed.
All **3,074 other tracked hashes** remain unchanged. Reserved package SHA256:
`ce5d9f9063d41a8d53dc865affeea01e87d08c47b9752318a8022bcc916529f3`.
Lock release is performed after push and recorded in the publication receipt.
No port8000/8002 editor or unreal-mcp connector was used.

Local evidence is preserved under `/tmp/pg127-batch/fade-runtime/`; reports:
`fade-fix.md`, `fade-fix.json`, `fade-closure.json`, `fade-log-summary.json`, native
apply/audit/idempotency/save receipts and screenshot hashes. `evidence.json`
records exact run timelines/fixture summaries, native readback, resources and
pre-publication closure. Original mac-smoke/lifecycle reports remain separate.
