"""Read replicated meetup-stage instructions; preserve paint and owning-player logic."""
import json,sys,hashlib
sys.path.insert(0,str(HERE))
from context import *
path='/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD';bp=ue.load_asset(path)
baseline=json.loads((QUEUE/'hud-baseline.json').read_text())
before={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
assert hashlib.sha256((ROOT/'Content/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.uasset').read_bytes()).hexdigest()==baseline['asset_sha256'],'Saved HUD changed since inspection'
graph=BP.get_graph(bp,'UpdateSixHUD')
sets=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.endswith('SetDisplayObjective')]
normal=[n for n in sets if n.find_input_pin('DisplayObjective').list_connected_pins()];assert len(normal)==1
root=normal[0].find_input_pin('DisplayObjective').list_connected_pins()[0].get_owning_node()
assert root.get_class().get_name()=='K2Node_Select'
cleared=root.find_input_pin('Option 0').list_connected_pins()[0].get_owning_node()
assert cleared.get_class().get_name()=='K2Node_Select'
target=cleared.find_input_pin('Option 0');old=list(target.list_connected_pins());assert len(old)==1
cast=[n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.endswith('CastToBP_CoopGameState')];assert len(cast)==1
getter=BP.create_node(graph,'Class|BPCoopGameState|GetAdventureInstruction',ue.IntPoint(0,-300),declaring_class=ue.load_asset('/Game/Core/BP_CoopGameState').generated_class())
as_state=[p for p in BP._list_pins(cast[0],ue.EdGraphPinDirection.EGPD_OUTPUT) if str(p.get_pin_name()).lower().startswith('as')];assert len(as_state)==1
assert as_state[0].try_create_connection(getter.find_input_pin('self'))
target.break_single_pin_link(old[0]);assert getter.find_output_pin('AdventureInstruction').try_create_connection(target)
renamed=0
for node in BP.find_nodes(graph):
    for pin in BP._list_pins(node,ue.EdGraphPinDirection.EGPD_INPUT):
        if str(pin.get_pin_value())=='THE MEETING HALL':pin.set_pin_value('THE MEETUP HALLS');renamed+=1
assert renamed==1,renamed
save(bp)
after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
assert all(after[n]==body for n,body in before.items() if n!='UpdateSixHUD')
report={'asset':path,'changed_graph':'UpdateSixHUD only','paint_and_owner_graphs_preserved':True,
        'failure_clear_complete_prompts_preserved':True,'stage_text_source':'Replicated GameState.AdventureInstruction',
        'sha256':hashlib.sha256((ROOT/'Content/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.uasset').read_bytes()).hexdigest()}
(QUEUE/'hud-patch.json').write_text(json.dumps(report,indent=2));RESULT=report
