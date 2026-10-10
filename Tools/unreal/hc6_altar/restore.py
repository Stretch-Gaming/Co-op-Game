import json,pathlib,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
HERE=pathlib.Path(__file__).parent;assert not ue.EditorLevelLibrary.get_pie_worlds(True)
original=json.loads((HERE/'original-settings.json').read_text())
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),json.dumps(original['play']))
ObjectTools.set_properties(ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),json.dumps(original['performance']))
RESULT={'session_settings_restored':True,'project_config_saved':False}
