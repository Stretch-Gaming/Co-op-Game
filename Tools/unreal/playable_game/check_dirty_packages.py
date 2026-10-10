import unreal as ue
RESULT={'content':[p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'maps':[p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
