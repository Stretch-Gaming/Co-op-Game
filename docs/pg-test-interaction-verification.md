# PG-1 test character compatibility repair — #23

Owner: Stretch. Base: `91a5195`. The sole binary change is `Content/Player/Test/BP_PG_TestCharacter.uasset`, edited through Unreal 5.8.3 under LFS lock `56109203`. Core, maps, other gameplay assets and imported art are unchanged.

The test subclass's parameterless `Server_InteractBegin` shadowed Core's RPC with a `Target` actor input, making the full Blueprint scan fail. The subclass now uses inherited `PressInteract`/`ReleaseInteract` and the server's existing validated interaction lifecycle. Its controller-change chain also runs Core's shared input setup. The obsolete interaction graphs are removed; construction, ghost spawning and test-context handling are preserved.

Fresh project-wide compilation passed with zero errors and warnings. Actual Enhanced Input at 2, 3 and 4 Play As Client players passed instant use, timed cancellation/completion, continuous release and owning-player input/prompt checks. A listen host with two local players and two remote clients passed the same checks independently. Site 01 passed a separate two-client startup, ownership and class-load regression. Win64 Development packaging passed with zero cook errors/warnings and includes the previously failing PG test map.

Exact world observations, graph snapshots, hashes, compiled assets and package fingerprints are in `Tools/unreal/pg_signature_fix/evidence/verification.json` and its adjacent reports. Native gameplay input exercised RPC transport; editor Python only configured transient fixtures and read state. No maps were saved during tests. Editor settings were restored.

The checks are headless Windows execution. They do not establish rendered appearance, physical controller routing, Mac execution or the complete first/third-person goal of #23. Production carrying attachment/input is owned by the active HC-2 integration chat; health/downed implementation remains a separate dependency. No duplicate Core implementation was added.
