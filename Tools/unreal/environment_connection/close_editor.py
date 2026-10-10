import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
RESULT={'exit_requested':True,'protected_assets_saved':False}
ue.SystemLibrary.quit_editor()
