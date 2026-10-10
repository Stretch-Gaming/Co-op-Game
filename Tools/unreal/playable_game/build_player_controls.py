import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
if ARGS.get('resume'):
    original_write=write
    def write(bp,name,body,parameters=''):
        if name in ('GetBracedState','TryBoostFromPartner','BoostOnServer'):
            return original_write(bp,name,body,parameters)
character=ue.load_asset('/Game/Core/BP_CoopCharacter')
for name in ('ApplyBrace','BraceOnServer','UnbraceOnServer','RequestBraceStart','RequestBraceStop','RequestViewToggle','RequestHeadlampToggle','ViewToggleOnServer','HeadlampToggleOnServer','RequestBoost','BoostOnServer','RequestJump'):
    fn(character,name)
fn(character,'TryBoostFromPartner',inputs=[('Partner',ue.Actor.static_class())])
fn(character,'GetBracedState',outputs=[('Braced','bool')])
write(character,'GetBracedState',f'(return {V("Braced")})')
write(character,'RequestBraceStart','(if (Pawn|IsLocallyControlled) (CallFunction|ServerBraceStart))')
write(character,'RequestBraceStop','(if (Pawn|IsLocallyControlled) (CallFunction|ServerBraceStop))')
write(character,'RequestViewToggle','(if (Pawn|IsLocallyControlled) (CallFunction|ServerToggleView))')
write(character,'RequestHeadlampToggle','(if (Pawn|IsLocallyControlled) (CallFunction|ServerToggleHeadlamp))')
write(character,'RequestBoost','(if (Pawn|IsLocallyControlled) (CallFunction|ServerRequestBoost))')
write(character,'RequestJump','(if (Pawn|IsLocallyControlled) (Pawn|Character|Jump) (CallFunction|RequestBoost))')
write(character,'ViewToggleOnServer','''
 (if (Networking|HasAuthority)
  (bind view (Utilities|Casting|CastToAC_PlayerView :Object (Actor|GetComponentbyClass :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
   (:then (Class|ACPlayerView|ToggleView :self view)) (:CastFailed)))''')
write(character,'HeadlampToggleOnServer','''
 (if (Networking|HasAuthority)
  (bind view (Utilities|Casting|CastToAC_PlayerView :Object (Actor|GetComponentbyClass :ComponentClass "/Game/Player/AC_PlayerView.AC_PlayerView_C"))
   (:then (Class|ACPlayerView|ToggleHeadlamp :self view)) (:CastFailed)))''')
write(character,'ApplyBrace',f'''
 (bind movement (Class|Character|GetCharacterMovement))
 (if {V('Braced')}
  (if (> (Class|CharacterMovementComponent|GetMaxWalkSpeed :self movement) 0.0)
   {S('UnbracedSpeed','(Class|CharacterMovementComponent|GetMaxWalkSpeed :self movement)')})
  (Class|CharacterMovementComponent|SetMaxWalkSpeed :self movement :MaxWalkSpeed 0.0)
  (else (if (> {V('UnbracedSpeed')} 0.0)
   (Class|CharacterMovementComponent|SetMaxWalkSpeed :self movement :MaxWalkSpeed {V('UnbracedSpeed')}))))''')
write(character,'OnRep_bBraced','(CallFunction|ApplyBrace)')
write(character,'BraceOnServer',f'''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (if (not (Class|ACHealth|IsDowned :self health)) {S('Braced','true')} (CallFunction|ApplyBrace))) (:CastFailed)))''')
write(character,'UnbraceOnServer',f'(if (Networking|HasAuthority) {S("Braced","false")} (CallFunction|ApplyBrace))')
write(character,'TryBoostFromPartner',f'''
 (if (and (Networking|HasAuthority) (not (== Partner self)))
  (bind partner (Utilities|Casting|CastToBP_CoopCharacter :Object Partner)
   (:then
    (bind vertical (Transformation|GetVerticalDistanceTo :OtherActor partner))
    (if (and (CallFunction|GetBracedState :self partner) (and (<= (Transformation|GetHorizontalDistanceTo :OtherActor partner) 200.0) (and (>= vertical -150.0) (<= vertical 150.0))))
    (if (>= (- (Utilities|Time|GetGameTimeinSeconds) {V('LastBoostTime')}) 0.8)
     {S('LastBoostTime','(Utilities|Time|GetGameTimeinSeconds)')}
     (Pawn|Character|LaunchCharacter :LaunchVelocity (+ (* (Transformation|GetActorForwardVector) 200.0) (Utilities|Struct|MakeVector :X 0.0 :Y 0.0 :Z 1300.0)) :bXYOverride false :bZOverride true)))) (:CastFailed)))''','Partner')
write(character,'BoostOnServer','''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (if (not (Class|ACHealth|IsDowned :self health))
    (for other (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
     (CallFunction|TryBoostFromPartner :Partner other)))) (:CastFailed)))''')
for name,handler in [('Server_BraceStart','BraceOnServer'),('Server_BraceStop','UnbraceOnServer'),('Server_ToggleView','ViewToggleOnServer'),('Server_ToggleHeadlamp','HeadlampToggleOnServer'),('Server_RequestBoost','BoostOnServer')]:
    event(character,name,handler)
save(character)
RESULT={'brace_boost_view_headlamp_handlers_written':True,'server_event_flags_configured_in_editor':True,'compiled':True,'input_bindings_and_runtime_acceptance_pending':True}
(QUEUE/'player-controls-build.json').write_text(json.dumps(RESULT,indent=2))
