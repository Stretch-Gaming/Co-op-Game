"""Read saved owning jump path and server mantle forwarding."""
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
RESULT={'functions':{},'jump_bindings':[]}
for name in ('RequestJump','RequestBoost','BoostOnServer'):
    RESULT['functions'][name]=BP.read_graph_dsl(BP.get_graph(bp,name))
for node in BP.find_nodes(BP.get_graph(bp,'EventGraph')):
    info=BP._get_node_info(node)
    if 'IA_Jump' not in info.type_id:continue
    item={'type':info.type_id,'outputs':{}}
    for name in ('Started','Triggered','Completed','Canceled'):
        pin=node.find_output_pin(name)
        item['outputs'][name]=[BP._get_node_info(p.get_owning_node()).type_id for p in pin.list_connected_pins()] if pin else None
    RESULT['jump_bindings'].append(item)
