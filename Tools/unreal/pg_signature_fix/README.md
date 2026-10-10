# PG test interaction compatibility — #23

`BP_PG_TestCharacter` previously declared a parameterless `Server_InteractBegin`, conflicting with Core's `Target` actor parameter. Its separate interaction implementation also treated timed use as instant and its controller-change override skipped Core input setup.

The saved Blueprint now inherits Core's interaction RPCs. `IA_PG_Interact` Started calls `PressInteract`; Completed and Canceled call `ReleaseInteract`. Controller changes call the shared `HC1ControllerChanged` setup before the preserved PG mapping chain. The old interaction lookup/handlers are removed. Ghost-spawn, construction and PG test-context graphs are preserved.

The explicit one-shot `repair.py` uses Unreal editor APIs and saves only the locked PG test asset. It is pinned to this repair's isolated checkout, UE 5.8.3 and the original asset hash. It refuses another checkout or an already-modified asset. Do not rerun it on the delivered Blueprint. `inspect.py` is read-only; other helpers drive this session's isolated editor on MCP port 8028 and PIE port 17828. They never connect to the default MCP endpoint.

`test_input.py` configures transient PIE probes and observes every peer. Input is injected in each pawn's owning Enhanced Input subsystem. No interaction RPC or gameplay function is invoked from Python. `finalize.py` checks saved hashes, fresh compilation/cook logs and captured runtime reports.

Evidence is in `evidence/`. The 2/3/4-client tests cover owning contexts/prompts, instant use, short timed cancellation, completed timed use and continuous begin/release. The four-player split test has two local host owners and two remote clients. Site 01 passes a separate two-client startup/ownership/class-load smoke. Win64 Development packaging includes both production maps, the PG test map and all four HC test maps.

These are headless Windows checks. Physical gamepad routing, visual/Mac acceptance and health/downed gameplay remain separate. Issue #23's complete first/third-person acceptance is not closed by this compatibility repair.
