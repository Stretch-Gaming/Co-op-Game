# Audit: HC-QA1

Date: 2026-10-10 (America/New_York). Base: `b9ed193` from latest `origin/main` when the worktree was created. Worktree: `C:\Users\Stretch\.codex\worktrees\hc-qa-validation\Co op Game`. Branch: `codex/hc-qa-validation`. Only `Tools/qa/` changed.

Acceptance: 34 tests ran on Windows with bundled Python 3.12.14 and Git; 33 passed, one symlink test was skipped because the account could not create symlinks. Python 3.9 syntax parsing also passed. Native macOS/Linux and actual Python 3.9 runtime tests were not available here. The implementation uses standard-library APIs available in Python 3.9 and no platform-specific shell commands.

Independent verification hashed all 642 tracked files outside the new QA folder, including their mtimes, and hashed the worktree Git index and shared Git configuration before/after validation. Those snapshots were identical. Source input hashes, implementation/test hashes and results are in [results/audit.json](results/audit.json). These are hashes of the checked-out files: binary entries currently contain pointer text, not hydrated asset data.

| Task | Assets | Errors | Warnings | Exit |
| --- | ---: | ---: | ---: | ---: |
| HC-A1 | 13 | 13 | 6 | 1 |
| HC-A2 | 22 | 22 | 11 | 1 |
| All HC | 35 | 35 | 17 | 1 |

Detailed outputs: [HC-A1](results/hc-a1.json), [HC-A2](results/hc-a2.json). Their repository label is normalized to `<attached worktree>` for portability.

All 35 errors are unhydrated LFS pointers in this separate checkout (14 FBXs, 21 PNGs). Effective LFS attributes and index pointers pass; all working pointers match their indexed identities. Naming and lowercase extensions pass. Hydrated image dimensions, asset hashes and appearance cannot be established from these working files. Validation never downloads or hydrates them.

All 14 cleanup-export JSON records pass the structural/internal checks, but none has an output SHA-256 binding measurements to the current FBX. Each produces `record.unbound`. LFS's recorded object identity does not bind the historical Blender measurements.

HC-A1's scarab record reports `[18.0, 16.3004, 7.0937]` cm, below the small-relic 20â€“30 cm brief on its longest axis. This is a recorded-metadata review warning, not an independent geometry measurement. All HC-A1 records stay under 10k triangles. The heart records 62 cm height and 74.0457 cm full bounds along Y, including its assembly; no invented longest-axis failure is applied to its approximate 60 cm brief.

The gate frame records full bounds `[156.0, 708.8224, 511.2001]` cm, and the leaf `[30.4, 430.0, 450.0]` cm. They are not flagged for failing a 400 cm full-bounds target. The modeled 4 Ã— 4 m opening and sliding clearance require Blender/Unreal verification.

Neither HC-A1 nor HC-A2 has a local README/delivery/provenance record, so each task produces `provenance.missing`. During task setup, GitHub comments on [#18](https://github.com/Stretch-Gaming/Co-op-Game/issues/18) and [#19](https://github.com/Stretch-Gaming/Co-op-Game/issues/19) were inspected: they record team-scripted Blender work and permission to publish. The offline validator does not fetch those comments or invent a license from the tool name. This finding means local evidence is absent, not that provenance is absent everywhere.

HC-A3 PR [#68](https://github.com/Stretch-Gaming/Co-op-Game/pull/68) had not been merged into this base. Its existing `generation.json` and `validation.json` schemas were read and covered by synthetic tests; no live HC-A3 source audit is claimed. No HC import manifests are committed on this audited base. Optional manifest behavior was tested with synthetic source/import files.

No assets, shared scripts, import folders, maps, Blueprints, project settings, credits or planning documents were repaired or modified. No Unreal/Blender launch or human engine test was performed. The tooling acceptance gate passes while existing asset hydration/evidence and human geometry/appearance gates remain outstanding.
