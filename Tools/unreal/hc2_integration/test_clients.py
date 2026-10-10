"""Actual Enhanced Input -> character server RPC -> relic acceptance.
Fixture positioning uses Python; pickup actions are injected for owning local players.
"""
import json,time,math,traceback
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools
N=ARGS['clients'];report={'passed':False,'clients':N,'checks':[],'action_path':'EnhancedInputLocalPlayerSubsystem.inject_input_vector_for_action -> IA_Interact Started/Completed -> reliable character RPC'}
state={'stage':0,'at':0,'held':[],'deadline':time.monotonic()+120}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
locals=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
action=ue.load_asset('/Game/Core/Input/IA_Interact')
subsystems={p.get_controller():next(s for s in ue.ObjectIterator(ue.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in s.get_path_name() and s.get_world()==p.get_world()) for p in locals}

def target(w,name):return ue.GameplayStatics.get_all_actors_with_tag(w,'HC2_'+name)[0]
def totals():return [(ue.GameplayStatics.get_game_state(w).get_editor_property('RelicsCollected'),ue.GameplayStatics.get_game_state(w).get_editor_property('RelicsAvailable')) for w in worlds]
def inject(p,value,act=action):subsystems[p.get_controller()].inject_input_vector_for_action(act,ue.Vector(float(value),0,0),[],[])
def focus(p,name,offset=0):
 pid=p.player_state.get_editor_property('PlayerId');a=target(p.get_world(),name)
 for w in worlds:
  for other in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   other.set_actor_enable_collision(False)
   if other.player_state.get_editor_property('PlayerId')==pid:
    other.set_actor_location(a.get_actor_location()+ue.Vector(-230,offset,-12),False,True)
 pc=p.get_controller();camera=p.get_editor_property('FollowCamera')
 look=a.get_actor_location()+ue.Vector(0,0,12)-camera.get_world_location()
 pc.set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x)),roll=0))
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 report['final_totals']=totals()
 (HERE/f'clients-{N}.json').write_text(json.dumps(report,indent=2))
 for p in state['held']:inject(p,0)
 ue.unregister_slate_post_tick_callback(handle)
 ue.log('HC2_CLIENT_ACCEPTANCE_'+str(N)+': '+str(ok))
def step(number,delay):state['stage']=number;state['at']=time.monotonic()+delay

def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Acceptance timed out'
  for p in state['held']:inject(p,1)
  if now<state['at']:return
  stage=state['stage']
  if stage==0:
   assert len(worlds)==N+1 and len(locals)==N
   expected={2:8,3:11,4:15}[N]
   assert totals()==[(0,expected)]*len(worlds),totals()
   for w in worlds:
    gs=ue.GameplayStatics.get_game_state(w)
    assert set(s.get_editor_property('ColorSlot') for s in gs.player_array)==set(range(N))
    assert str(gs.call_method('GetScalingRow'))==str(N)
    for name,minimum in [('Base',2),('Bonus3',3),('Bonus4',4)]:
     a=target(w,name);visible=N>=minimum
     assert a.get_editor_property('Available')==visible
     assert a.get_editor_property('hidden')!=visible
     assert a.get_actor_enable_collision()==visible
   hud=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
   for p in locals:
    component=p.get_component_by_class(hud);widget=component.get_editor_property('HUDWidget')
    assert widget and widget.get_owning_player()==p.get_controller()
    assert p.get_editor_property('PromptWidget').get_owning_player()==p.get_controller()
   report['checks'].append({'initial_available_value':expected,'min_players_replicated':True,'unique_colors':N,'owning_huds':N})
   focus(locals[0],'Base');step(1,2)
  elif stage==1:
   assert locals[0].get_editor_property('FocusedTarget')==target(locals[0].get_world(),'Base'),str(locals[0].get_editor_property('FocusedTarget'))
   state['held']=[locals[0]];step(2,.5)
  elif stage==2:
   state['held']=[];inject(locals[0],0);step(3,1)
  elif stage==3:
   assert all(c==2 for c,a in totals()),totals()
   for w in worlds:
    a=target(w,'Base');assert a.get_editor_property('Collected') and a.get_editor_property('hidden') and not a.get_actor_enable_collision()
    assert a.get_editor_property('PickupFeedbackCount')==1
   report['checks'].append({'client_pickup_value_2_replicated':True,'hidden_collision_off_every_world':True})
   for i,p in enumerate(locals[:2]):focus(p,'Race',(-35,35)[i])
   step(4,2)
  elif stage==4:
   assert all(p.get_editor_property('FocusedTarget')==target(p.get_world(),'Race') for p in locals[:2]),[str(p.get_editor_property('FocusedTarget')) for p in locals[:2]]
   state['held']=locals[:2];step(5,.5)
  elif stage==5:
   state['held']=[]
   for p in locals[:2]:inject(p,0)
   step(6,1)
  elif stage==6:
   assert all(c==7 for c,a in totals()),totals()
   assert all(target(w,'Race').get_editor_property('Collected') for w in worlds)
   assert all(target(w,'Race').get_editor_property('PickupFeedbackCount')==1 for w in worlds)
   report['checks'].append({'simultaneous_two_client_pickup_added_value_5_once':True,'unreliable_cosmetic_sound_event_each_world_once':True})
   # A repeat press at the same now-collected actor cannot collect again.
   state['held']=locals[:2];step(7,.4)
  elif stage==7:
   state['held']=[]
   for p in locals[:2]:inject(p,0)
   step(8,1)
  elif stage==8:
   assert all(c==7 for c,a in totals()),totals()
   report['checks'].append({'repeat_press_no_double_collection':True})
   # Remote input must not change host controls.
   state['held']=[]
   for act in ['IA_DebugStart','IA_DebugClear','IA_DebugFail']:
    for p in locals:inject(p,1,ue.load_asset('/Game/Core/Input/'+act))
   step(9,1)
  elif stage==9:
   rounds=[json.loads(ObjectTools.get_properties(ue.GameplayStatics.get_game_state(w),['RoundState']))['RoundState'] for w in worlds]
   assert all(r['phase']=='Lobby' for r in rounds),rounds
   report['checks'].append({'remote_host_debug_input_rejected':True})
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)


