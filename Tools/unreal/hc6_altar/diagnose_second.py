import unreal as ue
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();out=[]
for w in ue.EditorLevelLibrary.get_pie_worlds(True):
 a=ue.GameplayStatics.get_all_actors_with_tag(w,'KeyB')[0]
 rows=[]
 for p in ue.GameplayStatics.get_all_actors_of_class(w,C):
  camera=p.get_component_by_class(ue.CameraComponent)
  rows.append({'id':p.player_state.player_id,'local':p.is_locally_controlled(),'location':str(p.get_actor_location()),'camera':str(camera.get_world_location()),'rotation':str(camera.get_world_rotation()),'control':str(p.get_controller().get_control_rotation()) if p.get_controller() else None,'distance':p.get_distance_to(a),'focus':str(p.get_editor_property('FocusedTarget')),'inputheld':p.get_editor_property('InputHeld'),'carried':str(p.get_component_by_class(AC).get_editor_property('CarriedItem')),'key_can':a.call_method('CanInteract',args=(p,))})
 out.append({'world':w.get_path_name(),'key_location':str(a.get_actor_location()),'key_state':a.get_editor_property('CarryState'),'players':rows})
RESULT=out
