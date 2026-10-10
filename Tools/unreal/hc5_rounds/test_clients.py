"""Native owning-client IA_Interact fixture path; no direct Python RPC invocation."""
import json,time,math,traceback,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
N=ARGS['clients'];report={'passed':False,'clients':N,'checks':[],'input_path':'native IA_Interact -> existing reliable character RPC -> HC5 fixture -> production round actors','health_or_death_recovery_tested':False}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();locals=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC5/BP_HC5InputProbe').generated_class());subsystems={p.get_controller():ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),))) for p in locals};action=ue.load_asset('/Game/Core/Input/IA_Interact')
state={'held':[],'at':time.monotonic()+2,'deadline':time.monotonic()+140,'step':0};queue=[]
def target(w,name):return ue.GameplayStatics.get_all_actors_with_tag(w,'HC5_'+name)[0]
def rows():return [json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'] for w in worlds]
def check(index,phase,attempt,label):
 r=rows();assert all(x['index']==index and x['phase']==phase and x['attempt']==attempt and x['scalingRow']==str(N) for x in r),r
 report['checks'].append({'name':label,'states':r})
def inject(p,v,act=action):subsystems[p.get_controller()].inject_input_vector_for_action(act,ue.Vector(float(v),0,0),[],[])
def focus(p,name,offset=0):
 a=target(p.get_world(),name);pid=p.player_state.get_editor_property('PlayerId')
 for w in worlds:
  for other in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   other.set_actor_enable_collision(False)
   if other.player_state.get_editor_property('PlayerId')==pid:other.set_actor_location(a.get_actor_location()+ue.Vector(-230,offset,-12),False,True)
 look=a.get_actor_location()+ue.Vector(0,0,12)-p.get_editor_property('FollowCamera').get_world_location();p.get_controller().set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))
def add(fn,delay=1):queue.append((fn,delay))
def release():
 for p in state['held']:inject(p,0)
 state['held']=[]
def command(name,result,players=None):
 players=players or locals[:1]
 def aim():
  for i,p in enumerate(players):focus(p,name,(i-.5)*40)
 def start():
  assert all(p.get_editor_property('FocusedTarget')==target(p.get_world(),name) for p in players),[(str(p.get_editor_property('FocusedTarget')),name) for p in players]
  state['held']=players
 add(aim,1.2);add(start,.3);add(release,.8);add(result,.2)
def initial():
 assert len(worlds)==N+1 and len(locals)==N,(len(worlds),len(locals))
 check(0,'Lobby',0,'lobby roster scaling')
 assert target(server,'Director').get_editor_property('CurrentCheckpoint')==target(server,'Checkpoint0')
 for p in locals:target(p.get_world(),'Entrance1').call_method('TryEnter',args=(p,))
 check(0,'Lobby',0,'client-local entrance invocation cannot mutate server')
add(initial,.2)
command('Enter2',lambda:check(0,'Lobby',0,'skip from lobby rejected'))
command('Enter1',lambda:check(1,'Playing',1,'two competing client entrances start round once'),locals[:2])
command('Enter1',lambda:check(1,'Playing',1,'duplicate entrance keeps Attempt'))
command('Clear',lambda:check(1,'Cleared',1,'native client fixture clears through GameMode'))
command('Enter3',lambda:check(1,'Cleared',1,'skipped next round rejected'))
command('Enter2',lambda:check(2,'Playing',1,'next round selects matching checkpoint'))
def failed():
 check(2,'Failed',1,'competing failure requests preserve Attempt until timer')
 d=target(server,'Director');assert d.get_editor_property('RetryPending') and d.get_editor_property('RetryIndex')==2 and d.get_editor_property('RetryAttempt')==1
command('Fail',failed,locals[:2]);add(lambda:None,3.5)
def retry():
 check(2,'Playing',2,'one timed retry increments Attempt once')
 d=target(server,'Director');assert not d.get_editor_property('RetryPending') and d.get_editor_property('CurrentCheckpoint')==target(server,'Checkpoint2')
 for w in worlds:
  for name in ['Enter1','Enter2','Enter3','Clear','Fail']:
   a=target(w,name);assert a.get_editor_property('ResetCount')==1 and a.get_editor_property('LastResetIndex')==2 and a.get_editor_property('LastResetAttempt')==2
 positions=[]
 for ps in ue.GameplayStatics.get_game_state(server).player_array:
  p=ps.get_pawn();slot=ps.get_editor_property('ColorSlot');expected=target(server,'Checkpoint2').call_method('GetSpawnTransform',args=(slot,)).translation;actual=p.get_actor_location();assert (actual-expected).length()<30,(actual,expected)
  positions.append((actual.x,actual.y,actual.z))
 assert len(set(positions))==N,positions
 report['checks'].append({'distinct_checkpoint_spots':N,'server_reset_and_replication':True,'positions':positions})
add(retry,3.5);add(lambda:check(2,'Playing',2,'timer cannot repeat'),.2)
command('Enter3',lambda:check(2,'Playing',2,'advance while playing rejected'))
command('Clear',lambda:check(2,'Cleared',2,'round two clear'))
command('Enter3',lambda:check(3,'Playing',1,'round three progression'))
command('Clear',lambda:check(3,'Cleared',1,'round three clear'))
command('Enter1',lambda:check(3,'Cleared',1,'return to earlier round rejected'))
def finish(ok,error=None):
 release();report['passed']=ok
 if error:report['error']=error
 report['final_states']=rows();(HERE/f'clients-{N}.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Acceptance deadline exceeded'
  for p in state['held']:inject(p,1)
  if now<state['at']:return
  if state['step']==len(queue):finish(True);return
  fn,delay=queue[state['step']];state['step']+=1;fn();state['at']=now+delay
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
