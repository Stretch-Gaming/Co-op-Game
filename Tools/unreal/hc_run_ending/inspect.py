import json, unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
report={'identity':{'project':ue.Paths.project_dir(),'engine':ue.SystemLibrary.get_engine_version()},'assets':{}}
for path in ['/Game/Puzzles/BP_MapExit','/Game/Core/BP_CoopGameInstance','/Game/Core/BP_CoopPlayerController','/Game/Hazards/AC_Health']:
 bp=ue.load_asset(path)
 report['assets'][path]=None if not bp else {'variables':list(BP.list_variables(bp)), 'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
(HERE/'baseline.json').write_text(json.dumps(report,indent=2))
print(report['identity'])
