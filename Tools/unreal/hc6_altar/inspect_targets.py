import pathlib,json,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
out={};bp=unreal.load_asset('/Game/Puzzles/BP_Altar')
for name in ['CanAccept','AcceptKey','ResetAltar']:
 rows=[]
 for n in BP.find_nodes(BP.get_graph(bp,name)):
  info=BP._get_node_info(n)
  if any(t in info.type_id.lower() for t in ['carried','reset','attach','clearr','carry']):rows.append({'type':info.type_id,'class':n.get_class().get_name(),'pins':[{'name':p.name,'type':p.type_id,'links':len(p.connected_pins)} for p in info.input_pins]})
 out[name]=rows
RESULT=out
