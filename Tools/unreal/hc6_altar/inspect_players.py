import unreal as ue
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
RESULT=[{'world':w.get_path_name(),'players':[{'id':p.player_state.player_id if p.player_state else None,'local':p.is_locally_controlled(),'pawn':p.get_name()} for p in ue.GameplayStatics.get_all_actors_of_class(w,C)]} for w in ue.EditorLevelLibrary.get_pie_worlds(True)]
