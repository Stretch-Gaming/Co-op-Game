import unreal as ue
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();out=[]
for w in ue.EditorLevelLibrary.get_pie_worlds(True):
 k=ue.GameplayStatics.get_all_actors_with_tag(w,'KeyA')[0];carrier=k.get_editor_property('Carrier')
 out.append({'world':w.get_path_name(),'key_state':k.get_editor_property('CarryState'),'carrier_id':carrier.player_state.player_id if carrier and carrier.player_state else None,'players':[{'id':p.player_state.player_id,'local':p.is_locally_controlled(),'carried':str(p.get_component_by_class(AC).get_editor_property('CarriedItem')),'speed':p.character_movement.max_walk_speed} for p in ue.GameplayStatics.get_all_actors_of_class(w,C)]})
RESULT=out
