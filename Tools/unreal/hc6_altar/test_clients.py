import pathlib,json,time,math,traceback,unreal as ue
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent;N=json.loads((ROOT/'Saved/HC6Altar/options.json').read_text(encoding='utf-8-sig'))['clients']
log_path=ROOT/'Saved/Logs/HC6Altar.log';log_offset=log_path.stat().st_size
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC6_Altar/BP_HC6InputProbe').generated_class())
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));gm=ue.GameplayStatics.get_game_mode(server)
locals=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.get_world().get_path_name());pids=[p.player_state.player_id for p in locals]
report={'clients':N,'passed':False,'input_path':'native IA_Interact/IA_Drop -> production RPC -> BPI_Interactable','checks':[],'snapshots':{}};focus_targets={}
state={'stage':0,'at':time.monotonic()+2,'held':[],'frames':0,'deadline':time.monotonic()+130}
def target(w,t):return ue.GameplayStatics.get_all_actors_with_tag(w,t)[0]
def owner(w,i=0):return next(p for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.player_state and p.player_state.player_id==pids[i])
def comp(p):return p.get_component_by_class(AC)
def inject(i,name,value):
 p=locals[i];s=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),)))
 s.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(value,0,0),[],[])
def aim(t,i=0):
 p=locals[i];dest=target(p.get_world(),t).get_actor_location()
 if t=='Altar':dest.z+=50
 p.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
def focus(t,i=0):
 focus_targets[i]=t
 a=target(server,t);loc=a.get_actor_location();loc.z=92
 for w in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(w,C):
   p.set_actor_enable_collision(False);p.character_movement.gravity_scale=0;p.character_movement.velocity=ue.Vector()
   if p.player_state and p.player_state.player_id==pids[i]:p.set_actor_location(ue.Vector(loc.x-210,loc.y+(i*30 if t=='Altar' else 0),loc.z),False,True)
 p=locals[i];arm=p.get_component_by_class(ue.SpringArmComponent);arm.target_arm_length=0
 dest=target(p.get_world(),t).get_actor_location()
 if t=='Altar':dest.z+=50
 p.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
def pulse(i=0,name='IA_Interact'):
 state['held']=[(i,name)];state['frames']=0
 def stop():
  for i,n in state['held']:inject(i,n,0)
  state['held']=[]
 return stop
def snapshot(label):
 rows=[]
 for w in worlds:
  altar=target(w,'Altar');gs=ue.GameplayStatics.get_game_state(w);r=gs.get_editor_property('RoundState')
  rows.append({'world':w.get_path_name(),'server':w==server,'round':r.export_text(),'completed':altar.get_editor_property('Completed'),'placed':str(altar.get_editor_property('PlacedKey')),'clear_calls':altar.get_editor_property('ClearCallCount'),'accept_count':altar.get_editor_property('AcceptCount'),'players':[{'id':p.player_state.player_id,'speed':p.character_movement.max_walk_speed,'crouch':p.character_movement.max_walk_speed_crouched,'carried':str(comp(p).get_editor_property('CarriedItem'))} for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.player_state],'items':[{'tag':t,'state':target(w,t).get_editor_property('CarryState'),'carrier':str(target(w,t).get_editor_property('Carrier')),'parent':str(target(w,t).get_attach_parent_actor()),'physics':target(w,t).static_mesh_component.is_simulating_physics(),'collision':str(target(w,t).static_mesh_component.get_collision_enabled()),'location':str(target(w,t).get_actor_location())} for t in ['KeyA','KeyB','Wrong']]})
 report['snapshots'][label]=rows
 return rows
def check_rejected(label):
 assert not target(server,'Altar').get_editor_property('Completed');assert target(server,'Altar').get_editor_property('ClearCallCount')==0
 report['checks'].append(label);snapshot(label)
def check_held(t,i=0):
 for w in worlds:
  a=target(w,t);p=owner(w,i)
  assert a.get_editor_property('CarryState')==1,(t,w,a.get_editor_property('CarryState'))
  assert a.get_editor_property('Carrier')==p and comp(p).get_editor_property('CarriedItem')==a
  assert abs(p.character_movement.max_walk_speed-300)<.01
 report['checks'].append('native heavy pickup '+t)
def check_placed(count=1):
 for w in worlds:
  altar=target(w,'Altar');assert altar.get_editor_property('Completed'),w
  key=altar.get_editor_property('PlacedKey');assert key and key.get_editor_property('CarryState')==2
  assert not key.get_editor_property('Carrier') and not key.static_mesh_component.is_simulating_physics()
  assert key.get_attach_parent_actor()==altar,(w,key.get_attach_parent_actor())
  assert key.static_mesh_component.get_collision_enabled()==ue.CollisionEnabled.QUERY_AND_PHYSICS
  assert (key.get_actor_location()-altar.get_editor_property('AltarSocket').get_world_location()).length()<.1
 assert target(server,'Altar').get_editor_property('ClearCallCount')==count
 assert target(server,'Altar').get_editor_property('AcceptCount')==count
 report['checks'].append('replicated placement and exactly once clear '+str(count));snapshot('placed'+str(count))
def check_cleanup():
 for w in worlds:
  p=owner(w);assert comp(p).get_editor_property('CarriedItem') is None
  assert abs(p.character_movement.max_walk_speed-600)<.01 and abs(p.character_movement.max_walk_speed_crouched-300)<.01
 report['checks'].append('server and owning peers clear slot and restore heavy speed')
def reset():
 target(server,'Altar').call_method('ResetForRound',args=(2,2))
 for t in ['KeyA','KeyB','Wrong']:target(server,t).call_method('ResetForRound',args=(2,2))
 gm.call_method('StartRound',args=(2,))
def check_reset():
 for w in worlds:
  assert not target(w,'Altar').get_editor_property('Completed') and target(w,'Altar').get_editor_property('PlacedKey') is None
  for t in ['KeyA','KeyB','Wrong']:
   a=target(w,t);assert a.get_editor_property('CarryState')==0 and not a.get_attach_parent_actor() and a.static_mesh_component.is_simulating_physics()
 report['checks'].append('existing BPI_RoundReset resets altar and key; order idempotent');snapshot('reset')
stop=lambda:None
steps=[]
def add(fn,delay=1):steps.append((fn,delay))
add(lambda:gm.call_method('StartRound',args=(1,)));add(lambda:focus('Altar'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_rejected('wrong round rejects'))
add(lambda:gm.call_method('StartRound',args=(2,)));add(lambda:focus('Altar'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_rejected('empty hands rejects'))
add(lambda:focus('Wrong'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_held('Wrong'));add(lambda:focus('Altar'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_rejected('wrong heavy statue rejects'));add(lambda:pulse(name='IA_Drop'));add(lambda:state.update(held=[]) or inject(0,'IA_Drop',0))
add(lambda:target(server,'Wrong').set_actor_location(ue.Vector(0,1100,65),False,True),2)
add(lambda:focus('KeyA'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_held('KeyA'));add(lambda:focus('Altar'));add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_placed());add(check_cleanup)
add(lambda:pulse());add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_placed())
add(reset,2);add(check_reset)
add(lambda:focus('KeyA',0));add(lambda:pulse(0));add(lambda:state.update(held=[]) or inject(0,'IA_Interact',0));add(lambda:check_held('KeyA',0));add(lambda:focus('KeyB',1));add(lambda:pulse(1));add(lambda:state.update(held=[]) or inject(1,'IA_Interact',0));add(lambda:check_held('KeyB',1));add(lambda:focus('Altar',0));add(lambda:focus('Altar',1));add(lambda:state.update(held=[(0,'IA_Interact'),(1,'IA_Interact')],frames=0));add(lambda:state.update(held=[]) or (inject(0,'IA_Interact',0),inject(1,'IA_Interact',0)));add(lambda:check_placed(2))
def finish(ok,error=None):
 report['passed']=ok
 log_interval=log_path.read_bytes()[log_offset:].decode('utf-8',errors='replace')
 report['log_errors']=[line for line in log_interval.splitlines() if any(t in line for t in ['Blueprint Runtime Error','Accessed None',': Error:'])]
 report['log_start_offset']=log_offset
 HERE.joinpath('clients-'+str(N)+'-runtime.log').write_text(log_interval)
 if error:report['error']=error
 try:snapshot('final')
 except:pass
 HERE.joinpath('clients-'+str(N)+'.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Input matrix timeout'
  for i,n in state['held']:
   if n=='IA_Interact':
    aim(focus_targets[i],i)
    t=focus_targets[i]
    needs_focus=t!='Altar' or target(locals[i].get_world(),'Altar').call_method('IsRoundActive')
    if state['frames']==0 and needs_focus and locals[i].get_editor_property('FocusedTarget')!=target(locals[i].get_world(),t):return
   inject(i,n,1)
  if state['held']:state['frames']+=1
  if now<state['at'] or state['held'] and state['frames']<3:return
  if state['stage']==len(steps):finish(True);return
  fn,delay=steps[state['stage']]
  try:fn()
  except AssertionError:
   if state.get('retry_stage')!=state['stage']:state.update(retry_stage=state['stage'],retry_deadline=now+8)
   if now<state['retry_deadline']:state['at']=now+.4;return
   raise
  state['stage']+=1;state['at']=now+delay
 except Exception:finish(False,traceback.format_exc())
assert len(locals)==N and len(worlds)==N+1,(len(locals),len(worlds))
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'started':N,'steps':len(steps)}







