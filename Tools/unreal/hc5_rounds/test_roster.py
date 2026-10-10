"""Native local split-player removal fixture; actual production director handles restart."""
import json,time,math,traceback,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
N=ARGS['players'];report={'passed':False,'players':N,'checks':[],'roster_setup':'native GameplayStatics.create_player/remove_player','input_path':'owning IA_Interact -> production character RPC -> fixture entrance','death_or_health_tested':False}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();extra=ue.GameplayStatics.create_player(server,-1,True);assert extra
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC5/BP_HC5InputProbe').generated_class());action=ue.load_asset('/Game/Core/Input/IA_Interact');state={'stage':0,'at':time.monotonic()+3,'held':False,'deadline':time.monotonic()+60};host=None;sub=None

def target(w,name):return ue.GameplayStatics.get_all_actors_with_tag(w,'HC5_'+name)[0]
def snapshot():
 return [{'count':ue.GameplayStatics.get_game_state(w).call_method('GetPlayerCount'),'state':json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState']} for w in worlds]
def check(count,phase,attempt,row,label):
 r=snapshot();assert all(x['count']==count and x['state']['index']==1 and x['state']['phase']==phase and x['state']['attempt']==attempt and x['state']['scalingRow']==str(row) for x in r),r
 report['checks'].append({'name':label,'worlds':r})
def inject(v):sub.inject_input_vector_for_action(action,ue.Vector(v,0,0),[],[])
def step(n,delay):state['stage']=n;state['at']=time.monotonic()+delay

def finish(ok,error=None):
 if sub:inject(0)
 report['passed']=ok
 if error:report['error']=error
 report['final']=snapshot();(HERE/f'roster-{N}.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 global host,sub
 try:
  now=time.monotonic();assert now<state['deadline'],'Roster deadline exceeded'
  if state['held']:inject(1)
  if now<state['at']:return
  n=state['stage']
  if n==0:
   assert all(r['count']==N for r in snapshot()),snapshot()
   host=next(p for p in ue.GameplayStatics.get_all_actors_of_class(server,cls) if p.is_locally_controlled() and p.get_controller()!=extra);sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(host.get_controller(),)));assert sub
   a=target(server,'Enter1')
   for p in ue.GameplayStatics.get_all_actors_of_class(server,cls):p.set_actor_enable_collision(False)
   host.set_actor_location(a.get_actor_location()+ue.Vector(-230,0,-12),False,True);look=a.get_actor_location()+ue.Vector(0,0,12)-host.get_editor_property('FollowCamera').get_world_location();host.get_controller().set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=0));step(1,1.2)
  elif n==1:
   assert host.get_editor_property('FocusedTarget')==target(server,'Enter1');state['held']=True;step(2,.3)
  elif n==2:state['held']=False;inject(0);step(3,.7)
  elif n==3:
   check(N,'Playing',1,N,'start with split player in frozen scaling');ue.GameplayStatics.remove_player(extra,True);step(4,.8)
  elif n==4:
   check(N-1,'Failed',1,N,'native local-player departure fails once');assert target(server,'Director').get_editor_property('RetryPending');step(5,3.5)
  elif n==5:
   check(N-1,'Playing',2,max(2,N-1),'retry samples fresh roster scaling')
   for w in worlds:
    a=target(w,'Enter1');assert a.get_editor_property('ResetCount')==1 and a.get_editor_property('LastResetAttempt')==2
   pts=[p.get_pawn().get_actor_location() for p in ue.GameplayStatics.get_game_state(server).player_array];assert len({(p.x,p.y,p.z) for p in pts})==N-1
   report['checks'].append({'remaining_spawn_spots':N-1,'one_reset':True});step(6,3.5)
  elif n==6:check(N-1,'Playing',2,max(2,N-1),'departure retry cannot repeat');finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
