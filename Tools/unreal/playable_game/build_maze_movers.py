import sys,importlib
sys.path.insert(0,str(HERE)); import authoring; importlib.reload(authoring)
from authoring import *
bp=ue.load_asset('/Game/Puzzles/Maze/BP_MazeMover')
if bp and BP.get_graph(bp,'CanPress'):write(bp,'CanPress','(return false)','PlayerPawn')
if not bp:bp=create('/Game/Puzzles/Maze/BP_MazeMover',ue.StaticMeshActor.static_class())
for name,value in [('replicates',True),('replicate_movement',True),('always_relevant',True)]:BP.get_default_object(bp).set_editor_property(name,value)
mesh=BP.get_default_object(bp).static_mesh_component
mesh.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));mesh.set_mobility(ue.ComponentMobility.MOVABLE);mesh.set_collision_profile_name('BlockAll')
for name,kind,value in [('Rest','Vector',ue.Vector()),('Active','Vector',ue.Vector()),('Plate1Center','Vector',ue.Vector()),('Plate1Extent','Vector',ue.Vector()),('Plate2Center','Vector',ue.Vector()),('Plate2Extent','Vector',ue.Vector()),('KeepCenter','Vector',ue.Vector()),('KeepExtent','Vector',ue.Vector()),('NeedsBrace','bool',False),('HasPlate2','bool',False),('HasKeepOpen','bool',False),('MoveSpeed','float',150.0)]:var(bp,name,kind,value,editable=True)
var(bp,'Pressed','bool',False,replicated=True)
fn(bp,'PawnInBox',[('PlayerPawn',ue.Character.static_class()),('Center','Vector'),('Extent','Vector')],[('Inside','bool')])
fn(bp,'CanPress',[('PlayerPawn',ue.Character.static_class())],[('Allowed','bool')])
for n in ('RefreshMover','StartMover','StopMover'):fn(bp,n)
write(bp,'PawnInBox','''
 (bind feet (- (Transformation|GetActorLocation :self PlayerPawn) (Math|Vector|MakeVector :Z (Components|Capsule|GetScaledCapsuleHalfHeight :self (Class|Character|GetCapsuleComponent :self PlayerPawn)))))
 (return (Math|Geometry|IsPointinBox :Point feet :BoxOrigin Center :BoxExtent Extent))''','PlayerPawn Center Extent')
write(bp,'CanPress',f'''
 (bind player (Utilities|Casting|CastToBP_CoopCharacter :Object PlayerPawn)
  (:then
   (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self player :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (bind downed (Class|ACHealth|IsDowned :self health)) (bind braced (Class|BPCoopCharacter|GetBracedState :self player)) (return (and (not downed) (and (Movement|IsMovingonGround :self (Class|Character|GetCharacterMovement :self player)) (or (not {V('NeedsBrace')}) braced))))) (:CastFailed (return false)))) (:CastFailed (return false)))''','PlayerPawn')
write(bp,'RefreshMover',f'''
 (if (Networking|HasAuthority)
  {S('Pressed','false')}
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (for state (Class|GameStateBase|GetPlayerArray :self gs)
     (bind player (Utilities|Casting|CastToCharacter :Object (PlayerState|GetPawn :self state))
      (:then
       (bind keeping (CallFunction|PawnInBox :PlayerPawn player :Center {V('KeepCenter')} :Extent {V('KeepExtent')}))
       (bind pressAllowed (CallFunction|CanPress :PlayerPawn player))
       (bind in1 (CallFunction|PawnInBox :PlayerPawn player :Center {V('Plate1Center')} :Extent {V('Plate1Extent')}))
       (bind in2 (CallFunction|PawnInBox :PlayerPawn player :Center {V('Plate2Center')} :Extent {V('Plate2Extent')}))
       (if (and {V('HasKeepOpen')} keeping) {S('Pressed','true')})
       (if pressAllowed
        (if (or in1 (and {V('HasPlate2')} in2)) {S('Pressed','true')}))) (:CastFailed)))
    (Transformation|SetActorLocation :NewLocation (Math|Interpolation|VInterptoConstant :Current (Transformation|GetActorLocation) :Target (select {V('Pressed')} {V('Active')} {V('Rest')}) :DeltaTime 0.05 :InterpSpeed {V('MoveSpeed')}) :bSweep false :bTeleport false)) (:CastFailed)))''')
write(bp,'StartMover','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshMover" :Time 0.05 :bLooping true))')
write(bp,'StopMover','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshMover")')
event(bp,'ReceiveBeginPlay','StartMover');event(bp,'ReceiveEndPlay','StopMover');save(bp)
RESULT={'asset':bp.get_path_name(),'compiled':True,'runtime_acceptance_pending':True}

