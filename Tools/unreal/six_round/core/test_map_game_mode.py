"""Test-only GameMode child: keep Core's six-round state machine and casts,
initialize test-map totals, and return results restart to the isolated map.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
from test_map_contract import *
guard();validate_args(globals().get('ARGS',{}))
parent=ue.load_asset('/Game/Core/BP_CoopGameMode');assert parent
before={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(parent)}
bp=create(TEST_MODE,parent.generated_class());assert bp.get_path_name().split('.')[0]==TEST_MODE
for name in ('BeginAdventure','RefreshRelicTotals','RestartAdventure','TravelToResults','CompleteMap'):
 existing=next((g for g in BP.list_graphs(bp) if g.get_name()==name),None)
 graph=existing or ue.BlueprintEditorLibrary.add_function_override(bp,ue.Name(name))
 assert graph,f'Native override creation failed for {name}; never create a shadow graph'
compile_bp(bp)
write(bp,'BeginAdventure',f'''
 (if (Networking|HasAuthority)
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then (bind gs {GS} (:then
    (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")
     (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 2)
     (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Egypt")
     (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Mission complete. The host can press R to play again.")
     (else
      (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 0)
      (Class|BPCoopGameInstance|SetRunActive :self gi :RunActive true)
      (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected 0)
      (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable 0)
      (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Cave")
      (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Stand together on the start pad. Carry the relic home through six rounds.")))
    (Class|BPCoopGameState|SetRelicsCollected :self gs :RelicsCollected (Class|BPCoopGameInstance|GetRunPrefixCollected :self gi))
    (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Class|BPCoopGameInstance|GetRunPrefixAvailable :self gi))) (:CastFailed))) (:CastFailed)))''')
write(bp,'RefreshRelicTotals',f'''
 (if (and (Networking|HasAuthority) (not (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")))
  {S('AvailableValue','0')}
  (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Relic.BP_Relic_C")
   (bind relic (Utilities|Casting|CastToBP_Relic :Object item)
    (:then (Class|BPRelic|RefreshAvailability :self relic)
     (if (or (Class|BPRelic|GetAvailable :self relic) (Class|BPRelic|GetCollected :self relic))
      {S('AvailableValue',f'(+ {V("AvailableValue")} (Class|BPRelic|GetValue :self relic))')})) (:CastFailed)))
  (for key (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C") {S('AvailableValue',f'(+ {V("AvailableValue")} 1)')})
  (bind gs {GS} (:then (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable {V('AvailableValue')})) (:CastFailed)))''')
write(bp,'RestartAdventure',f'''
 (if (Networking|HasAuthority)
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then
    (Class|BPCoopGameInstance|SetRunActive :self gi :RunActive false)
    (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 0)
    (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected 0)
    (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable 0)
    (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected 0)
    (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable 0)
    (Class|BPCoopGameMode|CancelAllUses :self self)
    (Development|ExecuteConsoleCommand :Command "ServerTravel {PERSISTENT}?listen")) (:CastFailed)))''')
write(bp,'TravelToResults',f'''
 (if (and (Networking|HasAuthority) (and {V('MissionDelivered')} {V('MapTravelPending')}))
  (bind gs {GS} (:then {STATE}
   (if (and (== index 6) {EQ('phase',COMPLETE)})
    (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
     (:then
      (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 2)
      (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
      (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
      (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
      (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
      {S('MapTravelPending','false')}
      (Development|ExecuteConsoleCommand :Command "ServerTravel /Game/Maps/L_Site02?game={TEST_MODE}.BP_SixRoundTestGameMode_C?listen")) (:CastFailed)))) (:CastFailed)))''')
# The existing results coordinator requests CompleteMap on its validated host transaction.
write(bp,'CompleteMap','''
 (if (Networking|HasAuthority)
  (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")
   (CallFunction|RestartAdventure)
   (else (CallFunction|TravelToResults))))''')
save(bp)
assert {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(parent)}==before,'Core parent graph changed'
RESULT={'writes':[TEST_MODE],'inherits_core_state_machine':True,'results_map_read_only':'/Game/Maps/L_Site02','results_game_override':TEST_MODE,'restart_target':PERSISTENT,'runtime_acceptance_pending':True}
