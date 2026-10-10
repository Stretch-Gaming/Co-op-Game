# HC2 editor workflow

Open this checkout's CoopGame.uproject in Unreal 5.8.3, using a separate MCP
port (8004 for this task). Core files require their LFS locks. Never use the
original checkout or another chat's editor.

The shipped Blueprint assets are already authored. Do not run build.py just
to play or verify. It preserves shared signatures and HC-1 interaction graphs,
but authoring is an explicit operation and is not an automatic migration.
For a new empty relic asset, add BPI_Interactable through Class Settings first.
Configure Multicast_Pickup as Multicast with Reliable unchecked in the editor;
this flag is not writable through the public Python API. The build requires
those existing contracts. Save only owned/locked packages.

editor_loop.py is an opt-in command loop for this exact checkout; it validates
the project and engine and refuses authoring/compile scripts during PIE.
Launch it with -ExecutePythonScript="<absolute forward/slash path>". Its local
command/ready files and saved Play settings are ignored. request.py submits one
owned script and waits for its result. rpc.py talks only to localhost:8004 and
checks the editor's exact project marker before executing a control.

Windows Python commands (replace the executable if needed):

    python -B Tools/unreal/hc2_integration/request.py engine_audit.py
    python -B Tools/unreal/hc2_integration/run_clients.py 2
    python -B Tools/unreal/hc2_integration/run_clients.py 3
    python -B Tools/unreal/hc2_integration/run_clients.py 4
    python -B Tools/unreal/hc2_integration/run_hc1.py 2

The early behavior recovery session used unattended NullRHI after the original renderer crash. Reliable Drop was configured through Slate in a D3D11/ray-tracing-disabled editor; final integrated checks use that editor. run_clients.py and run_hc1.py currently archive intervals from Saved/Logs/HC2-ui.log.
Do not treat NullRHI as visual evidence. The earlier normal-renderer tests and
reviewed delivery images have separate provenance.

For host tests, stop PIE, run configure.py with {"clients":2,"mode":"PIE_ListenServer"},
start PIE through the isolated EditorAppToolset, then request test_host.py.
It uses native CreatePlayer/RemovePlayer only for fixture joins; production
F5/F6 remain dependent on PG's BPFL_SplitScreen. Host/pickup actions go through
owning Enhanced Input, not Python calls to gameplay RPCs.

test_fresh_join.py derives the port from this editor's own latest "IpNetDriver listening on port" log line in HC2-ui.log; a supplied port must match it. Concurrent editors can occupy 17777;
never assume that port or connect to another chat's session. The test reloads
the remote client world, verifies initial collected-state replication and then
picks up another relic through the fresh owner's input.

Stop PIE before audit.py or engine_audit.py, restore the saved Play/performance
settings with restore.py, and review the changed paths before committing.
The only persisted test level is /Game/Puzzles/Test/HC2/L_HC2_Test. Cave tutorial
placement belongs to the cave/prop owner; see docs/hc2-verification.md.
