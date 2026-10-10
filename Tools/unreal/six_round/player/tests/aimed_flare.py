"""Owning Q at -60/-90 degrees, stock isolation, native burn and cleanup.

ARGS players=2/3/4, profile=joining/host_split, player_id actual input owner,
approach=[x,y,capsule_center_z] on a known clear floor, yaw=0, timeout>=35.
Fresh quiet Lobby, living empty-handed owner with at least two flares; no other
test/input callback or throws. Initial placement and controller aim are fixtures.
No direct spawn, inventory/state setter, interaction/round/RPC shortcut.
"""
import hashlib,json,sys,time
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
BaseHarness=load_harness()

evidence={'attempts':[],'burn_observations':[],'prerequisites':__doc__}
class FlareHarness(BaseHarness):
 def finish(self,passed,error=None):
  if self.finished:return
  result=super().finish(passed,error)
  result['aimed_flare']=evidence
  self.report.write_text(json.dumps(result,indent=2))
  return result

h=FlareHarness(ARGS,'pg-aimed-flare')
assert float(ARGS.get('timeout',90))>=35,'Burn-duration gate needs at least thirty-five seconds'
assert 'player_id' in ARGS and ARGS['player_id'] in h.ids,'Choose an actual input owner explicitly'
assert 'approach' in ARGS and len(ARGS['approach'])==3,'Known clear-floor approach is required'
pid=ARGS['player_id'];server_pawn=h.pawn(h.server,pid);owner=h.locals[pid]
assert server_pawn.call_method('CanAcceptSixInput') and not server_pawn.call_method('IsCarryingHeavy')
assert not h.prop(server_pawn,'health','bDead') and not server_pawn.get_editor_property('bTakenProtected')
baseline={other:h.prop(h.pawn(h.server,other),'tools','FlaresLeft') for other in h.ids}
assert baseline[pid]>=2,'Two genuine throws require two existing flares; never refill through a fixture'
root=Path(ue.Paths.project_dir()).resolve()
files=[Path(__file__),Path(__file__).with_name('common.py'),Path(__file__).with_name('pg_harness.py'),root/'Tools/unreal/six_round/player/tools.py',root/'Tools/unreal/six_round/fix_flare_spawn.py',root/'Content/Core/BP_CoopCharacter.uasset',root/'Content/Player/Tools/AC_Tools.uasset',root/'Content/Player/Tools/BP_Flare.uasset']
evidence.update({'source_asset_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'method':'Initial approach and owning-controller aim fixtures; genuine .2s Q pulses through the owning Enhanced Input subsystem. Native IsActive and ownership queries only.','irrelevant_remote_proxy_presence_required':False,'ghost_glow_acceptance':False,'spawn_collision_log_review_pending_primary':True})

def vector(value):return [value.x,value.y,value.z]
def owned_flares(world):
 return [a for a in ue.GameplayStatics.get_all_actors_of_class(world,h.classes['flare']) if a.get_owner() and a.get_owner().player_state and a.get_owner().player_state.player_id==pid]
assert not owned_flares(h.server),'Start after this owner previous flares have expired'
h.fixture_place(pid,ARGS['approach'])
state={'attempt':0,'pitch':-60.,'actors':[],'lights':[],'names':set(),'near_end_recorded':False}
def set_aim():
 owner.get_controller().set_control_rotation(ue.Rotator(pitch=state['pitch'],yaw=float(ARGS.get('yaw',0))))
set_aim();h.fixtures.append({'kind':'owning controller aim fixture','player_id':pid,'pitch':-60.,'yaw':ARGS.get('yaw',0)})
def angle_distance(a,b):return abs((a-b+180)%360-180)
def stock_isolated(expected):
 for world in h.worlds:
  # Native relevance can cull unrelated teammates; all visible proxies must agree.
  for pawn in h.pawns(world):
   other=pawn.player_state.player_id
   assert h.prop(pawn,'tools','FlaresLeft')==(expected if other==pid else baseline[other]),(world.get_path_name(),other,'wrong owner stock')
 for other in h.ids:
  assert h.prop(h.locals[other],'tools','FlaresLeft')==(expected if other==pid else baseline[other])
def capture_actor(actor):
 mesh=actor.get_component_by_class(ue.StaticMeshComponent);assert mesh
 ignored=mesh.copy_array_of_move_ignore_actors()
 assert actor.get_owner() in ignored,'Flare moving root must ignore its owner'
 lights=actor.get_components_by_class(ue.PointLightComponent);assert lights
 assert any(light.intensity>0 for light in lights),'Active flare attached light must emit'
 return {'name':actor.get_name(),'position':vector(actor.get_actor_location()),'owner_id':actor.get_owner().player_state.player_id,'active':bool(actor.call_method('IsActive')),'burn_seconds':actor.get_editor_property('BurnSeconds'),'moving_root':mesh.get_name(),'moving_root_ignored_actors':[a.get_name() for a in ignored],'light_intensity':[light.intensity for light in lights]},lights

def tick(delta):
 elapsed=h.elapsed()
 if h.phase=='warmup' or h.phase=='aim_settle':
  set_aim()
  local_pos=owner.get_actor_location();server_pos=server_pawn.get_actor_location()
  local_aim=owner.get_base_aim_rotation();server_aim=server_pawn.get_base_aim_rotation()
  if elapsed>=.8 and (local_pos-server_pos).length()<=30 and angle_distance(local_aim.pitch,state['pitch'])<=3 and angle_distance(server_aim.pitch,state['pitch'])<=3 and angle_distance(local_aim.yaw,server_aim.yaw)<=3:
   eye,eye_rotation=server_pawn.get_actor_eyes_view_point()
   evidence['attempts'].append({'pitch':state['pitch'],'owner_position':vector(local_pos),'server_position':vector(server_pos),'server_eye':vector(eye),'server_eye_rotation':{'pitch':eye_rotation.pitch,'yaw':eye_rotation.yaw},'owner_aim':{'pitch':local_aim.pitch,'yaw':local_aim.yaw},'server_aim':{'pitch':server_aim.pitch,'yaw':server_aim.yaw},'settle_seconds':elapsed,'input_pulse_seconds':.2})
   h.hold(pid,'flare');h.transition('Q_pulse')
 elif h.phase=='Q_pulse':
  if elapsed>=.2:h.release(pid,'flare');h.transition('spawn_replicate')
 elif h.phase=='spawn_replicate' and elapsed>=.8:
  stock_isolated(baseline[pid]-state['attempt']-1)
  owned=owned_flares(h.server);new=[a for a in owned if a.get_name() not in state['names']]
  assert len(new)==1 and len(owned)==state['attempt']+1,'One Q pulse must create exactly one owner flare'
  actor=new[0];record,lights=capture_actor(actor);assert record['active'] and abs(record['burn_seconds']-20)<.1
  peer=h.actor_peer(owner.get_world(),actor);assert peer.get_owner() and peer.get_owner().player_state.player_id==pid
  assert peer.call_method('IsActive'),'Owning client must see its active flare'
  state['actors'].append(actor);state['lights'].extend(lights);state['names'].add(actor.get_name())
  evidence['attempts'][-1]['spawn']=record
  h.check('downward Q creates one replicated owner flare and spends exactly one stock',{'player_id':pid,'pitch':state['pitch'],'spawn':record})
  state['attempt']+=1
  if state['attempt']==1:
   state['pitch']=-90.;set_aim();h.fixtures.append({'kind':'owning controller aim fixture','player_id':pid,'pitch':-90.,'yaw':ARGS.get('yaw',0)});h.transition('aim_settle')
  else:
   second=state['actors'][-1];state['second_name']=second.get_name();state['burn_start']=second.get_editor_property('BurnStarted');h.transition('burn_watch')
 elif h.phase=='burn_watch':
  age=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()-state['burn_start']
  second=next((a for a in owned_flares(h.server) if a.get_name()==state['second_name']),None)
  if 18.5<=age<19.5 and not state['near_end_recorded']:
   assert second and second.call_method('IsActive'),'Second flare must still burn near twenty seconds'
   peer=h.actor_peer(owner.get_world(),second);assert peer.call_method('IsActive')
   assert any(light.intensity>0 for light in second.get_components_by_class(ue.PointLightComponent))
   evidence['burn_observations'].append({'age_seconds':age,'server_active':True,'owner_active':True});state['near_end_recorded']=True
  if age>=21.:
   assert state['near_end_recorded'],'Near-end burn observation was missed; do not infer it from cleanup'
   for world in (h.server,owner.get_world()):
    assert not any(a.get_name() in state['names'] for a in ue.GameplayStatics.get_all_actors_of_class(world,h.classes['flare'])),'Expired actor remains in authoritative or owning world'
   assert all(not ue.SystemLibrary.is_valid(light) for light in state['lights']),'Expired actor attached server light remains valid'
   stock_isolated(baseline[pid]-2)
   h.check('flare remains active near twenty seconds then actor and attached lights expire',{'observed_cleanup_age_seconds':age,'burn_observations':evidence['burn_observations']})
   h.finish(True)
RESULT=h.register(tick)
