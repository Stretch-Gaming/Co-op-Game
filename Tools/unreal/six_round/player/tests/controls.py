"""Every owning local player drives view/lamp/sprint/move/flare input in turn."""
import sys,time
import unreal as ue
from pathlib import Path
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-owner-controls');cursor={'index':0};baseline={}
if ARGS.get('approaches'):
 assert len(ARGS['approaches'])==len(h.ids)
 for pid,position in zip(h.ids,ARGS['approaches']):
  h.fixture_place(pid,position)
  h.locals[pid].get_controller().set_control_rotation(ue.Rotator(yaw=0))
def capture():
 return {pid:{'view':h.prop(h.pawn(h.server,pid),'view','ViewMode'),'lamp':h.prop(h.pawn(h.server,pid),'view','bHeadlampOn'),'flares':h.prop(h.pawn(h.server,pid),'tools','FlaresLeft'),'position':h.pawn(h.server,pid).get_actor_location()} for pid in h.ids}
def unchanged_others(pid,fields):
 for world in h.worlds:
  for other in h.ids:
   if other==pid:continue
   pawn=h.pawn(world,other)
   for field in fields:
    key='view' if field in ('view','lamp') else 'tools'
    prop={'view':'ViewMode','lamp':'bHeadlampOn','flares':'FlaresLeft'}[field]
    assert h.prop(pawn,key,prop)==baseline[other][field],(other,'another owner changed',field)
def tick(delta):
 pid=h.ids[cursor['index']];elapsed=h.elapsed()
 if h.phase=='warmup' and elapsed>1:
  for owner in h.ids:
   pawn=h.pawn(h.server,owner);assert pawn.call_method('CanAcceptSixInput')
   assert not pawn.call_method('IsCarryingHeavy')
  baseline.update(capture());h.hold(pid,'view');h.hold(pid,'lamp');h.transition('toggle')
 elif h.phase=='toggle':
  if elapsed>.15:h.release(pid,'view');h.release(pid,'lamp')
  if elapsed>1:
   for world in h.worlds:
    pawn=h.pawn(world,pid)
    assert h.prop(pawn,'view','ViewMode')==(1 if baseline[pid]['view']==0 else 0)
    assert h.prop(pawn,'view','bHeadlampOn')!=baseline[pid]['lamp']
   unchanged_others(pid,('view','lamp'))
   h.check('owner viewV and headlampF actions reached server and every peer without changing another owner',{'player_id':pid})
   h.hold(pid,'sprint');h.hold(pid,'move',ue.Vector(0,1,0));h.transition('sprint')
 elif h.phase=='sprint':
  if elapsed>.45:h.release(pid,'move')
  if elapsed>1:
   for world in h.worlds:
    pawn=h.pawn(world,pid);assert h.prop(pawn,'traversal','bSprinting')
    assert abs(pawn.character_movement.max_walk_speed-h.prop(pawn,'traversal','SprintSpeed'))<1
    for other in h.ids:
     if other!=pid:assert not h.prop(h.pawn(world,other),'traversal','bSprinting')
   assert (h.pawn(h.server,pid).get_actor_location()-baseline[pid]['position']).length()>50,'Native move axis must move the sprinting owner'
   for other in h.ids:
    if other!=pid:assert (h.pawn(h.server,other).get_actor_location()-baseline[other]['position']).length()<30,'Another local player moved with the tested input'
   h.check('held sprint and move input changed only the owner, with replicated sprint speed',{'player_id':pid})
   h.release(pid,'sprint');h.transition('sprint_release')
 elif h.phase=='sprint_release' and elapsed>1:
  for world in h.worlds:
   pawn=h.pawn(world,pid);assert not h.prop(pawn,'traversal','bSprinting')
   assert abs(pawn.character_movement.max_walk_speed-h.prop(pawn,'traversal','WalkSpeed'))<1
  h.check('sprint release restored walking on every peer',{'player_id':pid})
  h.hold(pid,'flare');h.transition('flare')
 elif h.phase=='flare':
  if elapsed>.15:h.release(pid,'flare')
  if elapsed>1:
   for world in h.worlds:
    assert h.prop(h.pawn(world,pid),'tools','FlaresLeft')==baseline[pid]['flares']-1
    flares=ue.GameplayStatics.get_all_actors_of_class(world,h.classes['flare'])
    assert any(flare.get_owner() and flare.get_owner().player_state.player_id==pid for flare in flares),'Thrown flare owner must replicate'
   unchanged_others(pid,('flares',));h.check('one Q action spent exactly one owner flare and spawned its replicated flare',{'player_id':pid})
   h.hold(pid,'view');h.hold(pid,'lamp');h.transition('restore_toggle')
 elif h.phase=='restore_toggle':
  if elapsed>.15:h.release(pid,'view');h.release(pid,'lamp')
  if elapsed>1:
   for world in h.worlds:
    assert h.prop(h.pawn(world,pid),'view','ViewMode')==baseline[pid]['view']
    assert h.prop(h.pawn(world,pid),'view','bHeadlampOn')==baseline[pid]['lamp']
   cursor['index']+=1
   if cursor['index']==h.n:h.finish(True)
   else:
    baseline.clear();baseline.update(capture());h.transition('warmup')
RESULT=h.register(tick)

