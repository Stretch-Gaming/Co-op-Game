import json,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(ARGS.get('map','/Game/Puzzles/Test/HC5/L_HC5_Rounds'))
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
performance=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
if not (HERE/'original-settings.json').exists():
 (HERE/'original-settings.json').write_text(json.dumps({'play':json.loads(ObjectTools.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess'])),'performance':json.loads(ObjectTools.get_properties(performance,['bThrottleCPUWhenNotForeground']))}))
ObjectTools.set_properties(settings,json.dumps({'PlayNetMode':ARGS.get('mode','PIE_Client'),'PlayNumberOfClients':ARGS['clients'],'RunUnderOneProcess':True}))
ObjectTools.set_properties(performance,json.dumps({'bThrottleCPUWhenNotForeground':False}))

