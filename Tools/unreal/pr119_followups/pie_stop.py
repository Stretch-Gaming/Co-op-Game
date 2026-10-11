"""Request the end of PIE; with ARGS['restore'], turn background CPU throttling back on."""
import json
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.object import ObjectTools

# A stop requested while no PIE is running stays queued and ends the next session, so only ask while one runs.
if ue.EditorLevelLibrary.get_pie_worlds(True):
    ue.get_editor_subsystem(ue.LevelEditorSubsystem).editor_request_end_play()
if ARGS.get('restore'):
    with toolset_registry.tool_raising_exceptions():
        ObjectTools.set_properties(ue.load_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings'), json.dumps({'bThrottleCPUWhenNotForeground': True}))
RESULT = 'stop requested'
