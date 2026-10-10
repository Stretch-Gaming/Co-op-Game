import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Player/Tools/BP_Flare')
RESULT={'refresh_dsl':BP.read_graph_dsl(BP.get_graph(bp,'RefreshFlare')),'actors':[]}
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    now=ue.GameplayStatics.get_game_state(world).get_server_world_time_seconds()
    for actor in ue.GameplayStatics.get_all_actors_of_class(world,bp.generated_class()):
        row={'world':world.get_path_name(),'server':bool(ue.GameplayStatics.get_game_mode(world)),'name':actor.get_name(),'age':now-actor.get_editor_property('BurnStarted'),'seconds':actor.get_editor_property('BurnSeconds'),'active':bool(actor.call_method('IsActive')),'light_intensity':[c.intensity for c in actor.get_components_by_class(ue.PointLightComponent)]}
        if hasattr(ue.SystemLibrary,'is_timer_active'):row['timer_active']=ue.SystemLibrary.is_timer_active(actor,'RefreshFlare')
        RESULT['actors'].append(row)
(QUEUE/'flare-expiry-diagnostic.json').write_text(__import__('json').dumps(RESULT,indent=2))
