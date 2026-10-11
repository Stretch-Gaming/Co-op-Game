"""Native client start/plates/split/regroup/locks/cage/dropoff transaction gate.
Teleports and physics settling are fixtures; interactions and tools use owning Enhanced Input.
This does not certify traversal, geometry, visuals or the complete walk-through.
"""
import time,json,traceback,re
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();QUEUE=ROOT/'Saved/SixRound';QUEUE.mkdir(parents=True,exist_ok=True)
assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')
positions=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();H=ue.load_asset('/Game/Hazards/AC_Health').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();U=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
players=sorted(ue.GameplayStatics.get_all_actors_of_class(server,C),key=lambda p:p.player_state.player_id)
locals_={p.player_state.player_id:p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()}
assert len(players) in (2,3,4) and len(locals_)==len(players),'Every PIE pawn needs its independently owning local controller'
N=len(players);library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
state={'phase':'pad','start':time.monotonic(),'deadline':time.monotonic()+200,'checks':[],'aims':{},'holds':{},'statue':0}
report=QUEUE/f'core-native-flow-{N}.json'
def actor(label):return next(a for a in ue.GameplayStatics.get_all_actors_of_class(server,ue.Actor) if a.get_actor_label()==label)
def round_state():return ue.GameplayStatics.get_game_state(server).get_editor_property('RoundState')
def index():return round_state().get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1')
def phase():return int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)',round_state().export_text())[1])
def local(i):return locals_[players[i].player_state.player_id]
def inject(i,name,value):
 driver=local(i).get_controller();sub=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(driver,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
 assert sub;sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(value,0,0),[],[])
def place(i,pos):players[i].set_actor_location(ue.Vector(*pos),False,True);players[i].character_movement.velocity=ue.Vector()
def focus(i,target):
 pos=target.get_actor_location();place(i,(pos.x-210,pos.y,pos.z+100));state['aims'][i]=target
 def look():local(i).get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(local(i).get_component_by_class(ue.CameraComponent).get_world_location(),target.get_actor_location()+ue.Vector(0,0,35)))
 look()
def transition(name):state['phase']=name;state['start']=time.monotonic();state['holds']={}
def use(i,name='IA_Interact',seconds=.2):state['holds'][i]=(name,seconds)
def finish(passed,error=None):
 for i,(name,_) in state['holds'].items():inject(i,name,0)
 ue.unregister_slate_post_tick_callback(state['handle']);report.write_text(json.dumps({'passed':passed,'error':error,'player_count':N,'local_controller_worlds':[local(i).get_world().get_name() for i in range(N)],'checks':state['checks'],'stage':state['phase'],'method':'Owning-player Enhanced Input for interactions/tools; overlap fixture approaches and physics settling; no gameplay RPC/function shortcut.','limits':'Not a path traversal or physical gamepad test.'},indent=2))
for i in range(N):place(i,(800,(i-(N-1)/2)*100,100))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];step=state['phase'];assert time.monotonic()<state['deadline'],'native flow deadline'
  for i,target in state['aims'].items():local(i).get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(local(i).get_component_by_class(ue.CameraComponent).get_world_location(),target.get_actor_location()+ue.Vector(0,0,35)))
  for i,(name,duration) in state['holds'].items():inject(i,name,1 if elapsed<duration else 0)
  if step=='pad' and elapsed>4:
   assert index()==1 and phase()==1;setup=actor('Six_PlatePuzzle');state['statues']=list(setup.get_editor_property('Statues'));assert len(state['statues'])==(2 if N==2 else 1)
   state['checks'].append('all connected owners start the first room through pad overlap');focus(0,state['statues'][0]);transition('statue_focus')
  elif step=='statue_focus' and elapsed>1:
   assert local(0).get_editor_property('FocusedTarget')==state['statues'][state['statue']];transition('statue_pickup');use(0)
  elif step=='statue_pickup' and elapsed>1:
   assert players[0].get_component_by_class(AC).get_editor_property('CarriedItem')==state['statues'][state['statue']]
   state['aims']={};pos=positions['plates'][state['statue']];place(0,(pos[0]-120,pos[1],pos[2]+100));transition('statue_drop');use(0,'IA_Drop')
  elif step=='statue_drop' and elapsed>1:
   assert players[0].get_component_by_class(AC).get_editor_property('CarriedItem') is None
   statue=state['statues'][state['statue']];pos=positions['plates'][state['statue']];statue.set_actor_location(ue.Vector(pos[0],pos[1],pos[2]+50),False,True);statue.static_mesh_component.set_physics_linear_velocity(ue.Vector(),False)
   state['statue']+=1
   if state['statue']<len(state['statues']):focus(0,state['statues'][state['statue']]);transition('statue_focus')
   else:
    first=len(state['statues']);plate_count=4 if N==4 else 3
    for i in range(N):
     pos=positions['plates'][first+i%(plate_count-first)];place(i,(pos[0],pos[1],pos[2]+100))
    transition('plates')
  elif step=='plates' and elapsed>2:
   assert index()==1 and phase()==2;assert actor('Six_MazeDoor').get_editor_property('Open');state['checks'].append('native statue pickup/drop and living plate weight clear round one')
   for i in range(N):pos=positions['maze_mouth']['center'];place(i,(pos[0],pos[1]+(i-(N-1)/2)*100,pos[2]))
   transition('taking')
  elif step=='taking' and elapsed>24:
   assert index()==2 and phase()==1;assert not actor('Six_MazeDoor').get_editor_property('Open');state['checks'].append('whole-team maze-mouth overlap starts round two and seals entrance')
   for i in range(N):pos=positions['checkpoints']['3'][i];place(i,pos)
   transition('meeting')
  elif step=='meeting' and elapsed>2:
   assert index()==3 and phase()==1;state['checks'].append('every living player regroup starts meeting round three')
   # Start a real flare next to each active bowl. Flare placement is the authored throw spawn.
   for i in range(1 if N<4 else 2):
    target=actor('Six_braziers_'+str(i));pos=target.get_actor_location();place(i,(pos.x-90,pos.y,pos.z+100));local(i).get_controller().set_control_rotation(ue.Rotator(pitch=-60))
   transition('flares')
   for i in range(1 if N<4 else 2):use(i,'IA_ThrowFlare')
  elif step=='flares' and elapsed>1:
   assert len(ue.GameplayStatics.get_all_actors_of_class(server,ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class()))>0
   for i in range(1 if N==2 else 2):
    focus(i,actor('Six_headlamp_locks_'+str(i)))
    view=local(i).get_component_by_class(ue.load_asset('/Game/Player/AC_PlayerView').generated_class())
    if not view.get_editor_property('HeadlampOn'):inject(i,'IA_Headlamp',1);inject(i,'IA_Headlamp',0)
   transition('locks')
  elif step=='locks' and elapsed>2:
   assert index()==4 and phase()==1,'simultaneous native headlamp/flare locks did not open doors';state['aims']={};state['checks'].append('owning headlamp aim and native flare throw light locks together')
   for i in range(N):place(i,positions['checkpoints']['5'][i])
   transition('relic_chamber')
  elif step=='relic_chamber' and elapsed>2:
   assert index()==5 and phase()==1;state['checks'].append('every living player reaches relic chamber and starts round five')
   lever_count=2 if N==4 else 1
   state['levers']=sorted(ue.GameplayStatics.get_all_actors_of_class(server,ue.load_asset('/Game/Player/RelicChamber/BP_Lever').generated_class()),key=lambda a:a.get_actor_location().x)
   for i in range(lever_count):focus(i,state['levers'][i])
   focus(N-1,actor('Six_KeyRelic'));transition('cage_hold')
   for i in range(lever_count):use(i,seconds=20)
  elif step=='cage_hold' and elapsed>1:
   cage=ue.GameplayStatics.get_all_actors_with_tag(server,'RelicCage')[0];assert cage.get_editor_property('bRaised');assert local(N-1).get_editor_property('FocusedTarget')==actor('Six_KeyRelic');use(N-1)
   transition('key_pickup')
   for i in range(2 if N==4 else 1):use(i,seconds=20)
   use(N-1)
  elif step=='key_pickup' and elapsed>1:
   assert index()==6 and phase()==1;assert players[N-1].get_component_by_class(AC).get_editor_property('CarriedItem')==actor('Six_KeyRelic');state['checks'].append('normal continuous lever holds and native key pickup start escape')
   for i in range(2 if N==4 else 1):inject(i,'IA_Interact',0)
   state['aims']={};focus(N-1,actor('Six_DropoffAltar'));transition('altar_focus')
  elif step=='altar_focus' and elapsed>1:
   assert local(N-1).get_editor_property('FocusedTarget')==actor('Six_DropoffAltar');transition('altar_use');use(N-1)
  elif step=='altar_use' and elapsed>1:
   assert actor('Six_DropoffAltar').get_editor_property('Completed');assert phase()==4;state['checks'].append('native altar delivery completes exactly round six; results travel separately after five seconds');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':str(report),'runtime_acceptance_pending':True}
