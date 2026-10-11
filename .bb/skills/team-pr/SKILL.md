---
name: team-pr
description: Prepare a Co-op-Game pull request using the shared HC, PG and HZ team format, with linked issues, exact ownership, tested commits and image or log evidence. Use /team-pr for a PR description or team handoff; publishing requires a request to open or update the PR.
---

# Team pull request

Read root `AGENTS.md`, `docs/pull-requests.md` and
`.github/pull_request_template.md`. Read only the design, sprint contracts and
lane issues relevant to the actual diff. This repository uses GitHub Issues.

Identify the current branch, base and head, author and affected asset owners.
Inspect the final diff and validation records, then fill the template as a PR
description for someone who has not read the conversation. Use a phase-coded
title tied to a real issue. Distinguish production cave-and-maze gameplay,
connected environment previews and the separate C++ prototype. Name dependent
PRs and exact target branches when applicable; do not presume another lane's
unpublished work or change asset ownership.

Link the implementation issue, relevant epic/checkpoint and evidence directly.
Embed available images/videos when they support a visual claim, with map,
platform and tested commit in the caption. GitHub-visible descriptions need
accessible repository or uploaded URLs; local `/tmp`, `Saved/` paths and BB-only
links do not substitute for evidence. If media is missing, record that gap. Do
not invent screenshots, results, issue numbers, lock receipts or test coverage.
Check public-repo source/license records for new third-party assets.

Record tests actually run on the described head, including platform, map, mode,
roster/split configuration and limitations. Carry forward historical evidence
only with its original commit and qualification. Docs/tools-only work uses
appropriate focused checks and marks gameplay gates N/A with a reason. Use
`Closes` only when the issue's complete Done-when criteria pass.

With `/team-pr` alone, write the populated description to ignored
`Saved/Review/pr-body.md` and return its link and proposed title. Do not publish.
When the user's request explicitly includes opening or updating a PR, carry out
the already authorized preparation, branch publication and `gh pr create --draft`
or `gh pr edit`, passing the exact description via `--body-file`. Re-fetch an
existing PR before editing it. Preserve user Git identity and omit AI trailers.
Applicable `AGENTS.md` before-push gates still apply to a draft. If required
client/split checks are blocked, prepare the review material and report that
publication gate instead of treating draft status as a waiver.
Merging, approvals and messages on other people's issues require authorization
from the conversation. Report the PR link, base/head, validation and open gates.
