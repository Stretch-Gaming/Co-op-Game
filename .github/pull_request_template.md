<!-- Title: <phase>: <observable result> (#<issue>), e.g. PG-6: restore the victim's view after interrupted taking (#106).
     Replace placeholders, remove irrelevant rows, and describe actual results. Guide: docs/pull-requests.md. -->

## Change

<What happens before and after? Name the exact map and whether this changes the combined cave-and-maze adventure, connected environment preview, separate prototype, or tooling/docs.>

- Work: [issue](https://github.com/Stretch-Gaming/Co-op-Game/issues/NUMBER); epic: [HC #1](https://github.com/Stretch-Gaming/Co-op-Game/issues/1) / [PG #2](https://github.com/Stretch-Gaming/Co-op-Game/issues/2) / [HZ #3](https://github.com/Stretch-Gaming/Co-op-Game/issues/3) — keep applicable lanes.
- Sprint: [milestone](https://github.com/Stretch-Gaming/Co-op-Game/milestones); checkpoint: [#4](https://github.com/Stretch-Gaming/Co-op-Game/issues/4) / <specific checkpoint sub-issue, or N/A>.
- Candidate: `<base branch>@<SHA>` → `<head branch>@<SHA>`; depends on <linked PR and merge order, or none>.

## Team scope and handoff

Author: <person who ran the work>. Reviewer / integration owner: <person>. <Name any agreed handoff and link its issue comment.>

| Changed paths / sublevels | Asset owner | Lock / agreement | Next owner and action |
| --- | --- | --- | --- |
| `<actual path or folder>` / `<actual sublevel or N/A>` | <HC / Stretch, PG / PK, HZ / Ak47> | <own lane; lock ID + released/retained; linked cross-lane agreement> | <person + action, or none> |

Shared contract or dependency change: <linked agreement + affected callers, or none>. Asset delivery: <generated / imported / placed, with source and license link, or N/A>.

## Validation and evidence

Tested commit: `<SHA>`; engine: <version + changelist>; map: `<package path>`. State **pass, fail, blocked, not run, or N/A with reason**; add only checks relevant to this change. Preserve separate rows when platform, candidate or mode differs.

| Check | Platform / mode / topology | Result and linked evidence |
| --- | --- | --- |
| Blueprint compile + runtime log | <Mac/Win; changed assets; interval checked> | <result; log/report; errors and Accessed None> |
| 2 / 3 / 4 players | <one row per actual roster; joining clients; PIE / engine -game / packaged; rendered / headless> | <result; scenario + evidence> |
| Host split-screen | <total players, host locals + remote clients; both owning views/input; injected / physical devices> | <result; screenshot/video/log> |
| Packaged build and launch | <Mac/Win; Development/Shipping; build/cook/package/startup/gameplay separately> | <result; build receipt + runtime log> |
| Changed behavior | <steps; before/after image or video where useful> | <result; durable evidence link> |

<!-- Upload screenshots/videos to the PR or link a committed report/artifact accessible to teammates.
     An ignored Saved/ path or a local /tmp/ file alone is not shared evidence. -->

## Remaining work and issue disposition

<Known limits, failed/blocked checks, and the next check with its owner and linked issue. Say what must be rerun after a dependency merge or rebase.>

<Use “Related to #N” while acceptance remains open. Add “Closes #N” only when that issue's complete “Done when” passes on this candidate; link the proof.>
