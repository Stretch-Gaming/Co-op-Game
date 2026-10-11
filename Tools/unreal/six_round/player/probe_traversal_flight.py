"""Focused server boundary fixture, not owning input/network acceptance.

Primary runs on an idle empty-handed living pawn in PIE with explicit player_id.
Movement fixture state is restored even if an assertion fails.
"""
import json
import unreal as ue
assert 'player_id' in ARGS,'Select an explicit idle test player_id'
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
T=ue.load_asset('/Game/Player/AC_Traversal').generated_class()
matches=[p for p in ue.GameplayStatics.get_all_actors_of_class(server,C) if p.player_state.player_id==ARGS['player_id']]
assert len(matches)==1
pawn=matches[0];traversal=pawn.get_component_by_class(T);movement=pawn.character_movement
assert traversal.call_method('CanTraverse'),'Fixture requires alive, unprotected, empty-handed pawn'
assert not pawn.call_method('IsCarryingHeavy')
fields=['bSprinting','bClimbing','bMantling','bTraversalFlightApplied','ClimbForwardInput']
original={field:traversal.get_editor_property(field) for field in fields}
mode=movement.movement_mode;walk=movement.max_walk_speed;fly=movement.max_fly_speed
checks=[]
try:
 for field in fields:traversal.set_editor_property(field,0.0 if field=='ClimbForwardInput' else False)
 movement.set_movement_mode(ue.MovementMode.MOVE_FLYING)
 movement.max_walk_speed=321.0
 traversal.call_method('ApplyTraversal')
 assert movement.movement_mode==ue.MovementMode.MOVE_FLYING
 assert movement.max_walk_speed==321.0
 assert not traversal.get_editor_property('bTraversalFlightApplied')
 for request in ('SprintOnServer','ClimbOnServer','MantleOnServer'):traversal.call_method(request)
 assert not traversal.get_editor_property('bSprinting')
 assert not traversal.get_editor_property('bClimbing')
 assert not traversal.get_editor_property('bMantling')
 assert movement.movement_mode==ue.MovementMode.MOVE_FLYING
 checks.append('foreign zipline-style flight and walk speed survive refresh and traversal requests')
 pawn.call_method('SetTakingProtected',args=(True,))
 traversal.set_editor_property('bTraversalFlightApplied',True)
 movement.set_movement_mode(ue.MovementMode.MOVE_NONE)
 restricted_walk=movement.max_walk_speed
 traversal.call_method('ApplyTraversal')
 assert movement.movement_mode==ue.MovementMode.MOVE_NONE
 assert movement.max_walk_speed==restricted_walk
 assert not traversal.get_editor_property('bTraversalFlightApplied')
 checks.append('protected MOVE_None survives owned-flight cleanup; cleanup does not force500 speed')
 pawn.call_method('SetTakingProtected',args=(False,))
 traversal.set_editor_property('bTraversalFlightApplied',True)
 movement.set_movement_mode(ue.MovementMode.MOVE_FLYING)
 traversal.call_method('StopClimbOnServer')
 assert movement.movement_mode==ue.MovementMode.MOVE_FALLING
 assert not traversal.get_editor_property('bTraversalFlightApplied')
 checks.append('an ended traversal-owned climb restores falling for a living unprotected pawn')
finally:
 pawn.call_method('SetTakingProtected',args=(False,))
 for field,value in original.items():traversal.set_editor_property(field,value)
 movement.set_movement_mode(mode)
 movement.max_walk_speed=walk;movement.max_fly_speed=fly
report={'passed':True,'scope':'server fixture boundaries only; no input, latency or real zipline geometry gate','checks':checks,'player_id':ARGS['player_id']}
(QUEUE/'traversal-flight-probe.json').write_text(json.dumps(report,indent=2))
RESULT=report
