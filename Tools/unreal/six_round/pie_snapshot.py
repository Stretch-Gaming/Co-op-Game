import json,unreal as ue
character=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
health=ue.load_asset('/Game/Hazards/AC_Health').generated_class()
tools=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
items=[]
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    gs=ue.GameplayStatics.get_game_state(world)
    data={'world':world.get_path_name(),'server':bool(ue.GameplayStatics.get_game_mode(world)),'area':str(gs.get_editor_property('AreaName')) if gs else None,'round':gs.get_editor_property('RoundState').export_text() if gs else None,'players':[]}
    for pawn in ue.GameplayStatics.get_all_actors_of_class(world,character):
        location=pawn.get_actor_location()
        data['players'].append({'id':pawn.player_state.player_id if pawn.player_state else None,'slot':pawn.player_state.get_editor_property('ColorSlot') if pawn.player_state else None,'local':pawn.is_locally_controlled(),'dead':pawn.get_component_by_class(health).get_editor_property('bDead'),'flares':pawn.get_component_by_class(tools).get_editor_property('FlaresLeft'),'position':[location.x,location.y,location.z]})
    items.append(data)
(QUEUE/'pie-snapshot.json').write_text(json.dumps(items,indent=2))
RESULT=items
