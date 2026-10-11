import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
parent=BP.get_parent(bp)
context=ue.load_asset('/Game/Core/Input/IMC_Coop')
RESULT={'parent':parent.get_path_name(),'actions':[{'action':m.action.get_path_name(),'key':str(m.key.get_editor_property('key_name'))} for m in context.default_key_mappings.mappings]}
parent_bp=ue.load_asset(parent.get_path_name().split('.')[0])
RESULT['parent_graphs']={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(parent_bp)} if isinstance(parent_bp,ue.Blueprint) else {}
(QUEUE/'movement-bindings.json').write_text(json.dumps(RESULT,indent=2))
