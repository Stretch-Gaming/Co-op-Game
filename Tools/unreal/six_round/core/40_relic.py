"""The caged heavy relic, death drop, escape reset and final altar transaction."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();key=ue.load_asset('/Game/Puzzles/BP_KeyRelic');carry=ue.load_asset('/Game/Puzzles/BP_Carryable')
var(key,'CageAvailable','bool',False)
write(key,'CageAllowsPickup',f'''
 (bind gs {GS} (:then {STATE}
  {S('CageAvailable','false')}
  (if (and (or (== index 5) (== index 6)) {EQ('phase',PLAY)})
   (if (== index 6) {S('CageAvailable','true')}
    (else (for item (Actor|GetAllActorswithTag :Tag "RelicCage")
     (bind cage (Utilities|Casting|CastToBP_RelicCage :Object item)
      (:then (if (Class|BPRelicCage|IsRaised :self cage) {S('CageAvailable','true')})) (:CastFailed))))))
  (return {V('CageAvailable')})) (:CastFailed (return false)))''')
write(carry,'CanClaim',f'''
 (if (and (Networking|HasAuthority) (== {V('CarryState')} 0))
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Instigator)
   (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
    (:then (if (not (Class|ACHealth|IsDead :self health))
     (bind key (Utilities|Casting|CastToBP_KeyRelic :Object self)
      (:then (bind allowed (Class|BPKeyRelic|CageAllowsPickup :self key)) (return allowed)) (:CastFailed (return true))))) (:CastFailed))) (:CastFailed)))
 (return false)''','Instigator')
write(key,'LiftRelic',f'''
 (if (Networking|HasAuthority)
  (bind allowed (CallFunction|CageAllowsPickup))
  (if allowed
   (bind ac (Utilities|Casting|CastToAC_Carrying :Object (Components|GetComponentbyClass :self Instigator :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
    (:then (if (Class|ACCarrying|TryPickup :self ac :Item self)
     (for item (Actor|GetAllActorswithTag :Tag "RelicCage")
      (bind cage (Utilities|Casting|CastToBP_RelicCage :Object item)
       (:then (Class|BPRelicCage|LatchOpen :self cage)) (:CastFailed)))
     (bind gs {GS} (:then {STATE}
      (if (== index 5) (bind gm {GM} (:then (Class|BPCoopGameMode|ClearRound :self gm)) (:CastFailed)))) (:CastFailed)))) (:CastFailed))))''','Instigator')
# Escape retry returns the key to its saved pedestal through inherited ResetItem.
write(key,'ResetRelic','''
 (if (Networking|HasAuthority)
  (Class|BPCarryable|ResetItem :self self)
  (if (== Index 6)
   (for item (Actor|GetAllActorswithTag :Tag "RelicCage")
    (bind cage (Utilities|Casting|CastToBP_RelicCage :Object item)
     (:then (Class|BPRelicCage|LatchOpen :self cage)) (:CastFailed)))))''','Index Attempt')
exclusive_event(key,'Interact','LiftRelic',['Instigator']);exclusive_event(key,'ResetForRound','ResetRelic',['Index','Attempt'])
for bp in (carry,key):save(bp)
altar=ue.load_asset('/Game/Puzzles/BP_Altar')
write(altar,'IsRoundActive',f'(bind gs {GS} (:then {STATE} (return (and (== index 6) {EQ("phase",PLAY)}))) (:CastFailed (return false)))')
# Delivered CanAccept revalidates living character, carry state, carrier, range and single-use transaction.
# Reuse its proven release/attach transaction, but replace its round-two completion call.
graph=BP.get_graph(altar,'AcceptKey')
existing=BP.read_graph_dsl(graph)
# Read only the existing graph, then regenerate the narrow completion path; no editor byte edits.
body=f'''
 (bind allowed (CallFunction|CanAccept :Instigator Instigator))
 (if allowed
  (bind gm {GM} (:then
   {S('TransactionBusy','true')}
   (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object {V('CandidateCharacter')})
    (:then (bind released (Class|BPCoopCharacter|ReleaseCarried :self pawn))
     (if (== released {V('CandidateKey')})
      {S('PlacedKey','released')}
      (bind attached (Transformation|AttachActorToComponent :self released :Parent {V('AltarSocket')} :SocketName {V('SocketName')} :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false))
      (if attached
       {S('Completed','true')} {S('AcceptCount',f'(+ {V("AcceptCount")} 1)')}
       (CallFunction|ApplyAltarState) (Networking|ForceNetUpdate)
       (Class|BPCoopGameMode|SetMissionDelivered :self gm :MissionDelivered true)
       (Class|BPCoopGameMode|AddRelics :self gm :Count 1)
       (Class|BPCoopGameMode|ClearRound :self gm)
       (else (Class|BPIRoundReset|ResetforRound(Message) :self released :Index 6 :Attempt 0) {S('PlacedKey','"None"')})))
     {S('TransactionBusy','false')}) (:CastFailed {S('TransactionBusy','false')}))) (:CastFailed)))'''
write(altar,'AcceptKey',body,'Instigator');save(altar)
# Dead bodies never hold plates.
plate=ue.load_asset('/Game/Puzzles/BP_PressurePlate')
write(plate,'Refresh',f'''
 (if (Networking|HasAuthority)
  {S('OccupantCount','0')}
  (if {V('Enabled')}
   (for occupant (Collision|GetOverlappingActors)
    (if (Actor|ActorHasTag :self occupant :Tag "HC_PlateWeight")
     {S('OccupantCount',f'(+ {V("OccupantCount")} 1)')}
     (else (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object occupant)
      (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
       (:then (if (not (Class|ACHealth|IsDead :self health)) {S('OccupantCount',f'(+ {V("OccupantCount")} 1)')})) (:CastFailed))) (:CastFailed)))))
  {S('Pressed',f'(and {V("Enabled")} (> {V("OccupantCount")} 0))')}))''');save(plate)
gate=ue.load_asset('/Game/Puzzles/BP_ChamberGate')
write(gate,'Refresh',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('Open',f'(or (>= index 6) (and (== index {V("RoundIndex")}) {EQ("phase",CLEAR)}))')}
   (CallFunction|ApplyVisual)) (:CastFailed)))''');save(gate)
RESULT={'stage':'relic_and_dropoff','runtime_acceptance_pending':True}
