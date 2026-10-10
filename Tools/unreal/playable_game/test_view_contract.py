import time,json,traceback,unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();V=ue.load_asset('/Game/Player/AC_PlayerView').generated_class();library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
locals_=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.player_state.player_id)
owner=locals_[0];pid=owner.player_state.player_id;sub=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(owner.get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
state={'phase':0,'start':time.monotonic(),'checks':[],'deadline':time.monotonic()+20};report=QUEUE/'view-contract-runtime.json'
def pawn(world):return next(p for p in ue.GameplayStatics.get_all_actors_of_class(world,C) if p.player_state.player_id==pid)
def finish(passed,error=None):
 ue.unregister_slate_post_tick_callback(state['handle']);report.write_text(json.dumps({'passed':passed,'error':error,'players':len(locals_),'checks':state['checks']},indent=2))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];phase=state['phase'];assert time.monotonic()<state['deadline']
  if phase==0 and elapsed>1:
   for p in locals_:
    assert p.get_component_by_class(ue.SpringArmComponent).target_arm_length==0;assert p.get_component_by_class(ue.CameraComponent).field_of_view==90
   for w in worlds:
    p=pawn(w);assert p.use_controller_rotation_yaw;assert not p.character_movement.orient_rotation_to_movement
   state['checks'].append('first person and facing mode applied from scratch on server and clients');state['phase']=1;state['start']=time.monotonic()
  elif phase==1:
   sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/IA_ToggleView'),ue.Vector(1 if elapsed<.2 else 0,0,0),[],[])
   if elapsed>1:
    for w in worlds:
     p=pawn(w);assert p.get_component_by_class(V).get_editor_property('ViewMode')==1;assert not p.use_controller_rotation_yaw;assert p.character_movement.orient_rotation_to_movement
    assert owner.get_component_by_class(ue.SpringArmComponent).target_arm_length==380;assert owner.get_component_by_class(ue.CameraComponent).field_of_view==75
    state['checks'].append('client switch glides fully to third person and every peer uses the correct facing mode');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':'view-contract-runtime.json'}
