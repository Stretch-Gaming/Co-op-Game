import json
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
if (HERE/'original-settings.json').exists():
 saved=json.loads((HERE/'original-settings.json').read_text())
 ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),json.dumps(saved['play']))
 ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),json.dumps(saved['performance']))
(HERE/'settings-restored.json').write_text(json.dumps({'restored':True,'saved_config':False}))
