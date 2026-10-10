import unreal as ue
editor=ue.get_editor_subsystem(ue.AssetEditorSubsystem)
for path in ['/Game/Player/S_GhostScaling','/Game/Hazards/S_HazardScaling','/Game/Core/BP_CoopCharacter','/Game/Core/BP_CoopPlayerController']:
 editor.close_all_editors_for_asset(ue.load_asset(path))
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True) if ue.GameplayStatics.get_game_mode(w))
pc=next(pc for pc in ue.ObjectIterator(ue.PlayerController) if pc.get_world()==world and pc.is_local_controller() and pc.is_primary_player())
ue.SystemLibrary.execute_console_command(world,'Shot SHOWUI',pc)
RESULT={'game_screen_capture_requested':True}
