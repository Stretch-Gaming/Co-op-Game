"""Native owning Enhanced Input -> HC client RPC -> real PG lever/gate -> HC objective.

Python positioning, bootstrap and restart are labeled fixtures. The positive
crossover uses actual IA_Move through the real gate with collision enabled.
Latch completion uses an explicit fixture bridge; it is not PG latch acceptance.
"""
import json,time,math,traceback,re
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_GauntletInputProbe').generated_class())
interact=ue.load_asset('/Game/Core/Input/IA_Interact')
move=ue.load_asset('/Game/Input/Actions/IA_Move');assert move
state={'stage':0,'at':time.monotonic()+2,'held':[],'moving':None,'deadline':time.monotonic()+180}
report={'passed':False,'mode':ARGS.get('mode','clients'),'checks':[],'input_path':'owning EnhancedInputLocalPlayerSubsystem action injection -> inherited character events -> reliable character server RPC','fixture_setup':'Python positions/bootstrap/restart; native create_player only for host second owner','latch':'explicit fixture simulation; actual PG gate closure recorded separately'}
subsystems={};owners=[];holders=[];crossing=None;count=0
def target(world,tag):
 a=ue.GameplayStatics.get_all_actors_with_tag(world,tag);assert len(a)==1,(tag,len(a));return a[0]
def coordinator(world=server):return target(world,'HC_GauntletCoordinator')
def snapshot():
 return [{'world':w.get_path_name(),'round':json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'],'attempt':coordinator(w).get_editor_property('CurrentAttempt'),'crossed':len(coordinator(w).get_editor_property('CrossedPawns')),'completed':coordinator(w).get_editor_property('Completed'),'count':coordinator(w).get_editor_property('CompletionCount'),'gate_open':target(w,'HC_GauntletGate').get_editor_property('bOpen'),'latched':target(w,'HC_GauntletBridge').get_editor_property('Latched')} for w in worlds]
def resolve(pc):
 if pc not in subsystems:
  obj=probe.call_method('ResolveInput',args=(pc,));subsystems[pc]=ue.EnhancedInputLocalPlayerSubsystem.cast(obj);assert subsystems[pc],pc
 return subsystems[pc]
def inject(pc,action,value):resolve(pc).inject_input_vector_for_action(action,value,[],[])
def place(pc,location):
 pawn=pc.get_controlled_pawn();pid=pawn.player_state.get_editor_property('PlayerId')
 for w in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   if p.player_state and p.player_state.get_editor_property('PlayerId')==pid:
    p.set_actor_enable_collision(True);p.set_actor_location(ue.Vector(*location),False,True)
 pc.set_control_rotation(ue.Rotator(pitch=0,yaw=0))
def aim(pc,tag):
 a=target(pc.get_world(),tag);p=pc.get_controlled_pawn();camera=p.get_editor_property('FollowCamera')
 aimpoint=a.get_actor_location()+ue.Vector(0,0,12)
 look=aimpoint-camera.get_world_location()
 pc.set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))
def focus(pc,tag):
 loc=target(pc.get_world(),tag).get_actor_location()
 place(pc,(loc.x-200,loc.y,max(100,loc.z-12)))
 aim(pc,tag)
def hold(pc):
 if pc not in state['held']:state['held'].append(pc)
def release(pc=None):
 for p in list(state['held']):
  if pc is None or pc==p:inject(p,interact,ue.Vector());state['held'].remove(p)
def step(number,delay=.8):state['stage']=number;state['at']=time.monotonic()+delay
def phase(expected):
 rows=snapshot();assert all(r['round']['index']==3 and r['round']['phase']==expected for r in rows),rows;return rows
def check(value,label):assert value,label;report['checks'].append(label)
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 try:report['snapshot']=snapshot()
 except Exception:pass
 release()
 if state['moving']:inject(state['moving'],move,ue.Vector())
 (HERE/ARGS['output']).write_text(json.dumps(report,indent=2))
 ue.unregister_slate_post_tick_callback(handle)
 ue.log('HC_GAUNTLET_INPUT_RESULT: '+str(ok))
def tick(dt):
 global owners,holders,crossing,count,worlds
 try:
  now=time.monotonic();assert now<state['deadline'],'Gauntlet input deadline'
  for pc in state['held']:inject(pc,interact,ue.Vector(1,0,0))
  if state['moving']:inject(state['moving'],move,ue.Vector(0,1,0))
  if now<state['at']:return
  stage=state['stage']
  if stage==0:
   if ARGS.get('mode')=='host':
    host=next(p.get_controller() for p in ue.GameplayStatics.get_all_actors_of_class(server,cls) if p.is_locally_controlled())
    second=ue.GameplayStatics.create_player(server,-1,True);assert second and second!=host
   step(1,2)
  elif stage==1:
   owners=[p.get_controller() for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
   count=ue.GameplayStatics.get_game_state(server).call_method('GetPlayerCount')
   assert count in (2,3,4) and len(owners)==count,(count,len(owners))
   for pc in owners:resolve(pc)
   assert len(set(subsystems.values()))==count
   if ARGS.get('mode')=='host':
    pair=[pc for pc in owners if pc.get_world()==server]
    check(len(pair)==2 and subsystems[pair[0]]!=subsystems[pair[1]],'host two local owners share world and have distinct owning input subsystems')
    owners=pair+[pc for pc in owners if pc.get_world()!=server]
   report['players']=count
   holders=owners[:(2 if count==4 else 1)];crossing=owners[-1]
   gm=ue.GameplayStatics.get_game_mode(server)
   gm.call_method('StartRound',args=(2,));gm.call_method('ClearRound')
   focus(owners[0],'HC_GauntletStart');step(2,1.5)
  elif stage==2:
   check(owners[0].get_controlled_pawn().get_editor_property('FocusedTarget')==target(owners[0].get_world(),'HC_GauntletStart'),'owned start prompt resolves through live interaction validation')
   hold(owners[0]);step(3,.4)
  elif stage==3:
   release();step(4,1)
  elif stage==4:
   phase('Playing')
   check(all(str(ue.GameplayStatics.get_game_state(w).call_method('GetScalingRow'))==str(count) for w in worlds),'start input requested Round3 with locked scaling row for actual roster')
   focus(crossing,'HC_GauntletObjective');step(5,1)
  elif stage==5:
   check(not coordinator().get_editor_property('CrossedPawns'),'far-side fixture teleport has no server entry/crossover token')
   check(crossing.get_controlled_pawn().get_editor_property('FocusedTarget')!=target(crossing.get_world(),'HC_GauntletObjective'),'bypassing crossing cannot focus far-side objective')
   hold(crossing);step(6,.3)
  elif stage==6:
   release();phase('Playing')
   for i,pc in enumerate(holders):focus(pc,'HC_GauntletLever'+str(i+1))
   place(crossing,(300,0,100));step(7,1)
  elif stage==7:
   check(all(pc.get_controlled_pawn().get_editor_property('FocusedTarget')==target(pc.get_world(),'HC_GauntletLever'+str(i+1)) for i,pc in enumerate(holders)),'real PG levers focused by each owning player')
   hold(holders[0]);step(8,1.8)
  elif stage==8:
   gate=target(server,'HC_GauntletGate')
   check(gate.call_method('GetLeverCount')==(2 if count==4 else 1),'real PG lever requirement is one at2/3 and two at4')
   if count==4:
    check(not gate.get_editor_property('bOpen'),'four-player real gate stays closed with one holder')
    hold(holders[1])
   step(9,2)
  elif stage==9:
   check(all(target(w,'HC_GauntletGate').get_editor_property('bOpen') for w in worlds),'real PG gate open state replicates after required native input holds')
   place(crossing,(700,0,100));release(holders[0]);step(10,.7)
  elif stage==10:
   gate=target(server,'HC_GauntletGate')
   check(gate.call_method('SomeoneUnder') and gate.get_editor_property('bOpen'),'real PG safety overlap holds raised gate after lever release')
   place(crossing,(300,0,100));step(11,1.5)
  elif stage==11:
   gate=target(server,'HC_GauntletGate')
   check(not gate.call_method('SomeoneUnder') and not gate.get_editor_property('bOpen'),'real PG gate closes on release once pawn clears safety volume')
   hold(holders[0]);step(12,2)
  elif stage==12:
   check(coordinator().get_editor_property('EnteredPawns') and target(server,'HC_GauntletGate').get_editor_property('bOpen'),'server entry token recorded within local route bounds while real gate reopens')
   state['moving']=crossing;state['move_start']=crossing.get_controlled_pawn().get_actor_location().x
   step(13,.1)
  elif stage==13:
   x=crossing.get_controlled_pawn().get_actor_location().x
   if x<1500:step(13,.1);return
   inject(crossing,move,ue.Vector());state['moving']=None
   check(x-state['move_start']>1000,'positive crossover used actual IA_Move with collision enabled through open real PG gate')
   aim(crossing,'HC_GauntletObjective');step(14,1)
  elif stage==14:
   pid=crossing.get_controlled_pawn().player_state.get_editor_property('PlayerId')
   token_ids=[[p.player_state.get_editor_property('PlayerId') for p in coordinator(w).get_editor_property('CrossedPawns')] for w in worlds]
   check(all(ids==[pid] for ids in token_ids),'only the actual crossing pawn receives the replicated crossover token; holders remain untokened')
   report['crossing_token_player_ids']=token_ids
   check(crossing.get_controlled_pawn().get_editor_property('FocusedTarget')==target(crossing.get_world(),'HC_GauntletObjective'),'eligible far-side objective focuses after actual traversal')
   hold(crossing);step(15,.4)
  elif stage==15:
   release();step(16,1.5)
  elif stage==16:
   rows=phase('Cleared')
   check(all(r['completed'] and r['count']==1 and r['latched'] for r in rows),'owned objective input completes matching Round3 attempt once after fixture latch acknowledgement')
   check(all(not r['gate_open'] for r in rows),'unmodified real PG gate closes after Core cancels holders; fixture latch is not production persistent latch')
   hold(crossing);step(17,.3)
  elif stage==17:
   release();check(all(coordinator(w).get_editor_property('CompletionCount')==1 for w in worlds),'duplicate far-side input cannot clear matching attempt twice')
   if ARGS.get('reconnect'):
    oldpc=next(pc for pc in holders if pc.get_world()!=server)
    state['old_client']=oldpc.get_world();state['old_pc']=oldpc;state['prior_worlds']=list(worlds)
    port=int(re.findall(r'IpNetDriver listening on port (\d+)',(ROOT/'Saved/Logs/HC-Gauntlet-session2.log').read_text(errors='replace'))[-1])
    assert 1024<=port<=65535
    ue.SystemLibrary.execute_console_command(oldpc.get_world(),'open 127.0.0.1:'+str(port),oldpc)
    step(170,3);return
   step(171,.1)
  elif stage==170:
   worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
   fresh=[w for w in worlds if w not in state['prior_worlds'] and ue.GameplayStatics.get_game_state(w)]
   if not fresh:step(170,.3);return
   new=fresh[0];pcs=[p.get_controller() for p in ue.GameplayStatics.get_all_actors_of_class(new,cls) if p.is_locally_controlled() and p.get_editor_property('InputReady')]
   if not pcs:step(170,.3);return
   freshpc=pcs[0];gs=ue.GameplayStatics.get_game_state(new)
   if gs.call_method('GetPlayerCount')!=count:step(170,.3);return
   row=next(r for r in snapshot() if r['world']==new.get_path_name())
   check(row['round']['phase']=='Cleared' and row['attempt']==1 and row['completed'] and row['count']==1 and row['latched'],'distinct fresh client world receives current completed attempt and fixture latch snapshot on late join')
   oldpc=state['old_pc'];owners=[freshpc if pc==oldpc else pc for pc in owners];holders=[freshpc if pc==oldpc else pc for pc in holders]
   resolve(freshpc);state['fresh_pc']=freshpc
   check(freshpc.get_controlled_pawn().get_editor_property('PromptWidget').get_owning_player()==freshpc,'fresh late-join pawn restores owning prompt and Enhanced Input subsystem')
   step(171,.1)
  elif stage==171:
   gm=ue.GameplayStatics.get_game_mode(server)
   gm.call_method('FailRound');gm.call_method('StartRound',args=(3,));step(18,1.5)
  elif stage==18:
   rows=phase('Playing')
   check(all(r['attempt']==2 and r['crossed']==0 and not r['completed'] and not r['latched'] for r in rows),'interruption/restart observed by polling resets stale token and fixture latch without dispatcher binding')
   pid=crossing.get_controlled_pawn().player_state.get_editor_property('PlayerId')
   serverpawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(server,cls) if p.player_state.get_editor_property('PlayerId')==pid)
   check(not coordinator().call_method('HasProgress',args=(serverpawn,)),'server-world pawn at stale far-side position cannot reuse prior attempt token')
   for i,pc in enumerate(holders):focus(pc,'HC_GauntletLever'+str(i+1))
   place(crossing,(300,0,100));step(19,1)
  elif stage==19:
   for pc in holders:hold(pc)
   step(20,2)
  elif stage==20:
   lever=target(server,'HC_GauntletLever1')
   check(lever.get_editor_property('bActive'),'owning input works on the next attempt, including fresh owner after reconnect when requested')
   state['moving']=crossing;step(21,.1)
  elif stage==21:
   if crossing.get_controlled_pawn().get_actor_location().x<1100:step(21,.1);return
   inject(crossing,move,ue.Vector());state['moving']=None;step(22,.5)
  elif stage==22:
   pid=crossing.get_controlled_pawn().player_state.get_editor_property('PlayerId')
   serverpawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(server,cls) if p.player_state.get_editor_property('PlayerId')==pid)
   check(coordinator().get_editor_property('CrossedPawns')==[serverpawn],'second actual input traversal creates observable current-attempt progress before interface reset')
   bridge=target(server,'HC_GauntletBridge')
   check(bridge.call_method('RequestLatch',args=(3,2)) and bridge.call_method('QueryLatch',args=(3,2)),'labeled fixture latch setup acknowledges exact current attempt before explicit interface reset')
   step(220,.8)
  elif stage==220:
   check(all(target(w,'HC_GauntletBridge').get_editor_property('Latched') for w in worlds),'fixture latch pre-reset state replicates to every client')
   lever=target(server,'HC_GauntletLever1')
   check(lever.get_editor_property('bActive'),'real PG holder remains active immediately before interface reset fixture call')
   reset=ue.load_asset('/Game/Core/BPI_RoundReset').generated_class()
   for tag in ['HC_GauntletCoordinator','HC_GauntletGate','HC_GauntletLever1','HC_GauntletLever2','HC_GauntletBridge']:
    actor=target(server,tag);assert ue.SystemLibrary.does_implement_interface(actor,reset)
    probe.call_method('DispatchFixtureReset',args=(actor,3,2))
   check(not coordinator().get_editor_property('CrossedPawns') and not lever.get_editor_property('bActive'),'actual BPI_RoundReset message dispatch clears owned tokens and unmodified PG holder through labeled fixture caller')
   release();step(23,1)
  elif stage==23:
   rows=snapshot()
   check(all(r['crossed']==0 and not r['gate_open'] and not r['latched'] for r in rows) and all(not target(w,'HC_GauntletLever1').get_editor_property('bActive') for w in worlds),'actual interface reset token/holder/gate and fixture unlatch results replicate to every client')
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
