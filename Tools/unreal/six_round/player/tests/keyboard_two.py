"""Exercise keyboard-two controller actions before their secondary-owner bridge.
This tests both Enhanced Input layers, not physical keyboard hardware.
"""
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-keyboard-two');assert h.profile=='host_split'
host=[pid for pid in h.ids if h.locals[pid].get_world()==h.server]
primary=next(pid for pid in host if h.locals[pid].get_controller().is_primary_player())
secondary=next(pid for pid in host if not h.locals[pid].get_controller().is_primary_player())
paths={name:'/Game/Core/Input/IA_P2'+name for name in ('Brace','Forward','View','Lamp','Flare','Climb')}
actions={name:ue.load_asset(path) for name,path in paths.items()};assert all(actions.values())
values={};state={'view':h.prop(h.pawn(h.server,secondary),'view','ViewMode'),'lamp':h.prop(h.pawn(h.server,secondary),'view','bHeadlampOn'),'stock':h.prop(h.pawn(h.server,secondary),'tools','FlaresLeft'),'primary_view':h.prop(h.pawn(h.server,primary),'view','ViewMode'),'primary_lamp':h.prop(h.pawn(h.server,primary),'view','bHeadlampOn')}
assert all(pawn.call_method('CanAcceptSixInput') and not pawn.call_method('IsCarryingHeavy') for pawn in h.server_pawns)
def prefix(name,value):
 h.subsystems[primary].inject_input_vector_for_action(actions[name],ue.Vector(float(value),0,0),[],[])
def hold(name):values[name]=1
def release(name):values.pop(name,None);prefix(name,0)
def release_prefixes():
 for name in actions:release(name)
h.cleanup.append(release_prefixes)
def check_others():
 for world in h.worlds:
  assert h.prop(h.pawn(world,primary),'view','ViewMode')==state['primary_view']
  assert h.prop(h.pawn(world,primary),'view','bHeadlampOn')==state['primary_lamp']
  assert not h.prop(h.pawn(world,primary),'traversal','bSprinting')
def tick(delta):
 for name,value in values.items():prefix(name,value)
 elapsed=h.elapsed()
 if h.phase=='warmup' and elapsed>.8:
  hold('View');hold('Lamp');h.transition('toggle')
 elif h.phase=='toggle':
  if elapsed>.15:release('View');release('Lamp')
  if elapsed>1:
   for world in h.worlds:
    assert h.prop(h.pawn(world,secondary),'view','ViewMode')!=state['view']
    assert h.prop(h.pawn(world,secondary),'view','bHeadlampOn')!=state['lamp']
   check_others();h.check('host primaryP2 C/H action events changed only the resolved secondary owner')
   hold('Brace');hold('Forward');state['start']=h.pawn(h.server,secondary).get_actor_location();h.transition('sprint')
 elif h.phase=='sprint':
  if elapsed>.45:release('Forward')
  if elapsed>1:
   for world in h.worlds:assert h.prop(h.pawn(world,secondary),'traversal','bSprinting')
   assert (h.pawn(h.server,secondary).get_actor_location()-state['start']).length()>50
   check_others();h.check('RightShift prefix now injects secondaryIA_Sprint and Up moves only that owner')
   release('Brace');hold('Flare');h.transition('flare')
 elif h.phase=='flare':
  if elapsed>.15:release('Flare')
  if elapsed>1:
   for world in h.worlds:
    assert not h.prop(h.pawn(world,secondary),'traversal','bSprinting')
    assert h.prop(h.pawn(world,secondary),'tools','FlaresLeft')==state['stock']-1
   h.check('RightAlt prefix reaches secondary native flare input and spends exactly one')
   assert 'approach' in ARGS and 'climb_actor_label' in ARGS
   h.fixture_place(secondary,ARGS['approach']);h.transition('climb_approach')
 elif h.phase=='climb_approach' and elapsed>.8:
  volumes=[a for a in ue.GameplayStatics.get_all_actors_with_tag(h.server,'Climbable') if a.get_actor_label()==ARGS['climb_actor_label']]
  assert len(volumes)==1 and volumes[0] in h.pawn(h.server,secondary).get_overlapping_actors(ue.Actor)
  state['start_z']=h.pawn(h.server,secondary).get_actor_location().z;hold('Climb');h.transition('climb')
 elif h.phase=='climb' and elapsed>.8:
  for world in h.worlds:
   assert h.prop(h.pawn(world,secondary),'traversal','bClimbing')
   for other in h.ids:
    if other!=secondary:assert not h.prop(h.pawn(world,other),'traversal','bClimbing')
  assert h.pawn(h.server,secondary).get_actor_location().z-state['start_z']>80
  h.check('P prefix holds only the secondary owning native climb action')
  release('Climb');hold('View');hold('Lamp');h.transition('finish_release')
 elif h.phase=='finish_release':
  if elapsed>.15:release('View');release('Lamp')
  if elapsed>1:
   for world in h.worlds:
    assert not h.prop(h.pawn(world,secondary),'traversal','bClimbing')
    assert h.prop(h.pawn(world,secondary),'view','ViewMode')==state['view']
    assert h.prop(h.pawn(world,secondary),'view','bHeadlampOn')==state['lamp']
   h.check('prefix releases restore secondary walking/view/light without changing primary',{'first_layer_owner':primary,'resolved_secondary_owner':secondary,'prefix_actions':paths,'route':'primary subsystem -> controller keyboard handler -> secondary subsystem -> pawn input -> serverRPC'})
   h.finish(True)
RESULT=h.register(tick)

