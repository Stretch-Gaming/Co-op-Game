"""Native second-local-host altar check; CreatePlayer is fixture setup only."""
import pathlib,json,time,traceback,unreal as ue
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent;C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in ws if ue.GameplayStatics.get_game_mode(w));pc=ue.GameplayStatics.create_player(server,-1,True);assert pc
report={'passed':False,'native_fixture_CreatePlayer_only':True,'checks':[]};state={'stage':0,'at':time.monotonic()+2,'deadline':time.monotonic()+50,'frames':0,'pawn':None,'held':False}
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC6_Altar/BP_HC6InputProbe').generated_class());log_path=ROOT/'Saved/Logs/HC6Altar.log';offset=log_path.stat().st_size

def target(w,t):return ue.GameplayStatics.get_all_actors_with_tag(w,t)[0]
def inject(v):
 p=state['pawn'];sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),)));sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/IA_Interact'),ue.Vector(v,0,0),[],[])
def focus(t):
 state['focus']=t;p=state['pawn'];loc=target(server,t).get_actor_location()
 for w in ws:
  for q in ue.GameplayStatics.get_all_actors_of_class(w,C):
   q.set_actor_enable_collision(False);q.character_movement.gravity_scale=0;q.character_movement.velocity=ue.Vector()
   if q.player_state and q.player_state.player_id==p.player_state.player_id:q.set_actor_location(ue.Vector(loc.x-210,loc.y,92),False,True)
 p.get_component_by_class(ue.SpringArmComponent).target_arm_length=0

def aim():
 p=state['pawn'];dest=target(p.get_world(),state['focus']).get_actor_location()
 if state['focus']=='Altar':dest.z+=50
 p.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 log=log_path.read_bytes()[offset:].decode('utf-8',errors='replace');report['log_errors']=[l for l in log.splitlines() if any(t in l for t in ['Blueprint Runtime Error','Accessed None',': Error:'])];HERE.joinpath('host-split-runtime.log').write_text(log);HERE.joinpath('host-split.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Second-local-owner timeout'
  if now<state['at']:return
  st=state['stage']
  if st==0:
   p=pc.get_pawn()
   if not p or not p.player_state:return
   assert not pc.is_primary_player() and p.is_locally_controlled() and p.get_world()==server
   assert len([p for p in ue.GameplayStatics.get_all_actors_of_class(server,C) if p.is_locally_controlled()])==2
   assert len(ue.GameplayStatics.get_all_actors_of_class(server,C))==4
   state['pawn']=p;ue.GameplayStatics.get_game_mode(server).call_method('StartRound',args=(2,));focus('KeyA');state.update(stage=1,at=now+1)
  elif st in [1,4]:
   aim()
   if state['frames']==0 and state['pawn'].get_editor_property('FocusedTarget')!=target(server,state['focus']):return
   inject(1);state['frames']+=1
   if state['frames']>=4:inject(0);state.update(stage=st+1,at=now+2,frames=0)
  elif st==2:
   p=state['pawn'];a=target(server,'KeyA');assert p.call_method('GetCarried')==a and a.get_editor_property('Carrier')==p and abs(p.character_movement.max_walk_speed-300)<.01
   report['checks'].append('second local host owns native heavy-key pickup');focus('Altar');state.update(stage=3,at=now+1)
  elif st==3:aim();state.update(stage=4,at=now+.3)
  elif st==5:
   p=state['pawn'];assert p.call_method('GetCarried') is None and abs(p.character_movement.max_walk_speed-600)<.01
   for w in ws:
    a=target(w,'Altar');k=target(w,'KeyA');assert a.get_editor_property('Completed') and a.get_editor_property('PlacedKey')==k and k.get_attach_parent_actor()==a and k.get_editor_property('CarryState')==2 and not k.static_mesh_component.is_simulating_physics()
   assert target(server,'Altar').get_editor_property('ClearCallCount')==1
   report['checks'].append('second local host places/clears once and restores carrying speed across two remote clients');report['second_local_player_id']=p.player_state.player_id;finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'started':'second local host + two remote clients'}
