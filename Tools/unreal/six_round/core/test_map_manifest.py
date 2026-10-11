"""Human/review manifest for the bounded isolated-map milestone (no Unreal)."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
MANIFEST={
 'worktree':str(ROOT),
 'execution_order':['world full connection-derived route with include_test_cave_proxies=false','player/place_test.py','core/puzzle_door_adapter.py','core/test_map_game_mode.py','core/test_map_build.py','core/50_place.py','core/test_map_audit.py'],
 'new_asset_writes':[
  '/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor',
  '/Game/Puzzles/Test/SixRound/BP_SixRoundTestGameMode',
  '/Game/Puzzles/Test/SixRound/L_SixRound_Test',
  '/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test',
  '/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'],
 'read_only_sources':['/Game/Hazards/L_Site01_HZ','/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor','/Game/Puzzles/EnvironmentConnection/Art/SM_ConnectionDoor','/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze','/Game/Core/BP_CoopGameMode'],
 'streamed_test_levels':['/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test','/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test','/Game/Hazards/Test/SixRound/L_WorldRoute_Test','/Game/Player/Test/SixRound/L_SixRound_PG_Test'],
 'forbidden_streams':['/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze','/Game/Puzzles/L_Site01_HC','/Game/Player/L_Site01_PG'],
 'door':{'count':1,'closed_root':[325,1400,200],'open_root':[325,1400,650],'bounds_extent':[150,17.5,200],'manual_e_bypass':False,'policy':'Round1 Cleared or Round6 opens; otherwise closes'},
 'native_editor_gates':['Explicit BlueprintEditorLibrary.add_function_override must return an actual override graph; no same-name fallback/shadow allowed','Inherited BPI_RoundReset must be present on the test door','Compile all new Blueprint assets','Copied cave boundary straddles must be inspected for collision duplication; source geometry is never silently edited','WorldRoute contains full clipped connection-derived maze once, no cave proxies; PG test placement exists'],
 'runtime_gates':['Fresh 2/3/4-player client/split native closed-door input test','Native first-room plate solution opens sole connection and mouth starts Round2','Both maze splits and all living-player regroups','All six round wipe/retry checkpoints including relic pedestal/cage escape retry','Taking protection, carrying, tools, cage, chase and return route','Native altar completion, five-second travel URL GameMode override, results counts, host R restart to isolated map','Output Log and split presentation'],
 'test_methods':{'core/test_map_native_gate.py':'Each independent local owner uses real movement/Interact; only approach positions are fixtures','core/test_map_native_flow.py':'Reuses existing owning-input flow fixture with the sole new door label; no direct gameplay RPC; approach/physics fixtures remain explicit'},
 'production_entry_later':'After PK publishes/unlocks the production layout, primary can assemble the same full route once with the owning production HC/PG sublevels and one puzzle door adapter, then adapt the production GameMode entry/restart target. No production persistent/sublevel, standalone preview door, or PK lock is modified by these test scripts.',
 'acceptance':'Scripts/offline gates only; no editor execution, binary changes, runtime or production completion claimed.'
}
if __name__=='__main__':
 out=ROOT/'Saved/SixRound/test-map-packet.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(MANIFEST,indent=2));print(json.dumps(MANIFEST,indent=2))
