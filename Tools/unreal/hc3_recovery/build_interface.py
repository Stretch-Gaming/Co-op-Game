import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
guard()
path='/Game/Puzzles/Recovery/BPI_HCHealthBridge'
bp=unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset('BPI_HCHealthBridge','/Game/Puzzles/Recovery',unreal.Blueprint.static_class(),unreal.BlueprintInterfaceFactory())
owned(bp)
for g in list(BP.list_graphs(bp)):
 if g.get_name()=='NewFunction':BP.remove_function_graph(bp,'NewFunction')
for name,ins,outs in [('IsDowned',[],[('Downed','bool')]),('GetReviveSeconds',[],[('Seconds','float')]),('Revive',[('Reviver',unreal.Actor.static_class())],[]),('ResetHealth',[],[])]:fn(bp,name,ins,outs)
save(bp)
(HERE/'interface.json').write_text(json.dumps({'path':path,'functions':[str(x) for x in BP.list_functions(bp)]},indent=2))
