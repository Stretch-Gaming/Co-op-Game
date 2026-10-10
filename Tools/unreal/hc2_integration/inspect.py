import json
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools
report={}
for path in ['/Game/Core/BP_CoopGameMode','/Game/Core/BP_CoopGameState','/Game/Core/BP_CoopPlayerState','/Game/Core/BP_CoopPlayerController','/Game/Core/BP_CoopCharacter','/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD']:
 bp=unreal.load_asset(path)
 report[path]={'variables':list(BP.list_variables(bp)),'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
(HERE/'baseline-graphs.json').write_text(json.dumps(report,indent=2))
