"""Test-only round adapter. The delivered standalone door remains unchanged."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard()
PATH='/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor'
PARENT='/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor'
MESH='/Game/Puzzles/EnvironmentConnection/Art/SM_ConnectionDoor'
parent=ue.load_asset(PARENT);assert parent and ue.load_asset(MESH)
before={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(parent)}
bp=create(PATH,parent.generated_class())
assert bp.get_path_name().split('.')[0]==PATH
# These overrides keep parent BeginPlay/Tick links and actor movement replication.
for name in ('InitializeDoor','CanInteract','GetInteractInfo','OpenFromPlayer','MoveDoor'):
 existing=next((g for g in BP.list_graphs(bp) if g.get_name()==name),None)
 graph=existing or ue.BlueprintEditorLibrary.add_function_override(bp,ue.Name(name))
 assert graph,f'Native door override creation failed for {name}; never shadow the parent'
compile_bp(bp)
fn(bp,'ResetPuzzleDoor',[('Index','int'),('Attempt','int')])
write(bp,'CanInteract','(return false)','Instigator')
write(bp,'GetInteractInfo','(return "Solve the first-room plates" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))','Instigator')
write(bp,'OpenFromPlayer','','Instigator')
write(bp,'InitializeDoor',f'''
 (if (Networking|HasAuthority)
  {S('ClosedLocation','(Math|Vector|MakeVector :X 325.0 :Y 1400.0 :Z 200.0)')}
  {S('Open','false')}
  (Transformation|SetActorLocation :NewLocation {V('ClosedLocation')} :bSweep false :bTeleport true))''')
write(bp,'MoveDoor',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('Open',f'(or (>= index 6) (and (== index 1) {EQ("phase",CLEAR)}))')}
   (bind target (+ {V('ClosedLocation')} (Math|Vector|MakeVector :Z (select {V('Open')} 450.0 0.0))))
   (bind next (Math|Interpolation|VInterptoConstant :Current (Transformation|GetActorLocation) :Target target :DeltaTime DeltaSeconds :InterpSpeed 600.0))
   (Transformation|SetActorLocation :NewLocation next :bSweep false :bTeleport true)) (:CastFailed)))''','DeltaSeconds')
write(bp,'ResetPuzzleDoor',f'''
 (if (Networking|HasAuthority)
  {S('Open','(>= Index 6)')}
  (Transformation|SetActorLocation :NewLocation (+ {V('ClosedLocation')} (Math|Vector|MakeVector :Z (select {V('Open')} 450.0 0.0))) :bSweep false :bTeleport true))''','Index Attempt')
# Parent inherits the interaction/reset interface from the delivered objective basis.
# Primary must inspect inherited BPI_RoundReset; add via Class Settings if absent.
event(bp,'ResetForRound','ResetPuzzleDoor',['Index','Attempt'])
cdo=BP.get_default_object(bp);cdo.set_editor_properties({'replicates':True,'replicate_movement':True,'always_relevant':True})
mesh=cdo.static_mesh_component;assert mesh.get_outer()==cdo,'Refuse editing a parent-owned component template'
mesh.set_static_mesh(ue.load_asset(MESH));mesh.set_mobility(ue.ComponentMobility.MOVABLE);mesh.set_collision_profile_name('BlockAll');mesh.set_simulate_physics(False);mesh.set_enable_gravity(False)
save(bp)
assert {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(parent)}==before,'Standalone door graph changed'
RESULT={'writes':[PATH],'parent_read_only':PARENT,'mesh_read_only':MESH,'closed_root':[325,1400,200],'open_root':[325,1400,650],'manual_interact_allowed':False,'round_policy':'Round1 Cleared or Round6 opens; all other phases close','inherited_reset_interface_inspection_required':True,'runtime_acceptance_pending':True}
