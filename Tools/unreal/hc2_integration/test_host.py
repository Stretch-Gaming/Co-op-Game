"""Listen host + remote client, native fixture joins, owning input and travel.
Engine Create/RemovePlayer here are test setup, not production split-screen hooks.
"""
import json,time,math,traceback
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools
report={'passed':False,'checks':[],'production_pg_split_contract_present':False,'join_fixture':'native GameplayStatics.create_player/remove_player','input_path':'owning Enhanced Input action injection'}
state={'stage':0,'at':0,'held':[],'deadline':time.monotonic()+180}
if ARGS.get('resume_travel'):
 report['checks']=json.loads((HERE/'host-split-latejoin.json').read_text())['checks']
 state['stage']=23
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
client=next(w for w in worlds if not ue.GameplayStatics.get_game_mode(w))
cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
probecls=ue.load_asset('/Game/Puzzles/Test/HC2/BP_HC2InputProbe').generated_class()
probes={};subsystems={}
controllers=[p.get_controller() for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
host=next(pc for pc in controllers if pc.get_world()==server)
remote=next(pc for pc in controllers if pc.get_world()==client)
second=None;late=None

def snapshot():
 ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));out=[]
 for w in ws:
  gs=ue.GameplayStatics.get_game_state(w)
  if not gs:continue
  out.append({'world':w.get_path_name(),'count':gs.call_method('GetPlayerCount'),'slots':sorted(s.get_editor_property('ColorSlot') for s in gs.player_array),'state':json.loads(ObjectTools.get_properties(gs,['RoundState','RelicsCollected','RelicsAvailable']))})
 return out

def resolve(pc):
 if pc in subsystems:return subsystems[pc]
 w=pc.get_world()
 if w not in probes:probes[w]=ue.get_default_object(probecls)
 obj=probes[w].call_method('ResolveInput',args=(pc,))
 result=ue.EnhancedInputLocalPlayerSubsystem.cast(obj);assert result,(pc,obj)
 subsystems[pc]=result;return result

def inject(pc,action,value):resolve(pc).inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+action),ue.Vector(float(value),0,0),[],[])
def press(pc,action,duration=.3):state['held']=[(pc,action)];state['at']=time.monotonic()+duration

def focus(pc,name,offset=0):
 p=pc.get_controlled_pawn();a=ue.GameplayStatics.get_all_actors_with_tag(pc.get_world(),'HC2_'+name)[0]
 for w in worlds:
  for other in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   other.set_actor_enable_collision(False)
   if other.player_state.get_editor_property('PlayerId')==p.player_state.get_editor_property('PlayerId'):
    other.set_actor_location(a.get_actor_location()+ue.Vector(-230,offset,-12),False,True)
 camera=p.get_editor_property('FollowCamera');look=a.get_actor_location()+ue.Vector(0,0,12)-camera.get_world_location()
 pc.set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))

def step(number,delay=1):state['stage']=number;state['at']=time.monotonic()+delay

def release():
 for pc,act in state['held']:inject(pc,act,0)
 state['held']=[]

def check(count,row,collected,available,phase='Lobby'):
 rows=snapshot();assert len(rows)==2,rows
 assert all(r['count']==count and len(set(r['slots']))==count and all(0<=slot<4 for slot in r['slots']) and r['state']['RoundState']['scalingRow']==str(row) and r['state']['RoundState']['phase']==phase and r['state']['RelicsCollected']==collected and r['state']['RelicsAvailable']==available for r in rows),rows
 return rows

def owned_hud(pcs):
 hudcls=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class();widgets=[]
 for pc in pcs:
  p=pc.get_controlled_pawn();assert p and p.get_editor_property('InputReady')
  widget=p.get_component_by_class(hudcls).get_editor_property('HUDWidget');assert widget and widget.get_owning_player()==pc
  assert p.get_editor_property('PromptWidget').get_owning_player()==pc
  widgets.append(widget.get_path_name())
 assert len(set(widgets))==len(widgets)
 return widgets

def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 report['final_snapshot']=snapshot()
 (HERE/'host-split-latejoin.json').write_text(json.dumps(report,indent=2))
 ue.unregister_slate_post_tick_callback(handle);ue.log('HC2_HOST_ACCEPTANCE: '+str(ok))

def tick(dt):
 global second,late,worlds,server,client,host,remote,probes,subsystems
 try:
  now=time.monotonic();assert now<state['deadline'],'Acceptance timeout'
  for pc,act in state['held']:inject(pc,act,1)
  if now<state['at']:return
  s=state['stage']
  if s==0:
   check(2,2,0,8);owned_hud([host,remote]);focus(remote,'Base');step(1,2)
  elif s==1:press(remote,'IA_Interact');state['stage']=2
  elif s==2:release();step(3,1)
  elif s==3:
   check(2,2,2,8);second=ue.GameplayStatics.create_player(server,-1,True);assert second;step(4,3)
  elif s==4:
   check(3,3,2,11);widgets=owned_hud([host,second,remote]);assert second.player_state.get_editor_property('ColorSlot')==2
   assert not second.get_editor_property('DebugInputAdded')
   report['checks'].append({'host_split_join_scales_lobby_to_3':True,'distinct_owned_widgets':widgets,'new_color_slot':2})
   press(second,'IA_DebugStart');state['stage']=5
  elif s==5:release();step(6,1)
  elif s==6:
   check(3,3,2,11);report['checks'].append({'second_local_host_controls_rejected':True})
   focus(second,'Bonus3');step(7,2)
  elif s==7:press(second,'IA_Interact');state['stage']=8
  elif s==8:release();step(9,1)
  elif s==9:
   check(3,3,5,11);report['checks'].append({'second_local_actual_pickup_value_3':True})
   ue.GameplayStatics.remove_player(second,True);step(10,3)
  elif s==10:
   check(2,2,5,11);second=ue.GameplayStatics.create_player(server,-1,True);step(11,3)
  elif s==11:
   check(3,3,5,11);assert second.player_state.get_editor_property('ColorSlot')==2
   report['checks'].append({'lobby_leave_rescales_to_2':True,'collected_value_keeps_denominator':11,'first_free_color_reused':2})
   late=ue.GameplayStatics.create_player(client,-1,True);step(12,4)
  elif s==12:
   late=next(pc for pc in ue.GameplayStatics.get_all_actors_of_class(client,ue.PlayerController) if pc!=remote and pc.is_local_controller())
   check(4,4,5,15);owned_hud([host,second,remote,late]);assert late.player_state.get_editor_property('ColorSlot')==3
   for name in ('Base','Bonus3'):
    a=ue.GameplayStatics.get_all_actors_with_tag(late.get_world(),'HC2_'+name)[0]
    assert a.get_editor_property('Collected') and a.get_editor_property('hidden') and not a.get_actor_enable_collision()
   report['checks'].append({'remote_late_join_observes_collected_and_totals':True,'late_join_color':3,'four_player_scaling':True})
   press(host,'IA_DebugStart');state['stage']=13
  elif s==13:release();step(14,1)
  elif s==14:
   check(4,4,5,15,'Playing');ue.GameplayStatics.remove_player(second,True);step(15,3)
  elif s==15:
   check(3,4,5,15,'Playing');report['checks'].append({'row_locked_during_playing_after_leave':True})
   press(host,'IA_DebugStart');state['stage']=16
  elif s==16:release();step(17,1)
  elif s==17:
   check(3,3,5,11,'Playing');second=ue.GameplayStatics.create_player(server,-1,True);report['checks'].append({'new_round_start_refreshes_scaling_to_3':True,'collected_survives_round_restart':True})
   press(host,'IA_DebugClear');state['stage']=18
  elif s==18:release();step(19,1)
  elif s==19:
   check(4,3,5,11,'Cleared');report['checks'].append({'host_clear_via_actual_input':True})
   # A non-primary local player cannot run F4.
   press(second,'IA_DebugComplete');state['stage']=20
  elif s==20:release();step(21,1)
  elif s==21:
   check(4,3,5,11,'Cleared');report['checks'].append({'second_local_travel_input_rejected':True})
   press(host,'IA_DebugComplete');state['stage']=22
  elif s==22:
   # Release before old controllers are destroyed by non-seamless travel.
   release();step(23,6)
  elif s==23:
   rows=snapshot()
   if len(rows)!=2 or not all('L_Site02' in r['world'] and r['count']==4 for r in rows):return
   worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));client=next(w for w in worlds if not ue.GameplayStatics.get_game_mode(w))
   pcs=[p.get_controller() for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
   owned_hud(pcs);host=next(pc for pc in pcs if pc.get_world()==server and pc.is_primary_player());probes={};subsystems={}
   report['checks'].append({'F4_server_travel_to_site02_with_host_split_and_remote':True,'after_travel_owned_huds':len(pcs)})
   press(host,'IA_DebugComplete');state['stage']=24
  elif s==24:release();step(25,6)
  elif s==25:
   rows=snapshot()
   if len(rows)!=2 or not all('L_Site01' in r['world'] and r['count']==4 for r in rows):return
   worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
   pcs=[p.get_controller() for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
   owned_hud(pcs);report['checks'].append({'F4_returns_every_player_to_site01':True,'after_return_owned_huds':len(pcs)})
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)

