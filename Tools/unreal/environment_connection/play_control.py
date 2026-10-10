import json,unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings');perf=ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings');editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
action=ARGS['action']
if action=='prepare':
 assert not ue.EditorLevelLibrary.get_pie_worlds(True)
 p=OUTPUT/'original-preferences.json'
 if not p.exists():p.write_text(json.dumps({'play':json.loads(OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess'])),'performance':json.loads(OBJ.get_properties(perf,['bThrottleCPUWhenNotForeground']))}))
 OBJ.set_properties(settings,json.dumps({'PlayNetMode':ARGS.get('mode','PIE_Client'),'PlayNumberOfClients':ARGS.get('players',2),'RunUnderOneProcess':True}));OBJ.set_properties(perf,json.dumps({'bThrottleCPUWhenNotForeground':False}))
 assert editor.load_level('/Game/Maps/L_ConnectedRoomMaze')
elif action=='start':editor.editor_request_begin_play()
elif action=='stop':editor.editor_request_end_play()
elif action=='restore':
 assert not ue.EditorLevelLibrary.get_pie_worlds(True)
 j=json.loads((OUTPUT/'original-preferences.json').read_text());OBJ.set_properties(settings,json.dumps(j['play']));OBJ.set_properties(perf,json.dumps(j['performance']))
RESULT={'action':action,'pie':[w.get_path_name()for w in ue.EditorLevelLibrary.get_pie_worlds(True)]}
