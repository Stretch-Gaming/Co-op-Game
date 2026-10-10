import json
import unreal as ue
character=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();healthclass=ue.load_asset('/Game/Hazards/AC_Health').generated_class();viewclass=ue.load_asset('/Game/Player/AC_PlayerView').generated_class()
rows=[]
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
 gm=ue.GameplayStatics.get_game_mode(world);gs=ue.GameplayStatics.get_game_state(world);players=ue.GameplayStatics.get_all_actors_of_class(world,character)
 row={'world':world.get_path_name(),'server':bool(gm),'players':[],'area':gs.get_editor_property('AreaName'),'round':str(gs.get_editor_property('RoundState'))}
 for pawn in players:
  health=pawn.get_component_by_class(healthclass);view=pawn.get_component_by_class(viewclass)
  assert health and view
  data={'name':pawn.get_name(),'local':pawn.is_locally_controlled(),'input':pawn.get_editor_property('InputReady'),'health':health.get_editor_property('Health'),'downed':health.get_editor_property('bDowned'),'view':view.get_editor_property('ViewMode'),'location':str(pawn.get_actor_location())}
  if data['local']:
   widget=pawn.get_editor_property('PromptWidget');assert widget and widget.get_owning_player()==pawn.get_controller()
   data['camera']=pawn.get_component_by_class(ue.CameraComponent).field_of_view;data['arm']=pawn.get_component_by_class(ue.SpringArmComponent).target_arm_length
  row['players'].append(data)
 rows.append(row)
RESULT={'worlds':rows}
(QUEUE/'runtime-snapshot.json').write_text(json.dumps(RESULT,indent=2))
