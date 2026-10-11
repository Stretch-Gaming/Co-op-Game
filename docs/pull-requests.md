# Pull requests for the combined team

Use the [PR template](../.github/pull_request_template.md) for HC, PG and HZ deliveries, integration fixes and workflow changes. Keep the description short: explain the changed behavior, who owns the touched assets, what was actually tested, and what the next person needs to do. Remove irrelevant rows and replace every placeholder before review. Work stays in this repo's [GitHub Issues](https://github.com/Stretch-Gaming/Co-op-Game/issues).

## Title, links and candidate

Use `<phase>: <observable result> (#<issue>)`, for example `PG-6: restore the victim's view after interrupted taking (#106)`. This follows the [commit format](../AGENTS.md#tracking-work). For a combined delivery, lead with the integrating phase and list the contributing phases in the body. Link the work issue, each affected [HC](https://github.com/Stretch-Gaming/Co-op-Game/issues/1), [PG](https://github.com/Stretch-Gaming/Co-op-Game/issues/2) or [HZ](https://github.com/Stretch-Gaming/Co-op-Game/issues/3) epic, the sprint milestone, and the applicable [playable checkpoint](https://github.com/Stretch-Gaming/Co-op-Game/issues/4). Mark a checkpoint N/A when the change has no checkpoint claim.

Record the exact base and head branches and SHAs. If a fix targets another open PR, link that parent and state the intended merge order. Test evidence belongs to the tested SHA; after a merge or rebase, update the candidate and identify the affected checks that need repeating. A clean Git merge does not establish runtime compatibility.

Name the actual map and delivery:

- **Combined adventure:** the cave-and-maze six-round route, including its production gameplay.
- **Connected preview:** the environment preview; name which gameplay, if any, is included in this revision.
- **Separate prototype:** identify its project and map; its result does not establish behavior in `CoopGame.uproject`.
- **Tooling or docs:** describe the command or workflow affected and its checks.

Use package paths from the candidate rather than assuming a launcher's name identifies the route. The [design](design/direction-2026-10-10.md), [shared contracts and checkpoints](sprints.md), and [playtest instructions](../README.md#playtesting) define the acceptance target.

## People, ownership and handoffs

The author is the person who ran the work, using their own Git identity. Credit collaborators for their actual deliveries; omit AI co-author trailers and “Generated with” lines. Separate authorship from asset ownership and integration responsibility:

| Lane | Asset owner | Primary scope |
| --- | --- | --- |
| HC | Stretch / Parker | Core, puzzles, round integration and persistent maps |
| PG | PK | Player view, split-screen, traversal, tools and ghosts |
| HZ | Ak47 | Cave, traps and atmosphere |

Combined work still follows [AGENTS.md](../AGENTS.md): list actual changed paths and sublevels, required LFS lock IDs and their status, and the linked agreement for any cross-lane work. Name who receives each handoff and what they need to do. Do not imply that one PR gives its author ownership of every touched system. Project settings and plugins still require HC's agreement.

For assets, distinguish chosen source output, import, and placement. Link the asset issue's source/license record and an in-game image when available. Follow [the public-repo asset rules](assets.md#licenses-this-repo-is-public); a licensed import does not prove visual acceptance or gameplay integration.

## Tests and shareable evidence

Report a small matrix of actual runs with the candidate SHA, engine version/changelist, platform, map, player topology and result. Count players rather than windows: “4 total: 2 host locals + 2 remote clients” is clear. Use separate rows for the 2-, 3- and 4-player results; use “not run” or “blocked” with a reason when a required roster was not exercised. For views, HUD and input, cover both local split-screen owners and distinguish action injection from physical keyboard/gamepad tests.

Label execution precisely:

| Mode | What its result can establish |
| --- | --- |
| Blueprint compile or cook/package | Asset/build checks; runtime behavior needs a separate run |
| PIE, Play As Client | Joining-client behavior for the stated roster; record whether rendered or headless |
| Engine executable with `-game` | Runtime from an installed engine and checkout; it is not a packaged app |
| Packaged app | Cooked/staged artifact for the named platform; separate build success, startup and gameplay results |
| Headless / NullRHI | State, replication and log checks; appearance, sound and device feel remain unverified |

Packaged checks complement the [required editor checks](../AGENTS.md#before-you-push). A Mac package does not prove Windows execution, and a host-only run does not prove joining-client behavior. For a packaged session, identify matching builds for every participant; do not mix packaged and engine `-game` instances.

Link screenshots or videos for visible behavior, and logs/reports for compile, package and runtime checks. Use GitHub-uploaded media, committed evidence, or an artifact teammates can access. Local `/tmp/` files and ignored `Saved/` folders are useful working records, but need a shared report or upload. Attach a caption with map, candidate, player/view and observed result; retain relevant failed evidence alongside the corrected passing run.

## Acceptance and review

List the remaining limits, the next concrete checks, their owners, and linked issues. Include any resource stop, deferred roster, platform, network, audio, device or full-route acceptance that prevents a broader claim. For docs-only changes, mark runtime rows N/A and record the documentation or command checks actually performed.

Use “Related to #N” until the entire issue's “Done when” passes on the candidate. Add `Closes #N` only with linked proof; importing assets, compiling, packaging or merging a branch alone does not close gameplay acceptance. Keep issue steps consistent with the delivery and re-fetch an issue before editing it because teammates may be updating it concurrently. A ready PR requests review; merging follows the team's current authorization and named integration owner.
