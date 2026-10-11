# Launch the adventure or connected preview

For the six-round adventure, double-click `Tools/play-adventure.bat` on Windows or run `bash Tools/play-adventure.command` on Mac. These explicit adventure launchers host `/Game/Puzzles/Test/SixRound/L_SixRound_Test`; teammates join with the existing join scripts and the host IP. Normal `Tools/host.bat` and `Tools/host.command` now default to that same adventure map.

For the connected environment preview, double-click `Tools/play-connected.bat` on Windows. On Mac, run `bash Tools/play-connected.command` from the project folder. To double-click on Mac, first run `chmod +x Tools/play-connected.command Tools/play-adventure.command Tools/host.command` once.

The connected preview launchers open `/Game/Maps/L_ConnectedRoomMaze` as a standalone preview. Windows uses the already tested DirectX 11 fallback with ray tracing off for this preview. These options do not change the project settings or the normal host command.

Unreal **5.8.3** must be installed. If installed elsewhere, set `UE_ROOT` to its installation folder (`set "UE_ROOT=D:\Path\To\UE_5.8"` in Windows Command Prompt, or `UE_ROOT="/path/to/UE_5.8" bash Tools/play-connected.command` on Mac). Launchers stop for a missing project, missing map, map stored as an unfetched Git LFS pointer, or wrong engine version. Run `git lfs pull` for an unfetched map. The map check covers the selected map, not every referenced asset.

To host another map explicitly:

```text
Tools\host.bat /Game/Maps/L_ConnectedRoomMaze
bash Tools/host.command /Game/Maps/L_ConnectedRoomMaze
```

Hosting adds `?listen`; the standalone preview does not. Picking the connected map for hosting does not prove its multiplayer gameplay. Use the existing join scripts with the host's IP address. Close the game window to leave the preview. The launchers print the current commit so teammates can compare their checkouts.

Add `--dry-run` to any launch command to run all checks and print each engine argument without opening Unreal. Paths containing spaces are supported. Map arguments must be an existing `/Game/...` package path, without `.umap`, travel options, dots, or extra flags.

Focused checks use temporary synthetic fixtures, never launch Unreal, and never change project maps:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\launch_preview\test-windows.ps1
bash Tools/launch_preview/test-mac.sh
```

The Mac checks can also run under Git Bash on Windows. Git Bash checks use synthetic Mac paths and an unexecuted stub engine. Actual macOS launch and six-round gameplay remain pending and require Unreal on that machine. Launcher dry runs do not establish full mission acceptance.
