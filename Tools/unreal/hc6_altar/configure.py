import pathlib,json,unreal
from editor_toolset.toolsets.object import ObjectTools
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
opts=json.loads((ROOT/'Saved/HC6Altar/options.json').read_text(encoding='utf-8-sig'))
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Puzzles/Test/HC6_Altar/L_HC6_Altar')
settings=unreal.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf=unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
if not (HERE/'original-settings.json').exists():(HERE/'original-settings.json').write_text(json.dumps({'play':json.loads(ObjectTools.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess','ServerPort'])),'performance':json.loads(ObjectTools.get_properties(perf,['bThrottleCPUWhenNotForeground']))}))
ObjectTools.set_properties(settings,json.dumps({'PlayNetMode':opts.get('mode','PIE_Client'),'PlayNumberOfClients':opts['clients'],'RunUnderOneProcess':True,'ServerPort':17792}))
ObjectTools.set_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
RESULT=opts

