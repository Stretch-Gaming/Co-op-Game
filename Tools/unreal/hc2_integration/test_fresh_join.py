"""Fresh client-world reconnect after actual client collection."""
import unreal as ue,json,time,math,traceback,re
PORT=int(re.findall(r'IpNetDriver listening on port (\d+)',(ROOT/'Saved/Logs/HC2-ui.log').read_text(errors='replace'))[-1]);assert 1024<=PORT<=65535
if 'port' in ARGS:assert ARGS['port']==PORT,'Stale port; do not connect to another session'
report={'passed':False,'checks':[],'fixture_travel':'client console open 127.0.0.1:'+str(PORT),'input_path':'owning Enhanced Input -> character server RPC'}
state={'stage':0,'at':time.monotonic()+2,'held':False,'deadline':time.monotonic()+90}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));oldclient=next(w for w in worlds if not ue.GameplayStatics.get_game_mode(w))
cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
pawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(oldclient,cls) if p.is_locally_controlled())
action=ue.load_asset('/Game/Core/Input/IA_Interact')

def inject(value):
 sub=next(s for s in ue.ObjectIterator(ue.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in s.get_path_name() and s.get_world()==pawn.get_world())
 sub.inject_input_vector_for_action(action,ue.Vector(float(value),0,0),[],[])
def target(w,name):return ue.GameplayStatics.get_all_actors_with_tag(w,'HC2_'+name)[0]
def focus(name):
 a=target(pawn.get_world(),name);pid=pawn.player_state.get_editor_property('PlayerId')
 for w in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   p.set_actor_enable_collision(False)
   if p.player_state.get_editor_property('PlayerId')==pid:p.set_actor_location(a.get_actor_location()+ue.Vector(-230,0,-12),False,True)
 look=a.get_actor_location()+ue.Vector(0,0,12)-pawn.get_editor_property('FollowCamera').get_world_location()
 pawn.get_controller().set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))
def step(n,delay):state['stage']=n;state['at']=time.monotonic()+delay

def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 (HERE/'fresh-client-latejoin.json').write_text(json.dumps(report,indent=2))
 ue.unregister_slate_post_tick_callback(handle);ue.log('HC2_FRESH_CLIENT_LATEJOIN: '+str(ok))
def tick(dt):
 global pawn,worlds
 try:
  now=time.monotonic();assert now<state['deadline'],'Fresh-world reconnect timed out'
  if state['held']:inject(1)
  if now<state['at']:return
  s=state['stage']
  if s==0:
   assert all(ue.GameplayStatics.get_game_state(w).get_editor_property('RelicsCollected')==0 for w in worlds)
   focus('Base');step(1,2)
  elif s==1:state['held']=True;step(2,.4)
  elif s==2:state['held']=False;inject(0);step(3,1)
  elif s==3:
   assert all(ue.GameplayStatics.get_game_state(w).get_editor_property('RelicsCollected')==2 for w in worlds)
   report['checks'].append({'actual_client_pickup_before_reconnect':2})
   ue.SystemLibrary.execute_console_command(pawn.get_world(),'open 127.0.0.1:'+str(PORT),pawn.get_controller());step(4,3)
  elif s==4:
   worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
   fresh=[w for w in worlds if w!=oldclient and w!=server and ue.GameplayStatics.get_game_state(w)]
   if not fresh:return
   newclient=fresh[0];gs=ue.GameplayStatics.get_game_state(newclient)
   if gs.call_method('GetPlayerCount')!=2 or gs.get_editor_property('RelicsCollected')!=2:return
   local=[p for p in ue.GameplayStatics.get_all_actors_of_class(newclient,cls) if p.is_locally_controlled()]
   if not local or not local[0].get_editor_property('InputReady'):return
   pawn=local[0];a=target(newclient,'Base')
   assert a.get_editor_property('Collected') and a.get_editor_property('hidden') and not a.get_actor_enable_collision()
   assert not a.call_method('CanInteract',args=(pawn,))
   assert gs.get_editor_property('RelicsAvailable')==8
   assert set(p.get_editor_property('ColorSlot') for p in gs.player_array)=={0,1}
   hud=pawn.get_component_by_class(ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()).get_editor_property('HUDWidget')
   if not hud:return
   assert hud.get_owning_player()==pawn.get_controller()
   report['checks'].append({'distinct_fresh_client_world':True,'collected_initial_replication':True,'hidden_and_collision_off':True,'totals':[2,8],'colors':[0,1],'owned_hud':True})
   focus('Base2');step(5,2)
  elif s==5:state['held']=True;step(6,.4)
  elif s==6:state['held']=False;inject(0);step(7,1)
  elif s==7:
   assert all(ue.GameplayStatics.get_game_state(w).get_editor_property('RelicsCollected')==3 for w in worlds if ue.GameplayStatics.get_game_state(w))
   report['checks'].append({'fresh_client_actual_pickup_after_join':True,'final_collected':3});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
