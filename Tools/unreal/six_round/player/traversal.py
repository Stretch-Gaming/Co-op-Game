"""Server-approved movement. Core forwards owning-player RPC requests."""
import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/AC_Traversal');assert bp
var(bp,'bTraversalFlightApplied','bool',False)
fn(bp,'CanAct',outputs=[('Allowed','bool')]);fn(bp,'CanStartTraversalFlight',outputs=[('Allowed','bool')]);fn(bp,'ReleaseTraversalFlight')
var(bp,'bMantling','bool',False,notify=True)
var(bp,'MantleStarted','float',-1.,replicated=True)
for name in ('MantleStart','MantleTarget'):var(bp,name,'Vector',ue.Vector())
for name in ('MantleOnServer','MantleAuthorityTick','EndMantle'):fn(bp,name)
var(bp,'ClimbForwardInput','float',0.,replicated=True)
fn(bp,'SetClimbForwardOnServer',[('Forward','float')])
write(bp,'CanTraverse',f'''
 (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {OWNER})
  (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health))
    (bind carrying (Class|BPCoopCharacter|IsCarryingHeavy :self pawn))
    (bind protected (Class|BPCoopCharacter|GetTakenProtected :self pawn))
    (return (and (not protected) (and (not dead) (not carrying))))) (:CastFailed (return false)))) (:CastFailed (return false)))''')
write(bp,'CanAct',f'''
 (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {OWNER})
  (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health))
    (bind protected (Class|BPCoopCharacter|GetTakenProtected :self pawn))
    (return (and (not protected) (not dead)))) (:CastFailed (return false)))) (:CastFailed (return false)))''')
write(bp,'CanStartTraversalFlight',f'''
 (bind allowed (CallFunction|CanTraverse))
 (if allowed (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then (bind movement (Class|Character|GetCharacterMovement :self pawn))
   (return (or {V('TraversalFlightApplied')} (not (AI|Components|NavMovement|IsFlying :self movement))))) (:CastFailed (return false)))
  (else (return false)))''')
write(bp,'ReleaseTraversalFlight',f'''
 (if {V('TraversalFlightApplied')}
  (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
   (:then (bind movement (Class|Character|GetCharacterMovement :self pawn))
    (bind active (CallFunction|CanAct))
    (if (and active (AI|Components|NavMovement|IsFlying :self movement))
     (Pawn|Components|CharacterMovement|SetMovementMode :self movement :NewMovementMode "MOVE_Falling"))
    {S('TraversalFlightApplied','false')}) (:CastFailed {S('TraversalFlightApplied','false')})))''')
write(bp,'ApplyTraversal',f'''
 (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then (bind movement (Class|Character|GetCharacterMovement :self pawn))
   (bind allowed (CallFunction|CanTraverse))
   (if (and allowed (or {V('Climbing')} {V('Mantling')}))
    (Pawn|Components|CharacterMovement|SetMovementMode :self movement :NewMovementMode "MOVE_Flying")
    (Class|CharacterMovementComponent|SetMaxFlySpeed :self movement :MaxFlySpeed (select {V('Mantling')} 0.0 {V('ClimbSpeed')}))
    {S('TraversalFlightApplied','true')}
    (else (CallFunction|ReleaseTraversalFlight)))
   (if (and allowed (or {V('TraversalFlightApplied')} (not (AI|Components|NavMovement|IsFlying :self movement))))
    (Class|CharacterMovementComponent|SetMaxWalkSpeed :self movement :MaxWalkSpeed (select {V('Sprinting')} {V('SprintSpeed')} {V('WalkSpeed')})))) (:CastFailed))''')
write(bp,'SprintOnServer',f'(if {AUTH_COMPONENT} (bind allowed (CallFunction|CanStartTraversalFlight)) (if (and allowed (and (not {V("Mantling")}) (not {V("Climbing")}))) {S("Sprinting","true")} (CallFunction|ApplyTraversal)))')
write(bp,'StopSprintOnServer',f'(if {AUTH_COMPONENT} {S("Sprinting","false")} (CallFunction|ApplyTraversal))')
# Tagged volumes validate climbing on the server; no client-supplied destination.
write(bp,'ClimbOnServer',f'''
 (if {AUTH_COMPONENT} (bind allowed (CallFunction|CanStartTraversalFlight))
  (if (and allowed (not {V('Mantling')})) (for volume (Collision|GetOverlappingActors :self {OWNER} :ClassFilter "/Script/Engine.Actor")
   (if (Utilities|ActorHasTag :self volume :Tag "Climbable")
    {S('Climbing','true')} {S('ClimbForwardInput','1.0')} {S('Sprinting','false')} (CallFunction|ApplyTraversal)))))''')
write(bp,'SetClimbForwardOnServer',f'''
 (if {AUTH_COMPONENT}
  (bind allowed (CallFunction|CanTraverse))
  (if (and allowed (not {V('Mantling')}))
   (if (and (> Forward 0.1) (not {V('Climbing')})) (CallFunction|ClimbOnServer))
   {S('ClimbForwardInput','(Math|Float|Clamp(Float) :Value Forward :Min -1.0 :Max 1.0)')}
   (else {S('ClimbForwardInput','0.0')})))''','Forward')
write(bp,'StopClimbOnServer',f'(if {AUTH_COMPONENT} {S("Climbing","false")} {S("ClimbForwardInput","0.0")} (CallFunction|ApplyTraversal))')
fn(bp,'TraversalAuthorityTick')
write(bp,'TraversalAuthorityTick',f'''
 (if {AUTH_COMPONENT} (bind allowed (CallFunction|CanTraverse))
  (if (not allowed) {S('Sprinting','false')} {S('Climbing','false')} {S('Mantling','false')} {S('ClimbForwardInput','0.0')})
  (if {V('Climbing')}
   (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
    (:then {S('InsideClimbable','false')}
     (for volume (Collision|GetOverlappingActors :self pawn :ClassFilter "/Script/Engine.Actor")
      (if (Utilities|ActorHasTag :self volume :Tag "Climbable") {S('InsideClimbable','true')}))
     (if {V('InsideClimbable')} (Pawn|AddMovementInput :self pawn :WorldDirection (Utilities|Struct|MakeVector :Z 1.0) :ScaleValue {V('ClimbForwardInput')})
      (else {S('Climbing','false')}))) (:CastFailed))))''')
write(bp,'EndMantle',f'(if {AUTH_COMPONENT} {S("Mantling","false")} (CallFunction|ApplyTraversal))')
write(bp,'MantleOnServer',f'''
 (if {AUTH_COMPONENT}
  (bind allowed (CallFunction|CanStartTraversalFlight))
  (if (and allowed (not {V('Mantling')}))
   (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
    (:then (bind start (Transformation|GetActorLocation :self pawn))
     (bind forward (Transformation|GetActorForwardVector :self pawn))
     (bind (floorHit floorBlocked) (Collision|LineTraceByChannel :Start (+ start (Utilities|Struct|MakeVector :Z 20.0)) :End (- start (Utilities|Struct|MakeVector :Z 300.0)) :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
     (bind (floorBlocking floorOverlap floorTime floorDistance floorLocation floorImpact floorNormal floorImpactNormal floorMaterial floorActor floorComponent floorBone floorMyBone floorItem floorElement floorFace floorTraceStart floorTraceEnd) (Collision|BreakHitResult :Hit floorHit))
     (if (or {V('Climbing')} (and floorBlocked (>= (.z floorNormal) 0.7)))
     (bind baseZ (select {V('Climbing')} (- (.z start) 96.0) (.z floorLocation)))
     (bind frontStart (Utilities|Struct|MakeVector :X (.x start) :Y (.y start) :Z (+ baseZ 50.0)))
     (bind ahead (+ start (* forward 160.0)))
     (bind topStart (Utilities|Struct|MakeVector :X (.x ahead) :Y (.y ahead) :Z (+ baseZ 300.0)))
     (bind topEnd (Utilities|Struct|MakeVector :X (.x ahead) :Y (.y ahead) :Z (+ baseZ 5.0)))
     (bind (frontHit frontBlocked) (Collision|LineTraceByChannel :Start frontStart :End (+ frontStart (* forward 180.0)) :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
     (if frontBlocked
      (bind (topHit topBlocked) (Collision|LineTraceByChannel :Start topStart :End topEnd :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
      (bind (blocking overlap time distance location impact normal impactNormal material hitActor component bone myBone item element face traceStart traceEnd) (Collision|BreakHitResult :Hit topHit))
      (bind height (- (.z location) baseZ))
      (if (and topBlocked (and (>= height 100.0) (and (<= height 200.0) (>= (.z normal) 0.7))))
       (bind destination (+ location (Utilities|Struct|MakeVector :Z 100.0)))
       (bind (clearanceHit clearanceBlocked) (Collision|CapsuleTraceByChannel :Start destination :End (+ destination (Utilities|Struct|MakeVector :Z 1.0)) :Radius 43.0 :HalfHeight 95.0 :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
       (if (not clearanceBlocked)
        {S('MantleStart','start')} {S('MantleTarget','destination')} {S('Mantling','true')} {S('Climbing','false')} {S('ClimbForwardInput','0.0')} {S('Sprinting','false')}
        (CallFunction|ApplyTraversal)
        (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
         (:then {S('MantleStarted','(GameState|GetServerWorldTimeSeconds :self gs)')}) (:CastFailed (CallFunction|EndMantle)))))))) (:CastFailed))))''')
write(bp,'MantleAuthorityTick',f'''
 (if (and {AUTH_COMPONENT} {V('Mantling')})
  (bind allowed (CallFunction|CanTraverse))
  (if allowed
   (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then (bind age (- (GameState|GetServerWorldTimeSeconds :self gs) {V('MantleStarted')}))
     (bind verticalTarget (+ {V('MantleStart')} (Utilities|Struct|MakeVector :Z (+ (- (.z {V('MantleTarget')}) (.z {V('MantleStart')})) 10.0))))
     (bind next (select (< age 0.25)
      (Math|Vector|Lerp(Vector) :A {V('MantleStart')} :B verticalTarget :Alpha (Math|Float|Clamp(Float) :Value (/ age 0.25) :Min 0.0 :Max 1.0))
      (Math|Vector|Lerp(Vector) :A verticalTarget :B {V('MantleTarget')} :Alpha (Math|Float|Clamp(Float) :Value (/ (- age 0.25) 0.25) :Min 0.0 :Max 1.0))))
     (Transformation|SetActorLocation :self {OWNER} :NewLocation next :bSweep true :bTeleport false)
     (if (>= age 0.5) (CallFunction|EndMantle))) (:CastFailed (CallFunction|EndMantle)))
   (else (CallFunction|EndMantle))))''')
write(bp,'RefreshTraversal','(CallFunction|TraversalAuthorityTick) (CallFunction|MantleAuthorityTick) (CallFunction|ApplyTraversal)')
for name in ('OnRep_bSprinting','OnRep_bClimbing','OnRep_bMantling'):write(bp,name,'(CallFunction|ApplyTraversal)')
write(bp,'BeginTraversal','(CallFunction|ApplyTraversal) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTraversal" :Time 0.05 :bLooping true)')
event(bp,'ReceiveBeginPlay','BeginTraversal');save(bp)
RESULT={'stage':'traversal graphs','runtime_acceptance_pending':True,'mantle':'server front/top/clearance traces,100..200cm,vertical-first0.5s swept pullup; node/pin checks pending'}
