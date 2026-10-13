"""Read-only live network positions for movement diagnostics."""
import unreal as ue
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
RESULT=[{'world':w.get_path_name(),'server':ue.SystemLibrary.is_server(w),'players':[{'position':str(p.get_actor_location()),'speed':p.character_movement.max_walk_speed,'jump_z':p.character_movement.jump_z_velocity,'velocity':str(p.character_movement.velocity),'mode':str(p.character_movement.movement_mode)} for p in ue.GameplayStatics.get_all_actors_of_class(w,C)]} for w in ue.EditorLevelLibrary.get_pie_worlds(True)]
for w,row in zip(ue.EditorLevelLibrary.get_pie_worlds(True),RESULT):
    for p,data in zip(ue.GameplayStatics.get_all_actors_of_class(w,C),row['players']):
        ignored=[p]+list(ue.GameplayStatics.get_all_actors_of_class(w,ue.load_asset('/Game/Puzzles/BP_KeyRelic').generated_class()))
        hit=ue.SystemLibrary.capsule_trace_single(w,p.get_actor_location(),p.get_actor_location()+p.get_actor_forward_vector()*100,42,96,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignored,ue.DrawDebugTrace.NONE,True)
        if hit:
            d=hit.to_dict();a=d.get('hit_actor');data['forward_block']={'actor':a.get_actor_label() if a else None,'point':str(d.get('impact_point')),'normal':str(d.get('impact_normal')),'class':a.get_class().get_name() if a else None}
