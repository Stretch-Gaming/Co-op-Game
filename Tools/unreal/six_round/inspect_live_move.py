import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter');graph=BP.get_graph(bp,'EventGraph')
nodes=[]
for node in BP.find_nodes(graph):
    info=BP._get_node_info(node)
    if 'IA_Move' in info.type_id:
        nodes.append({'id':info.type_id,'links':{str(pin.name):[BP._get_node_info(p.get_owning_node()).type_id for p in node.find_output_pin(str(pin.name)).list_connected_pins()] for pin in info.output_pins}})
players=[]
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    for pawn in ue.GameplayStatics.get_all_actors_of_class(world,bp.generated_class()):
        players.append({'local':pawn.is_locally_controlled(),'id':pawn.player_state.player_id,'mode':str(pawn.character_movement.movement_mode),'blocked':pawn.get_editor_property('InteractionBlocked'),'velocity':str(pawn.character_movement.velocity)})
RESULT={'nodes':nodes,'players':players,'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp) if 'move' in g.get_name().lower()}}
(QUEUE/'live-movement-binding.json').write_text(json.dumps(RESULT,indent=2))
