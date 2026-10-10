import time,json,traceback,unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();D=ue.load_asset('/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor').generated_class();lib=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
ps=sorted(ue.GameplayStatics.get_all_actors_of_class(server,C),key=lambda p:p.player_state.player_id);assert len(ps)==2
local=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C)if p.is_locally_controlled()],key=lambda p:p.player_state.player_id);assert len(local)==2
original=[p.player_state.player_id for p in ps];door=ue.GameplayStatics.get_all_actors_of_class(server,D)[0];closed_z=door.get_actor_location().z
state={'phase':'closed','start':time.monotonic(),'deadline':time.monotonic()+100,'checks':[]}
report=OUTPUT/ARGS.get('report','client-walkthrough.json')
def move(i,value):
 controller=local[i].get_controller();action='/Game/Input/Actions/IA_Move';vector=ue.Vector(0,value,0)
 if i==1 and local[i].get_world()==server and local[0].get_world()==server:
  controller=local[0].get_controller();action='/Game/Core/Input/IA_P2Forward';vector=ue.Vector(value,0,0)
 sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
 sub.inject_input_vector_for_action(ue.load_asset(action),vector,[],[])
def use(value):
 sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(local[0].get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
 sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/IA_Interact'),ue.Vector(value,0,0),[],[])
def step(name):state['phase']=name;state['start']=time.monotonic()
def finish(ok,error=None):
 ue.unregister_slate_post_tick_callback(state['handle']);move(0,0);move(1,0)
 report.write_text(json.dumps({'passed':ok,'error':error,'phase':state['phase'],'checks':state['checks'],'players':[{ 'id':p.player_state.player_id,'position':str(p.get_actor_location())}for p in ps],'door_position':str(door.get_actor_location()),'worlds':[w.get_path_name()for w in worlds],'method':'Two joining clients use native movement and E interaction; only initial approach positions are fixtures. No map travel and no puzzle calls.'},indent=2))
if ARGS.get('resume_walk'):
 state['phase']='maze';state['checks']=json.loads((OUTPUT/'client-walk-timing-attempt.json').read_text())['checks']
 for p in local:p.get_controller().set_control_rotation(ue.Rotator(yaw=90))
else:
 for i,p in enumerate(ps):
  p.set_actor_location(ue.Vector(275+i*100,1100-i*150,100),False,True);p.character_movement.stop_movement_immediately();local[i].get_controller().set_control_rotation(ue.Rotator(yaw=90))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];phase=state['phase'];assert time.monotonic()<state['deadline'],'walkthrough timed out'
  if phase=='closed':
   move(0,1)
   if elapsed>2:
    pos=ps[0].get_actor_location();assert 1200<pos.y<1380 and 70<pos.z<160,('closed door failed to block',str(pos))
    move(0,0);state['checks'].append('closed door physically blocks walking from the room');step('focus')
  elif phase=='focus':
   local[0].get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(local[0].get_component_by_class(ue.CameraComponent).get_world_location(),door.get_actor_location()))
   if elapsed>1:
    focused=local[0].get_editor_property('FocusedTarget');assert focused and focused.get_class()==D,('door focus',str(focused));step('open')
  elif phase=='open':
   use(1 if elapsed<.2 else 0)
   if elapsed>1.5:
    assert door.get_editor_property('Open');assert door.get_actor_location().z>closed_z+440
    for w in worlds:
     other=ue.GameplayStatics.get_all_actors_of_class(w,D)[0];assert other.get_editor_property('Open');assert abs(other.get_actor_location().z-door.get_actor_location().z)<5
    state['checks'].append('normal E opens the moving door on server and both clients');local[0].get_controller().set_control_rotation(ue.Rotator(yaw=90));step('maze')
  elif phase=='maze':
   move(0,1)
   if ps[0].get_actor_location().y>3600:
    pos=ps[0].get_actor_location();assert pos.y>3450 and -100<pos.z<300,('maze approach blocked',str(pos));move(0,0)
    state['checks'].append('client walks from room through open doorway and joined passage into maze fork');step('return')
  elif phase=='return':
   move(0,-1)
   if ps[0].get_actor_location().y<1000:
    pos=ps[0].get_actor_location();assert pos.y<1200 and 70<pos.z<160,('return path blocked',str(pos));move(0,0);state['checks'].append('same client walks back into original room');step('second')
  elif phase=='second':
   move(1,1)
   if ps[1].get_actor_location().y>3600:
    assert ps[1].get_actor_location().y>3450,('second client path blocked',str(ps[1].get_actor_location()));move(1,0)
    for w in worlds:
     players=ue.GameplayStatics.get_all_actors_of_class(w,C);assert sorted(p.player_state.player_id for p in players)==original
     assert 'L_ConnectedRoomMaze' in w.get_path_name()
    forbidden=('BP_PuzzleSetup_C','BP_StartPad_C','BP_RoundDirector_C','BP_HCGauntletCoordinator_C','BP_Altar_C')
    assert not [a for a in ue.GameplayStatics.get_all_actors_of_class(server,ue.Actor)if a.get_class().get_name()in forbidden]
    state['checks'].append('second joining client walks into maze; both players keep same world/roster; no puzzle actors active');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':str(report)}
