import json,unreal as ue
classes={name:ue.load_asset(path).generated_class() for name,path in {'pawn':'/Game/Core/BP_CoopCharacter','tools':'/Game/Player/Tools/AC_Tools','flare':'/Game/Player/Tools/BP_Flare'}.items()}
data=[]
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
    row={'world':world.get_path_name(),'flares':len(ue.GameplayStatics.get_all_actors_of_class(world,classes['flare'])),'players':[]}
    for pawn in ue.GameplayStatics.get_all_actors_of_class(world,classes['pawn']):
        tools=pawn.get_component_by_class(classes['tools']);eyes,rot=pawn.get_actor_eyes_view_point()
        row['players'].append({'id':pawn.player_state.player_id,'local':pawn.is_locally_controlled(),'allowed':tools.call_method('CanUseTools'),'stock':tools.get_editor_property('FlaresLeft'),'eye':str(eyes),'aim':str(rot),'position':str(pawn.get_actor_location())})
    data.append(row)
RESULT=data
(QUEUE/'flare-runtime-diagnostic.json').write_text(json.dumps(data,indent=2))
