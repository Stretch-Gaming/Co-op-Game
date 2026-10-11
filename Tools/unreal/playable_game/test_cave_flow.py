import time,json,traceback,re
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();H=ue.load_asset('/Game/Hazards/AC_Health').generated_class();library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
players=sorted(ue.GameplayStatics.get_all_actors_of_class(server,C),key=lambda p:p.player_state.player_id);assert len(players)==2
locals_=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.player_state.player_id);assert len(locals_)==2
state={'phase':'pad','start':time.monotonic(),'checks':[],'deadline':time.monotonic()+140,'held':None,'focus':None,'statue':0};report=QUEUE/'cave-puzzle-flow.json'
def actor(label):return next(a for a in ue.GameplayStatics.get_all_actors_of_class(server,ue.Actor) if a.get_actor_label()==label)
def round_state():return ue.GameplayStatics.get_game_state(server).get_editor_property('RoundState')
def phase():return int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)',round_state().export_text())[1])
def index():return round_state().get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1')
def inject(i,name,value):
 driver=locals_[i].get_controller();mapped=name
 if i==1 and driver.get_world()==server and name=='IA_Interact':driver=locals_[0].get_controller();mapped='IA_P2Use'
 sub=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(driver,ue.EnhancedInputLocalPlayerSubsystem.static_class()));sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+mapped),ue.Vector(value,0,0),[],[])
def place(i,pos):players[i].set_actor_location(ue.Vector(*pos),False,True);players[i].character_movement.velocity=ue.Vector()
def aim(target,i=0):
 local=locals_[i];local.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(local.get_component_by_class(ue.CameraComponent).get_world_location(),target.get_actor_location()+ue.Vector(0,0,40)))
def focus(target,i=0):
 pos=target.get_actor_location();place(i,(pos.x-210,pos.y,pos.z+92));state['focus']=(target,i)
def transition(name):state['phase']=name;state['start']=time.monotonic();state['held']=None

def finish(passed,error=None):
 ue.unregister_slate_post_tick_callback(state['handle']);report.write_text(json.dumps({'passed':passed,'error':error,'checks':state['checks'],'phase':state['phase'],'round':round_state().export_text(),'method':'Real pad overlaps and owning-player Enhanced Input; server approach positions are test fixtures.'},indent=2))
for i,p in enumerate(players):
 p.get_component_by_class(H).call_method('ResetHealth');place(i,(800,(i-.5)*150,100))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];step=state['phase'];assert time.monotonic()<state['deadline'],'flow timed out'
  if state['focus']:aim(*state['focus'])
  if state['held']:
   i,name,duration=state['held'];inject(i,name,1 if elapsed<duration else 0)
  if step=='pad' and elapsed>4:
   assert index()==1 and int(phase())==1
   setup=actor('Adventure_PlatePuzzle');assert setup.get_editor_property('Ready');state['statues']=list(setup.get_editor_property('Statues'));assert len(state['statues'])==2
   state['checks'].append('the team start pad begins round one and creates scaled statues');focus(state['statues'][0]);transition('statue_focus')
  elif step=='statue_focus' and elapsed>1:
   assert locals_[0].get_editor_property('FocusedTarget')==state['statues'][state['statue']],('statue trace',str(locals_[0].get_editor_property('FocusedTarget')))
   transition('statue_pickup');state['held']=(0,'IA_Interact',.2)
  elif step=='statue_pickup' and elapsed>1:
   carried=players[0].get_component_by_class(AC).get_editor_property('CarriedItem');assert carried==state['statues'][state['statue']]
   state['focus']=None;plate=actor('Adventure_Plate_'+str(state['statue']));pos=plate.get_actor_location();place(0,(pos.x-120,pos.y,100));locals_[0].get_controller().set_control_rotation(ue.Rotator());transition('statue_drop');state['held']=(0,'IA_Drop',.2)
  elif step=='statue_drop' and elapsed>1:
   assert players[0].get_component_by_class(AC).get_editor_property('CarriedItem') is None
   statue=state['statues'][state['statue']];plate=actor('Adventure_Plate_'+str(state['statue']));pos=plate.get_actor_location()
   # Settle the released physics weight at the middle of this test plate.
   statue.set_actor_location(ue.Vector(pos.x,pos.y,80),False,True);statue.static_mesh_component.set_physics_linear_velocity(ue.Vector(),False)
   state['statue']+=1
   if state['statue']<2:focus(state['statues'][1]);transition('statue_focus')
   else:
    place(0,(4800,-800,100));place(1,(4800,-800+100,100));transition('plates')
  elif step=='plates' and elapsed>2:
   assert int(phase())==2,'plate puzzle did not clear';assert actor('Adventure_ChamberGate_1').get_editor_property('Open');state['checks'].append('normal pickup and drop, plus standing players, solve the plate chamber');place(0,(5700,0,100));place(1,(5700,120,100));transition('round2')
  elif step=='round2' and elapsed>1:
   assert index()==2 and int(phase())==1;focus(actor('Adventure_KeyRelic'));transition('key_focus')
  elif step=='key_focus' and elapsed>1:
   assert locals_[0].get_editor_property('FocusedTarget')==actor('Adventure_KeyRelic');transition('key_pickup');state['held']=(0,'IA_Interact',.2)
  elif step=='key_pickup' and elapsed>1:
   assert players[0].get_component_by_class(AC).get_editor_property('CarriedItem')==actor('Adventure_KeyRelic');assert players[0].character_movement.max_walk_speed==300
   focus(actor('Adventure_Altar'));transition('altar_focus')
  elif step=='altar_focus' and elapsed>1:
   assert locals_[0].get_editor_property('FocusedTarget')==actor('Adventure_Altar');transition('altar_use');state['held']=(0,'IA_Interact',.2)
  elif step=='altar_use' and elapsed>1:
   assert actor('Adventure_Altar').get_editor_property('Completed');assert int(phase())==2;state['checks'].append('the heavy key slows its carrier and the normal altar interaction clears round two');state['focus']=None;place(0,(11700,0,100));place(1,(11700,120,100));transition('round3')
  elif step=='round3' and elapsed>1:
   assert index()==3 and int(phase())==1
   levers=ue.GameplayStatics.get_all_actors_with_tag(server,'HC_GauntletLever');state['lever']=levers[0];focus(state['lever']);place(1,(12050,100,100));transition('lever_focus')
  elif step=='lever_focus' and elapsed>1:
   assert locals_[0].get_editor_property('FocusedTarget')==state['lever'];transition('lever_hold');state['held']=(0,'IA_Interact',30)
  elif step=='lever_hold' and elapsed>1:
   assert state['lever'].get_editor_property('bActive');state['focus']=None;place(1,(12900,100,100));transition('crossed');state['held']=(0,'IA_Interact',30)
  elif step=='crossed' and elapsed>1:
   focus(actor('Adventure_GauntletObjective'),1);transition('objective_focus');state['held']=(0,'IA_Interact',30)
  elif step=='objective_focus' and elapsed>1:
   assert locals_[1].get_editor_property('FocusedTarget')==actor('Adventure_GauntletObjective');inject(1,'IA_Interact',1);transition('objective_use');state['held']=(0,'IA_Interact',30)
  elif step=='objective_use':
   inject(1,'IA_Interact',0)
   if elapsed>1:
    gate=ue.GameplayStatics.get_all_actors_with_tag(server,'HC_GauntletGate')[0];assert gate.get_editor_property('bLatched');assert int(phase())==2;inject(0,'IA_Interact',0);state['checks'].append('lever-held crossing and the far switch latch the gate and clear round three');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':'cave-puzzle-flow.json'}
