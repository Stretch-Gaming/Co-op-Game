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
We're in Sprint N. I'm lane VG, and my phase is VG-N in docs/epics/epic-vehicle-getaway.md.
Read AGENTS.md first. The current level is L_Site01_VG. Only work in Content/Vehicle/.
Start by listing the Unreal MCP toolsets you have.
```

## Smoke test (Sprint 0, every machine)

Ask your agent to do each of these, and record the results below. VG owns this table; the others report anything different on their machine.

1. List the toolsets.
2. Spawn a cube in your lane's sublevel and move it.
3. Create a Blueprint actor in your lane folder and give it a variable.
4. Add a node to that Blueprint's graph, connect it, and compile.
5. Add a row to your lane's scaling data table.
6. Start and stop Play In Editor.

| Task | Works? | Notes |
| --- | --- | --- |
| List toolsets | | |
| Spawn, move and label actors | | |
| Set actor and component properties | | |
| Create a Blueprint asset | | |
| Add components and variables | | |
| Add and connect graph nodes | | |
| Compile a Blueprint | | |
| Create or edit a widget | | |
| Edit data table rows | | |
| Start and stop Play In Editor | | |
| Run a console command | | |

## Working with the agent

- **Good agent work:** blocking out rooms from the layout doc, placing and labeling actors, setting properties and defaults, material instances, data table rows, and scaffolding Blueprints (assets, components, variables, empty functions).
- **Usually human work:** wiring Blueprint graphs if the smoke test shows the tools can't, game feel, and tuning during playtests.
- Name the folder and sublevel in every request. Agents put things in the wrong place when you don't.
- The server runs one tool call at a time on the editor's main thread. Don't ask for parallel calls.
- After each batch of changes: compile, Save All, and run `git status`. Commit only your lane's files and any you've locked.
