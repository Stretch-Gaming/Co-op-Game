"""Use published PR123 CC0 sound assets without modifying their import settings."""
import sys,importlib
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
guard()
source=ROOT/'SourceArt/PG/PG-A3'
names=['SFX_Taking_HandDrag','SFX_Taking_FloorCrack','SFX_Taking_FloorShut','SFX_Taking_LightsOut','SFX_Taking_HeadlampRoll','SFX_Taking_Sting_2D','SFX_Taker_Breath_Loop','SFX_Chase_Loop_2D','SFX_Chase_Build_Loop_2D']
assert (source/'README.md').is_file()
for name in names:
 path='/Game/Player/Art/Audio/'+name
 sound=ue.load_asset(path);assert sound,path
taking=ue.load_asset('/Game/Player/Taking/BP_TakingDirector')
fn(taking,'PlayTakingAudio')
write(taking,'PlayTakingAudio',f'''
 (if (and (>= {V('TakingStarted')} 0.0) (!= {V('VisualStarted')} {V('TakingStarted')}))
  (Utilities|IsValid :InputObject {V('Victim')}
   (:"Is Valid" (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
    (:then (if (>= (GameState|GetServerWorldTimeSeconds :self gs) {V('TakingStarted')}) {S('VisualStarted',V('TakingStarted'))}
    (if (== {V('ScareStyle')} 0)
     (Audio|PlaySoundatLocation :Sound "/Game/Player/Art/Audio/SFX_Taking_HandDrag.SFX_Taking_HandDrag" :Location {V('VictimOrigin')} :VolumeMultiplier 0.6)
     (else (if (== {V('ScareStyle')} 1)
      (Audio|PlaySoundatLocation :Sound "/Game/Player/Art/Audio/SFX_Taking_FloorCrack.SFX_Taking_FloorCrack" :Location {V('VictimOrigin')} :VolumeMultiplier 0.6)
      (else (Audio|PlaySoundatLocation :Sound "/Game/Player/Art/Audio/SFX_Taking_LightsOut.SFX_Taking_LightsOut" :Location {V('VictimOrigin')} :VolumeMultiplier 0.6))))))) (:CastFailed))) (:"Is Not Valid")))''')
fn(taking,'BeginTakingAudio');write(taking,'BeginTakingAudio','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "PlayTakingAudio" :Time 0.05 :bLooping true)')
event(taking,'ReceiveBeginPlay','BeginTakingAudio');save(taking)
chase=ue.load_asset('/Game/Player/Ghosts/BP_ChaseDirector')
var(chase,'bAudioPlaying','bool',False)
audio,handle=component(chase,'ChaseAudio',ue.AudioComponent)
audio.set_editor_property('sound',ue.load_asset('/Game/Player/Art/Audio/SFX_Chase_Loop_2D'))
audio.set_editor_property('auto_activate',False);audio.set_editor_property('volume_multiplier',.35)
fn(chase,'RefreshChaseAudio');fn(chase,'BeginChaseAudio')
write(chase,'RefreshChaseAudio',f'''
 (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
  (:then (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
   (bind active (and (== index 6) (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1"))))
   (if (and active (not {V('AudioPlaying')})) (Audio|Components|Audio|Play :self {V('ChaseAudio')}))
   (if (and (not active) {V('AudioPlaying')}) (Audio|Components|Audio|Stop :self {V('ChaseAudio')}))
   {S('AudioPlaying','active')}) (:CastFailed))''')
write(chase,'BeginChaseAudio','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshChaseAudio" :Time 0.2 :bLooping true)')
event(chase,'ReceiveBeginPlay','BeginChaseAudio');save(chase)
RESULT={'stage':'repository CC0 audio import/hooks','source_license':str(source/'README.md'),'runtime_acceptance_pending':True,'listen_pass_pending':True}
