import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter');g=BP.get_graph(bp,'EventGraph')
RESULT=[{'id':BP._get_node_info(n).type_id,'name':n.get_name(),'class':n.get_class().get_name()} for n in BP.find_nodes(g)]
