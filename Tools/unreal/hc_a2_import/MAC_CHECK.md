# HC-A2 Mac acceptance handoff

The Windows delivery cannot establish the other-platform appearance check required by docs/assets.md. #19 stays open until this is recorded.

1. On a teammate Mac, fetch this PR branch and hydrate Git LFS. Confirm Unreal 5.8.3 and a clean lane checkout. Do not rerun the importer with --execute: these assets are already committed.
2. Run `python3 -B Tools/unreal/hc_a2_import/validate_offline.py`. It should report ten matching FBX/LFS hashes and a read-only dry run with occupied destinations. No asset/package writes are needed.
3. Open `/Game/Puzzles/Test/L_HCA2_Props`. Compare all four plate symbols, both statue sizes, the altar/socket and gates with the Windows images. Use both Nanite-supported rendering and the project's supported fallback renderer; full fallback geometry is committed.
4. Open L_Site01 and view the main props under the added HZ lighting. Check all four symbols at half-screen size, the north-wall statues, altar and G1/G2/G3. Inspect 0, +200 and +400 cm gate poses in a temporary editor session, restore closed poses, and avoid saving those temporary changes. The upper leaf must be hidden by the pocket, not by actor visibility.
5. Record engine version, hardware/renderer, screenshots, visible material/fallback differences and Output Log errors on #19. Confirm the supplied dimensions and opening still fit. Do not claim Windows automation proves this Mac result.

Future pressure-plate counting, statue carry/view choice, altar relic interaction and replicated round/gate gameplay remain HC-4/5/6, separate from the art task. Do not implement or alter those systems during this appearance check.
