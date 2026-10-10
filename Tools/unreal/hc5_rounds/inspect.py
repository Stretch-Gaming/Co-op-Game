import json, inspect, unreal as u
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
out={}
for name in ['BP_CoopGameMode','BPI_RoundReset']:
 b=u.load_asset('/Game/Core/'+name);assert b,name
 out[name]={'graphs':{str(x):BP.read_graph_dsl(BP.get_graph(b,str(x))) for x in (['StartRound','ClearRound','FailRound'] if name=='BP_CoopGameMode' else ['ResetForRound'])}}
g=BP.get_graph(u.load_asset('/Game/Core/BP_CoopGameMode'),'EventGraph')
out['nodes']={f:BP.find_node_types(g,f) for f in ['GetAllActorsWithInterface','ResetForRound','SetTimer','ClearTimer','GetPawn','GetPlayerArray','SetActorTransform','GetActorTransform','GetOverlapping','GetPlayerCount','DoesImplement']}
out['methods']=[x for x in dir(BP) if 'interface' in x or 'array' in x]
(HERE/'inspection.json').write_text(json.dumps(out,indent=2,default=str))
