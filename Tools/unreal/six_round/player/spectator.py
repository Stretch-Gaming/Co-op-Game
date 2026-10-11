import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
bp=ue.load_asset('/Game/Player/AC_PlayerView')
for name in ('NextSpectatorSlot','WrapSpectatorSlot'):var(bp,name,'int',4)
for name in ('NextSpectator','WrapSpectator'):var(bp,name,ue.Actor.static_class())
fn(bp,'HasNextSpectator',outputs=[('Valid','bool')]);fn(bp,'HasSpectatedPawn',outputs=[('Valid','bool')])
for name,varname in [('HasNextSpectator','NextSpectator'),('HasSpectatedPawn','SpectatedPawn')]:
 write(bp,name,f'(Utilities|IsValid :InputObject {V(varname)} (:"Is Valid" (return true)) (:"Is Not Valid" (return false)))')
for name in ('ValidateSpectatedPawn','ApplySpectatorCamera','RefreshTargetCamera','BeginSpectator'):fn(bp,name)
fn(bp,'OwnerIsDead',outputs=[('Dead','bool')]);fn(bp,'InspectSpectatorCandidate',[('Candidate',ue.Actor.static_class())])
write(bp,'OwnerIsDead',f'''
 (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self {OWNER} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
  (:then (bind dead (Class|ACHealth|IsDead :self health)) (return dead)) (:CastFailed (return false)))''')
write(bp,'InspectSpectatorCandidate',f'''
 (if (not (== Candidate {OWNER}))
  (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self Candidate :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health))
    (if (not dead) (bind other (Utilities|Casting|CastToPawn :Object Candidate)
     (:then (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self other))
      (:then (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
       (if (and (>= slot 0) (<= slot 3))
        (if (< slot {V('WrapSpectatorSlot')}) {S('WrapSpectatorSlot','slot')} {S('WrapSpectator','Candidate')})
        (if (and (> slot {V('LastSpectatorSlot')}) (< slot {V('NextSpectatorSlot')}))
         {S('NextSpectatorSlot','slot')} {S('NextSpectator','Candidate')}))) (:CastFailed))) (:CastFailed)))) (:CastFailed)))''','Candidate')
write(bp,'CycleSpectator',f'''
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then (bind dead (CallFunction|OwnerIsDead))
   (if (and dead (Pawn|IsLocallyControlled :self pawn))
    {S('NextSpectatorSlot','4')} {S('WrapSpectatorSlot','4')}
    {S('NextSpectator','"None"')} {S('WrapSpectator','"None"')}
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (CallFunction|InspectSpectatorCandidate :Candidate actor))
    (bind nextExists (CallFunction|HasNextSpectator))
    (if (not nextExists)
     {S('NextSpectator',V('WrapSpectator'))} {S('NextSpectatorSlot',V('WrapSpectatorSlot'))})
    {S('SpectatedPawn',V('NextSpectator'))}
    (bind finalExists (CallFunction|HasNextSpectator))
    {S('LastSpectatorSlot',f'(select finalExists {V("NextSpectatorSlot")} -1)')})) (:CastFailed))''')
write(bp,'ValidateSpectatedPawn',f'''
 (Utilities|IsValid :InputObject {V('SpectatedPawn')}
  (:"Is Valid" (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self {V('SpectatedPawn')} :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind dead (Class|ACHealth|IsDead :self health)) (if dead {S('SpectatedPawn','"None"')}))
   (:CastFailed {S('SpectatedPawn','"None"')})))
  (:"Is Not Valid" {S('SpectatedPawn','"None"')}))''')
# Remote pawn cameras need the replicated first/third-person mode applied locally.
write(bp,'RefreshTargetCamera',f'''
 (bind target (Utilities|Casting|CastToPawn :Object {V('SpectatedPawn')})
  (:then (bind targetView (Utilities|Casting|CastToAC_PlayerView :Object (Actor|GetComponentbyClass :self target :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
   (:then (Class|ACPlayerView|ApplyCameraArm :self targetView) (Class|ACPlayerView|ApplyCameraFov :self targetView)
    (bind arm (Utilities|Casting|CastToSpringArmComponent :Object (Actor|GetComponentbyClass :self target :ComponentClass "/Script/Engine.SpringArmComponent"))
     (:then (Transformation|SetWorldRotation :self arm :NewRotation (Pawn|GetBaseAimRotation :self target))) (:CastFailed))) (:CastFailed))) (:CastFailed))''')
write(bp,'ApplySpectatorCamera',f'''
 (bind pawn (Utilities|Casting|CastToPawn :Object {OWNER})
  (:then (if (Pawn|IsLocallyControlled :self pawn)
   (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self pawn))
    (:then (bind dead (CallFunction|OwnerIsDead))
     (if (and dead (CallFunction|HasSpectatedPawn))
      (CallFunction|RefreshTargetCamera)
      (if (not (== (Pawn|GetViewTarget :self pc) {V('SpectatedPawn')}))
       (Camera|SetViewTargetwithBlend :self pc :NewViewTarget {V('SpectatedPawn')} :BlendTime 0.2))
      (else (if (not (== (Pawn|GetViewTarget :self pc) pawn))
       (Camera|SetViewTargetwithBlend :self pc :NewViewTarget pawn :BlendTime 0.2))))) (:CastFailed)))) (:CastFailed))''')
write(bp,'RefreshSpectator',f'''
 (CallFunction|ValidateSpectatedPawn)
 (bind dead (CallFunction|OwnerIsDead))
 (if dead (if (not (CallFunction|HasSpectatedPawn)) (CallFunction|CycleSpectator))
  (else {S('SpectatedPawn','"None"')} {S('LastSpectatorSlot','-1')}))
 (CallFunction|ApplySpectatorCamera)''')
write(bp,'BeginSpectator','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshSpectator" :Time 0.05 :bLooping true)')
event(bp,'ReceiveBeginPlay','BeginSpectator');save(bp)
RESULT={'stage':'bounded per-owner dead spectator','runtime_acceptance_pending':True,'camera':'selected living pawn replicated view mode and aim; owner-only view target','core_input_hook':'own dead Interact locally calls CycleSpectator before gameplay RPC'}
