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

## Working with the agent

- **Good agent work:** blocking out rooms from the layout doc, placing and labeling actors, setting properties and defaults, material instances, data table rows, and scaffolding Blueprints (assets, components, variables, empty functions).
- **Usually human work:** wiring Blueprint graphs if the smoke test shows the tools can't, game feel, and tuning during playtests.
- Name the folder and sublevel in every request. Agents put things in the wrong place when you don't.
- The server runs one tool call at a time on the editor's main thread. Don't ask for parallel calls.
- After each batch of changes: compile, Save All, and run `git status`. Commit only your lane's files and any you've locked.
- To bring in generated assets, follow [assets.md](assets.md): raw output in `SourceArt/<lane>/`, imports in your lane's `Art/` folder.
