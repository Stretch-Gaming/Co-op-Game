import sys
sys.path.insert(0,str(HERE))
from authoring import *
guard()
paths=['/Game/Hazards/AC_Health','/Game/Player/AC_PlayerView','/Game/Core/BP_CoopCharacter','/Game/Core/BP_CoopPlayerController','/Game/Core/BP_CoopGameInstance','/Game/Core/BP_CoopGameState']
for path in paths:
    save(ue.load_asset(path))
struct=ue.load_asset('/Game/Hazards/S_HazardScaling')
assert ue.EditorAssetLibrary.save_loaded_asset(struct,False)
RESULT={'saved':paths+['/Game/Hazards/S_HazardScaling'],'player_logic_complete':False,'reason':'Preserve primary-owned work before editor control configuration'}
(QUEUE/'player-save-checkpoint.json').write_text(json.dumps(RESULT,indent=2))
if ARGS.get('close_editor'):
    ue.SystemLibrary.quit_editor()
