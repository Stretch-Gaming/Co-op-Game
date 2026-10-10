import sys
import importlib
sys.path.insert(0,str(HERE))
import authoring
importlib.reload(authoring)
from authoring import *
guard()
if ARGS.get('resume'):
    original_write=write
    def write(bp,name,body,parameters=''):
        if name not in ('CountLocalControllers','CanChangeLocalParty'):
            return original_write(bp,name,body,parameters)
pc=ue.load_asset('/Game/Core/BP_CoopPlayerController')
var(pc,'LocalControllerCount','int',0)
fn(pc,'CountLocalControllers',outputs=[('Count','int')])
write(pc,'CountLocalControllers',f'''
 {S('LocalControllerCount','0')}
 (for controller (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopPlayerController.BP_CoopPlayerController_C")
  (if (Pawn|IsLocalPlayerController :self controller) {S('LocalControllerCount',f'(+ {V("LocalControllerCount")} 1)')}))
 (return {V('LocalControllerCount')})''')
fn(pc,'CanChangeLocalParty',outputs=[('Allowed','bool')])
write(pc,'CanChangeLocalParty','''
 (if (and (Networking|HasAuthority) (and (Pawn|IsLocalPlayerController) (Game|Player|IsPrimaryPlayer)))
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then
    (bind (index phase attempt deadline row) (Utilities|Struct|BreakSRoundState (Class|BPCoopGameState|GetRoundState :self gs)))
    (return (or (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2"))))) (:CastFailed (return false)))
  (else (return false)))''')
write(pc,'HostAddLocalPlayer','''
 (if (CallFunction|CanChangeLocalParty)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
   (:then (if (and (< (CallFunction|CountLocalControllers) 2) (< (Class|BPCoopGameState|GetPlayerCount :self gs) 4))
    (Game|CreateLocalPlayer :ControllerId -1 :bSpawnPlayerController true))) (:CastFailed)))''')
write(pc,'HostRemoveLocalPlayer','''
 (if (CallFunction|CanChangeLocalParty)
  (for controller (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopPlayerController.BP_CoopPlayerController_C")
   (if (and (Pawn|IsLocalPlayerController :self controller) (not (Game|Player|IsPrimaryPlayer :self controller)))
    (Game|RemoveLocalPlayer :Player controller :bDestroyPawn true))))''')
save(pc)
library=ue.load_asset('/Game/Player/BPFL_SplitScreen')
if not library:
    library=ue.AssetToolsHelpers.get_asset_tools().create_asset('BPFL_SplitScreen','/Game/Player',ue.Blueprint,ue.BlueprintFunctionLibraryFactory())
    assert library
    compile_bp(library)
for name,handler in [('AddLocalPlayer','HostAddLocalPlayer'),('RemoveLocalPlayer','HostRemoveLocalPlayer')]:
    fn(library,name,inputs=[('HostController',ue.PlayerController.static_class())])
    write(library,name,f'''
     (bind pc (Utilities|Casting|CastToBP_CoopPlayerController :Object HostController)
      (:then (Class|BPCoopPlayerController|{handler} :self pc)) (:CastFailed))''','HostController')
save(pc)
save(library)
RESULT={'host_only':True,'max_local_players':2,'max_total_players':4,'allowed_phases':['Lobby','Cleared'],'owning_controller_required':True,'no_player_index_zero_lookup':True,'compiled':True,'runtime_acceptance_pending':True}
(QUEUE/'split-build.json').write_text(json.dumps(RESULT,indent=2))
