import json,os,unreal as ue
from pathlib import Path
from editor_toolset.toolsets.object import ObjectTools
assert Path(ue.Paths.project_dir()).resolve()==ROOT
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
original=json.loads((HERE/'original-settings.json').read_text())
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),json.dumps(original['play']))
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),json.dumps(original['performance']))
report={'pid':os.getpid(),'engine':ue.SystemLibrary.get_engine_version(),'project':str(ROOT),'settings_restored':True,'pie_stopped':True,'dirty_content':[p.get_path_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()],'dirty_maps':[p.get_path_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()]}
(HERE/'primary-editor-cleanup.json').write_text(json.dumps(report,indent=2))
