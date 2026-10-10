"""Native T and forward-axis climbing, followed by native jump release.
Use the actual HZ volume selected by label; initial approach is a fixture.
"""
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-climb-jump');pid=ARGS['player_id'];assert pid in h.ids
pawn=h.pawn(h.server,pid);assert pawn.call_method('CanAcceptSixInput') and not pawn.call_method('IsCarryingHeavy')
volumes=[actor for actor in ue.GameplayStatics.get_all_actors_with_tag(h.server,'Climbable') if actor.get_actor_label()==ARGS['climb_actor_label']]
assert len(volumes)==1;volume=volumes[0];box=volume.get_component_by_class(ue.BoxComponent);assert box
origin=volume.get_actor_location();extent=box.get_scaled_box_extent()
# Primary passes a verified floor approach; do not invent a floor height from bounds.
assert 'approach' in ARGS and len(ARGS['approach'])==3
h.fixture_place(pid,ARGS['approach']);state={'start_z':ARGS['approach'][2]};h.transition('overlap_settle')
def assert_climbing(expected):
 for world in h.worlds:
  assert bool(h.prop(h.pawn(world,pid),'traversal','bClimbing'))==expected
  for other in h.ids:
   if other!=pid:assert not h.prop(h.pawn(world,other),'traversal','bClimbing')
def tick(delta):
 elapsed=h.elapsed()
 if h.phase=='overlap_settle' and elapsed>1:
  assert volume in pawn.get_overlapping_actors(ue.Actor),'Approach fixture must actually overlap the authored climb volume'
  state['start_z']=pawn.get_actor_location().z;h.hold(pid,'climb');h.transition('native_t')
 elif h.phase=='native_t' and elapsed>.8:
  assert_climbing(True)
  assert pawn.get_actor_location().z-state['start_z']>80
  h.check('T owning input starts real tagged-volume climb on server and peers',{'player_id':pid,'volume':ARGS['climb_actor_label']})
  h.release(pid,'climb');h.transition('t_release')
 elif h.phase=='t_release' and elapsed>.6:
  assert_climbing(False)
  h.fixture_place(pid,ARGS['approach']);h.transition('axis_approach')
 elif h.phase=='axis_approach' and elapsed>.8:
  state['start_z']=pawn.get_actor_location().z;h.hold(pid,'move',ue.Vector(0,1,0));h.transition('native_forward')
 elif h.phase=='native_forward' and elapsed>.8:
  assert_climbing(True)
  assert pawn.get_actor_location().z-state['start_z']>80
  assert h.prop(pawn,'traversal','ClimbForwardInput')>.9,'Forward float RPC must be connected to the owning movement axis'
  h.release(pid,'move');h.transition('axis_pause')
 elif h.phase=='axis_pause' and elapsed>.4:
  assert abs(h.prop(pawn,'traversal','ClimbForwardInput'))<.01
  h.check('owning Move axis traverses the Forward float server RPC and release clears the axis')
  h.hold(pid,'jump');h.transition('jump_release')
 elif h.phase=='jump_release':
  if elapsed>.15:h.release(pid,'jump')
  if elapsed>.8:
   assert_climbing(False)
   assert not h.prop(pawn,'traversal','bMantling')
   h.check('native Jump lets go of marked climbing without affecting another owner');h.finish(True)
RESULT=h.register(tick)

