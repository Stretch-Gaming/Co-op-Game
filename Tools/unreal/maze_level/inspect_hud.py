import json,sys,hashlib
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD')
graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
graph=BP.get_graph(bp,'UpdateSixHUD');rows=[]
for n in BP.find_nodes(graph):
    info=BP._get_node_info(n)
    if any(t in info.type_id for t in ('SetDisplayObjective','Select','CastToBP_CoopGameState')):
        rows.append({'name':n.get_name(),'type':info.type_id,
            'inputs':[{'name':p.name,'type':p.type_id,'value':str(p.value),'links':[str(l) for l in p.connected_pins]} for p in info.input_pins],
            'outputs':[{'name':p.name,'type':p.type_id,'links':[str(l) for l in p.connected_pins]} for p in info.output_pins]})
report={'graphs':graphs,'nodes':rows,'asset_sha256':hashlib.sha256((ROOT/'Content/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.uasset').read_bytes()).hexdigest()}
path=QUEUE/'hud-baseline.json'
assert not path.exists(),'Do not overwrite HUD baseline'
path.write_text(json.dumps(report,indent=2));RESULT={'nodes':rows}
