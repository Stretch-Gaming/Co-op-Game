import json,unreal
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
packages=list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
owned=lambda p:p in ['/Game/Puzzles/BP_Checkpoint','/Game/Puzzles/BP_RoundStart'] or p.startswith(('/Game/Puzzles/Rounds/','/Game/Puzzles/Test/HC5/'))
ours=[p for p in packages if owned(p.get_path_name())]
others=[p.get_path_name() for p in packages if not owned(p.get_path_name())]
if ours:assert unreal.EditorLoadingAndSavingUtils.save_packages(ours,False)
(HERE/'owned-save.json').write_text(json.dumps({'passed':True,'saved':[p.get_path_name() for p in ours],'unowned_dirty_left_unsaved':others},indent=2))
