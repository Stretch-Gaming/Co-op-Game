"""Cave-only six-round run state, persistent totals, existing host result restart."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round/core'))
from common import *
guard();gm=ue.load_asset('/Game/Core/BP_CoopGameMode')
write(gm,'BeginAdventure',f'''
 (if (Networking|HasAuthority)
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then (bind gs {GS} (:then
    (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site01")
     (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 0)
     (Class|BPCoopGameInstance|SetRunActive :self gi :RunActive true)
     (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected 0)
     (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable 0)
     (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Cave")
     (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Stand together on the start pad. Carry the relic home through six rounds."))
    (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")
     (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 2)
     (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Egypt")
     (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Mission complete. The host can press R to play again."))
    (Class|BPCoopGameState|SetRelicsCollected :self gs :RelicsCollected (Class|BPCoopGameInstance|GetRunPrefixCollected :self gi))
    (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Class|BPCoopGameInstance|GetRunPrefixAvailable :self gi))) (:CastFailed))) (:CastFailed)))''')
write(gm,'RefreshRelicTotals',f'''
 (if (Networking|HasAuthority)
  (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site01")
   {S('AvailableValue','0')}
   (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Relic.BP_Relic_C")
    (bind relic (Utilities|Casting|CastToBP_Relic :Object item)
     (:then (Class|BPRelic|RefreshAvailability :self relic)
      (if (or (Class|BPRelic|GetAvailable :self relic) (Class|BPRelic|GetCollected :self relic))
       {S('AvailableValue',f'(+ {V("AvailableValue")} (Class|BPRelic|GetValue :self relic))')})) (:CastFailed)))
   (for key (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C")
    {S('AvailableValue',f'(+ {V("AvailableValue")} 1)')})
   (bind gs {GS} (:then (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable {V('AvailableValue')})) (:CastFailed))))''')
save(gm);RESULT={'stage':'run_totals','runtime_acceptance_pending':True}
