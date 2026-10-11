"""Runtime test helpers. Input actions are injected only through their owner.
Fixtures: server approach teleports, ApplyDamage, released-physics settling and
explicit lifecycle/disconnect setup. No helper invokes interaction or round RPCs.
"""
from pathlib import Path
import json,re,time,traceback
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game')
QUEUE=ROOT/'Saved/SixRound';QUEUE.mkdir(parents=True,exist_ok=True)
LAYOUT=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
I='Index_11_91104438409472A6DD374BADC8DC29B1';A='Attempt_12_246832B34F4E147660E8729696BDD44A';T='PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350';R='ScalingRow_14_43C74C304230A92B6620E1A520A230C0'
class Runtime:
 def __init__(self,expected=None,profile=None):
  self.C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();self.H=ue.load_asset('/Game/Hazards/AC_Health').generated_class();self.CARRY=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();self.TOOLS=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
  self.library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary');assert self.library
  self.expected=expected;self.profile=profile;assert profile in (None,'joining','host_split')
  self.players=[];self.locals={};self.subsystems={};self.world_inventory=[]
  assert self.refresh(),'Wait for a complete possessed network roster before starting the suite'
  self.expected=self.expected or len(self.players);assert self.expected in (2,3,4)
 def refresh(self):
  self.worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));servers=[w for w in self.worlds if ue.GameplayStatics.get_game_mode(w)]
  if len(servers)!=1:return False
  self.server=servers[0];self.gs=ue.GameplayStatics.get_game_state(self.server)
  if not self.gs:return False
  candidates=ue.GameplayStatics.get_all_actors_of_class(self.server,self.C)
  # Incomplete possession/replication during travel is readiness, not a failure.
  if not candidates or any(not p.player_state for p in candidates):return False
  players=sorted(candidates,key=lambda p:p.player_state.get_editor_property('ColorSlot'))
  ids=[p.player_state.player_id for p in players];slots=[p.player_state.get_editor_property('ColorSlot') for p in players]
  if len(set(ids))!=len(ids) or len(set(slots))!=len(slots) or any(not 0<=slot<=3 for slot in slots):return False
  locals_={};subsystems={};inventory=[]
  if len(self.worlds)<2:return False
  for world in self.worlds:
   assert not ue.SystemLibrary.is_standalone(world),'A standalone fixture cannot certify online transactions'
   assert ue.SystemLibrary.is_server(world)==(world==self.server),'Expected exactly one authoritative multiplayer server'
   dedicated=ue.SystemLibrary.is_dedicated_server(world)
   assert not dedicated or world==self.server
   if world==self.server and self.profile:
    assert dedicated==(self.profile=='joining'),'Requested joining/listen profile differs from actual net mode'
   pawns=list(ue.GameplayStatics.get_all_actors_of_class(world,self.C))
   if any(not p.player_state for p in pawns):return False
   peer_ids=[p.player_state.player_id for p in pawns]
   # Distant remote proxies may legitimately be culled on clients. The server
   # remains complete; every visible peer must belong to that server roster.
   if len(set(peer_ids))!=len(peer_ids) or not set(peer_ids).issubset(set(ids)):return False
   if world==self.server and set(peer_ids)!=set(ids):return False
   expected_slots=dict(zip(ids,slots))
   if any(p.player_state.get_editor_property('ColorSlot')!=expected_slots[p.player_state.player_id] for p in pawns):return False
   owned=[p for p in pawns if p.is_locally_controlled()]
   for pawn in owned:
    pid=pawn.player_state.player_id;controller=pawn.get_controller()
    if pid in locals_ or not controller or not controller.is_local_controller() or controller.get_world()!=world:return False
    sub=self.library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
    if not sub:return False
    locals_[pid]=pawn;subsystems[pid]=sub
   inventory.append({'world':world.get_path_name(),'net_mode':'NM_Client' if world!=self.server else ('NM_DedicatedServer' if dedicated else 'NM_ListenServer'),'authoritative_player_ids':ids,'visible_player_ids':peer_ids,'local_player_ids':[p.player_state.player_id for p in owned],'controllers':[p.get_controller().get_path_name() for p in owned]})
  if set(locals_)!=set(ids) or not any(p.get_world()!=self.server for p in locals_.values()):return False
  if self.profile=='host_split' and sum(p.get_world()==self.server for p in locals_.values())!=2:return False
  self.players=players;self.locals=locals_;self.subsystems=subsystems;self.world_inventory=inventory
  return True
 def ready(self):return self.refresh() and len(self.players)==self.expected
 def mode(self):return ue.GameplayStatics.get_game_mode(self.server)
 def round(self):
  data=self.gs.get_editor_property('RoundState');phase=int(re.search(r'Phase_[^=]+=NewEnumerator(\d+)',data.export_text())[1]);return {'index':data.get_editor_property(I),'phase':phase,'attempt':data.get_editor_property(A),'ends':data.get_editor_property(T),'row':str(data.get_editor_property(R))}
 def clock(self):return self.gs.get_server_world_time_seconds()
 def map(self):return ue.GameplayStatics.get_current_level_name(self.server,True)
 def local(self,i):return self.locals[self.players[i].player_state.player_id]
 def actor(self,label,world=None):
  found=[a for a in ue.GameplayStatics.get_all_actors_of_class(world or self.server,ue.Actor) if a.get_actor_label()==label];assert len(found)==1,(label,len(found));return found[0]
 def key(self,world=None):
  matches=ue.GameplayStatics.get_all_actors_of_class(world or self.server,ue.load_asset('/Game/Puzzles/BP_KeyRelic').generated_class());assert len(matches)==1,('key actor count',len(matches));return matches[0]
 def tagged(self,tag,world=None):return ue.GameplayStatics.get_all_actors_with_tag(world or self.server,tag)
 def dead(self,i):return self.players[i].get_component_by_class(self.H).get_editor_property('bDead')
 def carried(self,i):return self.players[i].get_component_by_class(self.CARRY).get_editor_property('CarriedItem')
 def kill(self,i):
  assert not self.players[i].get_editor_property('bTakenProtected'),'Do not damage a protected taking victim'
  ue.GameplayStatics.apply_damage(self.players[i],9999,None,None,None)
 def place(self,i,pos):self.players[i].set_actor_location(ue.Vector(*pos),False,True);self.players[i].character_movement.velocity=ue.Vector()
 def inject(self,i,name,value):
  local=self.local(i);controller=local.get_controller();sub=self.library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()));assert sub
  folder='/Game/Input/Actions/' if name in ('IA_Move','IA_Jump','IA_Look') else '/Game/Core/Input/'
  action=ue.load_asset(folder+name);assert action,(folder,name)
  value=value if isinstance(value,ue.Vector) else ue.Vector(value,0,0)
  sub.inject_input_vector_for_action(action,value,[],[])
 def aim(self,i,target):
  local=self.local(i);local.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(local.get_component_by_class(ue.CameraComponent).get_world_location(),target.get_actor_location()+ue.Vector(0,0,30)))
 def focus(self,i,target):
  loc=target.get_actor_location()
  # Enter the west-wall altar alcove around the end of its decorative rail.
  if target.get_class().get_name()=='BP_Altar_C':self.place(i,(loc.x,loc.y+205,loc.z+95))
  else:self.place(i,(loc.x-205,loc.y,loc.z+95))
  self.aim(i,target)
 def focused(self,i,target):
  focus=self.local(i).get_editor_property('FocusedTarget')
  return focus is not None and focus.get_class()==target.get_class() and (focus.get_actor_location()-target.get_actor_location()).length()<80
 def alive_roster(self):return [i for i in range(len(self.players)) if not self.dead(i)]
 def assert_recovered(self,index,old_attempt=None):
  state=self.round();assert state['index']==index and state['phase']==1
  if old_attempt is not None:assert state['attempt']==old_attempt+1
  for pawn in self.players:
   health=pawn.get_component_by_class(self.H);assert not health.get_editor_property('bDead');assert health.get_editor_property('Health')==health.get_editor_property('MaxHealth')
   slot=pawn.player_state.get_editor_property('ColorSlot');expected=ue.Vector(*LAYOUT['checkpoints'][str(index)][slot]);assert (pawn.get_actor_location()-expected).length()<130,(slot,pawn.get_actor_location(),expected)
   assert pawn.get_component_by_class(self.TOOLS).get_editor_property('FlaresLeft')==(3 if self.round()['row']=='2' else 2)
 def assert_regroup(self,revived,checkpoint):
  for i in revived:
   assert not self.dead(i);health=self.players[i].get_component_by_class(self.H);assert health.get_editor_property('Health')==health.get_editor_property('MaxHealth')
   slot=self.players[i].player_state.get_editor_property('ColorSlot');expected=ue.Vector(*LAYOUT['checkpoints'][str(checkpoint)][slot]);assert (self.players[i].get_actor_location()-expected).length()<130
  for pawn in self.players:assert pawn.get_component_by_class(self.TOOLS).get_editor_property('FlaresLeft')==(3 if self.round()['row']=='2' else 2)
 def silence_occluding_small_relics(self,target):
  # Move only unrelated small relic actors out of this interaction ray, not target/state.
  moved=[]
  for item in ue.GameplayStatics.get_all_actors_of_class(self.server,ue.load_asset('/Game/Puzzles/BP_Relic').generated_class()):
   if item!=target and (item.get_actor_location()-target.get_actor_location()).length()<300:
    moved.append((item,item.get_actor_transform()));item.set_actor_location(item.get_actor_location()+ue.Vector(0,0,1000),False,True)
  return moved
 def restore_occluders(self,moved):
  for actor,transform in moved:actor.set_actor_transform(transform,False,True)
 def replicas_dead(self,pid,value):
  for world in self.worlds:
   matches=[p for p in ue.GameplayStatics.get_all_actors_of_class(world,self.C) if p.player_state and p.player_state.player_id==pid]
   assert len(matches)==1 and matches[0].get_component_by_class(self.H).get_editor_property('bDead')==value
 def cleanup_input(self):
  errors=[]
  for i in range(len(self.players)):
   for name in ('IA_Move','IA_Interact','IA_Drop','IA_Sprint','IA_ThrowFlare','IA_Climb'):
    try:self.inject(i,name,0)
    except Exception:errors.append(f'owner_index={i} action={name}\n'+traceback.format_exc())
  if errors:raise RuntimeError('\n'.join(errors))
