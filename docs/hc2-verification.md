# HC-2: relics and Core integration

Worktree: `C:/Users/Stretch/.codex/worktrees/hc2-core-integration/Co op Game`,
branch `codex/hc2-core-integration`, based on `dcecbab75999f1cc976d847a24912f4246ddbc8e`.
All authoring occurred in that checkout. The original main checkout and its
untracked HC-1 RPC probe were preserved.

## Behavior

`BP_Relic` implements the existing instant `BPI_Interactable` contract. The
character retains HC-1's owning-client input, reliable server RPC, range,
permission and visibility validation. The relic checks authority and permission
again, sets replicated `Collected` before adding its positive `Value`, then
applies hidden/collision state. Competing requests cannot add value twice.
`Available` and `Collected` RepNotifies plus BeginPlay apply presentation, so
visibility does not depend on receiving the cosmetic multicast. Relics are always relevant: hidden, collision-disabled StaticMeshActors otherwise omit their collected state from a fresh client world. The reconnect test caught and verified this correction.

`BP_CoopGameMode.AddRelics(Count)` updates replicated GameState totals only on
the server. Available total sums eligible relic **value**, in the same units as
collected value. A collected relic remains in the denominator if the lobby
shrinks. Neither round start nor restart clears collection.

The GameMode checks the roster every 0.2 seconds. In Lobby, it changes only the
scaling row when the clamped 2/3/4-player row changes. Starting a round samples
the current roster; other phases retain the chosen row. New PlayerStates begin
at ColorSlot -1 and receive the first free slot 0-3 on the server, including
local split players. ColorSlot replicates. Existing scaling struct signatures
and the data-table rows are preserved.

The consolidated #74 HUD reads RoundState and relic totals from GameState.
Its owning-player component replaces the need for a duplicate relic counter.
HC-1 interaction graphs and input mapping setup remain unchanged.

F4 uses the existing primary-local-host guard and calls non-seamless
`ServerTravel` to Site 02, or back to Site 01 when already in Site 02. Run-state
persistence across travel belongs to HC-7 and is not added here.

`Multicast_Pickup` is configured Multicast with Reliable unchecked. It invokes
PlaySoundAtLocation only when an instance's PickupSound is assigned. The default is the original 0.32-second mono 48 kHz HC2 chime in locked Core/Audio. Source, synthesis and provenance are included under SourceArt/HC/HC2 and recorded on #8 before commit. A non-replicated PickupFeedbackCount is diagnostic only; tests verify one received sound event per world, never derive gameplay totals from it. Physical listening/quality remains a team check.

## Reviewed integrations

- #70 at `1e2904c9d42fc6f56c3cb4712441217383d2e247`: imported relic art,
  source/provenance and engine evidence reviewed; used the delivered meshes.
- #73 at `14b967ff417d871c10fac08d7beef075f1994a1c`: read-only source QA,
  34 tests passed with one account-privilege symlink skip.
- #74 at `41ce132d72b26a709091af1961ed501ada857d99`: consolidated #68/#72
  HUD delivery, source and graph changes reviewed; owning split-screen render
  reviewed. Integrated once.
- #71 at `4a1e74e408c0b37a690aef660bb9e255cb39ca03`: repaired Windows gate reviewed, source image hashes matched, gate and doorway renders inspected. Integrated after publication with the editor closed. Mac appearance remains pending.
- Carrying at `a162df8d842ce347c14195c2cc6551543d7ab8a1`: server-only component API, input/late-join/ownership evidence and exact Core handoff reviewed, then integrated separately. The component and actors remain the carrying chat's implementation; no competing carrying behavior is authored.
- Round 1 at `d7167949b2ac08fa590747e7ec37a87de3a31388`: contracts reviewed as compatible with the existing scaling row/table and round notification. Its later-phase actor delivery stays separate from this HC2/Core slice; no Core adapter is required.

Each accepted delivery has its own integration commit. No binary merge
conflicts occurred in the reviewed deliveries. No cave actors were placed or authored by this chat. L_Site01_HC, the approved HZ repairs and carrying assets enter only through their exact reviewed delivery commits; their bytes are preserved.

## Windows verification

Unreal 5.8.3 CL 58210709. Evidence under `Tools/unreal/hc2_integration/`.

| Gate | Evidence | Result |
| --- | --- | --- |
| 2/3/4 Play As Client | `clients-2.json`, `clients-3.json`, `clients-4.json` | Passed: expected available values 8/11/15, MinPlayers filtering, unique colors, owning HUDs, client value-2 pickup, simultaneous value-5 pickup exactly once, repeat press rejection, remote host controls rejected |
| Listen host and local split ownership | `host-split-latejoin.json` | Passed: distinct widgets, second-local pickup, primary-only controls, lobby joins/leaves, first-free color reuse |
| Late remote split-player join | same | Passed: join handshake, ColorSlot 3, current totals and collected actors |
| Fresh independent client-world reconnect | `fresh-client-latejoin.json` | Passed: new world receives collected/hidden/collision state, 2/8 totals, colors and owning HUD; then collects through actual input |
| Core carrying adapters at 2/3/4 and second local owner | `production-carry-*.json`, `production-carry-split.json` | Passed: one replicated component per pawn, E pickup, reliable G Drop, re-pickup, GetCarried forwarding and heavy baseline/restore |
| HC1 interaction regressions at 2/3/4 | `hc1-regression-*.json` | Passed: instant, timed cancellation/completion, continuous release, range/permission/round/end-play cleanup |
| Scaling lock and round restart | same | Passed: playing row stays fixed after departure, next round start samples the roster, collected value survives |
| Four-player travel with host split pair | same | Passed: F4 Site 02 and back; all four regain owned HUD/input after reconnect |
| Main cave 2/3/4-client smoke | `site01-*.json` | Passed: original HC1 markers and 11 reviewed art actors, unique colors, owned HUDs, one carrying component per pawn, actual input movement/floor support |
| Successful HC-2 log intervals | `clients-*-log.json`, `host-log.json` | No errors, Blueprint Runtime Error or Accessed None |

One compile audit during active PIE crashed a background worker. The interrupted
regression is not a pass. Its record is `interrupted-regression.json`; the full
first-session log remains in ignored Saved/Logs/HC2-session1.log. Compile audits
now require stopped PIE. The restarted behavior editor used unattended NullRHI. Drop RPC configuration required Slate UI, so a separate D3D11/ray-tracing-disabled editor was used; final integrated behavior regressions run there. No project settings were saved. These renderer overrides are not Mac/default-renderer appearance acceptance.

## Dedicated fixtures and cave placement handoff

`Content/Puzzles/Test/HC2/L_HC2_Test.umap` holds four starts and five relics:
Base (MinPlayers 2, Value 2), Race (2,5), Bonus3 (3,3), Bonus4 (4,4), Base2 (2,1).
The owned map also has crate/heavy fixtures for the Core Drop adapter. `host-split-view.png` shows both owning HUDs in the final D3D11 fixture session. `BP_HC2InputProbe` only resolves an owning controller's input subsystem for tests.
Native CreatePlayer/RemovePlayer are fixture setup, not production split-screen
logic. Pickup and debug acceptance use Enhanced Input actions and their normal
Blueprint event/RPC path, never direct Python RPC calls.

For the cave/prop owner: after their environment gate passes, make
`L_Site01_HC` current before placing `/Game/Puzzles/BP_Relic`. Place tutorial
relics on supported surfaces in the spawn cavern, within normal interaction
reach; start with Value 1/MinPlayers 2. Add clearly separated bonus relics with
MinPlayers 3 and 4. Override the StaticMeshComponent with the supplied GoldIdol,
JadeMask or GemScarab mesh. The default PickupSound is already assigned to the original HC2 cue; override it only with an approved sound. Keep
Collected and Available at defaults; the server determines eligibility. Do not
save cross-sublevel actor references. Recheck available total and client pickup
once the owner publishes the placement candidate. This branch intentionally
contains no tutorial placements in the cave.

## Pending dependencies and acceptance

- PG `Content/Player/AC_PlayerView` and `BPFL_SplitScreen` are absent from main.
  No competing view, headlamp, split-screen library or F5/F6 implementation is
  created. Production hookup, physical gamepad routing and Mac travel remain
  pending PG's delivery/team tests.
- Production Drop now forwards to the reviewed AC_Carrying through the owning character's reliable Run on Server event. Server BeginPlay adds the replicated component only when absent, reusing the HC4 fixture's existing static component and avoiding duplicates. GetCarried/ReleaseCarried retain their CarriedActor return signatures and server-only component semantics. Production health/downed binding and carrying art/placement remain with their owners/future slice.
- #8 remains open for these dependencies and the cave placement/travel team
  acceptance. HC-3 revive and later puzzle logic are outside this slice.

## Completion follow-up

The latest published PG branch and PR #82 were reviewed on 2026-10-10.
PR #82 at `a54a2e692ccac00b1e95442de1b64877ef79ee0a` repairs the PG test
character RPC signature and forwards its input to inherited HC-1 behavior.
It is integrated as a separate reviewed delivery, without editing its binary
or tools. The protected PG graphs and the delivered asset hash match.
`pg-compatibility-review.json` records all 63 Blueprints compiling without errors or warnings against
HC-2 Core. `pg-core-input-*.json` and `pg-core-input-log.json` record the
reviewed PG input regression running against this integration: 419 assertions
passed at 2, 3 and 4 clients and with two local host owners plus two remote
clients; the log interval contains no errors or Accessed None.

This repair does not provide AC_PlayerView or BPFL_SplitScreen. Both assets
remain absent from all published repository branches examined; #23 and #24
remain open. The user confirmed that the existing PG and cave owners remain
responsible and will provide the delivery and Mac test access. HC-2 will
consume the reviewed PG contracts, wire production inputs under Core locks,
and verify the cave owner's tutorial placement once those deliveries exist.
Both Macs must actually join and travel in both directions with the host's
split-screen player before the travel checkbox is closed. Until then, #8 and
PR #81 remain open; no missing acceptance is inferred from Windows PIE.
