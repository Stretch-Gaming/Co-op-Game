import json,unreal as ue
data={'registry_contexts':list(ue.EditorAssetLibrary.list_assets('/Game/Core/Input',True,False)),'contexts':[]}
for name in ('IMC_SixRound','IMC_RunControls'):
    context=ue.load_asset('/Game/Core/Input/'+name)
    data['contexts'].append({'path':context.get_path_name(),'class':context.get_class().get_path_name(),
      'mappings':[{'action':mapping.action.get_path_name() if mapping.action else None,'key':str(mapping.key.get_editor_property('key_name'))} for mapping in context.mappings]})
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
movement=BP.get_default_object(ue.load_asset('/Game/Core/BP_CoopCharacter')).get_component_by_class(ue.CharacterMovementComponent)
data['movement']={'walk':movement.max_walk_speed,'jump_z':movement.jump_z_velocity,'gravity':movement.gravity_scale}
carry=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying')
data['carry_vars']=list(BP.list_variables(carry))
data['carry_speed_graphs']={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(carry) if 'speed' in g.get_name().lower()}
(QUEUE/'input-inspection.json').write_text(json.dumps(data,indent=2))
RESULT=data
