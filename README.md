# Co-op Game

A 2–4 player online co-op heist by Stretch, PK and Ak47, built in Unreal Engine 5.8 with MCP-driven editors.

We work in 45–60 minute sprints with three people in parallel. The Windows machine merges and hosts, and every few sprints we stop at a playable checkpoint and play it together.

- **Plan:** [docs/sprints.md](docs/sprints.md): the sprints, playable checkpoints, shared contracts and cut list
- **Epics, one per lane:** [docs/epics/](docs/epics/)
- **Map layout:** [docs/map/site01-layout.md](docs/map/site01-layout.md)
- **Rules for agents (and people):** [AGENTS.md](AGENTS.md)
- **Editor agent setup:** [docs/mcp.md](docs/mcp.md)
- **Design:** [docs/design/two-to-four-players.md](docs/design/two-to-four-players.md)

## Lanes

| Machine | Person | Lane | Folder and sublevel |
| --- | --- | --- | --- |
| Windows | Stretch | HC: heist core and round flow. Merges, hosts, owns project settings. | `Content/Heist/`, `L_Site01_HC`, plus `Content/Core/` and `Content/Maps/` |
| Mac 1 | PK | VG: vehicle and getaway chase | `Content/Vehicle/`, `L_Site01_VG` |
| Mac 2 | Ak47 | HZ: site layout, hazards and atmosphere | `Content/Hazards/`, `L_Site01_HZ` |

## One-time setup

Do this before the first session. Most of it is downloading, so allow 1–2 hours.

**Everyone**

1. **Unreal Engine 5.8.3** from the Epic Games Launcher. Everyone must run exactly this version: assets saved in a newer version won't open in an older one, and different versions can't join each other. In the install options, keep Templates and Feature Packs (the vehicle content comes from them) and skip platforms you won't build for, such as Android, iOS and Linux.
2. **About 100 GB of free disk.** The Launcher shows the engine's exact size before it installs, and the project and shader cache need room on top of that.
3. **Git and Git LFS**, then run `git lfs install`. On a Mac: `brew install git-lfs`. On Windows, [Git for Windows](https://git-scm.com/download/win) includes LFS.
4. **Push access to this repo**, then `git clone https://github.com/StretchGaming/Co-op-Game`.
5. **Claude Code**, or another MCP client, to drive the editor. Setup is in [docs/mcp.md](docs/mcp.md).

**Mac**

6. **Xcode 26.0 to 26.3.** Epic recommends 26.1.1, and Xcode 26.4 doesn't work with Unreal 5.8. Open Xcode once to accept the license.
7. **The Metal toolchain.** Unreal compiles Mac shaders with it, and Xcode 26 no longer installs it by default: `xcodebuild -downloadComponent MetalToolchain`.
8. **Run `Tools/check-mac.command`.** It checks all of the above and tells you what's missing.

**Windows**

6. No Visual Studio is needed while the project is Blueprint-only.
7. The first time you host, Windows asks whether Unreal Editor may use the network. Allow it on **private** networks, and make sure your network is set to private.
8. Run `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\check-windows.ps1` before HC-0. The execution-policy option applies only to this process; it does not change your machine's policy. The script checks the exact engine version, editor, templates, required plugin files, Git LFS and free disk space. Set `UE_ROOT` if the engine is installed elsewhere. It does not install anything or verify multiplayer.

## Rules for working in parallel

Unreal assets (`.uasset`, `.umap`) are binary and can't be merged. If two people edit the same one, someone's work is lost. These rules prevent that:

1. **Each lane owns one folder and one sublevel.** Work only there. The full ownership table is in [AGENTS.md](AGENTS.md).
2. **Shared folders are lockable:** `Content/Core/`, `Content/Maps/` and `Content/Shared/`. Their files are read-only until you lock them with `git lfs lock <path>`. See who holds what with `git lfs locks`, and unlock after you push with `git lfs unlock <path>`.
3. **If the save dialog lists a file you don't own, uncheck it.** The editor sometimes marks `L_Site01` or another lane's sublevel as changed.
4. **Project settings, plugins and `Config/` belong to Windows (HC).** Ask before changing them.
5. **Commit small and often.** Start each commit message with your phase code, like `VG-2: passenger seats`. Push with `git pull --rebase && git push`. Everyone works on `main`.
6. **Keep `main` playable.** Never push a Blueprint that doesn't compile. Keep unfinished work in your lane's test map until it works.
7. **Prefer data over graphs.** Tunable numbers go in your lane's scaling data table, where they're easy to tune and easy for an agent to edit.

## Sprint loop

| Step | 45-minute sprint | 60-minute sprint (checkpoint) |
| --- | --- | --- |
| Kickoff: confirm phases, name locks, log in `SPRINT_LOG.md` | 3 min | 3 min |
| Build | 30 min | 35 min |
| Macs push; Windows merges, checks and hosts | 7 min | 7 min |
| Play | 3 min smoke join | 10 min playtest at 2 and 4 players |
| Notes or retro | 2 min | 5 min |

The full timing and what each checkpoint should play like are in [docs/sprints.md](docs/sprints.md).

## Playtesting

Playtests run the game straight from each machine's engine install (`-game`), not from a packaged build. That way Macs and Windows can play together.

1. **Everyone pulls the same commit.** The scripts print the commit hash, so compare them.
2. **Windows hosts:** `Tools\host.bat`. It prints the PC's IP addresses.
3. **Macs join:** `Tools/join.command <IP>`, or double-click it and type the IP.
4. **For a 4th player,** the Windows machine also runs `Tools\join.bat 127.0.0.1` in a second window.

Any machine can host: a Mac runs `Tools/host.command`. If Unreal isn't in the default folder, set `UE_ROOT` to the engine folder (the one that contains `Engine/`) before running a script.

**If you can't connect:**

- Check that every machine runs Unreal 5.8.3 and is on the same commit.
- On the host, Windows Firewall must allow Unreal Editor on private networks, and the network must be set to private. The game uses UDP port 7777.
- On a Mac host, allow incoming connections when macOS asks.
- Not on the same network? Install [Tailscale](https://tailscale.com) on every machine and join with the host's Tailscale IP.
- Don't mix packaged builds and `-game` instances in one session. A packaged Windows build also won't run on the Macs.

## Sprint log

See [SPRINT_LOG.md](SPRINT_LOG.md).
