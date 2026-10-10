import json,pathlib,unreal
guard()
root=pathlib.Path(__file__).resolve().parents[3]
options=json.loads((root/'Saved/HC4/test_options.json').read_text(encoding='utf-8-sig'))
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert editor.load_level(options.get('map','/Game/Puzzles/Test/HC4/L_HC4_Carrying'))
settings=unreal.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
guard()
assert unreal.ToolsetLibrary.set_object_properties(settings,json.dumps({'PlayNetMode':'PIE_Client' if options.get('net','client')=='client' else 'PIE_ListenServer','PlayNumberOfClients':options['players'],'RunUnderOneProcess':True,'ServerPort':17774,'NewWindowWidth':800,'NewWindowHeight':450}))
perf=unreal.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
assert unreal.ToolsetLibrary.set_object_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
RESULT={'settings':unreal.ToolsetLibrary.get_object_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess','ServerPort'])}
