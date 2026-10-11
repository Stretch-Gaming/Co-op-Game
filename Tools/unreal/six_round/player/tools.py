import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
tools=ue.load_asset('/Game/Player/Tools/AC_Tools');flare=ue.load_asset('/Game/Player/Tools/BP_Flare')
view=ue.load_asset('/Game/Player/AC_PlayerView')
write(view,'GetHeadlampOn',f'(return {V("HeadlampOn")})');save(view)
write(tools,'CanUseTools',f'''
 (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {OWNER})
  (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health)) (bind carrying (Class|BPCoopCharacter|IsCarryingHeavy :self pawn))
    (bind protected (Class|BPCoopCharacter|GetTakenProtected :self pawn))
    (return (and (not protected) (and (not dead) (not carrying))))) (:CastFailed (return false)))) (:CastFailed (return false)))''')
write(tools,'GetFlareAllowance','''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
   (if (== row "2") (return 3)) (if (or (== row "3") (== row "4")) (return 2)) (return 0)) (:CastFailed (return 0)))''')
write(tools,'RestockFlares',f'(if {AUTH_COMPONENT} (bind count (CallFunction|GetFlareAllowance)) {S("FlaresLeft", "count")})')
write(tools,'ThrowFlareOnServer',f'''
 (if {AUTH_COMPONENT} (bind allowed (CallFunction|CanUseTools))
  (if (and allowed (> {V('FlaresLeft')} 0))
   (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
    (:then (bind (eye rotation) (Actor|GetActorEyesViewPoint :self pawn))
     (bind aim (Pawn|GetBaseAimRotation :self pawn))
     (bind forward (Math|Vector|GetForwardVector :InRot aim))
     (bind end (+ eye (* forward 90.0)))
     (bind (hit blocked) (Collision|SphereTraceByChannel :Start eye :End end :Radius 12.0 :TraceChannel "TraceTypeQuery1" :bTraceComplex false :bIgnoreSelf true :DrawDebugType "None"))
     (bind (blocking overlap time distance location impact normal impactNormal material hitActor component bone myBone item element face traceStart traceEnd) (Collision|BreakHitResult :Hit hit))
     (bind spawnLocation (select blocked (+ location (* normal 14.0)) end))
     (bind spawned (Game|SpawnActorfromClass :Class "/Game/Player/Tools/BP_Flare.BP_Flare_C" :SpawnTransform (Math|Transform|MakeTransform :Location spawnLocation :Rotation aim) :Owner pawn :CollisionHandlingOverride "AlwaysSpawn")
      (:then (Utilities|IsValid :InputObject spawned
       (:"Is Valid" {S('FlaresLeft',f'(- {V("FlaresLeft")} 1)')} (Class|BPFlare|SetBurnSeconds :self spawned :Seconds {V('FlareSeconds')})) (:"Is Not Valid"))))) (:CastFailed))))''')
write(tools,'ThrowFlare','(CallFunction|ThrowFlareOnServer)')
fn(tools,'EndBeamTarget')
write(tools,'EndBeamTarget',f'''
 (Utilities|IsValid :InputObject {V('BeamTarget')}
  (:"Is Valid" (Class|BPILightable|LightEnd(Message) :self {V('BeamTarget')} :Source {OWNER})) (:"Is Not Valid"))''')
write(tools,'ClearBeam',f'(CallFunction|EndBeamTarget) {S("BeamTarget",chr(34)+"None"+chr(34))}')
write(tools,'RefreshBeam',f'''
 (if {AUTH_COMPONENT}
  (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
   (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (bind dead (Class|ACHealth|IsDead :self health))
     (bind view (Utilities|Casting|CastToAC_PlayerView :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
      (:then (if (and (not dead) (Class|ACPlayerView|GetHeadlampOn :self view))
       (bind (eye rotation) (Actor|GetActorEyesViewPoint :self pawn))
       (bind forward (Math|Vector|GetForwardVector :InRot (Pawn|GetBaseAimRotation :self pawn)))
       (bind (hit blocked) (Collision|LineTraceByChannel :Start (+ eye (* forward 70.0)) :End (+ eye (* forward 1200.0)) :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
       (bind (blocking overlap time distance location impact normal impactNormal material hitActor component bone myBone item element face traceStart traceEnd) (Collision|BreakHitResult :Hit hit))
       (if (!= hitActor {V('BeamTarget')}) (CallFunction|ClearBeam) {S('BeamTarget','hitActor')})
       (Utilities|IsValid :InputObject {V('BeamTarget')} (:"Is Valid" (Class|BPILightable|LightBegin(Message) :self {V('BeamTarget')} :Source pawn)) (:"Is Not Valid"))
       (else (CallFunction|ClearBeam)))) (:CastFailed (CallFunction|ClearBeam)))) (:CastFailed (CallFunction|ClearBeam)))) (:CastFailed (CallFunction|ClearBeam))))''')
write(tools,'BeginTools',f'(if {AUTH_COMPONENT} (CallFunction|RestockFlares) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshBeam" :Time 0.2 :bLooping true))')
write(tools,'EndTools',f'(if {AUTH_COMPONENT} (CallFunction|ClearBeam)) (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshBeam")')
event(tools,'ReceiveBeginPlay','BeginTools');event(tools,'ReceiveEndPlay','EndTools');save(tools)
write(flare,'SetBurnSeconds',f'(if (Networking|HasAuthority) {S("BurnSeconds","Seconds")})','Seconds')
fn(flare,'EndFlareTarget')
write(flare,'EndFlareTarget',f'(Utilities|IsValid :InputObject {V("LightTarget")} (:"Is Valid" (Class|BPILightable|LightEnd(Message) :self {V("LightTarget")} :Source self)) (:"Is Not Valid"))')
fn(flare,'IsBurningFlare',outputs=[('Active','bool')])
write(flare,'IsBurningFlare',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (return (and (>= {V('BurnStarted')} 0.0) (< (GameState|GetServerWorldTimeSeconds :self gs) (+ {V('BurnStarted')} {V('BurnSeconds')}))))) (:CastFailed (return false)))''')
write(flare,'IsActive','(bind active (CallFunction|IsBurningFlare)) (return active)')
write(flare,'RefreshFlare',f'''
 (bind active (CallFunction|IsBurningFlare))
 (Rendering|Components|Light|SetIntensity :self {V('FlareLight')} :NewIntensity (select active 2500.0 0.0))
 (if (Networking|HasAuthority)
  (if active
   (for lock (Actor|GetAllActorswithTag :Tag "FlareLock")
    (if (<= (Transformation|GetDistanceTo :OtherActor lock) 180.0)
     (if (!= lock {V('LightTarget')})
      (CallFunction|EndFlareTarget)
      {S('LightTarget','lock')})
     (Class|BPILightable|LightBegin(Message) :self lock :Source self)))
   (Utilities|IsValid :InputObject {V('LightTarget')}
    (:"Is Valid" (if (> (Transformation|GetDistanceTo :OtherActor {V('LightTarget')}) 180.0)
     (Class|BPILightable|LightEnd(Message) :self {V('LightTarget')} :Source self) {S('LightTarget','"None"')})) (:"Is Not Valid"))
   (else (CallFunction|EndFlare) (Actor|DestroyActor :self self))))''')
write(flare,'EndFlare',f'(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshFlare") (if (Networking|HasAuthority) (Utilities|IsValid :InputObject {V("LightTarget")} (:"Is Valid" (Class|BPILightable|LightEnd(Message) :self {V("LightTarget")} :Source self)) (:"Is Not Valid")))')
write(flare,'BeginFlare',f'''
 (Collision|IgnoreActorwhenMoving :self {V('FlareRoot')} :Actor (Actor|GetOwner) :bShouldIgnore true)
 (if (Networking|HasAuthority) (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then {S('BurnStarted','(GameState|GetServerWorldTimeSeconds :self gs)')}
   (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshFlare" :Time 0.1 :bLooping true)) (:CastFailed))
  (else (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshFlare" :Time 0.1 :bLooping true)))''')
event(flare,'ReceiveBeginPlay','BeginFlare');event(flare,'ReceiveEndPlay','EndFlare');save(flare)
RESULT={'stage':'tools graphs','scaling_fallback':'GetScalingRow returns allowance 3/2/2, duration20','runtime_acceptance_pending':True}
