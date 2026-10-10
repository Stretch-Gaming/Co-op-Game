import pathlib,json,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
HERE=pathlib.Path(__file__).parent;bp=unreal.load_asset('/Game/Puzzles/BP_Altar');assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
(HERE/'saved-graphs.json').write_text(json.dumps({g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)},indent=2))
out={}
for name in ['CanAccept','AcceptKey','ResetAltar','IsRoundActive']:
 rows=[]
 for n in BP.find_nodes(BP.get_graph(bp,name)):
  info=BP._get_node_info(n)
  rows.append({'type':info.type_id,'node_class':n.get_class().get_name(),'inputs':[{'name':p.name,'type':p.type_id,'value':p.value,'links':[str(link) for link in p.connected_pins]} for p in info.input_pins],'outputs':[{'name':p.name,'type':p.type_id,'links':[str(link) for link in p.connected_pins]} for p in info.output_pins]})
 out[name]=rows
(HERE/'node-audit.json').write_text(json.dumps(out,indent=2));RESULT={'final_saved_graphs':True,'node_counts':{n:len(v) for n,v in out.items()}}
