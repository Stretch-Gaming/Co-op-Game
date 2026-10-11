# Unreal MCP: driving the editor with an agent

We use **Unreal MCP**, the MCP server Epic ships inside Unreal Engine 5.8. It runs inside the editor and ships with the engine on both Mac and Windows, so there's nothing to compile or install per machine. Epic marks it **experimental**: tools and data formats can change between engine versions.

Reference: [Unreal MCP in Unreal Editor](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor).

## Project setup (Windows, once, in HC-0)

1. Enable the plugins **Unreal MCP** and **All Toolsets**, then restart the editor. All Toolsets provides the actual tools; without it the server has none. Toolset Registry turns on automatically.
2. In the editor console, run `ModelContextProtocol.GenerateClientConfig ClaudeCode`. This writes `.mcp.json` to the repo root, pointing at `http://127.0.0.1:8000/mcp`.
3. Commit `.mcp.json`. The address is the same on every machine.

## Each machine

1. In the editor, go to Edit → Editor Preferences → General → Model Context Protocol and turn on **Auto Start Server**. This is a per-user setting, so each person sets it once.
2. With the editor open, start Claude Code from the repo root: `cd Co-op-Game && claude`. Approve the `unreal-mcp` server when asked, then run `/mcp` to check it's connected.
3. The server lives inside the editor, so the agent loses its tools when the editor closes.

If the server isn't running, use the editor console command `ModelContextProtocol.StartServer 8000`. After a plugin change, run `ModelContextProtocol.RefreshTools` and reconnect. Errors go to the `LogModelContextProtocol` log category. Keep the port at 8000; a different port would need a different `.mcp.json` on that machine.

The server has no authentication and only listens on your own machine. Never expose port 8000 to the network.

## Starting a sprint with your agent

Paste this at kickoff, with your lane and phase filled in:

```
We're in Sprint N. I'm lane PG, and my phase is PG-N in docs/epics/epic-player-ghosts.md.
Read AGENTS.md first. The current level is L_Site01_PG. Only work in Content/Player/.
Start by listing the Unreal MCP toolsets you have.
```

## Smoke test (Sprint 0, every machine)

Ask your agent to do each of these, and record the results below. PG owns this table; the others report anything different on their machine.

1. List the toolsets.
2. Spawn a cube in your lane's sublevel and move it.
3. Create a Blueprint actor in your lane folder and give it a variable.
4. Add a node to that Blueprint's graph, connect it, and compile.
5. Add a row to your lane's scaling data table.
6. Start and stop Play In Editor.

| Task | Works? | Notes |
| --- | --- | --- |
| List toolsets | Works | `list_toolsets` returns about 60 toolsets; `describe_toolset` gives each tool's schema. Call a tool with its short name plus `toolset_name` (the full dotted name fails with "Unknown tool"); inside `execute_tool_script`, use the full dotted name. `BlueprintTools` and `UMGToolSet` descriptions are 60–70 KB, so save them to a file and search them rather than reading them whole. |
| Spawn, move and label actors | Works | `SceneTools.add_to_scene_from_asset` (`/Engine/BasicShapes/Cube`) spawns into the current level; `ActorTools.set_actor_transform`, `set_label` and `add_tag`. No MCP tool sets the current level: `SceneTools.get_current_level` only returns the persistent map, and the viewport's Current Context dropdown can't be driven through `SlateInspectorToolset.SelectOption`. Set it in the Levels panel, or with `py` (see "Run a console command"): `unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name('L_Site01_PG')`. |
| Set actor and component properties | Works | `ObjectTools.list_properties`, `get_properties` and `set_properties` (values as a JSON string), for example `CastShadow` on a `StaticMeshComponent`. Some engine state isn't exposed as properties, such as `UWorld.CurrentLevel`. |
| Create a Blueprint asset | Works | `BlueprintTools.create` with a folder, a name and the parent class (`/Script/Engine.Actor`). |
| Add components and variables | Works | `BlueprintTools.add_variable` takes primitives plus `Vector`, `Rotator`, `Transform`, `Vector2D` and `LinearColor`; `add_object_variable` and `add_struct_variable` cover the rest. `set_variable_replication` and `set_variable_instance_editable` exist. `ActorTools.add_component` works on a Blueprint. |
| Add and connect graph nodes | Works | `add_event` (`ReceiveBeginPlay`), `find_node_types`, `create_node` (`Development\|PrintString`), `connect_pins` with pin IDs from `get_node_infos` (node, direction, index), and `set_pin_value`. `read_graph_dsl` and `write_graph_dsl` read and write a whole graph as an S-expression script. |
| Compile a Blueprint | Works | `compile_blueprint` with `warnings_as_errors: true` came back clean. |
| Create or edit a widget | Works | `UMGToolSet.CreateWidgetBlueprint`, `AddWidget` (a `CanvasPanel` root, then a `TextBlock`), `ObjectTools.set_properties` for `Text`, then `CompileWidgetBlueprint`. |
| Edit data table rows | Works | `DataTableTools.create`, `add_rows`, `set_rows` (camelCase field names), `rename_rows`, `remove_rows` and `get_rows`. PG's `DT_GhostScaling` arrives in PG-1, so this ran on a throwaway table in `Content/Player/Test/` with HC's `S_RoundScaling` as its row struct, then deleted it. |
| Start and stop Play In Editor | Partly | `EditorAppToolset.StartPIE`, `IsPIERunning` and `StopPIE` work, but `StartPIE` has no net mode or player count; it uses the editor's play settings (here Standalone, 1 player). Those are readable on `/Script/UnrealEd.Default__LevelEditorPlaySettings` (`PlayNetMode`, `PlayNumberOfClients`); set them in the Play menu before a client test. |
| Run a console command | Partly | No MCP tool for it. Workaround: `SlateInspectorToolset.Snapshot` to find the status bar's Cmd textbox, then `Type` with `submit: true`; read the result with `LogsToolset.GetLogEntries`. With `PythonScriptPlugin`, `py <file.py>` runs full editor Python this way. `ProgrammaticToolset.execute_tool_script` is a different, sandboxed Python (only `json`, `math`, `re`, `time`, `datetime` and `copy`; no `unreal` module) for batching MCP calls. |

Also available but not part of the smoke test: `MaterialTools` (create materials and functions, add, connect and delete expressions, connect to material outputs, recompile), `MaterialInstanceTools`, `EditorAppToolset.CaptureViewport` and `CaptureEditorImage` (base64 PNGs, too big to read inline, so decode them to a file), `SetCameraTransform`, and `AssetTools`.

### PG-0 — 2026-10-09, PK's Mac (M4 Pro)

Ran on Unreal 5.8.3 with `L_Site01` open and `L_Site01_PG` made current through `py`. The test cube, `BP_PG_SmokeTest`, `WBP_PG_SmokeTest`, `DT_PG_SmokeTest` and the `Content/Player/Test/` folder were deleted afterwards, and `L_Site01_PG` wasn't saved, so nothing changed on disk.

Mac-specific notes:

- The editor raised a Memory Pressure Warning toast while idle with `L_Site01` open. Close other apps before long sessions.
- PIE started by the agent logged `max tick rate 3` while the terminal had focus. Bring the editor to the front for any check where frame rate matters.
- `LogAudioMixerAudioUnit: Error querying Sample Rate` appears at startup and on PIE. It's harmless.

Material building (PG-A0 style kit): `M_Stylized` has 92 expressions and was built in one editor Python script run through `py`, with `MaterialEditingLibrary` (`create_material_expression`, `connect_material_expressions`, `connect_material_property`, `recompile_material`), then checked with `MaterialTools.recompile`, which raises on shader errors and came back clean. `MaterialTools` alone could build the same graph node by node, but each node and wire is a separate call, so a script is much faster. What the tools can't do or don't expose:

- Read compile errors back as data. Look for `LogMaterial` errors with `LogsToolset`, or capture the material's thumbnail.
- Change texture import settings. Use Python to set `srgb` and `compression_settings` (for example `TC_Masks` for packed masks). The sampler type on each texture parameter must match those settings, or the material fails to compile.
- Set a level's exposure. A post-process volume is needed for a stable look; `L_StyleTest` locks it at EV100 1.3.
- Hide editor sprites in `CaptureViewport`, even with `bShowUI: false`. Turn on game view first with `LevelEditorSubsystem.editor_set_game_view(True)`.
- Use `CaptureViewport` without an `annotations` object. Pass one with zero values to get a plain image.
- Check property names in advance. Some differ from the Details panel, such as `enable_volumetric_fog` on the height fog and `fog_inscattering_luminance` for its color.

`EditorLoadingAndSavingUtils.new_blank_map(False)` and `save_map` created `L_StyleTest` without a save prompt. Save the open assets first, because the map switch discards unsaved changes in other maps.

### PG-3 and PG-7: wiring whole Blueprints, 2026-10-09

`BP_Ghost`, `BP_Zipline` and `BP_ZiplineTrolley` were wired entirely by the agent, mostly with `write_graph_dsl`. What to know:

- `write_graph_dsl` **appends** to a graph and never replaces it. To rewrite a graph, delete its nodes first (`find_nodes` with an empty title, then `delete_node` on each one except the function entry and result). A failed write can leave half a graph behind.
- Look up node IDs with `find_node_types` before writing. Your own functions are `CallFunction|Name`, another Blueprint's are `Class|BPName|Name` (without underscores), and bool variables lose their `b` (`Variables|Default|GetRiding`). Giving a variable a category changes its ID to `Variables|<Category>|Get…`. The construction script is `(fn ConstructionScript () …)`.
- For member functions, a positional argument goes to `self` first. Pass everything else by pin name, such as `(Actor|SetLifeSpan :InLifespan 2.0)`. Read the graph back after writing it: an argument that went to the wrong pin shows up as `0`.
- The DSL can't create Enhanced Input action events or custom events. Make them with `create_node` (`Input|EnhancedActionEvents|IA_Name`, `AddEvent|Custom|Name`), put the logic in a function, and join the pins with `connect_pins`.
- Nothing in MCP or editor Python can make a custom event **Run on Server**: the flag is protected. Set it in the Blueprint editor's Details panel; driving that through `SlateInspectorToolset` works, as `SelectOption`, then `Click` on the option.
- You can't set another actor's `bCanBeDamaged` from an Actor Blueprint, because the setter only targets `self`. A non-Actor Blueprint gets a Target pin, so `AC_ZiplineRide.SetRiderProtected` does it. Function-library functions don't show up in `find_node_types`, so a library can't host this.
- Editor Python is the fast way to create Blueprints and components (`SubobjectDataSubsystem`), set class defaults (`get_default_object`) and import FBX files (`AssetImportTask` with `FbxImportUI`).
- To set the play options for a client test, write `PlayNetMode` and `PlayNumberOfClients` with `ObjectTools.set_properties`. Turn off `bThrottleCPUWhenNotForeground` on `/Script/UnrealEd.Default__EditorPerformanceSettings` while testing, or the editor drops to 3 frames a second, and turn it back on afterwards. Read every world during PIE with `EditorLevelLibrary.get_pie_worlds(True)`.
- Editor Python runs actor functions locally, even RPCs, so calling `Server_…` from Python doesn't test replication. Inject the input instead: `EnhancedInputLocalPlayerSubsystem.inject_input_vector_for_action` on a client's subsystem (find it with `unreal.ObjectIterator`) goes down the real input-to-RPC path.

### PG-7: 4-player PIE and reimports, 2026-10-10

- Save a level through its own package: use `actor.get_outermost()` or `world.get_outermost()`, then `EditorLoadingAndSavingUtils.save_packages`. Calling `unreal.load_package()` on a sublevel that's already loaded, then saving the result, wrote `L_Site01_PG` with its greybox cubes stripped of their mesh and transform. It had to be restored from Git.
- Play As Client with 4 players in one process runs at about 12 fps on PK's M4 Pro, with 5 worlds. Gameplay that's driven by server time still works, but the editor crashed once in `FSceneViewport::Destroy` when `StopPIE` closed the 4 client windows. Save everything before a 4-player PIE.
- After an editor crash, `CrashReportClient` can keep port 8000 open, so the relaunched editor's MCP server can't bind. Close the crash reporter first. If Auto Start Server is off, relaunch with `-ExecCmds="ModelContextProtocol.StartServer 8000"`.
- The `EnhancedInputLocalPlayerSubsystem` objects in PIE live under `/Engine/Transient`, not under a `PIE` path. Find them with `ObjectIterator` and skip `Default__`. An injected `IA_Move` follows each client's control rotation, so the same input can send different players in different directions.
- A `BoxComponent` with `OverlapOnlyPawn` still blocks `Visibility` line traces. Trace for `WorldStatic` objects when you want floors only.

### PG-1: structs, components and server events, 2026-10-10

- Nothing in MCP or editor Python adds members to a user-defined struct (`S_`). `EditorData` is protected. `S_GhostScaling` started as a duplicate of `S_RoundScaling`, and the struct editor did the rest. **Add Variable** works through `SlateInspectorToolset.Click`. Slate's `Type` and `PressKey` only append to a member's name; they can't select the old name. A real double-click on the name (a CGEvent, as in the PG-3 notes above) selects it all, and typing replaces it. The type dropdown needs real clicks too: open it, type `Float`, click the top row.
- `BlueprintTools.create` fails for a `BlueprintFunctionLibrary`. Use editor Python: `AssetTools.create_asset(name, folder, None, unreal.BlueprintFunctionLibraryFactory())`.
- `find_node_types` doesn't list a Blueprint that was just created, or a component just added to another Blueprint. `create_node` still makes the node if you pass `declaring_class`, such as `Class|ACPlayerView|ToggleView` with `/Game/Player/AC_PlayerView.AC_PlayerView_C`, or `Variables|Default|GetPlayerView` with the owning Blueprint's `_C` class.
- In `write_graph_dsl`, an engine property setter such as `Class|Pawn|SetUseControllerRotationYaw` sends a positional argument to the value pin, not to `self`. Pass `:self` by name.
- A pure node whose output feeds two places runs once for each, even after a `bind`. A tick that set `ViewBlend` from `FInterp To Constant`, then compared the same node's output with the target, stepped twice and stopped early. Compare against the Set node's `Output_Get` instead.
- `get_node_type_pins` returns pin names without adding a node to the graph.
- To bind a delegate, use `create_node` with `Pawn|AssignReceiveControllerChangedDelegate`. It adds the bind node and a matching custom event; connect its exec and target with `connect_pins`.
- With a Blueprint or struct editor open in its own window, that window has its own Cmd box. Type `py` commands into the main window's box, or close the other windows first.
- A second editor can run at the same time on another port: `open -n -a UnrealEditor.app --args <project> -ExecCmds="ModelContextProtocol.StartServer 8001"`. `open -a` without `-n` only brings the running editor to the front, even for a different project. Real clicks and `osascript ... activate` can land in either window, so use only Slate tools while two editors are open.
### HZ-1: struct members, pure functions and lighting, 2026-10-10

- No MCP tool or editor Python call edits a user-defined struct's members. Create the struct with `StructureFactory`, open it, and drive the struct editor with `SlateInspectorToolset`. Synthetic clicks on the type picker's rows don't commit. Open the picker, `Type` the type name into its focused Search box, then `PressKey` `Down` and `Enter`. To rename a member, `Type` an empty string into its name box to focus it, `PressKey` `Ctrl+A` and `BackSpace`, then `Type` the name into the inner focused textbox with `submit: true`. `Add Variable` reuses the last type picked.
- A Blueprint function's Pure flag isn't reachable from Python or `ObjectTools` (`ExtraFlags` is hidden). Double-click the function in My Blueprint with `SlateInspectorToolset`, then `Click` the Pure checkbox in Details.
- The cave prototype's sun had every lighting channel off, and its enclosure didn't cast shadows, so the sun lit nothing. Check `lighting_channels` and `cast_shadow` before blaming a light.
- `CaptureViewport` in the editor still draws actors that are only hidden in game, and their shadows. Turn on game view, or run Simulate, before judging light.
- `EditorLevelLibrary.get_pie_worlds(True)` includes the dedicated server's world. A test change made only in the client worlds is undone by server corrections.
- Python can't read which `PlayerController` owns an `EnhancedInputLocalPlayerSubsystem`. Nudge `IA_Move` through each subsystem in turn and see whose pawn moves.

## Working with the agent

- **Good agent work:** blocking out rooms from the layout doc, placing and labeling actors, setting properties and defaults, material instances, data table rows, and scaffolding Blueprints (assets, components, variables, empty functions).
- **Usually human work:** wiring Blueprint graphs if the smoke test shows the tools can't, game feel, and tuning during playtests.
- Name the folder and sublevel in every request. Agents put things in the wrong place when you don't.
- The server runs one tool call at a time on the editor's main thread. Don't ask for parallel calls.
- After each batch of changes: compile, Save All, and run `git status`. Commit only your lane's files and any you've locked.
- To bring in generated assets, follow [assets.md](assets.md): raw output in `SourceArt/<lane>/`, imports in your lane's `Art/` folder.
