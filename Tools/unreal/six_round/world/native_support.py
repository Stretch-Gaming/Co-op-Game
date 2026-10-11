"""World-owned native PIE evidence, using documented actor/input APIs only."""
import json,re,time,traceback,hashlib
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
ROOT=Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')
ACTION_PATHS={'move':'/Game/Input/Actions/IA_Move','jump':'/Game/Input/Actions/IA_Jump','sprint':'/Game/Core/Input/IA_Sprint','climb':'/Game/Core/Input/IA_Climb','interact':'/Game/Core/Input/IA_Interact'}
COMPONENT_PATHS={'health':'/Game/Hazards/AC_Health','traversal':'/Game/Player/AC_Traversal'}
class Harness:
 def __init__(self,args,name):
  assert Path(ue.Paths.project_dir()).resolve()==ROOT
  self.args=args;self.n=int(args['players']);assert self.n in (2,3,4)
  self.profile=args['profile'];assert self.profile in ('joining','host_split')
  self.classes={'pawn':ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class(),**{k:ue.load_asset(p).generated_class() for k,p in COMPONENT_PATHS.items()}}
  self.actions={k:ue.load_asset(p) for k,p in ACTION_PATHS.items()};assert all(self.actions.values())
  self.worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert self.worlds
  servers=[w for w in self.worlds if ue.GameplayStatics.get_game_mode(w)];assert len(servers)==1
  self.server=servers[0];self.clients=[w for w in self.worlds if w!=self.server]
  self.settings=json.loads(OBJ.get_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))
  assert self.settings['RunUnderOneProcess']
  assert self.settings['PlayNetMode']==('PIE_Client' if self.profile=='joining' else 'PIE_ListenServer')
  self.server_pawns=self.pawns(self.server);assert len(self.server_pawns)==self.n
  self.ids=sorted(p.player_state.player_id for p in self.server_pawns)
  self.slots={p.player_state.player_id:int(p.player_state.get_editor_property('ColorSlot')) for p in self.server_pawns}
  assert len(set(self.slots.values()))==self.n and all(0<=v<4 for v in self.slots.values())
  self.locals={};self.subsystems={};self.world_inventory=[]
  lib=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary');assert lib
  for world in self.worlds:
   visible=[p.player_state.player_id for p in self.pawns(world)]
   assert len(visible)==len(set(visible)) and set(visible)<=set(self.ids)
   if world==self.server:assert sorted(visible)==self.ids
   local=[]
   for p in self.pawns(world):
    assert int(p.player_state.get_editor_property('ColorSlot'))==self.slots[p.player_state.player_id]
    if not p.is_locally_controlled():continue
    pid=p.player_state.player_id;assert pid not in self.locals
    controller=p.get_controller();assert controller and controller.is_local_controller() and controller.get_world()==world
    assert p.get_editor_property('SixInputReady')
    sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()));assert sub
    self.locals[pid]=p;self.subsystems[pid]=sub;local.append(pid)
   self.world_inventory.append({'world':world.get_name(),'server':world==self.server,'owning_ids':local,'visible_ids':visible,'remote_proxy_presence':'subject to native network relevance'})
  assert set(self.locals)==set(self.ids)
  host=[pid for pid,p in self.locals.items() if p.get_world()==self.server]
  if self.profile=='joining':assert not host and len(self.clients)==self.n
  else:assert len(host)==2 and len(self.clients)==self.n-2
  self.controls={};self.aims={};self.fixtures=[];self.aim_fixtures={};self.checks=[];self.cleanup=[];self.phase='setup';self.finished=False
  self.fixture_times={};self.fixture_settle_evidence={};self.diagnostics=[];self.motion_evidence={}
  sources=['world/native_support.py','world/probe_native_route.py','world/path_driver.py','world/positions.json','player/traversal.py','finish_inputs.py','integration_inputs.py','fix_mantle.py']
  files=[ROOT/'Tools/unreal/six_round'/p for p in sources]+[ROOT/'Content/Core/BP_CoopCharacter.uasset',ROOT/'Content/Player/AC_Traversal.uasset',ROOT/'Content/Core/Input/IMC_Coop.uasset',ROOT/'Content/Core/Input/IMC_SixRound.uasset']
  files.extend((ROOT/'Content').rglob('L_SixRound*.umap'))
  self.input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
  self.start=time.monotonic();self.deadline=self.start+float(args.get('timeout',180))
  self.queue=ROOT/'Saved/SixRound';self.queue.mkdir(parents=True,exist_ok=True)
  self.report=self.queue/(name+'-'+self.profile+'-'+str(self.n)+'.json')
 def pawns(self,world):return list(ue.GameplayStatics.get_all_actors_of_class(world,self.classes['pawn']))
 def pawn(self,world,pid):
  matches=[p for p in self.pawns(world) if p.player_state.player_id==pid];assert len(matches)==1
  return matches[0]
 def comp(self,pawn,key):
  value=pawn.get_component_by_class(self.classes[key]);assert value
  return value
 def prop(self,pawn,key,name):return self.comp(pawn,key).get_editor_property(name)
 def hold(self,pid,role,value=1):self.controls[(pid,role)]=value
 def inject(self,pid,role,value):
  vec=value if isinstance(value,ue.Vector) else ue.Vector(float(value),0,0)
  self.subsystems[pid].inject_input_vector_for_action(self.actions[role],vec,[],[])
 def release(self,pid,role):self.controls.pop((pid,role),None);self.inject(pid,role,0)
 def release_all(self):
  for pid,role in list(self.controls):self.release(pid,role)
 def transition(self,phase):self.phase=phase;self.start=time.monotonic()
 def elapsed(self):return time.monotonic()-self.start
 def fixture_place(self,pid,position):
  assert not any(f.get('id')==pid for f in self.fixtures),'Only one initial approach per owner is allowed in a world gate'
  pawn=self.pawn(self.server,pid);pawn.set_actor_location(ue.Vector(*position),False,True);pawn.character_movement.velocity=ue.Vector()
  self.fixtures.append({'kind':'initial server approach placement','id':pid,'position':list(position)})
  self.fixture_times[pid]=time.monotonic()
 def fixture_settled(self,pid):
  if pid not in self.fixture_times:return True
  server=self.pawn(self.server,pid);owner=self.locals[pid]
  distance=(owner.get_actor_location()-server.get_actor_location()).length()
  age=time.monotonic()-self.fixture_times[pid]
  ready=age>=.8 and distance<=30.0
  if ready and pid not in self.fixture_settle_evidence:
   self.fixture_settle_evidence[pid]={'elapsed_seconds':age,'owner_server_distance_cm':distance,'position':self.vector(server.get_actor_location()),'owner_position':self.vector(owner.get_actor_location()),'minimum_seconds':.8,'maximum_distance_cm':30}
  return ready
 @staticmethod
 def vector(value):return [value.x,value.y,value.z]
 def mantle_diagnostic(self,pid,label):
  pawn=self.pawn(self.server,pid);owner=self.locals[pid];traversal=self.comp(pawn,'traversal')
  def state(p):
   return {'position':self.vector(p.get_actor_location()),'actor_yaw':p.get_actor_rotation().yaw,'controller_yaw':p.get_controller().get_control_rotation().yaw if p.get_controller() else None,'forward':self.vector(p.get_actor_forward_vector()),'movement_mode':str(p.character_movement.movement_mode),'mantling':bool(self.prop(p,'traversal','bMantling')),'climbing':bool(self.prop(p,'traversal','bClimbing'))}
  record={'id':pid,'label':label,'phase':self.phase,'server':state(pawn),'owner':state(owner),'can_start_traversal_flight':bool(traversal.call_method('CanStartTraversalFlight'))}
  # Mirror saved Blueprint TraceTypeQuery1, trace-complex default false, and
  # ignore only the component's owning pawn; other actors remain valid blockers.
  def trace(start,end,capsule=False):
   if capsule:hit=ue.SystemLibrary.capsule_trace_single(self.server,start,end,43.,95.,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],ue.DrawDebugTrace.NONE,True)
   else:hit=ue.SystemLibrary.line_trace_single(self.server,start,end,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[pawn],ue.DrawDebugTrace.NONE,True)
   data=hit.to_dict() if hit else {}
   out={'blocked':bool(hit),'start':self.vector(start),'end':self.vector(end),'trace_complex':False,'ignored_actor':pawn.get_path_name()}
   for key in ('location','impact_point','normal','impact_normal'):
    if key in data:out[key]=self.vector(data[key])
   return out,data
  start=pawn.get_actor_location();forward=pawn.get_actor_forward_vector()
  floor,floor_data=trace(start+ue.Vector(0,0,20),start-ue.Vector(0,0,300))
  climbing=record['server']['climbing'];normal=floor_data.get('normal');location=floor_data.get('location',floor_data.get('impact_point'))
  floor_ok=bool(floor['blocked'] and normal is not None and normal.z>=.7)
  base=start.z-96 if climbing else (location.z if location is not None else None)
  record.update({'floor':floor,'floor_walkable':floor_ok,'climb_floor_bypass':climbing,'base_z':base})
  if base is None:
   record['predicates']={'flight_guard':record['can_start_traversal_flight'],'not_already_mantling':not record['server']['mantling'],'floor_or_climb':False}
   record['failed_predicates']=[k for k,v in record['predicates'].items() if not v]
  if base is not None:
   front_start=ue.Vector(start.x,start.y,base+50);ahead=start+forward*160
   front,_=trace(front_start,front_start+forward*180)
   top,top_data=trace(ue.Vector(ahead.x,ahead.y,base+300),ue.Vector(ahead.x,ahead.y,base+5))
   top_location=top_data.get('location',top_data.get('impact_point'));top_normal=top_data.get('normal')
   height=top_location.z-base if top_location is not None else None
   top_ok=bool(top['blocked'] and height is not None and 100<=height<=200 and top_normal is not None and top_normal.z>=.7)
   record.update({'front':front,'top':top,'ledge_height':height,'top_height_normal_valid':top_ok})
   if top_location is not None:
    destination=top_location+ue.Vector(0,0,100);clearance,_=trace(destination,destination+ue.Vector(0,0,1),True)
    record['clearance']=clearance
   predicates={'flight_guard':record['can_start_traversal_flight'],'not_already_mantling':not record['server']['mantling'],'floor_or_climb':climbing or floor_ok,'front_blocked':front['blocked'],'top_height_normal':top_ok,'clearance_clear':not record.get('clearance',{'blocked':True})['blocked']}
   record['predicates']=predicates;record['failed_predicates']=[k for k,v in predicates.items() if not v]
  self.diagnostics.append(record)
  return record
 def aim_yaw(self,pid,yaw):
  self.locals[pid].get_controller().set_control_rotation(ue.Rotator(yaw=float(yaw)))
  data=self.aim_fixtures.setdefault(pid,{'kind':'controller yaw steering fixture, not physical look input','initial_yaw':float(yaw),'updates':0})
  data['updates']+=1;data['last_yaw']=float(yaw)
 def actor_peer(self,world,actor):
  if world==self.server:return actor
  peers=[a for a in ue.GameplayStatics.get_all_actors_of_class(world,actor.get_class()) if a.get_name()==actor.get_name()];assert len(peers)==1
  return peers[0]
 def round(self):
  s=ue.GameplayStatics.get_game_state(self.server).get_editor_property('RoundState')
  return {'index':s.get_editor_property('Index_11_91104438409472A6DD374BADC8DC29B1'),'attempt':s.get_editor_property('Attempt_12_246832B34F4E147660E8729696BDD44A'),'phase':int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)',s.export_text())[1])}
 def snapshot(self):
  return [{'world':w.get_name(),'players':[{'id':p.player_state.player_id,'slot':int(p.player_state.get_editor_property('ColorSlot')),'owner':p.is_locally_controlled(),'dead':bool(self.prop(p,'health','bDead')),'position':[p.get_actor_location().x,p.get_actor_location().y,p.get_actor_location().z],'heavy':bool(p.call_method('IsCarryingHeavy'))} for p in self.pawns(w)]} for w in self.worlds]
 def check(self,name,details=None):self.checks.append({'name':name,'details':details,'snapshot':self.snapshot()})
 def finish(self,passed,error=None):
  if self.finished:return
  self.finished=True
  try:self.release_all()
  except Exception as cleanup_error:
   passed=False;error=(error or '')+'\nInput release failed: '+str(cleanup_error)
  if hasattr(self,'handle'):ue.unregister_slate_post_tick_callback(self.handle)
  try:final_snapshot=self.snapshot()
  except Exception as snapshot_error:final_snapshot={'unavailable':str(snapshot_error)}
  evidence={'passed':bool(passed),'error':error,'phase':self.phase,'players':self.n,'profile':self.profile,'checks':self.checks,'fixtures':self.fixtures,'aim_fixtures':self.aim_fixtures,'final_snapshot':final_snapshot,'worlds':self.world_inventory,'pie_settings':self.settings,'actions':ACTION_PATHS,'method':'Real owning Enhanced Input and Blueprint/RPC path; documented actor ownership/roster checks, no NetDriver reflection.','physical_keyboard_gamepad':False,'visual_audio_acceptance':False,'packet_emulation':False,'mac':False}
  evidence.update({'input_sha256':self.input_hashes,'fixture_settle':self.fixture_settle_evidence,'mantle_diagnostics':self.diagnostics,'motion_evidence':self.motion_evidence,'diagnostic_trace_scope':'Read-only mirrors of saved server mantle predicates; sampled around input attempts, not a replacement for gameplay execution.'})
  self.report.write_text(json.dumps(evidence,indent=2),encoding='utf-8');return evidence
 def register(self,callback):
  settling=bool(self.fixture_times)
  def tick(delta):
   nonlocal settling
   try:
    assert time.monotonic()<self.deadline,'Native gate timeout in '+self.phase
    if settling:
     if not all(self.fixture_settled(pid) for pid in self.fixture_times):return
     settling=False;self.start=time.monotonic()
    for (pid,role),value in list(self.controls.items()):self.inject(pid,role,value)
    callback(delta)
   except Exception:self.finish(False,traceback.format_exc())
  self.handle=ue.register_slate_post_tick_callback(tick)
  return {'queued':str(self.report),'runtime_acceptance_pending':True}
