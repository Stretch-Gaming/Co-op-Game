# Connected preview performance observer

This slice collects evidence only. It does not change graphics, collision, scenery, actors, gameplay, assets, maps, input, or project settings, and does not start an editor or PIE session. The primary runs `collect.py` through its guarded editor runner after coordinating with the other chat's GPU work. No stutter cause or optimization benefit has been measured yet.

Use the exact attached checkout and Unreal 5.8.3, with `/Game/Maps/L_ConnectedRoomMaze` and exactly its original HZ room and HC connected maze loaded. The script refuses other projects/maps/loaded levels. PIE may already be running, but its world list must stay stable throughout the sample. Avoid collecting during another editor's GPU test, shader compilation, asset import, or external benchmark unless that contention is the explicit subject of the sample.

The primary supplies `ROOT` and `ARGS`, for example:

```python
ARGS = {'report': 'baseline-static-view.json',
        'context': 'No PIE; editor foreground; fixed camera facing maze entry; 1280x720 viewport; idle; other Unreal editor closed; shader compilation finished'}
```

The primary dispatcher is `Tools/unreal/playable_game/run_quality.py` with `ARGS['folder']='performance'` and `ARGS['script']='collect.py'`. Add `census_only: True` for an immediate inventory with no callback/timing collection. NullRHI runs are restricted to that mode. The collector intentionally writes to its assigned `Saved/QualityPerformance` folder rather than the dispatcher's generic output directory.

The observer inventories actors/components once, then waits 30 seconds and measures for 30 seconds. Its native Unreal Slate post-tick delta and wall intervals describe **editor cadence**. They do not isolate game-thread, render-thread or GPU time and cannot establish standalone-game FPS. Inventory cost and callback cost are recorded separately; costs are not subtracted from frame intervals. JSON includes actual raw samples, average, interpolated p50/p95, maximum, console settings, stable PIE world names, OS/CPU/memory context where available, component census, material-slot/section proxies, mesh-instance counts and light/collision/shadow flags. Missing optional system-load information is labeled, with no dependency installation.

If PIE already exists, native `GameplayStatics.get_world_delta_seconds` values are also sampled for each connected world, separately labeled as simulation delta. These may be capped, scaled, paused or repeated between Slate callbacks. Local installed UE 5.8.3 `GameplayStatics.h` exposes this getter; the inspected Kismet headers expose no equivalent GPU/game/render-thread timing getter. Use Unreal's native profiling display/capture for thread/GPU breakdown before attributing a bottleneck; the collector does not parse invented stat output or claim thread timing from simulation delta.

Reports go only to `Saved/QualityPerformance/`; an existing report is never overwritten. `status: complete` means the observation window finished, not that performance is good. Compare sample counts and context before interpreting results. A callback after 95 seconds marks timeout. Success, error, timeout and explicit cancellation unregister the callback; cancellation uses the same script with `ARGS = {'cancel': True}`. A fully stalled editor cannot execute callbacks or clean itself up until its main thread resumes. Restarting the script while an observer is active is refused. Project/map or PIE changes abort the sample. Closing the editor naturally destroys its callback registry; an interrupted external caller leaves the observer running until it finishes or is cancelled.

Primary measurement plan:

1. Record one foreground fixed-view baseline in the original room and another facing the maze, keeping resolution and settings unchanged. Include the exact view and background workload in each context.
2. If stutter repeats, record a separate, clearly labeled observation during a normal walk without changing player logic. Existing two-client/split-screen functional checks are already green and need no replay for this collector.
3. Compare p95/max against median, raw samples, observer cost and system contention. Use native Unreal CPU/GPU timing or profiling tools to determine the limiting work before changing anything; census is a suspect list, not causation.
4. Rank proposed changes only against measured evidence: remove duplicate/unused rendering work first if demonstrated; batch repeated scenery only if draw submission dominates; simplify visual-mesh collision only if collision dominates; adjust specific lights/shadows only if GPU timing demonstrates their cost. Geometry, collision, lighting, batching and quality changes all require primary review of visual/gameplay tradeoffs. No global quality reduction is proposed here.
5. If a narrow change is approved, repeat only the matching performance sample with identical view/settings/context. Preserve baseline and compare timing plus the affected visual/collision checks.

Offline verification (does not import Unreal):

```text
python Tools/quality/performance/test_stats.py
python Tools/quality/performance/test_context.py
python -c "import ast,pathlib; [ast.parse(p.read_text()) for p in pathlib.Path('Tools/quality/performance').glob('*.py')]"
```

Unreal API calls remain subject to primary editor execution. The collector uses supported Python reflection and read methods with unavailable-property diagnostics; offline tests cannot prove engine binding compatibility or callback behavior inside the actual editor.

## Native GPU/game/render timing capture (future primary run)

`native_csv.py` parses native CSV metrics rather than Slate cadence. Installed UE 5.8.3 `LaunchEngineLoop.cpp` (`UpdateCoreCsvStats_EndFrame`) records global `GameThreadTime`, `RenderThreadTime`, and `GPUTime` in milliseconds. `CsvProfiler.cpp` implements `csvprofile START`, `STOP`, `FRAMES=N`, and the final `EVENTS` header plus `[HasHeaderRowAtEnd]` metadata. The parser uses that final header, supports quoted events/metadata, requires all three native metrics, rejects negative/nonfinite/malformed values, counts incomplete early rows, and warns when GPU timing is entirely zero. It does not sum overlapping thread/GPU times or infer a bottleneck from actor counts.

Execution awaits the other chat's handback and the user's choice of which existing preview window to use. The original preview may still be running and competing for GPU time. Do not close it or another editor arbitrarily, and do not run a GPU comparison under NullRHI.

Primary procedure after coordination:

1. Use one existing coordinated GPU-rendering preview/editor window, with the exact connected map, fixed camera, existing 1280x720 resolution and existing rendering flags/settings. Record commit, engine, map, view, player/PIE state, RHI, resolution, graphics settings, foreground state and every other GPU workload. Standalone and editor/PIE samples are separate baselines.
2. Wait at least 30 seconds after startup, loading and shader compilation have finished. Then enter `csvprofile FRAMES=3600` in that window's console. This imposes a frame budget; it is **not** a 30-second duration. The primary stops it with `csvprofile STOP` after 30 seconds of wall time, or it may finish sooner if the frame budget is exhausted. Note actual wall duration and output-log completion/path. Profiler state is temporary; no config change is needed. Check profiler is stopped on early exit/error.
3. Use the completed, uncompressed `.csv` in the reported profiling path (normally `Saved/Profiling/CSV/`), without replacing the original. Compression can be selected as a capture-only launch option `-csvCompression=0` for a future coordinated launch if necessary; it does not change project graphics. This parser intentionally rejects non-UTF-8/compressed input.
4. Parse without launching Unreal: `python Tools/quality/performance/native_csv.py "PATH TO CAPTURE.csv"`. Redirect the JSON only to `Saved/QualityPerformance/native-<context>.json`. It includes source path/hash, retained raw samples and avg/p50/p95/max for each available metric. `--discard-frames N` optionally removes explicitly known warmup frames; it cannot convert frames to seconds or prove loading finished. Report discarded count.
5. `-csvCaptureFrames=N` is a future launch-only alternative confirmed in installed source, but starts during boot and includes startup/loading. Do not treat such a capture as steady gameplay unless startup boundaries and retained frames are independently identified. Prefer post-warmup runtime capture.

Verify CSV parsing with `python Tools/quality/performance/test_native_csv.py`. Its synthetic fixtures prove parser behavior only, and are never reported as measured game performance. A native capture with valid GPU/game/render data and matching context is required before suggesting a measured optimization benefit.
