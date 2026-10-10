import unreal as ue
path='/Game/Player/S_GhostScaling'
asset=ue.load_asset(path) or ue.EditorAssetLibrary.duplicate_asset('/Game/Hazards/S_HazardScaling',path)
assert asset;assert ue.EditorAssetLibrary.save_loaded_asset(asset,False)
ue.get_editor_subsystem(ue.AssetEditorSubsystem).open_editor_for_assets([asset])
RESULT={'struct_editor_open':path}
