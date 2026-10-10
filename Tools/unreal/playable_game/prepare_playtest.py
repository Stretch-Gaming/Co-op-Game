import json
import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings');performance=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
if not (QUEUE/'original-play-settings.json').exists():(QUEUE/'original-play-settings.json').write_text(json.dumps({'play':json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess'])),'performance':json.loads(OBJ.get_properties(performance,['bThrottleCPUWhenNotForeground']))}))
OBJ.set_properties(settings,json.dumps({'PlayNetMode':ARGS.get('mode','PIE_Client'),'PlayNumberOfClients':ARGS.get('players',2),'RunUnderOneProcess':True}))
OBJ.set_properties(performance,json.dumps({'bThrottleCPUWhenNotForeground':False}))
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(ARGS.get('map','/Game/Maps/L_Site01'))
RESULT={'settings':json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']))}
