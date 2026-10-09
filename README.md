# Co-op Game

A co-op game by Stretch, PK and Ak47, built in Unreal Engine 5 with MCP-driven editors.

We work in 30–60 minute sprints with three people in parallel, then build on the Windows machine and playtest together.

## One-time setup (everyone)

1. **Install the same Unreal Engine version.** Everyone must run the exact same version, down to the minor number (for example 5.6.1). Assets saved in a newer version will not open in an older one. Pinned version: **TBD — fill in before the first sprint.**
2. **Install Git LFS.**
   - macOS: `brew install git-lfs && git lfs install`
   - Windows: install [Git for Windows](https://git-scm.com/download/win) (includes LFS), then `git lfs install`
3. **Clone the repo.** `git clone https://github.com/StretchGaming/Co-op-Game`
4. **Compilers, only if the project has C++.**
   - Windows: Visual Studio 2022 with the "Game development with C++" workload.
   - macOS: the Xcode version listed in the Unreal release notes for the pinned engine version.
5. **Source control in the editor.** Use the [Project Borealis Git plugin](https://github.com/ProjectBorealis/UEGitPlugin) so the editor checks out (locks) a file when you start editing it. Configure it under *Editor Preferences → Source Control*.

## Creating the project (one person, once)

- Project names cannot contain hyphens or spaces. Pick something like `CoopGame`.
- Start from the **Third Person** template as a **Blueprint** project. Add C++ later only when needed, because every Mac then needs Xcode to open the project.
- Create it outside the repo, then move the `.uproject`, `Config/`, `Content/` (and `Source/` if present) into the repo root.
- In the main level, enable **World Partition** with **One File Per Actor** so placed actors save as separate files.
- Create the ownership folders listed below, commit, and push.

## Rules for working in parallel

Unreal assets (`.uasset`, `.umap`) are binary and cannot be merged. If two people edit the same one, someone's work is lost.

1. **Lock before you edit shared assets.** The editor plugin does this on checkout. From the command line: `git lfs lock Content/Path/To/Asset.uasset`. See current locks with `git lfs locks`.
2. **Stay in your folder for work in progress.**
   - `Content/Stretch/`
   - `Content/PK/`
   - `Content/AK/`
   - `Content/Shared/` — finished, promoted work. Lock before editing.
3. **Shared core assets have one owner per sprint.** That includes the GameMode, player character, player controller, and main map. Call it out at kickoff.
4. **Commit small, push often.** Pull before you start and before you push. Everyone works on `main`.
5. **Prefer data over graphs.** Put tunable numbers in Data Tables or Data Assets. They are smaller, easier to review, and easier for an MCP agent to edit.
6. **Unlock when you're done.** `git lfs unlock <path>`, or let the editor plugin release it on submit.

## Sprint loop

| Step | Time | What happens |
| --- | --- | --- |
| Kickoff | ~5 min | Each person picks one feature and names any shared assets they need to lock. Log it in `SPRINT_LOG.md`. |
| Build | 30–50 min | Work in your own editor with your MCP agent. Commit small. |
| Merge | ~5 min | Everyone pushes and releases locks. |
| Build & playtest | ~10 min | The Windows machine pulls, launches as the listen server, and everyone joins. |
| Retro | ~5 min | Keep, cut, or change. Pick next sprint's goals. |

## Playtesting

The Windows machine is the build and host machine.

- **Fastest:** the Windows machine pulls and runs the game as a listen server (*Play → Net Mode: Play As Listen Server*, or a packaged Win64 build). The Mac players pull the same commit and run *Standalone Game* from their editor, then connect with the console command `open <windows-machine-ip>`.
- Everyone must be on the **same commit** and the **same engine version**, or the connection will be refused.
- **Packaged build:** *Platforms → Windows → Package Project*. A Windows build only runs on Windows, so the Mac players still join from the editor.

## Sprint log

See [SPRINT_LOG.md](SPRINT_LOG.md).
