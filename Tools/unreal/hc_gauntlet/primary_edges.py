"""Primary native boundary checks, with transient fixture administration."""
import json,time,math,traceback
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
character=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
host_second=ue.GameplayStatics.create_player(server,-1,True) if ARGS.get('mode')=='host' else None
pc=host_second or next(p.get_controller() for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,character) if p.is_locally_controlled())
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_GauntletInputProbe').generated_class())
subsystem=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(pc,)))
action=ue.load_asset('/Game/Core/Input/IA_Interact')
report={'passed':False,'checks':[],'setup':'transient server fixture flags/spawns and GameMode bootstrap; requests use owning client Enhanced Input'}
state={'stage':0,'at':time.monotonic()+1,'deadline':time.monotonic()+65,'press':False,'duplicate':None}
def target(w,tag):
 actors=ue.GameplayStatics.get_all_actors_with_tag(w,tag);assert len(actors)==1,(tag,len(actors));return actors[0]
c=target(server,'HC_GauntletCoordinator')
def check(value,label):
 assert value,label
 report['checks'].append(label)
def rows():
 return [json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'] for w in worlds]
def unchanged():
 return all(r['index']==2 and r['phase']=='Cleared' for r in rows())
def stage(number,wait=.8):
 state['stage']=number;state['at']=time.monotonic()+wait
def place_start():
 pawn=pc.get_controlled_pawn();pid=pawn.player_state.get_editor_property('PlayerId')
 a=target(pc.get_world(),'HC_GauntletStart');loc=a.get_actor_location()
 for w in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(w,character):
   if p.player_state.get_editor_property('PlayerId')==pid:p.set_actor_location(loc+ue.Vector(-200,0,-12),False,True)
 look=a.get_actor_location()+ue.Vector(0,0,12)-pawn.get_editor_property('FollowCamera').get_world_location()
 pc.set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))
def spawn(path,tag=None):
 bridge=target(server,'HC_GauntletBridge')
 method='SpawnPrimaryCoordinator' if path.endswith('BP_HCGauntletCoordinator') else 'SpawnPrimaryBridge'
 actor=bridge.call_method(method);assert actor
 if tag:actor.set_editor_property('tags',[ue.Name(tag)])
 return actor
def finish(ok,error=None):
 state['press']=False;subsystem.inject_input_vector_for_action(action,ue.Vector(),[],[])
 report['passed']=ok
 if error:report['error']=error
 report['rounds']=rows()
 (HERE/'primary-boundaries.json').write_text(json.dumps(report,indent=2))
 ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Primary boundary deadline'
  if state['press']:subsystem.inject_input_vector_for_action(action,ue.Vector(1,0,0),[],[])
  if now<state['at']:return
  n=state['stage']
  if n==0:
   gm=ue.GameplayStatics.get_game_mode(server);gm.call_method('StartRound',args=(2,));gm.call_method('ClearRound')
   c.set_editor_property('AllowFixtureBridge',False);place_start();stage(1,1.2)
  elif n==1:
   check(not c.get_editor_property('DependencyReady'),'default production fixture prohibition disables startup readiness')
   state['press']=True;stage(2,.4)
  elif n==2:
   state['press']=False;subsystem.inject_input_vector_for_action(action,ue.Vector(),[],[])
   check(unchanged(),'actual client input cannot start with a forbidden fixture bridge')
   c.set_editor_property('AllowFixtureBridge',True)
   state['duplicate']=spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator')
   stage(3,1.2)
  elif n==3:
   check(not c.get_editor_property('SingletonValid'),'duplicate runtime coordinator is rejected')
   state['press']=True;stage(4,.4)
  elif n==4:
   state['press']=False;subsystem.inject_input_vector_for_action(action,ue.Vector(),[],[])
   check(unchanged(),'actual client input cannot start with ambiguous coordinator')
   state['duplicate'].destroy_actor();state['duplicate']=None;stage(45,.8)
  elif n==45:
   check(c.get_editor_property('SingletonValid') and c.get_editor_property('DependencyReady'),'pre-race startup readiness is valid')
   state['duplicate']=spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletGateBridge','HC_GauntletBridge')
   pid=pc.get_controlled_pawn().player_state.get_editor_property('PlayerId')
   serverpawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(server,character) if p.player_state.get_editor_property('PlayerId')==pid)
   target(server,'HC_GauntletStart').call_method('OnInteraction',args=(serverpawn,))
   check(unchanged() and not c.get_editor_property('DependencyReady'),'synchronous fixture start request revalidates a just-created bridge ambiguity before the polling timer can run')
   stage(5,1.2)
  elif n==5:
   check(not c.get_editor_property('DependencyReady'),'duplicate tagged gate bridges fail runtime resolution')
   state['press']=True;stage(6,.4)
  elif n==6:
   state['press']=False;subsystem.inject_input_vector_for_action(action,ue.Vector(),[],[])
   check(unchanged(),'actual client input cannot start with ambiguous bridge')
   state['duplicate'].destroy_actor();state['duplicate']=None;stage(7,1.2)
  elif n==7:
   check(c.get_editor_property('SingletonValid') and c.get_editor_property('DependencyReady'),'readiness recovers when fixture ambiguity is removed')
   state['press']=True;stage(8,.4)
  elif n==8:
   state['press']=False;subsystem.inject_input_vector_for_action(action,ue.Vector(),[],[]);stage(9,1)
  elif n==9:
   check(all(r['index']==3 and r['phase']=='Playing' for r in rows()),'same owning client input starts Round3 after valid fixture readiness is restored')
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
