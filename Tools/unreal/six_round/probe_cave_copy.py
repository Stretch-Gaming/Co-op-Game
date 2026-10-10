import unreal as ue
path='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
obj=ue.load_asset(path)
RESULT={'copy':str(obj),'path':obj.get_path_name() if obj else None,'package':obj.get_outermost().get_name() if obj else None,
        'level_save_api':[name for name in dir(ue.LevelEditorSubsystem) if 'sav' in name],
        'loading_save_api':[name for name in dir(ue.EditorLoadingAndSavingUtils) if 'sav' in name]}
if hasattr(ue.EditorLoadingAndSavingUtils,'save_map'):RESULT['save_map_doc']=ue.EditorLoadingAndSavingUtils.save_map.__doc__
