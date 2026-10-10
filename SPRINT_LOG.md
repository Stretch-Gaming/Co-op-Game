# Sprint Log

Copy the template for each sprint. Newest sprint at the top. The plan is in [docs/sprints.md](docs/sprints.md).

### Sprint 0: Setup — 2026-10-09 18:43, planned 60 min (HC project ready; team checkpoint pending)

**Checkpoint:** Playable 1 — local Windows client tests passed; cross-machine join pending

| Person | Phase | Doing | Locks |
| --- | --- | --- | --- |
| Stretch (HC) | HC-0 | Created the Blueprint project, plugins, Site 1 and always-loaded lane sublevels, vehicle content, core contracts and heist scaling table. Local client tests passed. | Core assets, persistent map and initial VG/HZ sublevels locked for bootstrap; release after push. |
| PK (VG) | VG-0 | Pulled HC's preparation through `e664177`; checked project and MCP availability; recorded the blocked smoke test in `docs/mcp.md`. Preflight gate skipped at PK's request. | None; no Unreal assets edited. |
| Ak47 (HZ) | HZ-0 | Not confirmed in this chat. | Not confirmed. |

**Merged commit:** This HC-0 project commit integrates preparation through `28bae03`, including VG's setup notes. Starting checkout: `cffd7e1`.

**Playtest:** with 2 clients: passed locally · with 4 clients: passed locally · Macs joining Windows: pending

- Worked: Git LFS 3.7.1 configured locally; Third Person and Vehicle Blueprint templates present; approximately 283 GB free on the project drive.
- Verification: Windows prerequisites passed after the engine update. All six core Blueprints compile. Play As Client tests verified player counts, scaling rows, server phase replication and client movement with 2 and 4 clients; the four-client run also verified replicated jumping. No errors or Accessed None in the test interval. See [HC-0 verification](docs/hc0-verification.md).
- Resolved: updated Unreal from 5.8.1 to 5.8.3 through the Epic Games Launcher at Stretch's request. The Launcher returned to Launch with version 5.8.3, and `Engine/Build/Build.version` reports 5.8.3 (changelist 58210709).
- Created: Third Person Blueprint project with no starter content; 43 vehicle feature-pack assets in `Content/VehicleTemplate/` for VG to use in place. Template assets were preserved. All asset edits ran inside Unreal Editor.
- Contracts: GameMode owns phase changes; GameState replicates phase and round fields. `NotifyGetawayStarted` only advances Collapse to Getaway. `RequestEndRound` prints inputs until HC-7; interaction and carrying remain stubs for HC-1/2.
- Remaining: both Macs and a second Windows client must join the Windows host at the same commit to complete Playable 1. Runtime listener counts for the phase dispatcher were not measured; its Blueprint wiring and phase replication were checked.
- Timing: engine installation, initial shaders and editor automation exceeded the planned setup cycle. HC-1 has not started.
- VG-0 status (2026-10-09 18:58 EDT): upstream still has no `.uproject`, `Content/` or `.mcp.json`; no Unreal Editor installation was found on PK's Mac, and localhost port 8000 refused the MCP connection. The smoke test and joining Playable 1 could not run. No Blueprint or map changes were made.
- VG preparation: Xcode 26.2 and Git LFS 3.8.0 are available. The Metal toolchain download started before PK requested skipping preflight and completed successfully; `xcrun -sdk macosx metal --version` now succeeds. Engine installation and disk-space remediation were not performed.

**Keep, cut or change:** Keep the required Unreal 5.8.3 version. No design, contract or lane changes.

**Next sprint:** Run the cross-machine Playable 1 checkpoint before HC-1. VG resumes its MCP smoke test after installing the editor and pulling this project, then joins the Windows host. Local tests do not complete the team checkpoint.

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
