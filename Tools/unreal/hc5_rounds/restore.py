import json,unreal
from editor_toolset.toolsets.object import ObjectTools
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
d=json.loads((HERE/'original-settings.json').read_text());ObjectTools.set_properties(unreal.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),json.dumps(d['play']));ObjectTools.set_properties(unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),json.dumps(d['performance']))
(HERE/'settings-restored.json').write_text(json.dumps({'passed':True,'values':d},indent=2))
