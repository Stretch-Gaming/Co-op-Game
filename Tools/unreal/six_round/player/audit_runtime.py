"""Read current settled PG invariants in PIE; root runs at each route checkpoint."""
import json
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert worlds
classes={key:ue.load_asset(path).generated_class() for key,path in {
 'pawn':'/Game/Core/BP_CoopCharacter','health':'/Game/Hazards/AC_Health',
 'traversal':'/Game/Player/AC_Traversal','tools':'/Game/Player/Tools/AC_Tools',
 'view':'/Game/Player/AC_PlayerView','cage':'/Game/Player/RelicChamber/BP_RelicCage',
 'lever':'/Game/Player/RelicChamber/BP_Lever','chase':'/Game/Player/Ghosts/BP_ChaseDirector',
 'taking':'/Game/Player/Taking/BP_TakingDirector'}.items()}
snapshots=[]
for world in worlds:
 pawns=ue.GameplayStatics.get_all_actors_of_class(world,classes['pawn']);assert len(pawns) in (2,3,4)
 authority=bool(ue.GameplayStatics.get_game_mode(world));players=[]
 for pawn in pawns:
  health=pawn.get_component_by_class(classes['health']);traversal=pawn.get_component_by_class(classes['traversal'])
  tools=pawn.get_component_by_class(classes['tools']);view=pawn.get_component_by_class(classes['view'])
  assert health and traversal and tools and view
  dead=bool(health.get_editor_property('bDead'))
  carrying=bool(pawn.call_method('GetCarryingRelic'))
  heavy=bool(pawn.call_method('IsCarryingHeavy'))
  protected=bool(pawn.call_method('GetTakenProtected'))
  sprint=bool(traversal.get_editor_property('bSprinting'));climb=bool(traversal.get_editor_property('bClimbing'));mantle=bool(traversal.get_editor_property('bMantling'))
  if dead or heavy or protected:
   assert not sprint and not climb and not mantle,(pawn.get_name(),'forbidden traversal while dead/heavy/protected')
   assert not traversal.call_method('CanTraverse')
  if dead or protected:assert not traversal.call_method('CanAct')
  flares=int(tools.get_editor_property('FlaresLeft'));assert 0<=flares<=3
  target=view.get_editor_property('SpectatedPawn')
  if pawn.is_locally_controlled():
   if dead and target:
    assert target!=pawn
    assert not target.get_component_by_class(classes['health']).get_editor_property('bDead')
    assert pawn.get_controller().get_view_target()==target,'Run after the0.2s spectator blend has settled'
   if not dead:assert pawn.get_controller().get_view_target()==pawn,'Regroup must restore the own camera'
  players.append({'id':pawn.player_state.player_id,'dead':dead,'carrying':carrying,'heavy':heavy,'protected':protected,'sprint':sprint,'climb':climb,'mantle':mantle,'flares':flares,'flight_owned':traversal.get_editor_property('bTraversalFlightApplied'),'movement_mode':str(pawn.character_movement.movement_mode),'spectated':target.player_state.player_id if target else None,'location':[pawn.get_actor_location().x,pawn.get_actor_location().y,pawn.get_actor_location().z]})
 cages=[]
 for cage in ue.GameplayStatics.get_all_actors_of_class(world,classes['cage']):
  raised=bool(cage.call_method('IsRaised'));latched=bool(cage.get_editor_property('bLatched'))
  if authority and not latched:
   held=sum(bool(lever.call_method('IsHeld')) for lever in ue.GameplayStatics.get_all_actors_of_class(world,classes['lever']))
   assert raised==(held>=cage.get_editor_property('RequiredLevers')),'Run after continuous-lease polling settles'
  cages.append({'raised':raised,'latched':latched,'required':cage.get_editor_property('RequiredLevers')})
 snapshots.append({'world':world.get_name(),'authority':authority,'players':players,'cages':cages})
report={'passed':True,'scope':'current settled state invariants only; no route/input/latency acceptance implied','snapshots':snapshots}
(QUEUE/'pg-runtime-audit.json').write_text(json.dumps(report,indent=2))
RESULT=report
