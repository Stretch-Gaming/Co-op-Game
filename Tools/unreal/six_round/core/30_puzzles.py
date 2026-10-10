"""Living-player zones, simultaneous meeting locks and individual path doors."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();zone=ue.load_asset('/Game/Puzzles/BP_RegroupVolume')
write(zone,'PollRegroup',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (or (and (not {V('StartsRound')}) (and (== index {V('RoundIndex')}) {EQ('phase',PLAY)}))
    (and {V('StartsRound')} (and (== index (- {V('RoundIndex')} 1)) {EQ('phase',CLEAR)})))
    {S('AllInside','true')} {S('LivingCount','0')}
    (bind inside (Collision|GetOverlappingActors))
    (for ps (Class|GameStateBase|GetPlayerArray :self gs)
     (bind pawn (PlayerState|GetPawn :self ps))
     (Utilities|IsValid :InputObject pawn (:"Is Valid"
      (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
       (:then (if (not (Class|ACHealth|IsDead :self health))
        {S('LivingCount',f'(+ {V("LivingCount")} 1)')}
        (if (not (Utilities|Array|ContainsItem :TargetArray inside :ItemToFind pawn)) {S('AllInside','false')}))) (:CastFailed {S('AllInside','false')}))) (:"Is Not Valid" {S('AllInside','false')})))
    (if (and {V('AllInside')} (> {V('LivingCount')} 0))
     (bind gm {GM} (:then
      (if {V('StartsRound')} (Class|BPCoopGameMode|StartRound :self gm :Index {V('RoundIndex')})
       (else (Class|BPCoopGameMode|ClearRound :self gm)))) (:CastFailed))))) (:CastFailed)))''')
write(zone,'BeginRegroup','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "PollRegroup" :Time 0.15 :bLooping true))')
event(zone,'ReceiveBeginPlay','BeginRegroup');save(zone)
lock=ue.load_asset('/Game/Puzzles/BP_CrystalLock')
interface(lock,'/Game/Player/Tools/BPI_Lightable')
# Signature-only interface events forward to distinct handler graphs.
fn(lock,'BeginLight',[('Source',ue.Actor.static_class())]);fn(lock,'EndLight',[('Source',ue.Actor.static_class())])
write(lock,'BeginLight',f'''
 (if (Networking|HasAuthority)
  (Utilities|IsValid :InputObject Source (:"Is Valid"
   (if {V('Brazier')}
    (bind flare (Utilities|Casting|CastToBP_Flare :Object Source)
     (:then (if (Class|BPFlare|IsActive :self flare) (Utilities|Array|AddUnique :TargetArray {V('LightSources')} :NewItem Source))) (:CastFailed))
    (else (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Source)
     (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self pawn :ComponentClass "{HEALTH}"))
      (:then (if (not (Class|ACHealth|IsDead :self health)) (Utilities|Array|AddUnique :TargetArray {V('LightSources')} :NewItem Source))) (:CastFailed))) (:CastFailed))))) (:"Is Not Valid")))''','Source')
write(lock,'EndLight',f'(if (Networking|HasAuthority) (Utilities|Array|RemoveItem :TargetArray {V("LightSources")} :Item Source))','Source')
write(lock,'ApplyLock',f'''
 (Actor|SetActorHiddenInGame :bNewHidden (not {V('Enabled')}))
 (Collision|SetActorEnableCollision :bNewActorEnableCollision {V('Enabled')})
 (Rendering|SetRenderCustomDepth :self (Variables|StaticMeshActor|GetStaticMeshComponent) :bValue {V('Lit')})''')
for n in ('OnRep_Lit','OnRep_Enabled'):write(lock,n,'(CallFunction|ApplyLock)')
write(lock,'RefreshLock',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('Enabled',f'(< {V("LockSlot")} (select {V("Brazier")} (select (== row "4") 2 1) (select (== row "2") 1 2)))')}
   {S('SourceCount','0')}
   (for source {V('LightSources')}
    (Utilities|IsValid :InputObject source (:"Is Valid"
     (if {V('Brazier')}
      (bind flare (Utilities|Casting|CastToBP_Flare :Object source)
       (:then (if (Class|BPFlare|IsActive :self flare) {S('SourceCount',f'(+ {V("SourceCount")} 1)')})) (:CastFailed))
      (else (bind health (Utilities|Casting|CastToAC_Health :Object (Components|GetComponentbyClass :self source :ComponentClass "{HEALTH}"))
       (:then (if (not (Class|ACHealth|IsDead :self health)) {S('SourceCount',f'(+ {V("SourceCount")} 1)')})) (:CastFailed))))) (:"Is Not Valid")))
   {S('Lit',f'(and {V("Enabled")} (> {V("SourceCount")} 0))')}
   (CallFunction|ApplyLock)) (:CastFailed)))''')
write(lock,'ResetLock',f'(if (Networking|HasAuthority) (Utilities|Array|Clear :TargetArray {V("LightSources")}) {S("Lit","false")} (CallFunction|ApplyLock))','Index Attempt')
write(lock,'BeginLock','(CallFunction|ApplyLock) (if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshLock" :Time 0.1 :bLooping true))')
exclusive_event(lock,'LightBegin','BeginLight',['Source']);exclusive_event(lock,'LightEnd','EndLight',['Source']);event(lock,'ResetForRound','ResetLock',['Index','Attempt']);event(lock,'ReceiveBeginPlay','BeginLock');save(lock)
# GameMode verifies every enabled lock at once, including exact required counts.
for n,k in [('MeetingLocks','int'),('MeetingNeeded','int'),('MeetingLit','int')]:var(gm:=ue.load_asset('/Game/Core/BP_CoopGameMode'),n,k,0)
fn(gm,'PollMeetingLocks')
write(gm,'PollMeetingLocks',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   (if (and (== index 3) {EQ('phase',PLAY)})
    {S('MeetingLocks','0')} {S('MeetingLit','0')}
    {S('MeetingNeeded','(select (== row "2") 2 (select (== row "3") 3 4))')}
    (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_CrystalLock.BP_CrystalLock_C")
     (bind lock (Utilities|Casting|CastToBP_CrystalLock :Object item)
      (:then (Class|BPCrystalLock|RefreshLock :self lock)
       (if (Class|BPCrystalLock|GetEnabled :self lock)
        {S('MeetingLocks',f'(+ {V("MeetingLocks")} 1)')}
        (if (Class|BPCrystalLock|GetLit :self lock) {S('MeetingLit',f'(+ {V("MeetingLit")} 1)')}))) (:CastFailed)))
    (if (and (== {V('MeetingLocks')} {V('MeetingNeeded')}) (== {V('MeetingLit')} {V('MeetingNeeded')})) (CallFunction|ClearRound)))) (:CastFailed)))''')
fn(gm,'BeginMeetingPoll');write(gm,'BeginMeetingPoll','(if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "PollMeetingLocks" :Time 0.1 :bLooping true))');event(gm,'ReceiveBeginPlay','BeginMeetingPoll');save(gm)
door=ue.load_asset('/Game/Puzzles/BP_MazeDoor');var(door,'SlotActive','bool',False);mesh='(Variables|StaticMeshActor|GetStaticMeshComponent)'
write(door,'ApplyDoor',f'(Rendering|SetVisibility :self {mesh} :bNewVisibility (not {V("Open")})) (if {V("Open")} (Collision|SetCollisionEnabled :self {mesh} :NewType "NoCollision") (else (Collision|SetCollisionEnabled :self {mesh} :NewType "QueryAndPhysics")))')
for n in ('OnRep_Open','OnRep_Used'):write(door,n,'(CallFunction|ApplyDoor)')
write(door,'RefreshDoor',f'''
 (if (Networking|HasAuthority)
  (bind gs {GS} (:then {STATE}
   {S('SlotActive','false')}
   (for state (Class|GameStateBase|GetPlayerArray :self gs)
    (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object state)
     (:then (if (== (Class|BPCoopPlayerState|GetColorSlot :self ps) {V('PathSlot')}) {S('SlotActive','true')})) (:CastFailed)))
   {S('Open',f'(or (>= index 6) (and (and (>= index 4) {V("SlotActive")}) (not {V("Used")})))')}
   (if (and (== index 4) {V('Open')})
    (for item (Collision|GetOverlappingActors)
     (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object item)
      (:then (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
       (:then (if (> (Math|Vector|DotProduct :A (- (Transformation|GetActorLocation :self pawn) (Transformation|GetActorLocation)) :B (Transformation|GetActorForwardVector)) 120.0)
        (if (== (Class|BPCoopPlayerState|GetColorSlot :self ps) {V('PathSlot')})
         {S('Used','true')} {S('Open','false')}
         (else (Transformation|SetActorLocation :self pawn :NewLocation (+ (Transformation|GetActorLocation) (* (Transformation|GetActorForwardVector) -220.0)) :bSweep false :bTeleport true))))) (:CastFailed))) (:CastFailed))))
   (CallFunction|ApplyDoor)) (:CastFailed)))''')
write(door,'ResetDoor',f'(if (and (Networking|HasAuthority) (or (== Index 3) (== Index 4))) {S("Used","false")} (CallFunction|RefreshDoor))','Index Attempt')
write(door,'BeginDoor','(CallFunction|ApplyDoor) (if (Networking|HasAuthority) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshDoor" :Time 0.1 :bLooping true))')
event(door,'ReceiveBeginPlay','BeginDoor');event(door,'ResetForRound','ResetDoor',['Index','Attempt']);save(door)
RESULT={'stage':'meeting_and_regroups','runtime_acceptance_pending':True}
