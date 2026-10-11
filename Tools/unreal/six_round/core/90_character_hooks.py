"""Core character hooks only, no component or input mutations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();c=ue.load_asset('/Game/Core/BP_CoopCharacter')
write(c,'CreateReviveTarget','')
write(c,'RefreshAdventurePlayer',f'''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
   (:then (bind dead (Class|ACHealth|IsDead :self health))
    (CallFunction|SetInteractionBlocked :Blocked dead)
    (if dead (CallFunction|CancelUse) (CallFunction|DropFromServer))) (:CastFailed)))''')
write(c,'ReceiveHealthDamage',f'''
 (if (Networking|HasAuthority)
  (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :ComponentClass "{HEALTH}"))
   (:then (Class|ACHealth|TakeDamage :self health :Damage Damage)) (:CastFailed)))''','Damage')
event(c,'ReceiveAnyDamage','ReceiveHealthDamage',['Damage']);save(c)
proxy=ue.load_asset('/Game/Puzzles/Recovery/BP_HCReviveTarget')
if proxy:
 write(proxy,'CanInteract','(return false)','Instigator');write(proxy,'FinishRevive','','Instigator')
 write(proxy,'BeginReviveTarget','(Actor|SetActorHiddenInGame :bNewHidden true) (Collision|SetActorEnableCollision :bNewActorEnableCollision false)');save(proxy)
RESULT={'stage':'character_death_hooks','runtime_acceptance_pending':True}
