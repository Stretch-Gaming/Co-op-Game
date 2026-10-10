import pathlib,json,time,traceback,unreal as ue
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in ws if ue.GameplayStatics.get_game_mode(w));client=next(w for w in ws if w!=server);old=next(p for p in ue.GameplayStatics.get_all_actors_of_class(client,C) if p.is_locally_controlled());old_pid=old.player_state.player_id;client_name=client.get_path_name()
report={'passed':False,'old_player_id':old_pid,'old_world_identity':str(client),'old_pawn_identity':str(old),'checks':[]};state={'stage':0,'at':time.monotonic()+1,'deadline':time.monotonic()+65,'pawn':None,'frames':0}
def target(w,t):return ue.GameplayStatics.get_all_actors_with_tag(w,t)[0]
def worlds():return list(ue.EditorLevelLibrary.get_pie_worlds(True))
def snap():
 return [{'world':w.get_path_name(),'completed':target(w,'Altar').get_editor_property('Completed'),'placed':str(target(w,'Altar').get_editor_property('PlacedKey')),'keys':[{'tag':t,'state':target(w,t).get_editor_property('CarryState'),'parent':str(target(w,t).get_attach_parent_actor()),'physics':target(w,t).static_mesh_component.is_simulating_physics(),'collision':str(target(w,t).static_mesh_component.get_collision_enabled())} for t in ['KeyA','KeyB']]} for w in worlds()]
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC6_Altar/BP_HC6InputProbe').generated_class())
def inject(v):
 p=state['pawn'];sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),)));sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/IA_Interact'),ue.Vector(v,0,0),[],[])
def aim():
 p=state['pawn'];a=target(p.get_world(),'KeyA');p.get_component_by_class(ue.SpringArmComponent).target_arm_length=0;p.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p.get_component_by_class(ue.CameraComponent).get_world_location(),a.get_actor_location()))
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 try:report['final']=snap()
 except:pass
 HERE.joinpath('fresh-client-latejoin.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Late-join test timeout'
  if now<state['at']:return
  st=state['stage']
  if st==0:
   report['before']=snap();ue.SystemLibrary.execute_console_command(client,'open 127.0.0.1:17792',old.get_controller());state.update(stage=1,at=now+5)
  elif st==1:
   players=[p for w in worlds() if w!=server for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled() and p.player_state and p != old and p.get_world().get_path_name()==client_name]
   if not players:state['at']=now+1;return
   p=players[0];state['pawn']=p;w=p.get_world();a=target(w,'Altar');k=a.get_editor_property('PlacedKey')
   assert a.get_editor_property('Completed') and k and k.get_attach_parent_actor()==a and k.get_editor_property('CarryState')==2
   assert not k.static_mesh_component.is_simulating_physics() and k.static_mesh_component.get_collision_enabled()==ue.CollisionEnabled.QUERY_AND_PHYSICS
   assert p!=old and w!=client
   report['new_world_identity']=str(w);report['new_pawn_identity']=str(p);report['new_player_id']=p.player_state.player_id;report['joined']=snap();report['checks'].append('fresh network client reconstructs completed altar, placed key, attachment, physics and collision')
   target(server,'Altar').call_method('ResetForRound',args=(2,3))
   for t in ['KeyA','KeyB','Wrong']:target(server,t).call_method('ResetForRound',args=(2,3))
   ue.GameplayStatics.get_game_mode(server).call_method('StartRound',args=(2,));state.update(stage=2,at=now+2)
  elif st==2:
   p=state['pawn'];loc=target(server,'KeyA').get_actor_location()
   for w in worlds():
    for q in ue.GameplayStatics.get_all_actors_of_class(w,C):
     q.set_actor_enable_collision(False)
     if q.player_state and q.player_state.player_id==p.player_state.player_id:q.set_actor_location(ue.Vector(loc.x-210,loc.y,92),False,True)
   aim();state.update(stage=3,at=now+1)
  elif st==3:
   aim()
   if state['frames']==0 and state['pawn'].get_editor_property('FocusedTarget')!=target(state['pawn'].get_world(),'KeyA'):return
   inject(1);state['frames']+=1
   if state['frames']>=4:state.update(stage=4,at=now+1)
  elif st==4:
   inject(0);state.update(stage=5,at=now+2)
  elif st==5:
   p=state['pawn'];pid=p.player_state.player_id
   for w in worlds():
    q=next(q for q in ue.GameplayStatics.get_all_actors_of_class(w,C) if q.player_state and q.player_state.player_id==pid)
    assert target(w,'KeyA').get_editor_property('CarryState')==1 and target(w,'KeyA').get_editor_property('Carrier')==q and comp(q).get_editor_property('CarriedItem')==target(w,'KeyA')
   report['checks'].append('new client uses native input to pick reset key');finish(True)
 except Exception:finish(False,traceback.format_exc())
def comp(p):return p.get_component_by_class(AC)
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'started':'fresh network join'}


