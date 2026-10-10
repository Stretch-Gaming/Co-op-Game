"""Native continuous lever leases, range cancellation, pickup and latch gate."""
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-cage');assert h.round()['index']==5 and h.round()['phase']==1
assert all(not h.prop(p,'health','bDead') for p in h.server_pawns)
cages=ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['cage']);assert len(cages)==1
cage=cages[0];assert not cage.call_method('IsRaised') and not cage.get_editor_property('bLatched')
levers=sorted(ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['lever']),key=lambda a:a.get_actor_location().x)
required=2 if h.n==4 else 1;assert len(levers)>=required
holders=h.ids[:required];carrier=h.ids[-1]
keys=[a for a in ue.GameplayStatics.get_all_actors_with_tag(h.server,'Relic') if a.get_class().get_name()=='BP_KeyRelic_C'];assert len(keys)==1
key=keys[0]
for pid,lever in zip(holders,levers):h.focus(pid,lever)
h.focus(carrier,key);h.transition('focus')
def raised_everywhere(value):
 for world in h.worlds:
  peer=ue.GameplayStatics.get_all_actors_of_class(world,h.classes['cage']);assert len(peer)==1
  assert bool(peer[0].call_method('IsRaised'))==value
def tick(delta):
 elapsed=h.elapsed()
 if h.phase=='focus' and elapsed>1:
  for pid,lever in zip(holders,levers):assert h.focused(pid,lever)
  h.hold(carrier,'interact');h.transition('closed_key')
 elif h.phase=='closed_key':
  if elapsed>.15:h.release(carrier,'interact')
  if elapsed>1:
   assert h.prop(h.pawn(h.server,carrier),'carry','CarriedItem') is None
   assert h.round()['index']==5 and not cage.call_method('IsRaised')
   h.check('native key use cannot lift the relic while the cage is closed')
   h.hold(holders[0],'interact');h.transition('first_hold')
 elif h.phase=='first_hold' and elapsed>1:
  assert levers[0].call_method('IsHeld')
  raised_everywhere(required==1)
  h.check('one continuous native holder obeys the roster lever count',{'required':required})
  if required==2:h.hold(holders[1],'interact')
  h.transition('all_hold')
 elif h.phase=='all_hold' and elapsed>1:
  raised_everywhere(True)
  assert all(lever.call_method('IsHeld') for lever in levers[:required])
  h.check('all required living native lever holders raise the replicated cage')
  moved=holders[0];pos=levers[0].get_actor_location()
  h.aims.pop(moved,None);h.fixture_place(moved,(pos.x+700,pos.y,pos.z+100));h.transition('range_cancel')
 elif h.phase=='range_cancel' and elapsed>.8:
  assert not levers[0].call_method('IsHeld')
  raised_everywhere(False)
  h.check('server range validation cancels a held native lease and immediately lowers the cage')
  h.release(holders[0],'interact');h.focus(holders[0],levers[0]);h.transition('refocus')
 elif h.phase=='refocus' and elapsed>1:
  assert h.focused(holders[0],levers[0])
  h.hold(holders[0],'interact');h.transition('rehold')
 elif h.phase=='rehold' and elapsed>1:
  raised_everywhere(True)
  assert h.focused(carrier,key),'Raised cage must expose the normal key interaction trace'
  h.hold(carrier,'interact');h.transition('pickup')
 elif h.phase=='pickup':
  if elapsed>.15:h.release(carrier,'interact')
  if elapsed>1:
   assert h.prop(h.pawn(h.server,carrier),'carry','CarriedItem')==key
   assert h.round()['index']==6 and h.round()['phase']==1
   for world in h.worlds:
    peer_cage=ue.GameplayStatics.get_all_actors_of_class(world,h.classes['cage'])[0]
    assert peer_cage.get_editor_property('bLatched') and peer_cage.call_method('IsRaised')
   for pid in holders:h.release(pid,'interact')
   h.transition('latched_release')
 elif h.phase=='latched_release' and elapsed>1:
  raised_everywhere(True)
  assert all(not lever.call_method('IsHeld') for lever in levers[:required])
  h.check('native first pickup alone starts escape; cage latches after every holder releases',{'carrier_id':carrier})
  h.finish(True)
RESULT=h.register(tick)

