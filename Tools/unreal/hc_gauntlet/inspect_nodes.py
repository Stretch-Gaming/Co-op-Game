import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator')
g=BP.get_graph(bp,'EventGraph')
terms=ARGS.get('terms',['GetPlayerState','ContainsItem','AddUnique','InverseTransformLocation','GetControlledPawn','GetController','GetOpen','GetCurrentLift','AreLeversHeld','GetComponentByClass','IsDowned','GetFixtureOnly','RequestLatch','QueryLatch','FindCoordinator','ResetForRound'])
report={term:BP.find_node_types(g,term) for term in terms}
(HERE/'node-types.json').write_text(json.dumps(report,default=str,indent=2))
