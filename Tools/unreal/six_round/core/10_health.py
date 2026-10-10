"""Lethal death; compatibility IsDowned is only an alias. No revive path."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();h=ue.load_asset('/Game/Hazards/AC_Health')
if not any(g.get_name() == 'OnDied' for g in BP.list_event_dispatchers(h)):
 BP.add_event_dispatcher(h, 'OnDied')
 compile_bp(h)
write(h,'IsDead',f'(return {V("Dead")})')
write(h,'IsDowned',f'(return {V("Dead")})')
write(h,'Revive','','Reviver')
write(h,'ApplyHealthState',f'''
 (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {OWNER})
  (:then
   (bind movement (Class|Character|GetCharacterMovement :self pawn))
   (if {V('Dead')}
    (Pawn|Components|CharacterMovement|DisableMovement :self movement)
    (Utilities|Array|AddUnique :TargetArray (Class|Actor|GetTags :self pawn) :NewItem "Downed")
    (Utilities|Array|AddUnique :TargetArray (Class|Actor|GetTags :self pawn) :NewItem "Dead")
    (else
     (Pawn|Components|CharacterMovement|SetMovementMode :self movement :NewMovementMode "MOVE_Walking")
     (Utilities|Array|RemoveItem :TargetArray (Class|Actor|GetTags :self pawn) :Item "Downed")
     (Utilities|Array|RemoveItem :TargetArray (Class|Actor|GetTags :self pawn) :Item "Dead")))
   (if (Networking|HasAuthority :self pawn)
    (Class|BPCoopCharacter|SetInteractionBlocked :self pawn :Blocked {V('Dead')})
    (if {V('Dead')}
     (Class|BPCoopCharacter|CancelUse :self pawn)
     (Class|BPCoopCharacter|DropFromServer :self pawn)))) (:CastFailed))''')
write(h,'OnRep_bDead','(CallFunction|ApplyHealthState)')
# Legacy notify remains solely to apply the same movement state.
write(h,'OnRep_bDowned','(CallFunction|ApplyHealthState)')
write(h,'TakeDamage',f'''
 (if (and {AUTH_COMPONENT} (and (> Damage 0.0) (not {V('Dead')})))
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {OWNER})
   (:then (if (not (Class|BPCoopCharacter|GetTakenProtected :self pawn))
    {S('Health',f'(Math|Float|Max(Float) :A (- {V("Health")} Damage) :B 0.0)')}
    (if (<= {V('Health')} 0.0)
     {S('Dead','true')} {S('Downed','true')}
     (CallFunction|ApplyHealthState)
     (Default|CallOnDied)))) (:CastFailed)))''','Damage')
write(h,'ResetHealth',f'''
 (if {AUTH_COMPONENT}
  {S('Health',V('MaxHealth'))} {S('Dead','false')} {S('Downed','false')}
  (CallFunction|ApplyHealthState))''')
write(h,'StartHealth',f'(if {AUTH_COMPONENT} (CallFunction|ResetHealth)) (CallFunction|ApplyHealthState)')
event(h,'ReceiveBeginPlay','StartHealth');save(h)
# Core hooks kept in a separate script so primary can order them after player integration.
RESULT={'stage':'death','runtime_acceptance_pending':True}
