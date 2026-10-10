import pathlib,json,unreal as ue
ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));out=[]
for w in ws:
 a=ue.GameplayStatics.get_all_actors_with_tag(w,'Altar')[0]
 out.append({'world':w.get_path_name(),'completed':a.get_editor_property('Completed'),'busy':a.get_editor_property('TransactionBusy'),'candidate':str(a.get_editor_property('CandidateKey')),'placed':str(a.get_editor_property('PlacedKey')),'socket':str(a.get_editor_property('AltarSocket').get_world_location()),'can_active':a.call_method('IsRoundActive'),'players':[{'id':p.player_state.player_id,'local':p.is_locally_controlled(),'focused':str(p.get_editor_property('FocusedTarget')),'carried':str(p.call_method('GetCarried')),'can':a.call_method('CanAccept',args=(p,))} for p in ue.GameplayStatics.get_all_actors_of_class(w,ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class())]})
RESULT=out
