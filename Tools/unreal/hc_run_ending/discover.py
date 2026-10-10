import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Puzzles/BP_MapExit');g=BP.get_graph(bp,'EventGraph');out={}
for q in ['IsPointinBoxwithTransform','GetActorTransform','GetWorldTransform','GetUnscaledBoxExtent','CollisionComponent','Utilities|Array|Contains','Utilities|Array|AddUnique','Utilities|Array|Clear','IsValid','GetWorld','GetGameInstance']:
 out[q]=list(BP.find_node_types(g,q))
for typ in ['Math|Geometry|IsPointinBoxwithTransform','Game|Player|IsPrimaryPlayer','Pawn|IsLocalController']:
 n=BP.create_node(g,typ,ue.IntPoint(10000,10000));out[typ]=str(BP._get_node_info(n));BP.delete_node(n)
(HERE/'needed-types.json').write_text(json.dumps(out,indent=2))
