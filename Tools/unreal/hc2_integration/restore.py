import unreal as ue,json
from editor_toolset.toolsets.object import ObjectTools
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
original=json.loads((HERE/'original-settings.json').read_text())
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),json.dumps(original['play']))
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),json.dumps(original['performance']))
(HERE/'settings-restored.json').write_text(json.dumps({'passed':True,'settings':original},indent=2))
