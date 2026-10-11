"""Primary-run bounded threats in rounds1..5. Existing Ghost/Chase are read-only.

First run declares/builds; primary adds BPI_RoundReset to the new director,
then reruns interfaces_ready=true and re-places the owned PG test map.
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from authoring import *
from editor_toolset.toolsets.data_table import DataTableTools as DT
guard()
layout=json.loads((ROOT/'Tools/unreal/six_round/world/positions.json').read_text())
ghost=ue.load_asset('/Game/Player/Ghosts/BP_Ghost');table=ue.load_asset('/Game/Player/DT_GhostScaling');assert ghost and table
rows=json.loads(DT.get_rows(table,['2','3','4']))
for row_name,data in rows.items():
 fields={name.lower():value for name,value in data.items()}
 assert 'ghostcount' in fields and 0<int(float(fields['ghostcount']))<=2,(row_name,'Official bounded room GhostCount must be1or2')
assert set(rows)=={'2','3','4'}
bp=create('/Game/Player/Ghosts/BP_RoundGhostDirector',ue.Actor.static_class())
BP.get_default_object(bp).set_editor_properties({'replicates':True,'always_relevant':True,'replicate_movement':False})
for name,kind,value,rep in [('ActiveRound','int',0,True),('SpawnedAttempt','int',-1,False),('SpawnedCount','int',0,True)]:var(bp,name,kind,value,replicated=rep)
var(bp,'OwnedThreats',ue.Actor.static_class(),array=True)
var(bp,'SpawnedSlots','int',array=True,replicated=True)
for stage,key in [('First','first_routes'),('Second','second_routes')]:
 routes={int(route['ColorSlot']):route for route in layout[key]};assert set(routes)=={0,1,2,3}
 for slot in range(4):
  nodes=routes[slot]['nodes'];assert len(nodes)>=4
  # Near the later path, separated from its protected checkpoint entrance.
  point=list(nodes[-2]);point[2]+=100
  var(bp,stage+'Threat'+str(slot),'Vector',ue.Vector(*point),editable=True)
room_centers={1:[0,0,0],3:layout['meeting']['center'],5:layout['relic']['center']}
for index,center in room_centers.items():
 for side in (0,1):
  point=[center[0]+(-1000 if side==0 else 1000),center[1]+650,center[2]+100]
  var(bp,'Room'+str(index)+'Threat'+str(side),'Vector',ue.Vector(*point),editable=True)
for name in ('ClearRoundThreats','SpawnRoomThreats','SpawnRoundThreats','RefreshRoundThreats','BeginRoundThreats','EndRoundThreats'):fn(bp,name)
fn(bp,'GetRoomThreatCount',outputs=[('Count','int')])
fn(bp,'SpawnPathThreat',[('Participant',ue.Actor.static_class())])
fn(bp,'SpawnThreatAt',[('Location','Vector')])
fn(bp,'ResetRoundThreats',[('Index','int'),('Attempt','int')])
write(bp,'GetRoomThreatCount','''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (bind data (Utilities|GetDataTableRow :DataTable "/Game/Player/DT_GhostScaling.DT_GhostScaling" :RowName (Class|BPCoopGameState|GetScalingRow :self gs))
   (:then (bind (count speed damage levers) (Utilities|Struct|BreakSGhostScaling :S_GhostScaling data))
    (return (Math|Integer|Clamp(Integer) :Value (Math|Float|Truncate :A count) :Min 0 :Max 2))) (:RowNotFound (return 0)))) (:CastFailed (return 0)))''')
write(bp,'ClearRoundThreats',f'''
 (if (Networking|HasAuthority)
  (for actor {V('OwnedThreats')} (Utilities|IsValid :InputObject actor (:"Is Valid" (Actor|DestroyActor :self actor)) (:"Is Not Valid")))
  (Utilities|Array|Clear :TargetArray {V('OwnedThreats')}) (Utilities|Array|Clear :TargetArray {V('SpawnedSlots')})
  {S('SpawnedCount','0')})''')
write(bp,'SpawnThreatAt',f'''
 (if (Networking|HasAuthority)
  (bind spawned (Game|SpawnActorfromClass :Class "/Game/Player/Ghosts/BP_Ghost.BP_Ghost_C" :SpawnTransform (Math|Transform|MakeTransform :Location Location) :CollisionHandlingOverride "AlwaysSpawn")
   (:then (Utilities|IsValid :InputObject spawned (:"Is Valid" (Utilities|Array|Add :TargetArray {V('OwnedThreats')} :NewItem spawned) {S('SpawnedCount',f'(+ {V("SpawnedCount")} 1)')}) (:"Is Not Valid")))))''','Location')
write(bp,'SpawnRoomThreats',f'''
 (bind count (CallFunction|GetRoomThreatCount))
 (for i (range count)
  (if (== {V('ActiveRound')} 1) (CallFunction|SpawnThreatAt :Location (select (== i 0) {V('Room1Threat0')} {V('Room1Threat1')})))
  (if (== {V('ActiveRound')} 3) (CallFunction|SpawnThreatAt :Location (select (== i 0) {V('Room3Threat0')} {V('Room3Threat1')})))
  (if (== {V('ActiveRound')} 5) (CallFunction|SpawnThreatAt :Location (select (== i 0) {V('Room5Threat0')} {V('Room5Threat1')}))))''')
first=f'(select (== slot 0) {V("FirstThreat0")} (select (== slot 1) {V("FirstThreat1")} (select (== slot 2) {V("FirstThreat2")} {V("FirstThreat3")})))'
second=f'(select (== slot 0) {V("SecondThreat0")} (select (== slot 1) {V("SecondThreat1")} (select (== slot 2) {V("SecondThreat2")} {V("SecondThreat3")})))'
write(bp,'SpawnPathThreat',f'''
 (if (Networking|HasAuthority)
  (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object Participant)
   (:then (bind health (Utilities|Casting|CastToAC_Health :Object (Actor|GetComponentbyClass :self pawn :ComponentClass "/Game/Hazards/AC_Health.AC_Health_C"))
    (:then (bind dead (Class|ACHealth|IsDead :self health))
     (if (not dead) (bind ps (Utilities|Casting|CastToBP_CoopPlayerState :Object (Class|Pawn|GetPlayerState :self pawn))
      (:then (bind slot (Class|BPCoopPlayerState|GetColorSlot :self ps))
       (if (and (>= slot 0) (and (<= slot 3) (not (Utilities|Array|ContainsItem :TargetArray {V('SpawnedSlots')} :ItemToFind slot))))
        (CallFunction|SpawnThreatAt :Location (select (== {V('ActiveRound')} 2) {first} {second}))
        (Utilities|Array|Add :TargetArray {V('SpawnedSlots')} :NewItem slot))) (:CastFailed)))) (:CastFailed))) (:CastFailed)))''','Participant')
write(bp,'SpawnRoundThreats',f'''
 (if (Networking|HasAuthority)
  (bind count (CallFunction|GetRoomThreatCount))
  (if (> count 0)
   (if (or (== {V('ActiveRound')} 2) (== {V('ActiveRound')} 4))
    (for pawn (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C") (CallFunction|SpawnPathThreat :Participant pawn))
    (else (CallFunction|SpawnRoomThreats)))))''')
write(bp,'RefreshRoundThreats',f'''
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (if (and (>= index 1) (and (<= index 5) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))))
     (if (or (!= index {V('ActiveRound')}) (!= attempt {V('SpawnedAttempt')}))
      (CallFunction|ClearRoundThreats) {S('ActiveRound','index')} {S('SpawnedAttempt','attempt')} (CallFunction|SpawnRoundThreats))
     (else (CallFunction|ClearRoundThreats) {S('ActiveRound','0')} {S('SpawnedAttempt','-1')}))) (:CastFailed (CallFunction|ClearRoundThreats))))''')
write(bp,'ResetRoundThreats',f'(if (Networking|HasAuthority) (CallFunction|ClearRoundThreats) {S("ActiveRound","0")} {S("SpawnedAttempt","-1")})','Index Attempt')
write(bp,'BeginRoundThreats','(if (Networking|HasAuthority) (CallFunction|RefreshRoundThreats) (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshRoundThreats" :Time 0.2 :bLooping true))')
write(bp,'EndRoundThreats','(Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshRoundThreats") (CallFunction|ClearRoundThreats)')
event(bp,'ReceiveBeginPlay','BeginRoundThreats');event(bp,'ReceiveEndPlay','EndRoundThreats')
if ARGS.get('interfaces_ready'):
 assert ue.SystemLibrary.does_implement_interface(BP.get_default_object(bp),ue.load_asset('/Game/Core/BPI_RoundReset').generated_class())
 event(bp,'ResetForRound','ResetRoundThreats',['Index','Attempt'])
save(bp)
RESULT={'new_asset':'/Game/Player/Ghosts/BP_RoundGhostDirector','writes':['/Game/Player/Ghosts/BP_RoundGhostDirector'],'official_scaling_rows_readonly':rows,'rooms':'GhostCount from official table, bounded at2','paths':'one per actual living unique ColorSlot, later first/second path point from world manifest','lifecycle':'server only, once per index+attempt; clear on nonPlaying/endPlay/enter6; BPI_RoundReset handler after primary interface setup','interfaces_ready':bool(ARGS.get('interfaces_ready')),'existing_parent_contract_evidence':'Saved/SixRound/bootstrap-probe.json has no RoundIndex on Ghost; existing parent UpdateTarget/health/light/move untouched','runtime_acceptance_pending':True}
(QUEUE/'round-ghost-authoring.json').write_text(json.dumps(RESULT,indent=2))
