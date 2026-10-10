import json,time,traceback,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();locals=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()];p=locals[0];probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC5/BP_HC5InputProbe').generated_class());sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),)));action=ue.load_asset('/Game/Input/Actions/IA_Move');assert action
report={'passed':False,'input_path':'owning-client native IA_Move -> movement RPC/prediction -> ReceiveActorBeginOverlap -> TryEnter -> RequestStart -> GameMode.StartRound','checks':[]};state={'stage':0,'at':time.monotonic()+2,'held':False,'deadline':time.monotonic()+25}
def rows():return [json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'] for w in worlds]
def inject(v):sub.inject_input_vector_for_action(action,ue.Vector(0,v,0),[],[])
def finish(ok,error=None):
 inject(0);report['passed']=ok;report['final_states']=rows()
 if error:report['error']=error
 (HERE/'entrance-overlap.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def step(n,delay):state['stage']=n;state['at']=time.monotonic()+delay
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Overlap deadline'
  if state['held']:inject(1)
  if now<state['at']:return
  n=state['stage']
  if n==0:
   assert all(r['phase']=='Lobby' for r in rows());pid=p.player_state.get_editor_property('PlayerId')
   for w in worlds:
    for other in ue.GameplayStatics.get_all_actors_of_class(w,cls):
     if other.player_state.get_editor_property('PlayerId')==pid:
      other.set_actor_enable_collision(True);other.set_actor_location(ue.Vector(3300,0,100),False,True);other.get_component_by_class(ue.CharacterMovementComponent).stop_movement_immediately()
   p.get_controller().set_control_rotation(ue.Rotator(0,0,0));step(1,1)
  elif n==1:
   assert all(r['phase']=='Lobby' for r in rows());report['checks'].append({'outside_trigger_before_input':True});state['held']=True;step(2,.75)
  elif n==2:state['held']=False;inject(0);step(3,1)
  elif n==3:
   r=rows();assert all(x['index']==1 and x['phase']=='Playing' and x['attempt']==1 for x in r),r
   report['checks'].append({'native_movement_overlap_started_round_once':True,'client_position':str(p.get_actor_location())});step(4,1.5)
  elif n==4:assert all(x['attempt']==1 for x in rows());finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)

