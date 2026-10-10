import json,unreal
guard()
settings=unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
assert unreal.ToolsetLibrary.set_object_properties(settings,json.dumps({'bThrottleCPUWhenNotForeground':True}))
RESULT={'dirty_content':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()], 'dirty_maps':[p.get_path_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
