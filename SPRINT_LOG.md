# Sprint Log

Copy the template for each sprint. Newest sprint at the top. The plan is in [docs/sprints.md](docs/sprints.md).

### Sprint 0: Setup — 2026-10-09 18:43, 60 min (prerequisites passed; project pending)

**Checkpoint:** Playable 1 — not yet run

| Person | Phase | Doing | Locks |
| --- | --- | --- | --- |
| Stretch (HC) | HC-0 | Windows preflight and local Git LFS setup complete. Unreal updated to 5.8.3; project creation is next. | None acquired; no shared assets created or edited. |
| PK (VG) | VG-0 | Not confirmed in this chat. | Not confirmed. |
| Ak47 (HZ) | HZ-0 | Not confirmed in this chat. | Not confirmed. |

**Merged commit:** HC-0 project integration pending. This update contains Windows preparation only. Starting checkout: `cffd7e1`.

**Playtest:** with 2 players: not run · with 4 players: not run

- Worked: Git LFS 3.7.1 configured locally; Third Person and Vehicle Blueprint templates present; approximately 283 GB free on the project drive.
- Verification: the initial `Tools/check-windows.ps1` run failed only on the engine version. After the engine update, it passed every prerequisite: exact engine version, editor, both templates, all four required plugin descriptors, Git/LFS setup and disk space. Plugin enablement and multiplayer remain unverified.
- Resolved: updated Unreal from 5.8.1 to 5.8.3 through the Epic Games Launcher at Stretch's request. The Launcher returned to Launch with version 5.8.3, and `Engine/Build/Build.version` reports 5.8.3 (changelist 58210709).
- Remaining: create the Third Person project, enable required plugins, acquire shared-asset locks, set up map/sublevels and core contracts, verify compilation and client play, then publish and run Playable 1 with the Macs.

**Keep, cut or change:** Keep the required Unreal 5.8.3 version. No design, contract or lane changes.

**Next sprint:** Finish HC-0 before starting HC-1. This entry records preparation, not a completed sprint or checkpoint.

## Template

### Sprint N: Name — YYYY-MM-DD HH:MM, 45 or 60 min

**Checkpoint:** none, or Playable 1–4, or Demo 1

| Person | Phase | Doing | Locks |
| --- | --- | --- | --- |
| Stretch (HC) | HC-N | | |
| PK (VG) | VG-N | | |
| Ak47 (HZ) | HZ-N | | |

**Merged commit:**

**Playtest:** with 2 players: yes/no · with 4 players: yes/no

- Worked:
- Broke:

**Keep, cut or change:**

**Next sprint:**
