import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
lever=ue.load_asset('/Game/Player/RelicChamber/BP_Lever');cage=ue.load_asset('/Game/Player/RelicChamber/BP_RelicCage')
clear_holder=S('Holder','"None"')
write(lever,'CanSixHold','''
 (Utilities|IsValid :InputObject PlayerPawn
  (:"Is Valid" (if (<= (Transformation|GetDistanceTo :OtherActor PlayerPawn) 400.0)
   (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self PlayerPawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (bind dead (Class|ACHealth|IsDead :self health)) (return (not dead))) (:CastFailed (return false))))
   (return false)) (:"Is Not Valid" (return false)))''','PlayerPawn')
write(lever,'CanInteract','(bind allowed (CallFunction|CanSixHold :PlayerPawn Instigator)) (return allowed)','Instigator')
write(lever,'GetInteractInfo','(return "Hold to raise the relic cage" 0.0 (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator2"))','Instigator')
write(lever,'BeginHold',f'''
 (if (Networking|HasAuthority) (bind allowed (CallFunction|CanSixHold :PlayerPawn PlayerPawn))
  (if (and allowed (or (not {V('Held')}) (== {V('Holder')} PlayerPawn)))
   (bind pawn (Utilities|Casting|CastToPawn :Object PlayerPawn)
    (:then {S('Holder','pawn')} {S('Held','true')}) (:CastFailed))))''','PlayerPawn')
write(lever,'EndHold',f'(if (and (Networking|HasAuthority) (== {V("Holder")} PlayerPawn)) {clear_holder} {S("Held","false")})','PlayerPawn')
write(lever,'IsHeld',f'(return {V("Held")})')
write(lever,'RefreshLever',f'''
 (if (Networking|HasAuthority) (bind allowed (CallFunction|CanSixHold :PlayerPawn {V('Holder')}))
  (if (not allowed) {S('Holder','"None"')} {S('Held','false')}))''')
fn(lever,'ResetSixLever',[('Index','int'),('Attempt','int')])
write(lever,'ResetSixLever',f'(if (Networking|HasAuthority) {clear_holder} {S("Held","false")})','Index Attempt')
write(lever,'BeginLever','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshLever" :Time 0.05 :bLooping true)')
# event helper expects matching parameter names: dedicated adapters preserve interface Instigator.
fn(lever,'LeverBeginAdapter',[('Instigator',ue.Actor.static_class())]);fn(lever,'LeverEndAdapter',[('Instigator',ue.Actor.static_class())])
write(lever,'LeverBeginAdapter','(CallFunction|BeginHold :PlayerPawn Instigator)','Instigator');write(lever,'LeverEndAdapter','(CallFunction|EndHold :PlayerPawn Instigator)','Instigator')
for event_name,handler,params in [('InteractBegin','LeverBeginAdapter',['Instigator']),('InteractEnd','LeverEndAdapter',['Instigator']),('ReceiveBeginPlay','BeginLever',[]),('ResetForRound','ResetSixLever',['Index','Attempt'])]:
 # This is a duplicated old gauntlet lever. Replace only these copied entry
 # links, preserving unrelated nodes and all inherited interface signatures.
 entry=BP.add_event(lever,event_name)
 for target in list(entry.find_then_pin().list_connected_pins()):
  entry.find_then_pin().break_single_pin_link(target)
 event(lever,event_name,handler,params)
save(lever)
write(cage,'IsRaised',f'(return (or {V("Raised")} {V("Latched")}))')
write(cage,'LatchOpen',f'(if (Networking|HasAuthority) {S("Latched","true")} {S("Raised","true")} (CallFunction|ApplyCage))')
write(cage,'ApplyCage',f'(Transformation|SetRelativeLocation :self {V("CageMesh")} :NewLocation (Utilities|Struct|MakeVector :Z (select (or {V("Raised")} {V("Latched")}) 350.0 0.0)) :bSweep false)')
fn(cage,'CageAuthorityTick')
write(cage,'CageAuthorityTick',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind row (Class|BPCoopGameState|GetScalingRow :self gs))
    {S('RequiredLevers','(select (== row "4") 2 (select (or (== row "2") (== row "3")) 1 999))')}
    {S('HeldLevers','0')}
    (for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Player/RelicChamber/BP_Lever.BP_Lever_C")
     (bind held (Class|BPLever|IsHeld :self actor))
     (if held {S('HeldLevers',f'(+ {V("HeldLevers")} 1)')}))
    {S('Raised',f'(or {V("Latched")} (>= {V("HeldLevers")} {V("RequiredLevers")}))')}) (:CastFailed)))''')
write(cage,'RefreshCage','(CallFunction|CageAuthorityTick) (CallFunction|ApplyCage)')
fn(cage,'ResetCage',[('Index','int'),('Attempt','int')])
write(cage,'ResetCage',f'(if (Networking|HasAuthority) {S("Latched","(== Index 6)")} {S("Raised","(== Index 6)")} (CallFunction|ApplyCage))','Index Attempt')
for name in ('OnRep_bRaised','OnRep_bLatched'):write(cage,name,'(CallFunction|ApplyCage)')
write(cage,'BeginCage','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshCage" :Time 0.05 :bLooping true)')
event(cage,'ResetForRound','ResetCage',['Index','Attempt']);event(cage,'ReceiveBeginPlay','BeginCage');save(cage)
RESULT={'stage':'continuous cage','scaling_fallback':'GetScalingRow -> 4 requires 2, other valid rows require 1','runtime_acceptance_pending':True}

