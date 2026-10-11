"""Expose only path destination settings; inspect the delivered zipline contract."""
import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/Taking/BP_TakingDirector')
for slot in range(4):BP.set_variable_instance_editable(bp,'PathStart'+str(slot),True)
save(bp)
zipline=ue.load_asset('/Game/Player/Zipline/BP_Zipline')
data={'variables':list(BP.list_variables(zipline)),'defaults':{},'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(zipline)}}
for name in data['variables']:
    try:data['defaults'][name]=str(BP.get_default_object(zipline).get_editor_property(name))
    except Exception as error:data['defaults'][name]=str(error)
(QUEUE/'zipline-contract.json').write_text(json.dumps(data,indent=2))
graph=BP.get_graph(ue.load_asset('/Game/Core/BP_CoopCharacter'),'EventGraph')
events=[]
for node in BP.find_nodes(graph):
    if node.get_class().get_name()=='K2Node_CustomEvent':
        events.append({'type_id':BP._get_node_info(node).type_id,'raw':ue.ToolsetLibrary.get_object_properties(node,['CustomFunctionName','FunctionFlags'])})
(QUEUE/'rpc-reflection.json').write_text(json.dumps(events,indent=2))
RESULT={'path_starts_editable':True,'zipline_report':'Saved/SixRound/zipline-contract.json','events':events}
