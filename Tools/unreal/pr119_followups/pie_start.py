"""Open ARGS['map'], set Play As Client with ARGS['clients'] players, and request PIE."""
import json
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.object import ObjectTools

editor = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
editor.editor_set_game_view(False)
world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
if world.get_outermost().get_name() != ARGS['map']:
    assert editor.load_level(ARGS['map'])
play = ue.load_object(None, '/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf = ue.load_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings')
with toolset_registry.tool_raising_exceptions():
    ObjectTools.set_properties(play, json.dumps({'PlayNetMode': 'PIE_Client', 'PlayNumberOfClients': ARGS['clients'], 'RunUnderOneProcess': True}))
    ObjectTools.set_properties(perf, json.dumps({'bThrottleCPUWhenNotForeground': False}))
    applied = ObjectTools.get_properties(play, ['PlayNetMode', 'PlayNumberOfClients', 'RunUnderOneProcess'])
editor.editor_request_begin_play()
RESULT = {'map': ARGS['map'], 'applied': str(applied)}
