"""Native PIE test support. All gameplay input uses its actual owning subsystem."""
import json,re,time,traceback,platform
from pathlib import Path
import unreal as ue

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from Tools.unreal.playable_state.ghosts.context import ROOT, QUEUE
EXPECTED=ROOT
ASSETS={'pawn':'/Game/Core/BP_CoopCharacter','health':'/Game/Hazards/AC_Health',
 'view':'/Game/Player/AC_PlayerView','traversal':'/Game/Player/AC_Traversal',
 'tools':'/Game/Player/Tools/AC_Tools','flare':'/Game/Player/Tools/BP_Flare',
 'carry':'/Game/Puzzles/Carrying/AC_Carrying','lever':'/Game/Player/RelicChamber/BP_Lever',
 'cage':'/Game/Player/RelicChamber/BP_RelicCage','taking':'/Game/Player/Taking/BP_TakingDirector'}
# Paths demonstrated by shipped template movement and existing native key tests.
ACTIONS={'move':'/Game/Input/Actions/IA_Move','look':'/Game/Input/Actions/IA_Look',
 'jump':'/Game/Input/Actions/IA_Jump','sprint':'/Game/Core/Input/IA_Sprint',
 'flare':'/Game/Core/Input/IA_ThrowFlare','climb':'/Game/Core/Input/IA_Climb',
 'lamp':'/Game/Core/Input/IA_Headlamp','view':'/Game/Core/Input/IA_ToggleView',
 'interact':'/Game/Core/Input/IA_Interact','drop':'/Game/Core/Input/IA_Drop'}
_ACTIVE_HARNESSES=set()

class Harness:
 def __init__(self,args,name):
  self.args=args;self.root=Path(ue.Paths.project_dir()).resolve();assert self.root==EXPECTED
  self.queue=QUEUE;self.queue.mkdir(parents=True,exist_ok=True)
  self.n=int(args['players']);assert self.n in (2,3,4)
  self.profile=args['profile'];assert self.profile in ('joining','host_split')
  self.classes={k:ue.load_asset(p).generated_class() for k,p in ASSETS.items()}
  self.actions={k:ue.load_asset(p) for k,p in ACTIONS.items()}
  assert all(self.actions.values()),'Input asset prerequisite failed; do not substitute action paths silently'
  self.worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert self.worlds
  servers=[w for w in self.worlds if ue.GameplayStatics.get_game_mode(w)];assert len(servers)==1
  self.server=servers[0];self.clients=[w for w in self.worlds if w!=self.server]
  from editor_toolset.toolsets.object import ObjectTools as OBJ
  settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
  self.settings=json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
  assert self.settings['RunUnderOneProcess'],'All PIE worlds must be in one process for this native gate'
  expected_mode='PIE_Client' if self.profile=='joining' else 'PIE_ListenServer'
  assert self.settings['PlayNetMode']==expected_mode,self.settings
  self.server_pawns=self.pawns(self.server);assert len(self.server_pawns)==self.n
  self.ids=sorted(p.player_state.player_id for p in self.server_pawns);assert len(set(self.ids))==self.n
  slots={p.player_state.player_id:p.player_state.get_editor_property('ColorSlot') for p in self.server_pawns}
  assert len(set(slots.values()))==self.n and all(0<=slot<=3 for slot in slots.values())
  self.locals={};self.subsystems={};self.world_inventory=[]
  library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary');assert library
  for world in self.worlds:
   pawns=self.pawns(world);assert {p.player_state.player_id for p in pawns}==set(self.ids),'Wait for roster replication before starting gate'
   assert all(p.player_state.get_editor_property('ColorSlot')==slots[p.player_state.player_id] for p in pawns),'ColorSlots must agree across peers'
   # Public BlueprintPure APIs verified in installed KismetSystemLibrary.h.
   # Non-Edit NetDriver fields are not assumed exposed by Python reflection.
   assert not ue.SystemLibrary.is_standalone(world),'This must be network PIE, not standalone'
   assert ue.SystemLibrary.is_server(world)==(world==self.server)
   dedicated=ue.SystemLibrary.is_dedicated_server(world)
   assert dedicated==(world==self.server and self.profile=='joining')
   net_mode='NM_Client' if world!=self.server else ('NM_DedicatedServer' if dedicated else 'NM_ListenServer')
   owned=[p for p in pawns if p.is_locally_controlled()]
   self.world_inventory.append({'world':world.get_name(),'authoritative_game_mode':world==self.server,'net_mode_from_public_network_queries':net_mode,'local_player_ids':[p.player_state.player_id for p in owned]})
   for pawn in owned:
    pid=pawn.player_state.player_id;assert pid not in self.locals,'An ID must have exactly one input owner'
    controller=pawn.get_controller();assert controller and controller.is_local_controller() and controller.get_world()==world
    assert pawn.get_editor_property('SixInputReady'),'Owning SixRound context must be installed before gate'
    subsystem=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
    assert subsystem,'Owning local-player Enhanced Input subsystem missing'
    self.locals[pid]=pawn;self.subsystems[pid]=subsystem
  assert set(self.locals)==set(self.ids)
  host_ids=[pid for pid,pawn in self.locals.items() if pawn.get_world()==self.server]
  client_ids=[pid for pid,pawn in self.locals.items() if pawn.get_world()!=self.server]
  if self.profile=='joining':
   assert not host_ids and len(self.clients)==self.n and len(client_ids)==self.n
  else:
   assert len(host_ids)==2 and len(self.clients)==self.n-2 and len(client_ids)==self.n-2
   assert sum(self.locals[pid].get_controller().is_primary_player() for pid in host_ids)==1
   if self.n==4:assert len(client_ids)==2,'Four-player split gate requires two joining clients and two host owners'
  self.controls={};self.aims={};self.checks=[];self.fixtures=[];self.cleanup=[];self.phase='warmup'
  self.start=time.monotonic();self.deadline=self.start+float(args.get('timeout',90))
  self.report=self.queue/(name+'-'+self.profile+'-'+str(self.n)+'.json');self.finished=False
 def pawns(self,world):return list(ue.GameplayStatics.get_all_actors_of_class(world,self.classes['pawn']))
 def pawn(self,world,pid):
  matches=[p for p in self.pawns(world) if p.player_state.player_id==pid];assert len(matches)==1,(world.get_name(),pid)
  return matches[0]
 def actor_peer(self,world,server_actor):
  if world==self.server:return server_actor
  matches=[a for a in ue.GameplayStatics.get_all_actors_of_class(world,server_actor.get_class()) if a.get_name()==server_actor.get_name()]
  assert len(matches)==1,(world.get_name(),server_actor.get_name(),'Expected one replicated/placed peer actor; never compare server and client UObject pointers')
  return matches[0]
 def focused(self,pid,server_actor):
  owner=self.locals[pid]
  return owner.get_editor_property('FocusedTarget')==self.actor_peer(owner.get_world(),server_actor)
 def comp(self,pawn,key):
  component=pawn.get_component_by_class(self.classes[key]);assert component,(pawn.get_name(),key)
  return component
 def prop(self,pawn,key,name):
  component=self.comp(pawn,key)
  if key=='view' and name=='bHeadlampOn':return bool(component.call_method('GetHeadlampOn'))
  return component.get_editor_property(name)
 def inject(self,pid,role,value):
  vector=value if isinstance(value,ue.Vector) else ue.Vector(float(value),0,0)
  self.subsystems[pid].inject_input_vector_for_action(self.actions[role],vector,[],[])
 def hold(self,pid,role,value=1):self.controls[(pid,role)]=value
 def release(self,pid,role):self.controls.pop((pid,role),None);self.inject(pid,role,0)
 def release_all(self):
  for pid,role in list(self.controls):self.release(pid,role)
 def transition(self,phase):self.phase=phase;self.start=time.monotonic()
 def elapsed(self):return time.monotonic()-self.start
 def tick_inputs(self):
  assert time.monotonic()<self.deadline,'Native gate deadline in '+self.phase
  for (pid,role),value in self.controls.items():self.inject(pid,role,value)
  for pid,target in self.aims.items():self.aim(pid,target)
 def round(self):
  state=ue.GameplayStatics.get_game_state(self.server).get_editor_property('RoundState')
  return {'index':state.get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1'),'attempt':state.get_editor_property('Attempt_12_246832B34F4E147660E8729696BDD44A'),'phase':int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)',state.export_text())[1])}
 def fixture_place(self,pid,position):
  pawn=self.pawn(self.server,pid);pawn.set_actor_location(ue.Vector(*position),False,True);pawn.character_movement.velocity=ue.Vector()
  self.fixtures.append({'kind':'server approach teleport','player_id':pid,'position':list(position)})
 def aim(self,pid,target):
  pawn=self.locals[pid];eye=pawn.get_component_by_class(ue.CameraComponent).get_world_location()
  destination=target.get_actor_location()+ue.Vector(0,0,35)
  pawn.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(eye,destination))
 def focus(self,pid,target):
  pos=target.get_actor_location();self.fixture_place(pid,(pos.x-210,pos.y,pos.z+100));self.aims[pid]=target;self.aim(pid,target)
  self.fixtures.append({'kind':'owning controller aim fixture, maintained while focusing','player_id':pid,'target':target.get_name()})
 def snapshot(self):
  return [{'world':w.get_name(),'players':[{'id':p.player_state.player_id,'local_owner':p.is_locally_controlled(),'dead':self.prop(p,'health','bDead'),'heavy':bool(p.call_method('IsCarryingHeavy')),'protected':p.get_editor_property('bTakenProtected'),'sprint':self.prop(p,'traversal','bSprinting'),'climb':self.prop(p,'traversal','bClimbing'),'mantle':self.prop(p,'traversal','bMantling'),'flares':self.prop(p,'tools','FlaresLeft'),'view':self.prop(p,'view','ViewMode'),'lamp':self.prop(p,'view','bHeadlampOn'),'position':[p.get_actor_location().x,p.get_actor_location().y,p.get_actor_location().z]} for p in self.pawns(w)]} for w in self.worlds]
 def check(self,name,details=None):self.checks.append({'name':name,'details':details,'snapshot':self.snapshot()})
 def finish(self,passed,error=None):
  if self.finished:return
  self.finished=True;cleanup_errors=[]
  try:self.release_all()
  except Exception:cleanup_errors.append(traceback.format_exc())
  for cleanup in self.cleanup:
   try:cleanup()
   except Exception:cleanup_errors.append(traceback.format_exc())
  try:
   if hasattr(self,'handle'):ue.unregister_slate_post_tick_callback(self.handle)
  except Exception:cleanup_errors.append(traceback.format_exc())
  finally:_ACTIVE_HARNESSES.discard(self)
  if cleanup_errors:passed=False
  evidence={'passed':passed,'error':error,'cleanup_errors':cleanup_errors,'stage':self.phase,'profile':self.profile,'players':self.n,'pie_settings':self.settings,'world_inventory':self.world_inventory,'actions':ACTIONS,'checks':self.checks,'fixture_actions':self.fixtures,'input_method':'Synthetic Enhanced Input through each actual owning local-player subsystem; real Blueprint input/RPC path.','physical_keyboard_gamepad_tested':False,'platform':platform.system(),'engine':ue.SystemLibrary.get_engine_version(),'packet_emulation_tested':False,'visual_audio_acceptance':False}
  self.report.write_text(json.dumps(evidence,indent=2));return evidence
 def register(self,callback):
  assert not _ACTIVE_HARNESSES,'Only one PG input injector may run at once'
  def guarded_tick(delta):
   if self.finished:return
   try:self.tick_inputs();callback(delta)
   except Exception:self.finish(False,traceback.format_exc())
  self.handle=ue.register_slate_post_tick_callback(guarded_tick)
  _ACTIVE_HARNESSES.add(self)
  return {'queued':str(self.report),'runtime_acceptance_pending':True}
