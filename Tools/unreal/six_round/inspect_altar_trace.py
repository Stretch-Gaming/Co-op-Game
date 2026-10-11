import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
RESULT={'focus_dsl':BP.read_graph_dsl(BP.get_graph(bp,'RefreshFocus')),'owners':[]}
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    for pawn in ue.GameplayStatics.get_all_actors_of_class(world,bp.generated_class()):
        if not pawn.is_locally_controlled():continue
        row={'id':pawn.player_state.player_id,'can_accept_input':bool(pawn.call_method('CanAcceptSixInput')),'cameras':[]}
        for camera in pawn.get_components_by_class(ue.CameraComponent):
            start=camera.get_world_location();end=start+ue.MathLibrary.get_forward_vector(camera.get_world_rotation())*800
            hit=ue.SystemLibrary.sphere_trace_single(world,start,end,18,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],ue.DrawDebugTrace.NONE,True)
            actor=hit.to_dict().get('hit_actor') if hit else None
            row['cameras'].append({'name':camera.get_name(),'active':camera.is_active(),'location':str(start),'rotation':str(camera.get_world_rotation()),'hit':actor.get_actor_label() if actor else None,'hit_class':actor.get_class().get_name() if actor else None})
        RESULT['owners'].append(row)
(QUEUE/'altar-trace-diagnostic.json').write_text(json.dumps(RESULT,indent=2))
