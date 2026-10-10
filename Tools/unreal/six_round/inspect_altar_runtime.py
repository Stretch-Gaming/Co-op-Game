import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Puzzles/BP_Altar');pawn_class=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
RESULT={'graphs':{n:BP.read_graph_dsl(BP.get_graph(bp,n)) for n in ('CanInteract','CanAccept','IsRoundActive')},'worlds':[]}
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    altar=ue.GameplayStatics.get_all_actors_of_class(world,bp.generated_class())[0]
    row={'world':world.get_path_name(),'round_active':bool(altar.call_method('IsRoundActive')),'players':[]}
    for pawn in ue.GameplayStatics.get_all_actors_of_class(world,pawn_class):
        if not pawn.is_locally_controlled():continue
        target=pawn.get_editor_property('FocusedTarget')
        row['players'].append({'id':pawn.player_state.player_id,'focus':target.get_class().get_path_name() if target else None,'can_interact':bool(altar.call_method('CanInteract',args=(pawn,))),'location':str(pawn.get_actor_location())})
    RESULT['worlds'].append(row)
(QUEUE/'altar-runtime-diagnostic.json').write_text(json.dumps(RESULT,indent=2))
