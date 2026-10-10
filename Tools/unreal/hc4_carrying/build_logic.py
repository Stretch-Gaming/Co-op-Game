import sys,pathlib,importlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
ac=unreal.load_asset('/Game/Puzzles/Carrying/AC_Carrying')
c=unreal.load_asset('/Game/Puzzles/BP_Carryable')
owned(c)
with toolset_registry.tool_raising_exceptions():
    for node in BP.find_nodes(BP.get_graph(c,'EventGraph')): BP.delete_node(node)
    for graph in BP.list_graphs(c):
        if graph.get_name() in ['TestStartRound','RecordInstant','RecordBegin','RecordEnd']:
            BP.remove_function_graph(c,graph.get_name())
for name,notify in [('CarryCrouchSpeed',True),('SavedCrouchSpeed',False)]: var(ac,name,'float',notify)
owned(ac)
with toolset_registry.tool_raising_exceptions():
    for node in BP.find_nodes(BP.get_graph(ac,'EventGraph')): BP.delete_node(node)
V=lambda n:f'(Variables|Default|Get{n})'
S=lambda n,val:f'(Variables|Default|Set{n} {val})'
OWNER='(Components|GetOwner)'
AUTH=f'(Networking|HasAuthority :self {OWNER})'

write(ac,'ApplyCarrySpeed',f'''
 (if (> {V('CarrySpeed')} 0.0)
   (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
     (:then
       (Class|CharacterMovementComponent|SetMaxWalkSpeed :self (Class|Character|GetCharacterMovement :self pawn) :MaxWalkSpeed {V('CarrySpeed')})
       (if (> {V('CarryCrouchSpeed')} 0.0)
         (Class|CharacterMovementComponent|SetMaxWalkSpeedCrouched :self (Class|Character|GetCharacterMovement :self pawn) :MaxWalkSpeedCrouched {V('CarryCrouchSpeed')})))
     (:CastFailed)))''')
write(ac,'OnRep_CarrySpeed','(CallFunction|ApplyCarrySpeed)')
write(ac,'OnRep_CarryCrouchSpeed','(CallFunction|ApplyCarrySpeed)')
write(ac,'OnRep_CarriedItem','(CallFunction|ApplyCarrySpeed)')
write(ac,'GetCarried',f'(if {AUTH} (return {V("CarriedItem")}) (else (return "None")))')
write(ac,'ClearCarried',f'''
 (if {AUTH}
   {S('CarriedItem','"None"')}
   (if {V('SpeedActive')}
     {S('CarrySpeed',V('SavedSpeed'))}
     {S('CarryCrouchSpeed',V('SavedCrouchSpeed'))}
     (CallFunction|ApplyCarrySpeed)
     {S('SpeedActive','false')}))''')
write(ac,'CanPickup',f'''
 (if {AUTH}
   (Utilities|IsValid :InputObject {V('CarriedItem')} (:"Is Valid" (return false)) (:"Is Not Valid"
     (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
       (:then
         (if (Actor|ActorHasTag :self pawn :Tag "Downed") (return false) (else
           (bind carry (Utilities|Casting|CastToBP_Carryable :Object Item)
             (:then
               (if (and (<= (Transformation|GetDistanceTo :self pawn :OtherActor carry) 250.0)
                        (Class|BPCarryable|CanClaim :self carry :Instigator pawn))
                 (bind (eye rotation) (Actor|GetActorEyesViewPoint :self pawn))
                 (bind (hit blocked) (Collision|LineTraceByChannel :Start eye :End (Transformation|GetActorLocation :self carry) :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
                 (bind (blocking overlap time distance location impact normal impactNormal material hitActor component bone myBone index element face start end) (Collision|BreakHitResult :Hit hit))
                 (return (or (not blocked) (== hitActor carry)))
                 (else (return false)))) (:CastFailed (return false))))))
       (:CastFailed (return false)))))
   (else (return false)))''','Item')
write(ac,'TryPickup',f'''
 (if (CallFunction|CanPickup :Item Item)
   (bind carry (Utilities|Casting|CastToBP_Carryable :Object Item)
     (:then
       (if (Class|BPCarryable|Claim :self carry :NewCarrier {OWNER} :NewComponent self)
         {S('CarriedItem','carry')}
         (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
           (:then
             {S('SavedSpeed','(Class|CharacterMovementComponent|GetMaxWalkSpeed :self (Class|Character|GetCharacterMovement :self pawn))')}
             {S('SavedCrouchSpeed','(Class|CharacterMovementComponent|GetMaxWalkSpeedCrouched :self (Class|Character|GetCharacterMovement :self pawn))')}
             {S('SpeedActive','true')}
             {S('CarrySpeed',f'(select (Class|BPCarryable|GetHeavy :self carry) (* {V("SavedSpeed")} 0.5) {V("SavedSpeed")})')}
             {S('CarryCrouchSpeed',f'(select (Class|BPCarryable|GetHeavy :self carry) (* {V("SavedCrouchSpeed")} 0.5) {V("SavedCrouchSpeed")})')}
             (CallFunction|ApplyCarrySpeed)
             (return true)) (:CastFailed (return false)))
         (else (return false)))) (:CastFailed (return false)))
   (else (return false)))''','Item')
write(ac,'DropCarried',f'''
 (if {AUTH}
   (bind carry (Utilities|Casting|CastToBP_Carryable :Object {V('CarriedItem')})
     (:then (Class|BPCarryable|Drop :self carry)) (:CastFailed (CallFunction|ClearCarried))))''')
write(ac,'ReleaseCarried',f'''
 (if {AUTH}
   (bind carry (Utilities|Casting|CastToBP_Carryable :Object {V('CarriedItem')})
     (:then (bind item (Class|BPCarryable|ReleaseCarried :self carry)) (return item))
     (:CastFailed (return "None")))
   (else (return "None")))''')
write(ac,'BeginCarrying','(CallFunction|ApplyCarrySpeed)')
write(ac,'EndCarrying','(CallFunction|DropCarried)')
event(ac,'ReceiveBeginPlay','BeginCarrying')
event(ac,'ReceiveEndPlay','EndCarrying')

write(c,'GetHeavy',f'(return {V("Heavy")})')
write(c,'GetCarryState',f'(return {V("CarryState")} {V("Carrier")})')
write(c,'CanClaim',f'''
 (if (and (Networking|HasAuthority) (== {V('CarryState')} 0))
   (bind pawn (Utilities|Casting|CastToCharacter :Object Instigator)
     (:then (return (not (Actor|ActorHasTag :self pawn :Tag "Downed"))))
     (:CastFailed (return false)))
   (else (return false)))''','Instigator')
write(c,'Claim',f'''
 (if (CallFunction|CanClaim :Instigator NewCarrier)
   (bind component (Utilities|Casting|CastToAC_Carrying :Object NewComponent)
     (:then
       (if (== (Components|GetOwner :self component) NewCarrier)
         {S('CarrierComponent','component')}
         {S('Carrier','NewCarrier')}
         {S('CarryState','1')}
         (CallFunction|ApplyCarryState)
         (Networking|ForceNetUpdate)
         (return true)
         (else (return false)))) (:CastFailed (return false)))
   (else (return false)))''','NewCarrier NewComponent')
write(c,'ClearCarrier',f'''
 (if (Networking|HasAuthority)
   (bind previous {V('CarrierComponent')})
   {S('Carrier','"None"')}
   (bind component (Utilities|Casting|CastToAC_Carrying :Object previous)
     (:then
       {S('CarrierComponent','"None"')}
       (Class|ACCarrying|ClearCarried :self component))
     (:CastFailed {S('CarrierComponent','"None"')})))''')
mesh='(Variables|StaticMeshActor|GetStaticMeshComponent)'
fn(c,'ApplyWeightTag')
write(c,'ApplyWeightTag',f'''
 (if (Networking|HasAuthority)
   (if (and {V('Heavy')} (!= {V('CarryState')} 1))
     (Utilities|Array|AddUnique :TargetArray (Variables|Actor|GetTags) :NewItem "HC_PlateWeight")
     (else (Utilities|Array|RemoveItem :TargetArray (Variables|Actor|GetTags) :Item "HC_PlateWeight"))))''')
fn(c,'DetachFree')
write(c,'DetachFree',f'''(if (== {V('CarryState')} 0)
 (Transformation|DetachFromActor :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld"))''')
write(c,'ApplyCarryState',f'''
 (CallFunction|ApplyWeightTag)
 (if (== {V('CarryState')} 1)
   (Physics|SetSimulatePhysics :self {mesh} :bSimulate false)
   (Collision|SetCollisionEnabled :self {mesh} :NewType "NoCollision")
   (Utilities|IsValid :InputObject {V('Carrier')}
     (:"Is Valid"
       (if (!= (Actor|GetAttachParentActor) {V('Carrier')})
         (Transformation|AttachActorToActor :ParentActor {V('Carrier')} :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
         (Transformation|SetActorRelativeLocation :NewRelativeLocation "(X=100,Y=0,Z=15)")))
     (:"Is Not Valid"))
   (else
     (CallFunction|DetachFree)
     (Collision|SetCollisionProfileName :self {mesh} :InCollisionProfileName "PhysicsActor")
     (Collision|SetCollisionEnabled :self {mesh} :NewType "QueryAndPhysics")
     (Physics|SetSimulatePhysics :self {mesh} :bSimulate (== {V('CarryState')} 0))))''')
write(c,'OnRep_Carrier','(CallFunction|ApplyCarryState)')
write(c,'OnRep_CarryState','(CallFunction|ApplyCarryState)')
var(c,'DropDirection','Vector')
write(c,'Drop',f'''
 (if (and (Networking|HasAuthority) (== {V('CarryState')} 1))
   {S('DropDirection',f'(Transformation|GetActorForwardVector :self {V("Carrier")})')}
   (Transformation|DetachFromActor :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld")
   (CallFunction|ClearCarrier)
   {S('CarryState','0')}
   (CallFunction|ApplyCarryState)
   (Physics|AddImpulse :self {mesh} :Impulse (* {V('DropDirection')} 100.0) :bVelChange true)
   (Networking|ForceNetUpdate))''')
write(c,'ReleaseCarried',f'''
 (if (and (Networking|HasAuthority) (== {V('CarryState')} 1))
   (Transformation|DetachFromActor :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld")
   (CallFunction|ClearCarrier)
   {S('CarryState','2')}
   (CallFunction|ApplyCarryState)
   (Networking|ForceNetUpdate)
   (return self)
   (else (return "None")))''')
write(c,'ResetItem',f'''
 (if (Networking|HasAuthority)
   (Physics|SetSimulatePhysics :self {mesh} :bSimulate false)
   (Transformation|DetachFromActor :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld")
   (CallFunction|ClearCarrier)
   {S('CarryState','0')}
   (Transformation|SetActorTransform :NewTransform {V('InitialTransform')} :bSweep false :bTeleport true)
   (CallFunction|ApplyCarryState)
   (Physics|SetPhysicsLinearVelocity :self {mesh} :NewVel "(X=0,Y=0,Z=0)" :bAddToCurrent false)
   (Physics|SetPhysicsAngularVelocityinDegrees :self {mesh} :NewAngVel "(X=0,Y=0,Z=0)" :bAddToCurrent false)
   (Networking|ForceNetUpdate))''')
write(c,'BeginCarryable',f'''
 (if (Networking|HasAuthority) {S('InitialTransform','(Transformation|GetActorTransform)')})
 (CallFunction|ApplyCarryState)
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ApplyCarryState" :Time 0.1 :bLooping true)''')
write(c,'GetInteractInfo','(return "Pick up" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))','Instigator')
write(c,'CanInteract',f'''
 (if (== {V('CarryState')} 0)
   (Utilities|IsValid :InputObject Instigator
     (:"Is Valid"
       (bind ac (Utilities|Casting|CastToAC_Carrying :Object (Actor|GetComponentbyClass :self Instigator :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
         (:then (Utilities|IsValid :InputObject (Class|ACCarrying|GetCarried :self ac) (:"Is Valid" (return false)) (:"Is Not Valid" (return true))))
         (:CastFailed (return false)))) (:"Is Not Valid" (return false)))
   (else (return false)))''','Instigator')
# Replace the duplicate probe's event chains with carrying-only behavior.
owned(c)
g=BP.get_graph(c,'EventGraph')
with toolset_registry.tool_raising_exceptions():
    for node in BP.find_nodes(g): BP.delete_node(node)
fn(c,'PickupBy',[('Instigator',unreal.Actor.static_class())])
write(c,'PickupBy','''
 (if (Networking|HasAuthority)
   (Utilities|IsValid :InputObject Instigator
     (:"Is Valid"
       (bind ac (Utilities|Casting|CastToAC_Carrying :Object (Actor|GetComponentbyClass :self Instigator :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
         (:then (Class|ACCarrying|TryPickup :self ac :Item self)) (:CastFailed)))
     (:"Is Not Valid")))''','Instigator')
event(c,'ReceiveBeginPlay','BeginCarryable')
event(c,'ResetForRound','ResetItem')
owned(c)
e=BP.add_event(c,'Interact')
call=BP.create_node(g,'CallFunction|PickupBy',unreal.IntPoint(400,600))
assert e.find_then_pin().try_create_connection(call.find_execute_pin())
assert e.find_output_pin('Instigator').try_create_connection(call.find_input_pin('Instigator'))
for bp in [ac,c,unreal.load_asset('/Game/Puzzles/BP_KeyRelic'),unreal.load_asset('/Game/Puzzles/BP_Statue')]: save(bp)
RESULT={'logic_built':True}
