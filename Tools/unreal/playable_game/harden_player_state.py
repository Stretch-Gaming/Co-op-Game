import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
health=ue.load_asset('/Game/Hazards/AC_Health')
write(health,'ApplyHealthState',f'''
 (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then
   (bind movement (Class|Character|GetCharacterMovement :self pawn))
   (if {V('Downed')}
    (Pawn|Components|CharacterMovement|DisableMovement :self movement)
    (Utilities|Array|AddUnique :TargetArray (Class|Actor|GetTags :self pawn) :NewItem "Downed")
    (else (Pawn|Components|CharacterMovement|SetMovementMode :self movement :NewMovementMode "MOVE_Walking")
     (Utilities|Array|RemoveItem :TargetArray (Class|Actor|GetTags :self pawn) :Item "Downed")))
   (bind player (Utilities|Casting|CastToBP_CoopCharacter :Object pawn)
    (:then (if (Networking|HasAuthority :self player) (Class|BPCoopCharacter|SetInteractionBlocked :self player :Blocked {V('Downed')}))) (:CastFailed))) (:CastFailed))''')
save(health)
character=ue.load_asset('/Game/Core/BP_CoopCharacter')
fn(character,'RestoreWalkingSpeed')
write(character,'RestoreWalkingSpeed',f'''
 (bind carry (Utilities|Casting|CastToAC_Carrying :Object (Components|GetComponentbyClass :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
  (:then
   (bind speed (Class|ACCarrying|GetCarrySpeed :self carry))
   (bind restored (select (> speed 0.0) speed {V('UnbracedSpeed')}))
   (if (> restored 0.0) (Class|CharacterMovementComponent|SetMaxWalkSpeed :self (Class|Character|GetCharacterMovement) :MaxWalkSpeed restored)))
  (:CastFailed (if (> {V('UnbracedSpeed')} 0.0) (Class|CharacterMovementComponent|SetMaxWalkSpeed :self (Class|Character|GetCharacterMovement) :MaxWalkSpeed {V('UnbracedSpeed')}))))''')
write(character,'ApplyBrace',f'''
 (bind movement (Class|Character|GetCharacterMovement))
 (if {V('Braced')}
  (if (> (Class|CharacterMovementComponent|GetMaxWalkSpeed :self movement) 0.0) {S('UnbracedSpeed','(Class|CharacterMovementComponent|GetMaxWalkSpeed :self movement)')})
  (Class|CharacterMovementComponent|SetMaxWalkSpeed :self movement :MaxWalkSpeed 0.0)
  (else (CallFunction|RestoreWalkingSpeed)))''')
# Holding still for a boost releases any carried weight first.
write(character,'BraceOnServer',f'''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (bind downed (Class|ACHealth|IsDowned :self health))
    (if (not downed) (CallFunction|ReleaseCarried) {S('Braced','true')} (CallFunction|ApplyBrace))) (:CastFailed)))''')
save(character)
RESULT={'damage_immediately_blocks_downed_uses':True,'downed_tags_match_delivered_contracts':True,'brace_preserves_carry_speed_cleanup':True}
