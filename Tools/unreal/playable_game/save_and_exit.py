import unreal as ue
for path in ['/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator','/Game/Puzzles/BP_ChamberGate']:
 assert ue.EditorAssetLibrary.save_loaded_asset(ue.load_asset(path),False)
RESULT={'checkpoint_saved':True}
ue.SystemLibrary.quit_editor()
