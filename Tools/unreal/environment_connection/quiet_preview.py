import sys,importlib,json,unreal as ue
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import *
bp=create('/Game/Puzzles/EnvironmentConnection/BP_EnvironmentPreview',ue.Actor.static_class())
for n in ('StartPreview','ClearPuzzleOverlay'):fn(bp,n)
write(bp,'ClearPuzzleOverlay','''(for actor (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C") (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object actor) (:then (if (Pawn|IsLocallyControlled :self pawn) (bind hud (Utilities|Casting|CastToAC_HCA3HUD :Object (Components|GetComponentbyClass :self pawn :ComponentClass "/Game/Puzzles/UI/HCA3/AC_HCA3HUD.AC_HCA3HUD_C")) (:then (Class|ACHCA3HUD|StopHUD :self hud)) (:CastFailed)))) (:CastFailed)))''')
write(bp,'StartPreview','(Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ClearPuzzleOverlay" :Time 0.5 :bLooping true)')
event(bp,'ReceiveBeginPlay','StartPreview');save(bp)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();sub=ue.GameplayStatics.get_streaming_level(world,'L_ConnectedMaze');ue.EditorLevelUtils.make_level_current(sub)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
if not [a for a in actors.get_all_level_actors()if a.get_actor_label()=='Environment_Preview']:
 a=actors.spawn_actor_from_class(bp.generated_class(),ue.Vector(0,0,-500),ue.Rotator());assert a.get_level()==sub.get_loaded_level();a.set_actor_label('Environment_Preview');a.set_actor_hidden_in_game(True)
assert ue.EditorLoadingAndSavingUtils.save_packages([sub.get_loaded_level().get_outermost()],False)
RESULT={'environment_only_overlay':True,'original_HUD_asset_changed':False}
