import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
report={}
for path in ['/Game/Core/BP_CoopGameMode','/Game/Core/BP_CoopGameState','/Game/Core/BP_CoopPlayerState','/Game/Puzzles/BP_Relic','/Game/Puzzles/Test/HC2/BP_HC2InputProbe']:
 bp=ue.load_asset(path);report[path]={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
(HERE/'final-graphs.json').write_text(json.dumps(report,indent=2))
