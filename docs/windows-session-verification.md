# Windows session verification for Stretch

HC-QA2 ([#75](https://github.com/Stretch-Gaming/Co-op-Game/issues/75)) owns the
tools under `Tools/qa/playtest/` and this checklist. It supplies evidence to
[#58](https://github.com/Stretch-Gaming/Co-op-Game/issues/58); it does not replace
that checkpoint's checklist or close its Mac acceptance requirements.

## Evidence inventory, 2026-10-10

The fresh worktree began at latest `origin/main`, full commit
`dcecbab75999f1cc976d847a24912f4246ddbc8e`. This is the inventory baseline,
**not a published combined gameplay candidate**.

| Existing record | What it establishes | What remains outside that evidence |
| --- | --- | --- |
| [HC-0 verification](hc0-verification.md), recorded at `f1011f9` | UE 5.8.3 CL 58210709; Play As Client at 2/3/4; split views; separate Windows listen host/client via real socket, successful join/welcome and clean logs | Both Macs in one session; physical gamepad routing; later gameplay |
| [Cave integration](../SourceArt/HZ/CaveIntegration/README.md) | Windows 2/3/4-player movement/jumping, split views and environment checks | Mac rendering and cross-machine joining |
| [HC-1 verification](hc1-verification.md), published in `dcecbab75999f1cc976d847a24912f4246ddbc8e` | Client instant/timed/continuous interactions at 2/3/4, independent local prompts/input, debug guards, clean successful intervals and Win64 package startup | Physical device routing and Mac joins; F4 only sets MapComplete here, travel belongs to HC-2 |
| [#58 acceptance audit](https://github.com/Stretch-Gaming/Co-op-Game/issues/58#issuecomment-6093651253) | Existing Windows evidence is accepted as Windows evidence | Both Macs joining and their movement checks remain unchecked |
| [PR #73](https://github.com/Stretch-Gaming/Co-op-Game/pull/73), head `14b967ff417d871c10fac08d7beef075f1994a1c` | Completed read-only asset validator; 33 passes/one privilege-related skip among 34 tests; source audits distinguish pointers and warnings | Still open/unmerged at inventory time; no session/Mac acceptance inferred |
| [PR #74](https://github.com/Stretch-Gaming/Co-op-Game/pull/74), delivery referenced in #20 | Separate HUD-art delivery reports 2/3/4-client and split-view checks | Unmerged delivery evidence does not establish behavior of the future combined candidate |

These are prior records, not sessions performed by this slice. Their original
logs were not copied into this worktree. Do not rerun unchanged green gates.
After integration, identify which changed inputs affect the session checks;
run those checks on the exact combined commit. Preserve the source-asset
validator, its reports, PR #73 and existing host/join scripts.

## Safe preparation and commands

Use Python 3.9+ and Git from Windows. The CLI uses only the Python standard
library. Execute it from this chat's dedicated worktree on
`codex/hc-windows-session-qa`. It discovers the root from its own file; there
is no switch to point it at another checkout. Do not use the original repository
or the shared Unreal MCP connection for this verification slice.

Before changing the candidate checkout, read the OS process command lines and
confirm no Unreal instance is using this worktree's `CoopGame.uproject`. Close
only your own windows, through their native UI, and wait for their processes to
exit. Never replace or hydrate files loaded by a running instance. Never close,
control or change another chat's editor. This harness does not fetch, checkout,
hydrate, save assets, alter settings/firewall, send RPCs or stop processes.

The integration chat must publish a full combined candidate SHA containing the
harness. Bring this QA branch to that exact commit while its processes are
stopped, hydrate its LFS files through Git if needed, and keep it clean. A later
tooling commit is a different candidate: record that SHA and get team agreement.
The CLI refuses short hashes, refs, a mismatched HEAD, a wrong branch, ordinary
checkouts, tracked/untracked changes, runtime LFS pointers, and engines other
than exact 5.8.3. It hashes Build.version, the editor executable, the project and
the harness; records the full Git tree; and rechecks them before each launch and
report. `EngineAssociation=5.8` alone is insufficient.

The examples below are PowerShell. Set `$candidate` to the integration chat's
full 40-character lowercase SHA; do not use the inventory baseline by default.
Replace `python` with your Python executable path if Windows has only an app
alias. `--engine` defaults to `UE_ROOT`, then the normal Epic install.

```powershell
$candidate = '<published full combined candidate SHA>'
python Tools/qa/playtest/session.py prepare --run win-2-solo --candidate $candidate --players 2 --host-local 1
python Tools/qa/playtest/session.py plan --run win-2-solo
python Tools/qa/playtest/session.py start --run win-2-solo --role host --launch
# Wait for native host window, Site 01 and listen readiness; inspect host.log.
python Tools/qa/playtest/session.py start --run win-2-solo --role client1 --launch --host-ready
```

`prepare` creates pending evidence; `plan` prints argument arrays without
launching. Only `start --launch` starts a process. `--host-ready` is the tester's
confirmation that this run's host is ready; it is not inferred from a timer or
a Python gameplay call. Repeat `start` separately for each planned client.
Every process uses this worktree's project with `-game -DisablePython`, native
input, and a real UDP connection. This is an engine-install session, not a
packaged session. No editor instance is needed. If an editor-only inspection is
needed, open a separate instance of this worktree after ending its test run;
do not use another chat's editor or shared MCP endpoint.

Default port is **17777** to avoid another chat's usual 7777 host. Clients use
`127.0.0.1:17777`; `--port` can select another unused port at preparation. The
host launch refuses an already-bound UDP port. A concurrent launch lock prevents
two harness writers; a stale lock requires inspection before manual removal.
Unreal instances with this project's path must match the run's recorded PID and
creation time. Unknown instances or reused PIDs cause refusal. Unrelated editors
are left alone. A role or existing role log cannot be launched twice; use a new
run after manually ending your own processes. If startup exits before PID
inspection, its launch record remains for diagnosis; no automatic cleanup kills
a process. Process inspection requires readable command lines and Windows
PowerShell/CIM and NetTCPIP; failure refuses launch.

All output is under ignored `Saved/WindowsSessionQA/<run>/`: manifest, one log
per role, editable observations, and uniquely named report snapshots. Report
paths cannot escape via symlinks/junctions. Nothing is written to tracked gameplay
or configuration. Do not share raw logs before checking for local paths/IPs.

| Fresh run | Total players | Host locals | Separate Windows clients | Purpose |
| --- | --- | --- | --- | --- |
| `win-2-solo` | 2 | 1 | `client1` | Smallest native network session |
| `win-3-solo` | 3 | 1 | `client1`, `client2` | Three-player scaling |
| `win-4-solo` | 4 | 1 | `client1`, `client2`, `client3` | Four-player scaling and duplicate race |
| `win-3-split` | 3 | 2 | `client1` | Independent local input/HUD plus remote client |
| `win-4-split` | 4 | 2 | `client1`, `client2` | Split pair plus two remote clients, travel restoration |

Prepare each row with its own `--run`, `--players` and `--host-local`; end your
previous run first. F5 adds the second local player through native gameplay,
once in Lobby (or Cleared); the parameter only describes the expected count.
F6 removes them. Never count windows as players when the host has two locals.
A two-local-only session has no separate client and is outside this socket
harness. Lack of a physical gamepad blocks the split input/routing checks;
an additional window does not substitute for independent device routing.

## Native session checklist

For every observation, retain the run ID, full candidate SHA, UTC interval,
tester, window/role, input device and expected/actual result. Capture native
screenshots/video showing each client, both host halves and counters as relevant,
and cite role logs with timestamps/line numbers. Put artifacts inside the run's
directory. Do not mark pass using editor Python RPC calls, direct property
changes, server-only observations or log absence. F1/F4 are existing gameplay
debug inputs; do not bypass their input path with scripting.

1. **Agreement and joining:** compare full candidate SHA and UE 5.8.3 Build.version
   (including changelist) for every machine. The local Windows processes share
   the verified editor executable. Retain startup Engine Version lines and
   host listening/client welcome/join lines. Observe players in Site 01 and
   check 2/3/4 PlayerStates, distinct ColorSlots and Lobby scaling on all screens.
   All participants run/jump and see one another move. Match the data-table rows,
   including both local players; do not hard-code a three-player expectation.
2. **Local input and HUD:** host presses F5 once, then uses keyboard/mouse while
   player two uses the actual gamepad. Move/look/jump/interact independently;
   aim at different targets simultaneously. Each half has its own prompt,
   hold progress and counter with no bleed, duplicates or shared focus. Record
   device model, connected devices, focus and which physical device controlled
   each player. F6 removes only player two; F5 recreates exactly one player and
   one HUD. The second local player and remote clients cannot use host controls.
3. **Relics (HC-2 present):** record starting collected/available totals on each
   screen and the candidate's placed relic values/MinPlayers. Pick up one with
   a remote client's E or gamepad Interact; every screen increases by exactly
   its value, with disappearance/collision removal replicated. Repeated input
   on the consumed relic cannot add again. Two native clients attempt the same
   visible relic nearly simultaneously: only one authoritative award occurs.
   Check bonus availability/scaling at 2/3/4, and no collected/available drift.
4. **Late join:** in a fresh 3- or 4-player run start one fewer client initially,
   collect a relic, then launch the remaining planned client with the same SHA.
   It immediately sees current totals, consumed relic state, phase and expected
   scaling without respawning the pickup. In Lobby, join/leave changes the row;
   after Round 1 begins the row changes only at the next round start per contract.
   Keep this distinct from the full-count run's starting totals.
5. **Carrying (HC-4 present):** a remote client picks up, walks, drops with G/B,
   picks up again; all peers see the same carrier/free state and physics without
   collision snags. Two clients contest one item: exactly one carrier. Heavy
   key/statue movement is half speed for server and owning client without
   correction stutter. Join late while the item is carried and confirm its
   carrier/collision state. If downed integration is available, verify native
   downing releases it; otherwise record that check blocked with its dependency.
6. **First puzzle (HC-6 present):** start Round 1 through the implemented entrance
   (or agreed native F1 fixture), use players/statues to satisfy the plates and
   observe gate/phase on every peer. The candidate's DT_RoundScaling is authority:
   currently 2 players -> 3 plates/2 statues; 3 -> 3/1; 4 -> 4/1. Unsatisfied
   plates must not clear the round; completion occurs once when all enabled
   plates are satisfied. Include the split pair as distinct participants. If
   the candidate has revised these values, record its contract and expected row.
7. **HC-2 travel:** in each total-count run, primary host presses F4 in Site 01.
   Observe every remote client and both local players reach Site 02, then press
   F4 again and observe return to Site 01. Record maps, counts and local player
   identities at all three stages. On both destinations test native movement,
   look/jump, interaction, per-player focus/prompts/counters and view/headlamp
   actions when implemented. There must be exactly the original number of
   locals/HUDs/input contexts, with no extra split player, duplicate handling,
   missing mapping or client left behind. Capture logs throughout reconnect and
   possession. HC-1 phase-only F4 is **blocked**, not a travel pass.
8. **Logs:** after manually closing only this run's windows and confirming their
   processes exited, scan the complete logs from startup through shutdown for
   every planned role. Review Error/Fatal, Accessed None, ensures/assertions,
   missing packages, network/timeouts and TravelFailure as failures requiring
   explanation/correction. Review all ordinary warnings too; retain timestamps
   and hashes. Startup cleanliness does not substitute for a runtime interval.

Carrying and first puzzle stay pending/blocked until the integration candidate
contains those implementations. Do not add assets to make a test pass. HC-2
travel validates connectivity/local-player/input/HUD restoration; **HC-7
run-state persistence (run relic totals and broader travel state) remains a
separate acceptance requirement** and is not completed here.

## Evidence reports and exit codes

Edit each entry in `observations.json` with `status` of `pending`, `blocked`,
`pass` or `fail`, and `evidence` citing the native observation and its artifacts.
Every non-pending entry requires evidence; for blocked entries describe the
missing implementation/device. Mark `physical_gamepad_routing` and
`both_macs_join` pending until those actions actually happen. The manifest's
planned count is not an observed count. Keep per-role logs intact.

```powershell
python Tools/qa/playtest/session.py check --run win-4-split
python -m unittest discover -s Tools/qa/playtest -p test_session.py -v
```

The log checker reports line-numbered errors and warnings with SHA-256 hashes,
and hashes the manifest/observations. It preserves every report snapshot.
Exit codes: **0** prepared/planned/launched, or all human observations recorded;
**1** logged error or human failure; **2** pending/blocked, missing/empty logs,
unlaunched roles or live worktree processes; **3** refused/invalid input.
A launch exit 0 means only a process was registered. Clean log files are marked
`review`, never gameplay pass. Even a fully recorded report is human evidence,
not automatic certification of gameplay, device routing or Mac compatibility.
The fixture suite launches no Unreal process and uses no network/RPC gameplay.

## Result ledger for this slice

| Item | Result |
| --- | --- |
| Inventory baseline | `dcecbab75999f1cc976d847a24912f4246ddbc8e` |
| Combined candidate tested | None published to this slice; pending integration |
| Installed Windows engine inspected | UE 5.8.3, CL 58210709; read-only inspection |
| New actual gameplay/session results | None; no game/editor was launched or controlled |
| Tooling fixtures | 26 Windows tests passed; temporary fake engine/Git worktrees, mocked launches; Python 3.9 grammar checked on Python 3.12 |
| Existing green gates | Retained from evidence inventory; not rerun |
| Physical gamepad routing | Pending actual device exercise |
| Both Macs joining | Pending same-commit UE 5.8.3 cross-machine session; Windows clients cannot prove Mac compatibility |
| HC-2/HC-4/HC-6 combined behavior | Pending candidate publication and native session checks above |
| HC-7 persistence | Separate acceptance, not claimed |

For #58, coordinate a fresh session at the same commit/engine: Windows host,
both Macs and a separate Windows client (four players), plus the required
two-player session. Macs use their existing `Tools/join.command <host-IP:port>`;
verify private-network/firewall permission manually if needed. Record each Mac's
startup/build/commit evidence and movement/jumping from its own native window.
Use a separate run/log set after ending the all-Windows tests; the automatic
Windows topology manifest is not a Mac process launcher or a substitute for
Mac-side evidence. Keep #58 unchecked until its actual required sessions pass.

Publish this slice as a PR without merging; post the candidate/result ledger and
tooling evidence on #58. Stop after that handoff. Raw dedicated test logs stay
ignored; durable conclusions and artifact hashes belong in the PR/issue comment.
