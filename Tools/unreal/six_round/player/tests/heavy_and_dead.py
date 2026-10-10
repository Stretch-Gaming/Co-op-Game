"""Normal statue pickup/input guards or death-fixture/spectator input gate.
ARGS case heavy/dead and explicit player_id; start in a safe Playing round.
"""
import sys,json
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-'+ARGS['case']);case=ARGS['case'];assert case in ('heavy','dead')
pid=ARGS['player_id'];assert pid in h.ids
server_pawn=h.pawn(h.server,pid);owner=h.locals[pid]
assert h.round()['phase']==1,'Start a safe Playing round before this gate'
assert all(not h.prop(p,'health','bDead') for p in h.server_pawns)
state={'stock':h.prop(server_pawn,'tools','FlaresLeft'),'lamp':h.prop(server_pawn,'view','bHeadlampOn')}
if case=='heavy':
 matches=[actor for actor in ue.GameplayStatics.get_all_actors_of_class(h.server,ue.Actor) if actor.get_actor_label()==ARGS['heavy_actor_label']]
 assert len(matches)==1,'Select an actual heavy statue by actor label'
 state['item']=matches[0];assert state['item'].get_editor_property('bHeavy')
 h.focus(pid,state['item']);h.transition('focus')
else:
 assert h.round()['index'] in (2,4),'Use a stable solo-path round; Round5 must fail when too few living players remain'
 assert all(not p.get_editor_property('bTakenProtected') for p in h.server_pawns),'Wait for the taking to finish'
 ue.GameplayStatics.apply_damage(server_pawn,9999,None,None,None)
 h.fixtures.append({'kind':'lethal ApplyDamage fixture through the gameplay health event','player_id':pid})
 state['death_position']=server_pawn.get_actor_location();h.transition('dead_wait')
def tick(delta):
 elapsed=h.elapsed()
 if h.phase=='focus' and elapsed>1:
  assert h.focused(pid,state['item'])
  h.hold(pid,'interact');h.transition('pickup')
 elif h.phase=='pickup':
  if elapsed>.15:h.release(pid,'interact')
  if elapsed>1:
   assert h.prop(server_pawn,'carry','CarriedItem')==state['item']
   assert server_pawn.call_method('IsCarryingHeavy'),'Fixture must use the real heavy carry state'
   h.aims.clear();h.hold(pid,'sprint');h.hold(pid,'climb');h.hold(pid,'flare');h.hold(pid,'lamp');h.transition('heavy_guards')
 elif h.phase=='heavy_guards':
  if elapsed>.15:h.release(pid,'flare');h.release(pid,'lamp')
  if elapsed>1:
   for world in h.worlds:
    pawn=h.pawn(world,pid)
    assert pawn.call_method('IsCarryingHeavy')
    assert not h.prop(pawn,'traversal','bSprinting') and not h.prop(pawn,'traversal','bClimbing') and not h.prop(pawn,'traversal','bMantling')
    assert not h.comp(pawn,'traversal').call_method('CanTraverse')
    assert h.prop(pawn,'tools','FlaresLeft')==state['stock']
    assert h.prop(pawn,'view','bHeadlampOn')!=state['lamp'],'Heavy statue holder must retain the working headlamp'
    assert abs(pawn.character_movement.max_walk_speed-h.prop(pawn,'traversal','WalkSpeed')*.5)<1
   h.check('native statue pickup blocks sprint/climb/flare, preserves half speed and headlamp',{'player_id':pid,'item_label':ARGS['heavy_actor_label']})
   h.release(pid,'sprint');h.release(pid,'climb');h.hold(pid,'drop');h.transition('drop')
 elif h.phase=='drop':
  if elapsed>.15:h.release(pid,'drop')
  if elapsed>1:
   assert h.prop(server_pawn,'carry','CarriedItem') is None
   assert not server_pawn.call_method('IsCarryingHeavy')
   h.hold(pid,'lamp');h.transition('restore_lamp')
 elif h.phase=='restore_lamp':
  if elapsed>.15:h.release(pid,'lamp')
  if elapsed>1:
   for world in h.worlds:assert h.prop(h.pawn(world,pid),'view','bHeadlampOn')==state['lamp']
   h.check('native drop restores empty hands after the heavy guard gate');h.finish(True)
 elif h.phase=='dead_wait' and elapsed>1:
  for world in h.worlds:
   pawn=h.pawn(world,pid);assert h.prop(pawn,'health','bDead')
   assert pawn.character_movement.movement_mode==ue.MovementMode.MOVE_NONE
  target=h.prop(owner,'view','SpectatedPawn');assert target and not h.prop(target,'health','bDead')
  assert owner.get_controller().get_view_target()==target
  state['first_target']=target.player_state.player_id
  h.hold(pid,'move',ue.Vector(0,1,0));h.hold(pid,'sprint');h.hold(pid,'climb');h.hold(pid,'flare');h.hold(pid,'interact');h.transition('dead_inputs')
 elif h.phase=='dead_inputs':
  if elapsed>.15:h.release(pid,'flare');h.release(pid,'interact')
  if elapsed>1:
   assert h.round()['phase']==1,'One dead teammate must remain dead until regroup, not restart immediately'
   assert (server_pawn.get_actor_location()-state['death_position']).length()<20
   target=h.prop(owner,'view','SpectatedPawn');assert target and not h.prop(target,'health','bDead')
   if h.n>2:assert target.player_state.player_id!=state['first_target'],'Interact must select the next living teammate'
   else:assert target.player_state.player_id==state['first_target'],'With one survivor, cycle must remain bounded on that survivor'
   assert owner.get_controller().get_view_target()==target
   for world in h.worlds:
    pawn=h.pawn(world,pid);assert h.prop(pawn,'health','bDead')
    assert not h.prop(pawn,'traversal','bSprinting') and not h.prop(pawn,'traversal','bClimbing')
    assert h.prop(pawn,'tools','FlaresLeft')==state['stock']
   for other in h.ids:
    if other!=pid:
     living_owner=h.locals[other];assert living_owner.get_controller().get_view_target()==living_owner,'Dead cycling must not change another local screen'
   h.check('dead owning input cannot move/throw/revive; Interact cycles one living camera without affecting another owner',{'victim':pid,'first_target':state['first_target'],'next_target':target.player_state.player_id})
   h.finish(True)
RESULT=h.register(tick)
