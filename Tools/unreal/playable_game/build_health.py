import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *

guard()
if ARGS.get('resume'):
    original_write = write
    def write(bp,name,body,parameters=''):
        if name in ('Revive','StartHealth','ReceiveHealthDamage'):
            return original_write(bp,name,body,parameters)
health = ue.load_asset('/Game/Hazards/AC_Health')
write(health,'IsDowned',f'(return {V("Downed")})')
write(health,'ApplyHealthState',f'''
 (bind pawn (Utilities|Casting|CastToCharacter :Object {OWNER})
  (:then
   (bind movement (Class|Character|GetCharacterMovement :self pawn))
   (if {V('Downed')}
    (Pawn|Components|CharacterMovement|DisableMovement :self movement)
    (else (Pawn|Components|CharacterMovement|SetMovementMode :self movement :NewMovementMode "MOVE_Walking"))))
  (:CastFailed))''')
write(health,'OnRep_bDowned','(CallFunction|ApplyHealthState)')
write(health,'TakeDamage',f'''
 (if (and {AUTH_COMPONENT} (and (> Damage 0.0) (not {V('Downed')})))
  {S('Health',f'(select (> (- {V("Health")} Damage) 0.0) (- {V("Health")} Damage) 0.0)')}
  (if (<= {V('Health')} 0.0)
   {S('Downed','true')}
   (CallFunction|ApplyHealthState)
   (Default|CallOnDowned)))''','Damage')
write(health,'ResetHealth',f'''
 (if {AUTH_COMPONENT}
  (bind wasDowned {V('Downed')})
  {S('Health',V('MaxHealth'))}
  {S('Downed','false')}
  (CallFunction|ApplyHealthState)
  (if wasDowned (Default|CallOnRevived)))''')
write(health,'Revive',f'''
 (if (and {AUTH_COMPONENT} {V('Downed')})
  (Utilities|IsValid :InputObject Reviver
   (:"Is Valid"
    (bind pawn (Utilities|Casting|CastToPawn :Object Reviver)
     (:then
      (if (<= (Transformation|GetDistanceTo :self {OWNER} :OtherActor pawn) 400.0)
       (bind otherHealth (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
        (:then (if (not (CallFunction|IsDowned :self otherHealth))
         {S('Health',f'(* {V("MaxHealth")} 0.5)')}
         {S('Downed','false')}
         (CallFunction|ApplyHealthState)
         (Default|CallOnRevived))) (:CastFailed))))
     (:CastFailed))) (:"Is Not Valid")))''','Reviver')
write(health,'StartHealth',f'(if {AUTH_COMPONENT} (CallFunction|ResetHealth)) (CallFunction|ApplyHealthState)')
event(health,'ReceiveBeginPlay','StartHealth')

character = ue.load_asset('/Game/Core/BP_CoopCharacter')
write(character,'ReceiveHealthDamage','''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
   (:then (Class|ACHealth|TakeDamage :self health :Damage Damage)) (:CastFailed)))''','Damage')
event(character,'ReceiveAnyDamage','ReceiveHealthDamage',['Damage'])
save(health)
compile_bp(character)
RESULT={'health_damage_reset_revive_written':True,'compiled':True,'core_damage_event_connected':True,'scaling_table_revive_time_pending':True,'runtime_acceptance_pending':True}
(QUEUE/'health-build.json').write_text(json.dumps(RESULT,indent=2))
