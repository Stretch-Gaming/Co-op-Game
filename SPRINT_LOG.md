# Sprint Log

Copy the template for each sprint. Newest sprint at the top. The plan is in [docs/sprints.md](docs/sprints.md).

### Sprint 0: Setup — 2026-10-09 18:43, planned 60 min (HC project ready; team checkpoint pending)

**Checkpoint:** Playable 1 — local Windows client tests passed; cross-machine join pending

| Person | Phase | Doing | Locks |
| --- | --- | --- | --- |
| Stretch (HC) | HC-0 (#6) | Published the cave foundation as `1be227b`, including current team documents. Local tests passed; preparing the cross-machine host. | All bootstrap/integration locks released after the verified push. |
| PK (PG) | PG-0 (#22), PG-A0 (#34) | Installed Unreal 5.8.3 on Mac 1 (preflight passes) and opened HC's project. Ran the MCP smoke test (`6d24645`, results in `docs/mcp.md`). Built the shared style kit in `Content/Shared/Style/` (`8c63860`, `d921d5d`) and committed the style frames in `SourceArt/PG/PG-A0/`. Joining the Windows host for Playable 1 is still to do. | Locked `Content/Shared/Style/` for the style kit; released after the push. |
| Ak47 (HZ) | HZ-0 | Not confirmed in this chat. | Not confirmed. |

**Merged commit:** This HC-0 alignment integrates the team plan through `f1011f9` and the locally saved foundation `9c534c7`. Earlier Mac setup notes are retained below. Starting checkout: `cffd7e1`.

**Playtest:** with 2, 3 and 4 clients: passed locally · two local split-screen players: passed · Macs joining Windows: pending

- Worked: Git LFS 3.7.1 configured locally; Third Person and Vehicle Blueprint templates present; approximately 283 GB free on the project drive.
- Verification: all eight core Blueprints and the contract test probe compile. Play As Client tests at 2, 3 and 4 clients verified player counts, full round-state replication, non-default field preservation, dispatcher callbacks, relic totals, movement and jumping. Successful test intervals contain no errors or Accessed None. See [HC-0 verification](docs/hc0-verification.md).
- Resolved: updated Unreal from 5.8.1 to 5.8.3 through the Epic Games Launcher at Stretch's request. The Launcher returned to Launch with version 5.8.3, and `Engine/Build/Build.version` reports 5.8.3 (changelist 58210709).
- Created: Third Person Blueprint project with no starter content. Site 1 uses Puzzles, Player and Hazards sublevels; Map 2 has a minimal HZ floor and environment for future travel tests. Both persistent maps contain four player starts only. Old lane redirects were fixed through Unreal. Original template content hashes are unchanged.
- Contracts: `SetRoundPhase` changes only the phase inside replicated `S_RoundState`; RepNotify fires `OnRoundStateChanged` on the server and every client. Round/gameplay functions remain Sprint 0 stubs. `ScalingRow` defaults to `2`; automatic lobby updates and round snapshots remain future work as planned.
- Remaining: both Macs and a second Windows client must join the Windows host at the same commit to complete Playable 1. Stretch confirmed both Macs are on 5.8.3 and ready to join. Physical gamepad routing has not been tested; the required offset setting is enabled.
- Legacy content: the earlier Vehicle feature pack remains unused reference content in `Content/VehicleTemplate/`, with its Chaos Vehicles plugin enabled. Neither cave map references its vehicle gameplay. Sources and distribution basis are recorded in `CREDITS.md`.
- Timing: engine installation, initial shaders and editor automation exceeded the planned setup cycle. HC-1 has not started.
- Standalone fix: the first `-game` host logged editor-toolset Python import errors. Host/join scripts now use Unreal's `-DisablePython` flag for game runs; editor Python and MCP remain enabled.
- Standalone verification: the Windows listen host and a separate Windows client connected successfully on UDP 7777 and loaded Site 1; both logs are free of Error and Accessed None. The Mac join checkpoint remains open.
- VG-0 status (2026-10-09 18:58 EDT): upstream still has no `.uproject`, `Content/` or `.mcp.json`; no Unreal Editor installation was found on PK's Mac, and localhost port 8000 refused the MCP connection. The smoke test and joining Playable 1 could not run. No Blueprint or map changes were made.
- VG preparation: Xcode 26.2 and Git LFS 3.8.0 are available. The Metal toolchain download started before PK requested skipping preflight and completed successfully; `xcrun -sdk macosx metal --version` now succeeds. Engine installation and disk-space remediation were not performed.

**Keep, cut or change:** Keep Unreal 5.8.3 and follow the revised cave-round contracts. The former heist fields, functions and lane sublevel names have been replaced.

**Next sprint:** Run cross-machine Playable 1 before HC-1. PG and HZ pull this project and join the Windows host; PG records its MCP smoke test. Local tests do not complete the team checkpoint.

## Template

### Sprint N: Name — YYYY-MM-DD HH:MM, 45 or 60 min

**Checkpoint:** none, or Playable 1–4, or Demo 1

| Person | Phase and issue | Doing | Locks |
| --- | --- | --- | --- |
| Stretch (HC) | HC-N (#) | | |
| PK (PG) | PG-N (#) | | |
| Ak47 (HZ) | HZ-N (#) | | |

**Merged commit:**

**Playtest:** with 2 players: yes/no · with 4 players: yes/no

- Worked:
- Broke:

**Keep, cut or change:**

**Next sprint:**
