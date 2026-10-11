import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
gm=ue.load_asset('/Game/Core/BP_CoopGameMode');pc=ue.load_asset('/Game/Core/BP_CoopPlayerController');co=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator')
for name in ('BeginAdventure','AdvanceAdventure','RestartAdventure'):fn(gm,name)
write(gm,'BeginAdventure','''
 (if (Networking|HasAuthority)
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then
    (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
     (:then
      (bind level (Game|GetCurrentLevelName :bRemovePrefixString true))
      (if (Utilities|String|EqualExactly(String) :A level :B "L_Site01")
       (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 0)
       (Class|BPCoopGameInstance|SetRunActive :self gi :RunActive true)
       (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected 0)
       (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable 0)
       (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Cave")
       (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Stand together on the start pad. Solve three chambers, then escape."))
      (if (Utilities|String|EqualExactly(String) :A level :B "L_Maze")
       (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 1)
       (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Maze")
       (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Follow the tunnels to the relic chamber. Shift: brace. Jump beside a braced teammate: boost."))
      (if (Utilities|String|EqualExactly(String) :A level :B "L_Site02")
       (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 2)
       (Class|BPCoopGameState|SetAreaName :self gs :AreaName "Egypt")
       (Class|BPCoopGameState|SetAdventureInstruction :self gs :AdventureInstruction "Adventure complete. The host can press R to play again."))
      (Class|BPCoopGameState|SetRelicsCollected :self gs :RelicsCollected (Class|BPCoopGameInstance|GetRunPrefixCollected :self gi))
      (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Class|BPCoopGameInstance|GetRunPrefixAvailable :self gi))) (:CastFailed))) (:CastFailed)))''')
write(gm,'AdvanceAdventure','''
 (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
  (:then
   (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then
     (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
     (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
     (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected (Class|BPCoopGameState|GetRelicsCollected :self gs))
     (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable (Class|BPCoopGameState|GetRelicsAvailable :self gs))
     (CallFunction|CancelAllUses)
     (CallFunction|SetRoundPhase :Phase "NewEnumerator4")
     (Development|ExecuteConsoleCommand :Command (select (== (Class|BPCoopGameInstance|GetRunStage :self gi) 0) "ServerTravel /Game/Maps/L_Maze?listen" "ServerTravel /Game/Maps/L_Site02?listen"))) (:CastFailed))) (:CastFailed))''')
write(gm,'RestartAdventure','''
 (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
  (:then
   (Class|BPCoopGameInstance|SetRunActive :self gi :RunActive false)
   (Class|BPCoopGameInstance|SetRunStage :self gi :RunStage 0)
   (Class|BPCoopGameInstance|SetRunPrefixCollected :self gi :RunPrefixCollected 0)
   (Class|BPCoopGameInstance|SetRunPrefixAvailable :self gi :RunPrefixAvailable 0)
   (Class|BPCoopGameInstance|SetRelicsCollected :self gi :RelicsCollected 0)
   (Class|BPCoopGameInstance|SetRelicsAvailable :self gi :RelicsAvailable 0)
   (CallFunction|CancelAllUses)
   (Development|ExecuteConsoleCommand :Command "ServerTravel /Game/Maps/L_Site01?listen")) (:CastFailed))''')
write(gm,'CompleteMap','''
 (if (Networking|HasAuthority)
  (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")
   (CallFunction|RestartAdventure)
   (else (CallFunction|AdvanceAdventure))))''')
write(gm,'RefreshRelicTotals','''
 (if (Networking|HasAuthority)
  (bind gi (Utilities|Casting|CastToBP_CoopGameInstance :Object (Game|GetGameInstance))
   (:then
    (if (!= (Class|BPCoopGameInstance|GetRunStage :self gi) 2)
     (Variables|Default|SetAvailableValue (Class|BPCoopGameInstance|GetRunPrefixAvailable :self gi))
     (for item (Actor|GetAllActorsOfClass :ActorClass "/Game/Puzzles/BP_Relic.BP_Relic_C")
      (bind relic (Utilities|Casting|CastToBP_Relic :Object item)
       (:then (Class|BPRelic|RefreshAvailability :self relic)
        (if (or (Class|BPRelic|GetAvailable :self relic) (Class|BPRelic|GetCollected :self relic))
         (Variables|Default|SetAvailableValue (+ (Variables|Default|GetAvailableValue) (Class|BPRelic|GetValue :self relic))))) (:CastFailed)))
     (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
      (:then (Class|BPCoopGameState|SetRelicsAvailable :self gs :RelicsAvailable (Variables|Default|GetAvailableValue))) (:CastFailed)))) (:CastFailed)))''')
event(gm,'ReceiveBeginPlay','BeginAdventure')
fn(co,'StartAdventureCoordinator');fn(co,'PollAdventureResults')
write(co,'PollAdventureResults','(bind restored (CallFunction|RestoreResults)) (if restored (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "PollAdventureResults"))')
write(co,'StartAdventureCoordinator','''
 (if (and (Networking|HasAuthority) (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02"))
  (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "PollAdventureResults" :Time 0.2 :bLooping true))''')
event(co,'ReceiveBeginPlay','StartAdventureCoordinator')
results=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults');component(pc,'AdventureResults',results.generated_class())
write(pc,'RequestRunRestart','''
 (if (and (Networking|HasAuthority) (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer)))
  (bind results (Utilities|Casting|CastToAC_RunResults :Object (Components|GetComponentbyClass :ComponentClass "/Game/Puzzles/UI/Results/AC_RunResults.AC_RunResults_C"))
   (:then (Class|ACRunResults|RequestLocalRestart :self results)) (:CastFailed)))''')
# The playable route uses its own entrances and puzzles.
write(pc,'HC1SetupDebugInput','')
for bp in (gm,pc,co):save(bp)
RESULT={'route':['L_Site01','L_Maze','L_Site02','L_Site01'],'cumulative_relics':True,'host_results_restart':True,'runtime_acceptance_pending':True}
(QUEUE/'adventure-route-build.json').write_text(json.dumps(RESULT,indent=2))

