# HC-0 verification — Windows, 2026-10-09

Unreal 5.8.3 (changelist 58210709), Blueprint-only. The project uses Epic's Third Person template and includes the Vehicle Blueprint feature pack under `Content/VehicleTemplate/`, owned by VG. Original Third Person content hashes match the creation baseline.

## Project and assets

- Required MCP, All Toolsets, Python editor and Chaos Vehicles plugins enabled. `.mcp.json` points to the local editor server at port 8000.
- After saving and closing the editor, the project reopened on Site 1 with no startup errors or Accessed None messages. MCP responded on port 8000. The GameFeatureData scan rule required by the toolset plugins is configured.
- Editor and game start on `/Game/Maps/L_Site01`, a non-World-Partition map. HC, VG and HZ sublevels are Always Loaded.
- Persistent actors are four player starts and navigation bounds/data. The Basic floor and environment actors are in HZ; HC and VG sublevels are empty bootstraps.
- Navigation generation is Dynamic; maximum players is 4. GameMode defaults reference the four Coop player/GameState classes.
- All six core Blueprints compile without errors. GameMode and GameState inherit the non-Base classes. The character/controller inherit the original template classes.
- `RoundPhase` uses RepNotify; its graph calls `OnRoundPhaseChanged(NewPhase)`. `PhaseEndsAt`, `LootSecured` and `EndReason` replicate.
- Interaction, carry and ending contracts have their agreed names and inputs. Their later-sprint behavior is intentionally stubbed.

## Local multiplayer checks

PIE used **Play As Client**, with a dedicated server and separate client worlds in one editor process.

| Check | Two clients | Four clients |
| --- | --- | --- |
| Player count agrees on server and every client | 2 | 4 |
| Scaling row agrees everywhere | `2` | `4` |
| Server changes replicate Heist → Collapse → Getaway | Passed | Passed |
| Getaway notification during Lobby leaves phase unchanged | Passed | Passed |
| RequestEndRound remains a printing stub | Passed | Passed |
| Owning-client movement appears on server and other clients | Passed | Passed |
| Owning-client jump appears on server and other clients | Not separately measured | Passed |

The four-client run had no Error or Accessed None messages during its test interval. Template input uses the owning local player and adds HUD widgets to that player's screen. HC-1 will move pawn input contexts to possession changes as planned.

Heist scaling data was checked for all three rows: `2` = (3 plates, 2 statues, 100 seconds, 1 loot); `3` = (3, 1, 90, 2); `4` = (4, 1, 80, 3).

## Automation and remaining checks

The built-in Unreal MCP server was used for discovery, editor UI operations, asset editors and PIE control. Editor Python also called Unreal's Blueprint, asset and data-table toolset APIs for asset construction and graph wiring. Enums and structs used editor UI. Binary assets were never edited directly on disk.

Phase dispatcher wiring was inspected and replicated values were observed at runtime. Python could not attach a listener to this Blueprint multicast signature, so callback counts were not measured.

Playable 1 remains pending: both Macs and a second Windows client must join the Windows host using the same engine patch and commit. Local PIE does not verify cross-machine joining, Mac support or packaging. No HC-1 features were added.
