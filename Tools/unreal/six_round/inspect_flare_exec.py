"""Read only execution links around the flare timer and expiry."""
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Player/Tools/BP_Flare')
RESULT={}
for name in ('BeginFlare','RefreshFlare','EndFlare'):
    graph=BP.get_graph(bp,name);rows=[]
    for node in BP.find_nodes(graph):
        info=BP._get_node_info(node);row={'type':info.type_id,'outputs':{}}
        execute=node.find_execute_pin()
        if execute:row['exec_from']=[BP._get_node_info(p.get_owning_node()).type_id for p in execute.list_connected_pins()]
        for label in ('then','else','True','False','CastFailed','Is Valid','Is Not Valid'):
            pin=node.find_output_pin(label)
            if pin:row['outputs'][label]=[BP._get_node_info(p.get_owning_node()).type_id for p in pin.list_connected_pins()]
        rows.append(row)
    RESULT[name]={'dsl':BP.read_graph_dsl(graph),'links':rows}
(QUEUE/'flare-exec-diagnostic.json').write_text(__import__('json').dumps(RESULT,indent=2))
