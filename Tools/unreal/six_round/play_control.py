"""Configure only this task editor; restore transient play preferences after QA."""
import json,unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings')
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
action=ARGS['action']
if action=='prepare':
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    record=QUEUE/'original-play-preferences.json'
    if not record.exists():record.write_text(json.dumps({'play':json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess'])),'performance':json.loads(OBJ.get_properties(perf,['bThrottleCPUWhenNotForeground']))}))
    OBJ.set_properties(settings,json.dumps({'PlayNetMode':ARGS.get('mode','PIE_Client'),'PlayNumberOfClients':ARGS.get('players',2),'RunUnderOneProcess':True}))
    OBJ.set_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
    target=ARGS.get('map','/Game/Puzzles/Test/SixRound/L_SixRound_Test')
    assert target in ('/Game/Puzzles/Test/SixRound/L_SixRound_Test','/Game/Player/Test/SixRound/L_SixRound_MantleProof')
    assert editor.load_level(target)
elif action=='start':editor.editor_request_begin_play()
elif action=='stop':editor.editor_request_end_play()
elif action=='restore':
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    record=json.loads((QUEUE/'original-play-preferences.json').read_text())
    OBJ.set_properties(settings,json.dumps(record['play']));OBJ.set_properties(perf,json.dumps(record['performance']))
else:raise AssertionError(action)
RESULT={'action':action,'pie':[w.get_path_name() for w in ue.EditorLevelLibrary.get_pie_worlds(True)]}
